from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import json

from app.database import get_db
from app.services.auth import get_current_user
from payments.config import payment_settings
from payments.models import Subscription, PaymentEvent
from payments.middleware import get_usage_stats, get_user_plan

router = APIRouter(prefix="/payments", tags=["payments"])
security = HTTPBearer()

def get_user(credentials: HTTPAuthorizationCredentials, db: Session):
    return get_current_user(credentials.credentials, db)

# ─── Plans Info ───────────────────────────────────────────

@router.get("/plans")
def get_plans():
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price_usd": 0,
                "price_bdt": 0,
                "messages_per_day": 20,
                "documents": 1,
                "models": "Basic",
                "features": [
                    "20 messages per day",
                    "1 document upload",
                    "Llama 3.3 model",
                    "Web search",
                ]
            },
            {
                "id": "pro",
                "name": "Pro",
                "price_usd": 9.99,
                "price_bdt": 1100,
                "messages_per_day": "Unlimited",
                "documents": 10,
                "models": "All 7 models",
                "features": [
                    "Unlimited messages",
                    "10 document uploads",
                    "All AI models",
                    "Web search",
                    "Image vision",
                    "Priority support",
                ]
            },
            {
                "id": "business",
                "name": "Business",
                "price_usd": 29.99,
                "price_bdt": 3300,
                "messages_per_day": "Unlimited",
                "documents": 50,
                "models": "All models + API",
                "features": [
                    "Everything in Pro",
                    "50 document uploads",
                    "API access",
                    "Team workspace",
                    "Analytics dashboard",
                    "Dedicated support",
                ]
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price_usd": 99.99,
                "price_bdt": 11000,
                "messages_per_day": "Unlimited",
                "documents": "Unlimited",
                "models": "All + Custom",
                "features": [
                    "Everything in Business",
                    "Unlimited documents",
                    "Private deployment",
                    "Custom model training",
                    "SLA guarantee",
                    "24/7 dedicated support",
                ]
            }
        ]
    }

# ─── Create Checkout ───────────────────────────────────────

@router.post("/checkout/{plan}")
def create_checkout(
    plan: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)

    if plan not in ["pro", "business", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid plan")

    try:
        print(f"Checkout requested for plan: {plan} by user: {user.id}")
        from payments.providers import get_payment_provider
        print("Getting payment provider...")
        provider = get_payment_provider()
        print(f"Provider: {provider}")

        result = provider.create_checkout_session(
            user_id=user.id,
            user_email=user.email,
            plan=plan,
            success_url=f"{payment_settings.FRONTEND_URL}/payment/success",
            cancel_url=f"{payment_settings.FRONTEND_URL}/pricing",
        )
        print(f"Checkout result: {result}")
        return result
    except Exception as e:
        print(f"CHECKOUT ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ─── Get Subscription ──────────────────────────────────────

@router.get("/subscription")
def get_subscription(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)
    plan = get_user_plan(user.id, db)
    usage = get_usage_stats(user.id, db)

    sub = db.query(Subscription).filter(
        Subscription.user_id == user.id
    ).first()

    return {
        "plan": plan,
        "usage": usage,
        "subscription": {
            "status": sub.status if sub else "none",
            "current_period_end": sub.current_period_end if sub else None,
            "provider": sub.provider if sub else None,
        } if sub else None
    }

# ─── Cancel Subscription ───────────────────────────────────

@router.post("/cancel")
def cancel_subscription(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)

    sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")

    try:
        from payments.providers import get_payment_provider
        provider = get_payment_provider()
        provider.cancel_subscription(sub.provider_subscription_id)
        sub.status = "cancelled"
        sub.cancelled_at = datetime.utcnow()
        db.commit()
        return {"message": "Subscription cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Webhook Handler ───────────────────────────────────────

@router.post("/webhook/{provider}")
async def handle_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    # Log the event
    event_log = PaymentEvent(
        provider=provider,
        event_type="incoming",
        payload=payload.decode(),
        processed=False
    )
    db.add(event_log)
    db.commit()

    try:
        from payments.providers import get_payment_provider
        prov = get_payment_provider()
        event = prov.handle_webhook(payload, signature)

        # Process subscription events
        if event["type"] == "checkout.session.completed":
            data = event["data"]
            user_id = int(data.get("metadata", {}).get("user_id", 0))
            plan = data.get("metadata", {}).get("plan", "pro")

            if user_id:
                sub = db.query(Subscription).filter(
                    Subscription.user_id == user_id
                ).first()

                if sub:
                    sub.plan = plan
                    sub.status = "active"
                    sub.provider_subscription_id = data.get("subscription")
                    sub.updated_at = datetime.utcnow()
                else:
                    sub = Subscription(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        plan=plan,
                        status="active",
                        provider=provider,
                        provider_subscription_id=data.get("subscription"),
                        provider_customer_id=data.get("customer"),
                        amount=data.get("amount_total", 0) / 100,
                        currency=data.get("currency", "usd"),
                    )
                    db.add(sub)
                db.commit()

        elif event["type"] == "customer.subscription.deleted":
            data = event["data"]
            sub = db.query(Subscription).filter(
                Subscription.provider_subscription_id == data.get("id")
            ).first()
            if sub:
                sub.status = "cancelled"
                sub.updated_at = datetime.utcnow()
                db.commit()

        event_log.processed = True
        db.commit()
        return {"status": "ok"}

    except Exception as e:
        return {"status": "error", "message": str(e)}