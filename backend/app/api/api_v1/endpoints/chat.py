from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.services import workspace

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    document_id: int | None = None  # If None, global search. If provided, local search.


class ChatResponse(BaseModel):
    answer: str


@router.post("/", response_model=ChatResponse)
def chat_with_rag(
    request: ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Contract search chat endpoint. Global or local context depending on document_id.
    """
    try:
        if request.document_id is None:
            result = workspace.build_workspace_query_result(db, current_user.id, request.query)
            answer = result.assistant_message
        else:
            answer = workspace.build_contract_chat_reply(
                db,
                current_user.id,
                request.document_id,
                request.query,
            )
        return {"answer": answer}
    except ValueError:
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
