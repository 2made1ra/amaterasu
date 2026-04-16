from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, chat, chat_sessions, documents

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(chat_sessions.router, prefix="/chat-sessions", tags=["chat-sessions"])
