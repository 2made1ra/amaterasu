from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_v1.api import api_router
from app.db.base import Base
from app.db.session import engine

# Create tables for Phase 1 without Alembic for speed/simplicity
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI RAG Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Changed to False to allow wildcard origins, or we could specify ["http://localhost:3000"]
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to AI RAG Assistant API"}
