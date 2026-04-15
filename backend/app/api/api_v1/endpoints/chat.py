from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api import deps

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    document_id: int = None # If None, global search. If provided, local search.

class ChatResponse(BaseModel):
    answer: str

@router.post("/", response_model=ChatResponse)
def chat_with_rag(
    request: ChatRequest,
    current_user = Depends(deps.get_current_user)
):
    """
    RAG Chat Endpoint. Global or Local context depending on document_id.
    """
    try:
        from app.services import rag
    except ImportError:
        raise HTTPException(status_code=503, detail="RAG service is unavailable due to missing dependencies.")

    try:
        answer = rag.query_rag(request.query, current_user.id, request.document_id)
        return {"answer": answer}
    except rag.RagDependencyError as exc:
        raise HTTPException(status_code=503, detail=f"RAG dependencies are unavailable: {exc}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
