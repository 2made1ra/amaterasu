from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.search_orchestration import safe_orchestrate_contract_search


@dataclass
class WorkspaceQueryResult:
    assistant_message: str
    result_tree: list[dict]
    total_matches: int
    route: str
    grouping_mode: str = "flat"


def _document_to_result_node(document) -> dict:
    badges = [document.status]
    if document.extracted_deadline:
        badges.append(document.extracted_deadline.date().isoformat())

    return {
        "id": f"contract-{document.id}",
        "type": "contract",
        "title": document.title,
        "document_id": document.id,
        "children": [],
        "has_children": False,
        "preview_available": True,
        "badges": badges,
        "meta": {
            "deadline": document.extracted_deadline.isoformat() if document.extracted_deadline else None,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "status": document.status,
        },
    }


def build_workspace_query_result(db: Session, owner_id: int, query: str) -> WorkspaceQueryResult:
    search_result = safe_orchestrate_contract_search(db, owner_id=owner_id, query=query)
    matched_documents = search_result.documents
    result_tree = [_document_to_result_node(document) for document in matched_documents]
    assistant_message = search_result.assistant_message

    return WorkspaceQueryResult(
        assistant_message=assistant_message,
        result_tree=result_tree,
        total_matches=len(result_tree),
        route=search_result.route.value,
    )


def build_contract_chat_reply(db: Session, owner_id: int, document_id: int, query: str) -> str:
    search_result = safe_orchestrate_contract_search(
        db,
        owner_id=owner_id,
        query=query,
        document_id=document_id,
    )
    if not search_result.documents:
        raise ValueError("Document not found")
    return search_result.assistant_message
