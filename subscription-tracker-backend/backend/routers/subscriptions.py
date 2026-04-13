from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, Subscription, Service, SubscriptionStatus, SubscriptionPeriod
from schemas import SubscriptionResponse, SubscriptionUpdate
from routers.auth import get_current_user

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("/", response_model=list[SubscriptionResponse])
def list_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subs = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .all()
    )
    result = []
    for sub in subs:
        service_name = None
        if sub.service_id:
            svc = db.query(Service).filter(Service.id == sub.service_id).first()
            if svc:
                service_name = svc.name
        result.append(
            SubscriptionResponse(
                id=sub.id,
                service_name=service_name,
                amount=sub.amount,
                currency=sub.currency,
                period=sub.period.value if sub.period else "unknown",
                start_date=sub.start_date,
                next_payment_date=sub.next_payment_date,
                status=sub.status.value if sub.status else "active",
                created_at=sub.created_at,
            )
        )
    return result


@router.put("/{sub_id}", response_model=SubscriptionResponse)
def update_subscription(
    sub_id: int,
    data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(Subscription).filter(
        Subscription.id == sub_id,
        Subscription.user_id == current_user.id,
    ).first()
    if not sub:
        raise HTTPException(404, "Subscription not found")

    if data.amount is not None:
        sub.amount = data.amount
    if data.period is not None:
        sub.period = SubscriptionPeriod(data.period)
    if data.status is not None:
        sub.status = SubscriptionStatus(data.status)
    if data.next_payment_date is not None:
        sub.next_payment_date = data.next_payment_date

    db.commit()
    db.refresh(sub)

    service_name = None
    if sub.service_id:
        svc = db.query(Service).filter(Service.id == sub.service_id).first()
        if svc:
            service_name = svc.name

    return SubscriptionResponse(
        id=sub.id,
        service_name=service_name,
        amount=sub.amount,
        currency=sub.currency,
        period=sub.period.value,
        start_date=sub.start_date,
        next_payment_date=sub.next_payment_date,
        status=sub.status.value,
        created_at=sub.created_at,
    )


@router.delete("/{sub_id}")
def cancel_subscription(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(Subscription).filter(
        Subscription.id == sub_id,
        Subscription.user_id == current_user.id,
    ).first()
    if not sub:
        raise HTTPException(404, "Subscription not found")
    sub.status = SubscriptionStatus.cancelled
    db.commit()
    return {"status": "cancelled", "id": sub_id}
