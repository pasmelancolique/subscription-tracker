from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session
from typing import Optional, Tuple

from models import Service


def match_service(
    merchant_name: str,
    db: Session,
    threshold: int = 65,
) -> Optional[Tuple[Service, int]]:
    """
    Match a merchant name to a known service using fuzzy matching.
    Returns (Service, score) or None.
    """
    if not merchant_name:
        return None

    services = db.query(Service).all()
    if not services:
        return None

    # Build choices dict: {service.name: service}
    choices = {}
    for svc in services:
        choices[svc.name] = svc
        # Also add aliases from price_plans keys or common variations
        if svc.price_plans and isinstance(svc.price_plans, dict):
            for alias in svc.price_plans.get("aliases", []):
                choices[alias] = svc

    if not choices:
        return None

    # Find best match
    result = process.extractOne(
        merchant_name,
        choices.keys(),
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold,
    )

    if result:
        match_name, score, _ = result
        return choices[match_name], score

    return None


def classify_transaction(
    amount: float,
    service: Optional[Service],
) -> dict:
    """
    Classify whether a transaction is a subscription or one-time payment.
    Returns {"is_subscription": bool, "period": str, "confidence": float}
    """
    if service and service.price_plans:
        plans = service.price_plans
        amount_f = float(amount)

        for period in ["monthly", "yearly", "weekly"]:
            if period in plans:
                plan_price = float(plans[period])
                # Allow 5% tolerance for price matching
                if abs(amount_f - plan_price) / plan_price < 0.05:
                    return {
                        "is_subscription": True,
                        "period": period,
                        "confidence": 0.95,
                    }

    # Default: unknown
    return {
        "is_subscription": False,
        "period": "unknown",
        "confidence": 0.3,
    }
