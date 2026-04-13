from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


# ── Auth ──────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── OCR Result ────────────────────────────────────────
class OCRResult(BaseModel):
    raw_text: str
    confidence: float
    amount: Optional[Decimal] = None
    merchant: Optional[str] = None
    transaction_date: Optional[str] = None
    bank_name: Optional[str] = None


# ── Transaction ───────────────────────────────────────
class TransactionResponse(BaseModel):
    id: int
    amount: Decimal
    currency: str
    merchant_name: Optional[str]
    transaction_date: Optional[datetime]
    raw_text: Optional[str]
    image_path: Optional[str]
    confidence_score: Optional[float]
    subscription_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionConfirm(BaseModel):
    transaction_id: int
    amount: Decimal
    merchant_name: str
    transaction_date: Optional[str] = None
    is_subscription: bool = False
    period: Optional[str] = "monthly"


# ── Subscription ──────────────────────────────────────
class SubscriptionResponse(BaseModel):
    id: int
    service_name: Optional[str] = None
    amount: Decimal
    currency: str
    period: str
    start_date: Optional[date]
    next_payment_date: Optional[date]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionUpdate(BaseModel):
    amount: Optional[Decimal] = None
    period: Optional[str] = None
    status: Optional[str] = None
    next_payment_date: Optional[date] = None


# ── Service ───────────────────────────────────────────
class ServiceResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]
    price_plans: Optional[dict]

    class Config:
        from_attributes = True


# ── Upload response ───────────────────────────────────
class UploadResponse(BaseModel):
    transaction: TransactionResponse
    ocr_result: OCRResult
    needs_review: bool
    matched_service: Optional[ServiceResponse] = None
    subscription_id: Optional[int] = None
