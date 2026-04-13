from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    Enum as SAEnum, JSON, ForeignKey, Text, Numeric
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from database import Base


class SubscriptionPeriod(str, enum.Enum):
    monthly = "monthly"
    yearly = "yearly"
    weekly = "weekly"
    trial = "trial"
    unknown = "unknown"


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    paused = "paused"
    trial = "trial"


class NotificationType(str, enum.Enum):
    upcoming_payment = "upcoming_payment"
    new_subscription = "new_subscription"
    price_change = "price_change"


# ── USER ──────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

    subscriptions = relationship("Subscription", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


# ── SERVICE ───────────────────────────────────────────
class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    website = Column(String, nullable=True)
    price_plans = Column(JSON, nullable=True)  # {"monthly": 199, "yearly": 1990}
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    subscriptions = relationship("Subscription", back_populates="service")


# ── BANK ──────────────────────────────────────────────
class Bank(Base):
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    bic = Column(String, nullable=True)
    sms_regex = Column(Text, nullable=True)
    push_regex = Column(Text, nullable=True)
    is_supported = Column(Boolean, default=True)

    transactions = relationship("Transaction", back_populates="bank")


# ── SUBSCRIPTION ──────────────────────────────────────
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="RUB")
    period = Column(SAEnum(SubscriptionPeriod), default=SubscriptionPeriod.monthly)
    start_date = Column(Date, nullable=True)
    next_payment_date = Column(Date, nullable=True)
    status = Column(SAEnum(SubscriptionStatus), default=SubscriptionStatus.active)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="subscriptions")
    service = relationship("Service", back_populates="subscriptions")
    transactions = relationship("Transaction", back_populates="subscription")
    notifications = relationship("Notification", back_populates="subscription")


# ── TRANSACTION ───────────────────────────────────────
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="RUB")
    merchant_name = Column(String, nullable=True)
    transaction_date = Column(DateTime, nullable=True)
    raw_text = Column(Text, nullable=True)
    image_path = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="transactions")
    subscription = relationship("Subscription", back_populates="transactions")
    bank = relationship("Bank", back_populates="transactions")


# ── NOTIFICATION ──────────────────────────────────────
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    type = Column(SAEnum(NotificationType), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="notifications")
    subscription = relationship("Subscription", back_populates="notifications")
