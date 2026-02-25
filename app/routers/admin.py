from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.conversation import Message, TrainingData
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()

def get_admin(credentials: HTTPAuthorizationCredentials, db: Session) -> User:
    user = get_current_user(credentials.credentials, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.get("/stats")
def get_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    admin = get_admin(credentials, db)
    total_users = db.query(User).count()
    total_messages = db.query(Message).count()
    total_training = db.query(TrainingData).filter(TrainingData.approved == True).count()
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "approved_training_data": total_training,
    }

@router.get("/training-data")
def get_training_data(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    admin = get_admin(credentials, db)
    data = db.query(TrainingData).filter(
        TrainingData.approved == True,
        TrainingData.used_in_training == False
    ).limit(100).all()
    return data