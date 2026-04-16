from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession


DEFAULT_SESSION_TITLE = "New workspace"
UNSET = object()


def list_sessions_for_owner(db: Session, owner_id: int) -> list[tuple[ChatSession, int]]:
    return (
        db.query(ChatSession, func.count(ChatMessage.id))
        .outerjoin(ChatMessage, ChatMessage.session_id == ChatSession.id)
        .filter(ChatSession.owner_id == owner_id)
        .group_by(ChatSession.id)
        .order_by(ChatSession.last_message_at.desc(), ChatSession.updated_at.desc())
        .all()
    )


def create_session(db: Session, owner_id: int, title: str | None = None) -> ChatSession:
    now = datetime.now(timezone.utc)
    session = ChatSession(
        owner_id=owner_id,
        title=title or DEFAULT_SESSION_TITLE,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_for_owner(db: Session, session_id: int, owner_id: int) -> ChatSession | None:
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.owner_id == owner_id)
        .first()
    )


def delete_session(db: Session, session: ChatSession) -> None:
    db.delete(session)
    db.commit()


def create_message(
    db: Session,
    session: ChatSession,
    role: str,
    content: str,
    meta: dict | None = None,
) -> ChatMessage:
    message = ChatMessage(session_id=session.id, role=role, content=content, meta=meta)
    db.add(message)
    session.updated_at = datetime.now(timezone.utc)
    if role == "assistant":
        session.last_message_at = session.updated_at
    db.add(session)
    db.commit()
    db.refresh(message)
    db.refresh(session)
    return message


def update_session_title(db: Session, session: ChatSession, title: str) -> ChatSession:
    session.title = title
    session.updated_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_snapshot(
    db: Session,
    session: ChatSession,
    *,
    result_tree: list | None | object = UNSET,
    selected_node_id: str | None | object = UNSET,
    expanded_node_ids: list | None | object = UNSET,
    view_mode: str | None | object = UNSET,
) -> ChatSession:
    if result_tree is not UNSET:
        session.result_tree_json = result_tree
    if selected_node_id is not UNSET:
        session.selected_node_id = selected_node_id
    if expanded_node_ids is not UNSET:
        session.expanded_node_ids = expanded_node_ids
    if view_mode is not UNSET:
        session.view_mode = view_mode
    session.updated_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
