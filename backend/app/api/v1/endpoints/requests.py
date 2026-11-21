import uuid
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.request import Request
from app.models.scope_item import ScopeItem
from app.models.user import User
from app.schemas.request import RequestCheckIn, RequestRead
from app.services.ai.base import AIServiceError, BaseAIService
from app.services.ai.factory import get_ai_service

router = APIRouter()


def build_request_read(req: Request, db: Session) -> RequestRead:
    """Helper to populate project name onto the RequestRead response."""
    project_name = None
    if req.project:
        project_name = req.project.name
    else:
        p = db.query(Project).filter(Project.id == req.project_id).first()
        if p:
            project_name = p.name

    return RequestRead(
        id=req.id,
        workspace_id=req.workspace_id,
        project_id=req.project_id,
        user_id=req.user_id,
        client_request=req.client_request,
        classification=req.classification,
        reason=req.reason,
        client_reply=req.client_reply,
        project_name=project_name,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


@router.post(
    "/check",
    response_model=RequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Check Client Request against Scope baseline",
    description="Uses AI to evaluate a client request strictly against the selected project's Included and Not Included scope items.",
)
def check_client_request(
    check_in: RequestCheckIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: BaseAIService = Depends(get_ai_service),
) -> RequestRead:
    # 1. Enforce that the project belongs to the user's workspace
    project = (
        db.query(Project)
        .filter(
            Project.id == check_in.project_id,
            Project.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in your workspace",
        )

    # 2. Fetch scope items ONLY for this project and workspace
    scope_items = (
        db.query(ScopeItem)
        .filter(
            ScopeItem.project_id == check_in.project_id,
            ScopeItem.workspace_id == current_user.workspace_id,
        )
        .order_by(ScopeItem.created_at.asc())
        .all()
    )

    # 3. Call modular AI Service with error handling
    try:
        classification_result = ai_service.classify_request(
            client_request=check_in.client_request.strip(),
            scope_items=scope_items,
        )
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI Service Error: {exc.message}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate request: {str(exc)}",
        )

    # 4. Save request and AI answer in PostgreSQL
    new_request = Request(
        id=uuid.uuid4(),
        workspace_id=current_user.workspace_id,
        project_id=check_in.project_id,
        user_id=current_user.id,
        client_request=check_in.client_request.strip(),
        classification=classification_result.classification.value,
        reason=classification_result.reason.strip(),
        client_reply=classification_result.client_reply.strip(),
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return build_request_read(new_request, db)


@router.get(
    "",
    response_model=List[RequestRead],
    summary="List Request History",
    description="Retrieves evaluated requests history within the user's workspace. Optionally filter by project_id.",
)
def list_requests(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RequestRead]:
    query = db.query(Request).filter(Request.workspace_id == current_user.workspace_id)

    if project_id is not None:
        query = query.filter(Request.project_id == project_id)

    requests = query.order_by(Request.created_at.desc()).all()
    return [build_request_read(r, db) for r in requests]


@router.get(
    "/{request_id}",
    response_model=RequestRead,
    summary="Get Evaluated Request by ID",
    description="Retrieves an individual evaluated request by ID within the user's workspace.",
)
def get_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RequestRead:
    req = (
        db.query(Request)
        .filter(
            Request.id == request_id,
            Request.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    return build_request_read(req, db)
