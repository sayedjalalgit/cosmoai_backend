from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.conversation import Conversation, Message, TrainingData
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse, ConversationResponse
from app.services.auth import get_current_user
from app.services.groq_service import chat_with_groq
from app.services.cache import get_cached_response, set_cached_response

router = APIRouter(prefix="/chat", tags=["chat"])
security = HTTPBearer()


def get_user(credentials: HTTPAuthorizationCredentials, db: Session) -> User:
    user = get_current_user(credentials.credentials, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.post("/send", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)

    # Get or create conversation
    if request.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == user.id
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = Conversation(
            user_id=user.id,
            title=request.message[:40]
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Save user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=request.message,
        language=request.language or "auto"
    )
    db.add(user_msg)
    db.commit()

    # Check Redis cache
    cached = get_cached_response(request.message, request.language or "auto")

    if cached:
        ai_content = cached
        response_time = 0.0
        tokens = 0
    else:
        # Get conversation history
        history = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at).limit(20).all()

        messages = [{"role": m.role, "content": m.content} for m in history]

        
       # Search user documents first (RAG)
        from app.services.rag_service import search_documents

        document_context = search_documents(user.id, request.message)
        # Debug print
        print(f"DEBUG - Calling chat_with_groq with query: {request.message}")
        # Call Groq with document context and current query
        ai_content, response_time, tokens = chat_with_groq(
            messages,
            request.language or "auto",
            document_context,
            request.message
        )

        # Cache the response
        set_cached_response(
            request.message,
            request.language or "auto",
            ai_content
        )

    # Save AI message
    ai_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=ai_content,
        language=request.language or "auto",
        response_time=response_time,
        tokens_used=tokens
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    # Save to training data
    training = TrainingData(
        message_id=ai_msg.id,
        quality_score=0.0,
        approved=False
    )
    db.add(training)
    db.commit()

    return ChatResponse(
        conversation_id=conv.id,
        message=MessageResponse.model_validate(ai_msg)
    )


@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)
    convs = db.query(Conversation).filter(
        Conversation.user_id == user.id
    ).order_by(Conversation.created_at.desc()).all()
    return [ConversationResponse.model_validate(c) for c in convs]


@router.get("/conversations/{conv_id}", response_model=ConversationResponse)
def get_conversation(
    conv_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conv)


@router.post("/conversations/{conv_id}/messages/{msg_id}/rate")
def rate_message(
    conv_id: str,
    msg_id: str,
    rating: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)

    msg = db.query(Message).filter(
        Message.id == msg_id
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.rating = rating

    training = db.query(TrainingData).filter(
        TrainingData.message_id == msg_id
    ).first()
    if training:
        training.quality_score = rating / 5.0
        training.approved = rating >= 4

    db.commit()
    return {"status": "rated", "rating": rating}


@router.delete("/conversations/{conv_id}")
def delete_conversation(
    conv_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"status": "deleted"}