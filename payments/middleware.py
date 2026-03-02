from datetime import datetime, date
from sqlalchemy.orm import Session
from fastapi import HTTPException
from payments.models import Subscription, UsageLog
from payments.config import payment_settings

PLAN_LIMITS = {
    "free":       {"messages": 20,      "documents": 1,  "models": ["llama-3.3-70b-versatile"]},
    "pro":        {"messages": 999999,  "documents": 10, "models": "all"},
    "business":   {"messages": 999999,  "documents": 50, "models": "all"},
    "enterprise": {"messages": 999999,  "documents": 999,"models": "all"},
}

def get_user_plan(user_id: str, db: Session) -> str:
    sub = db.query(Subscription).filter(
        Subscription.user_id == user_id
    ).first()

    if not sub:
        return "free"

    if sub.status != "active":
        return "free"

    if sub.current_period_end and sub.current_period_end < datetime.utcnow():
        return "free"

    return sub.plan

def check_message_limit(user_id: str, db: Session):
    plan = get_user_plan(user_id, db)
    limit = PLAN_LIMITS[plan]["messages"]

    today = date.today().isoformat()
    usage = db.query(UsageLog).filter(
        UsageLog.user_id == user_id,
        UsageLog.date == today
    ).first()

    count = usage.message_count if usage else 0

    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Message limit reached",
                "plan": plan,
                "limit": limit,
                "used": count,
                "upgrade_url": "/pricing"
            }
        )

def increment_usage(user_id: str, tokens: int, db: Session):
    today = date.today().isoformat()
    usage = db.query(UsageLog).filter(
        UsageLog.user_id == user_id,
        UsageLog.date == today
    ).first()

    if usage:
        usage.message_count += 1
        usage.token_count += tokens
    else:
        usage = UsageLog(
            user_id=user_id,
            date=today,
            message_count=1,
            token_count=tokens
        )
        db.add(usage)
    db.commit()

def get_usage_stats(user_id: str, db: Session) -> dict:
    plan = get_user_plan(user_id, db)
    limit = PLAN_LIMITS[plan]["messages"]
    today = date.today().isoformat()

    usage = db.query(UsageLog).filter(
        UsageLog.user_id == user_id,
        UsageLog.date == today
    ).first()

    used = usage.message_count if usage else 0

    return {
        "plan": plan,
        "messages_used": used,
        "messages_limit": limit,
        "messages_remaining": max(0, limit - used),
        "percentage": round((used / limit) * 100, 1) if limit < 999999 else 0
    }