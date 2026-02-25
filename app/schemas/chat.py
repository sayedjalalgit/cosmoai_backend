from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageCreate(BaseModel):
    content: str
    language: Optional[str] = "auto"

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    language: Optional[str]
    rating: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}

class ConversationCreate(BaseModel):
    title: Optional[str] = "New conversation"

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    messages: List[MessageResponse] = []

    model_config = {"from_attributes": True}

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    language: Optional[str] = "auto"

class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageResponse