from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_chat_session
from app.schemas.chat_session import (
    ChatSessionCreateRequest,
    ChatSessionDetail,
    ChatSessionSummary,
    SearchMetadata,
    SessionMessageCreateRequest,
    SessionMessageCreateResponse,
    SessionSnapshotUpdateRequest,
    WorkspaceSnapshot,
)
from app.services import workspace

router = APIRouter()


def _build_snapshot(session) -> WorkspaceSnapshot:
    return WorkspaceSnapshot(
        result_tree=session.result_tree_json or [],
        selected_node_id=session.selected_node_id,
        expanded_node_ids=session.expanded_node_ids or [],
        view_mode=session.view_mode or "flat",
    )


def _build_detail(session) -> ChatSessionDetail:
    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_message_at=session.last_message_at,
        messages=session.messages or [],
        snapshot=_build_snapshot(session),
    )


@router.get("/", response_model=list[ChatSessionSummary])
def list_chat_sessions(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    session_rows = crud_chat_session.list_sessions_for_owner(db, current_user.id)
    return [
        ChatSessionSummary(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_message_at=session.last_message_at,
            message_count=message_count,
        )
        for session, message_count in session_rows
    ]


@router.post("/", response_model=ChatSessionDetail)
def create_chat_session(
    request: ChatSessionCreateRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    session = crud_chat_session.create_session(db, current_user.id, request.title)
    return _build_detail(session)


@router.get("/{session_id}", response_model=ChatSessionDetail)
def get_chat_session(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    session = crud_chat_session.get_session_for_owner(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return _build_detail(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    session = crud_chat_session.get_session_for_owner(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    crud_chat_session.delete_session(db, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{session_id}/messages", response_model=SessionMessageCreateResponse)
def create_chat_session_message(
    session_id: int,
    request: SessionMessageCreateRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    session = crud_chat_session.get_session_for_owner(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    crud_chat_session.create_message(db, session, "user", query)
    query_result = workspace.build_workspace_query_result(db, current_user.id, query)

    next_selected_node = session.selected_node_id
    if query_result.result_tree and not next_selected_node:
        next_selected_node = query_result.result_tree[0]["id"]

    crud_chat_session.update_snapshot(
        db,
        session,
        result_tree=query_result.result_tree,
        selected_node_id=next_selected_node,
        expanded_node_ids=session.expanded_node_ids or [],
        view_mode=session.view_mode or "flat",
    )

    if session.title == crud_chat_session.DEFAULT_SESSION_TITLE:
        generated_title = query[:60].strip()
        if len(query) > 60:
            generated_title = f"{generated_title.rstrip()}..."
        session = crud_chat_session.update_session_title(db, session, generated_title or session.title)

    assistant_message = crud_chat_session.create_message(
        db,
        session,
        "assistant",
        query_result.assistant_message,
        meta={
            "route": query_result.route,
            "total_matches": query_result.total_matches,
            "grouping_mode": query_result.grouping_mode,
        },
    )
    session = crud_chat_session.get_session_for_owner(db, session_id, current_user.id)

    return SessionMessageCreateResponse(
        session_id=session.id,
        assistant_message=assistant_message,
        snapshot=_build_snapshot(session),
        session_title=session.title,
        search_metadata=SearchMetadata(
            route=query_result.route,
            total_matches=query_result.total_matches,
            grouping_mode=query_result.grouping_mode,
        ),
    )


@router.patch("/{session_id}/snapshot", response_model=WorkspaceSnapshot)
def update_chat_session_snapshot(
    session_id: int,
    request: SessionSnapshotUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    session = crud_chat_session.get_session_for_owner(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    provided_fields = request.model_dump(exclude_unset=True)
    updated = crud_chat_session.update_snapshot(
        db,
        session,
        result_tree=(
            [node.model_dump() for node in request.result_tree]
            if "result_tree" in provided_fields
            else crud_chat_session.UNSET
        ),
        selected_node_id=(
            request.selected_node_id
            if "selected_node_id" in provided_fields
            else crud_chat_session.UNSET
        ),
        expanded_node_ids=(
            request.expanded_node_ids
            if "expanded_node_ids" in provided_fields
            else crud_chat_session.UNSET
        ),
        view_mode=request.view_mode if "view_mode" in provided_fields else crud_chat_session.UNSET,
    )
    return _build_snapshot(updated)
