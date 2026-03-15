from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, chat, admin, documents
import app.models.user
import app.models.conversation
# for paymnet
from payments.router import router as payments_router

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="COSMOAI API",
    description="Private Intelligence System API",
    version="1.0.0"
)

# CORS — allows Next.js to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://89.167.100.143:3000",
        "https://cosmoai.hair",
        "https://www.cosmoai.hair",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(documents.router)
# for payment
app.include_router(payments_router)

@app.get("/")
def root():
    return {
        "app": "COSMOAI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
