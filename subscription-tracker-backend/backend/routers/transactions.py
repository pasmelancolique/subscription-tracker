import os
import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models import User, Transaction, Subscription, Service, Bank, SubscriptionPeriod, SubscriptionStatus
from schemas import (
    TransactionResponse, TransactionConfirm, UploadResponse,
    OCRResult, ServiceResponse,
)
from routers.auth import get_current_user
from services.ocr import recognize_image
from services.parser import parse_ocr_text
from services.matcher import match_service, classify_transaction
import config

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate file
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    # Save file
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(config.UPLOAD_DIR, filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # OCR
    ocr_result = recognize_image(filepath)
    raw_text = ocr_result["text"]
    confidence = ocr_result["confidence"]

    # Parse structured data
    parsed = parse_ocr_text(raw_text)
    amount = parsed["amount"] or Decimal("0.00")
    merchant = parsed["merchant"]
    tx_date_str = parsed["transaction_date"]
    bank_name = parsed["bank_name"]

    # Try to find bank in DB
    bank_id = None
    if bank_name:
        bank = db.query(Bank).filter(Bank.name == bank_name).first()
        if bank:
            bank_id = bank.id

    # Parse transaction date
    tx_date = None
    if tx_date_str:
        try:
            tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d")
        except ValueError:
            pass

    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        amount=amount,
        merchant_name=merchant,
        transaction_date=tx_date,
        raw_text=raw_text,
        image_path=filename,
        confidence_score=confidence,
        bank_id=bank_id,
    )
    db.add(transaction)
    db.flush()

    # Fuzzy match with services
    needs_review = confidence < 0.9 or amount == 0
    matched_svc = None
    subscription_id = None

    if merchant:
        match_result = match_service(merchant, db)
        if match_result:
            service, score = match_result
            matched_svc = service

            # Classify transaction
            classification = classify_transaction(amount, service)

            if classification["is_subscription"] and not needs_review:
                # Auto-create subscription
                sub = Subscription(
                    user_id=current_user.id,
                    service_id=service.id,
                    amount=amount,
                    period=SubscriptionPeriod(classification["period"]),
                    start_date=tx_date.date() if tx_date else None,
                    status=SubscriptionStatus.active,
                )
                db.add(sub)
                db.flush()
                transaction.subscription_id = sub.id
                subscription_id = sub.id

    db.commit()
    db.refresh(transaction)

    return UploadResponse(
        transaction=TransactionResponse.model_validate(transaction),
        ocr_result=OCRResult(
            raw_text=raw_text,
            confidence=confidence,
            amount=amount if amount > 0 else None,
            merchant=merchant,
            transaction_date=tx_date_str,
            bank_name=bank_name,
        ),
        needs_review=needs_review,
        matched_service=ServiceResponse.model_validate(matched_svc) if matched_svc else None,
        subscription_id=subscription_id,
    )


@router.post("/confirm")
def confirm_transaction(
    data: TransactionConfirm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manual correction endpoint — ФТ-7"""
    tx = db.query(Transaction).filter(
        Transaction.id == data.transaction_id,
        Transaction.user_id == current_user.id,
    ).first()
    if not tx:
        raise HTTPException(404, "Transaction not found")

    tx.amount = data.amount
    tx.merchant_name = data.merchant_name
    if data.transaction_date:
        try:
            tx.transaction_date = datetime.strptime(data.transaction_date, "%Y-%m-%d")
        except ValueError:
            pass

    if data.is_subscription:
        # Find or match service
        match_result = match_service(data.merchant_name, db, threshold=50)
        service_id = match_result[0].id if match_result else None

        sub = Subscription(
            user_id=current_user.id,
            service_id=service_id,
            amount=data.amount,
            period=SubscriptionPeriod(data.period) if data.period else SubscriptionPeriod.monthly,
            start_date=tx.transaction_date.date() if tx.transaction_date else None,
            status=SubscriptionStatus.active,
        )
        db.add(sub)
        db.flush()
        tx.subscription_id = sub.id

    db.commit()
    return {"status": "ok", "transaction_id": tx.id}


@router.get("/", response_model=list[TransactionResponse])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(100)
        .all()
    )
    return txs
