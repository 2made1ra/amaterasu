from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ResultTreeNode(BaseModel):
    id: str
    type: Literal["folder", "supplier", "contract"]
    title: str
    document_id: int | None = None
    children: list["ResultTreeNode"] = Field(default_factory=list)
    has_children: bool = False
    preview_available: bool = False
    badges: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class WorkspaceSnapshot(BaseModel):
    result_tree: list[ResultTreeNode] = Field(default_factory=list)
    selected_node_id: str | None = None
    expanded_node_ids: list[str] = Field(default_factory=list)
    view_mode: str = "flat"


class ChatMessagePayload(BaseModel):
    id: int
    role: str
    content: str
    meta: dict[str, Any] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ChatSessionDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    messages: list[ChatMessagePayload] = Field(default_factory=list)
    snapshot: WorkspaceSnapshot = Field(default_factory=WorkspaceSnapshot)


class ChatSessionCreateRequest(BaseModel):
    title: str | None = None


class SessionMessageCreateRequest(BaseModel):
    query: str


class SearchMetadata(BaseModel):
    route: str
    total_matches: int
    grouping_mode: str


class SessionMessageCreateResponse(BaseModel):
    session_id: int
    assistant_message: ChatMessagePayload
    snapshot: WorkspaceSnapshot
    session_title: str
    search_metadata: SearchMetadata


class SessionSnapshotUpdateRequest(BaseModel):
    result_tree: list[ResultTreeNode] | None = None
    selected_node_id: str | None = None
    expanded_node_ids: list[str] | None = None
    view_mode: str | None = None


ResultTreeNode.model_rebuild()
