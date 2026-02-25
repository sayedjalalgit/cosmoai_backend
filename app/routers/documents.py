import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.services.auth import get_current_user
from app.services.rag_service import process_pdf, delete_user_index

router = APIRouter(prefix="/documents", tags=["documents"])
security = HTTPBearer()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_user(credentials: HTTPAuthorizationCredentials, db: Session) -> User:
    user = get_current_user(credentials.credentials, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)

    if not file.filename.endswith('.pdf') and not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files allowed")

    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10MB")

    file_id = f"{user.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, file_id)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    doc = Document(
        user_id=user.id,
        filename=file_id,
        original_name=file.filename,
        file_size=len(content),
        status="processing"
    )
    db.add(doc)
    db.commit()

    try:
        
        if file.filename.endswith('.txt'):
           with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
               text_content = f.read()
               from app.services.rag_service import process_text
               chunk_count = process_text(text_content, user.id)

        else:
            chunk_count = process_pdf(file_path, user.id)       

        
        doc.chunk_count = chunk_count
        doc.status = "ready"
        db.commit()
    except Exception as e:
        doc.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    return {
        "id": doc.id,
        "filename": file.filename,
        "chunks": chunk_count,
        "status": "ready"
    }

@router.get("/")
def get_documents(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)
    docs = db.query(Document).filter(
        Document.user_id == user.id
    ).order_by(Document.created_at.desc()).all()
    return docs

@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = get_user(credentials, db)
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = os.path.join(UPLOAD_DIR, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(doc)
    db.commit()

    remaining = db.query(Document).filter(Document.user_id == user.id).count()
    if remaining == 0:
        delete_user_index(user.id)

    return {"status": "deleted"}