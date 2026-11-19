import uuid
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.scope_item import ScopeItem
from app.models.user import User
from app.schemas.scope_item import (
    ScopeItemCreate,
    ScopeItemRead,
    ScopeItemUpdate,
)

router = APIRouter()


@router.post(
    "",
    response_model=ScopeItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Scope of Work Item",
    description="Creates a new scope item with explicit included and not included descriptions. Validates project belongs to workspace.",
)
def create_scope_item(
    scope_item_in: ScopeItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScopeItemRead:
    # 1. Enforce that project exists and belongs to the user's workspace
    project = (
        db.query(Project)
        .filter(
            Project.id == scope_item_in.project_id,
            Project.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in your workspace",
        )

    # 2. Create scope item with workspace isolation
    new_scope_item = ScopeItem(
        id=uuid.uuid4(),
        workspace_id=current_user.workspace_id,
        project_id=scope_item_in.project_id,
        included_description=scope_item_in.included_description.strip(),
        not_included_description=scope_item_in.not_included_description.strip(),
    )
    db.add(new_scope_item)
    db.commit()
    db.refresh(new_scope_item)
    return ScopeItemRead.model_validate(new_scope_item)


@router.get(
    "",
    response_model=List[ScopeItemRead],
    summary="List Scope of Work Items",
    description="Lists all scope items in the authenticated user's workspace. Optionally filter by project_id.",
)
def list_scope_items(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ScopeItemRead]:
    query = db.query(ScopeItem).filter(ScopeItem.workspace_id == current_user.workspace_id)

    if project_id is not None:
        query = query.filter(ScopeItem.project_id == project_id)

    items = query.order_by(ScopeItem.created_at.desc()).all()
    return [ScopeItemRead.model_validate(item) for item in items]


@router.get(
    "/{scope_item_id}",
    response_model=ScopeItemRead,
    summary="Get Scope Item by ID",
    description="Retrieves a specific scope item by ID within the authenticated user's workspace.",
)
def get_scope_item(
    scope_item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScopeItemRead:
    item = (
        db.query(ScopeItem)
        .filter(
            ScopeItem.id == scope_item_id,
            ScopeItem.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scope item not found",
        )
    return ScopeItemRead.model_validate(item)


@router.put(
    "/{scope_item_id}",
    response_model=ScopeItemRead,
    summary="Update Scope Item",
    description="Updates a scope item's included/excluded deliverables or project assignment within the workspace.",
)
def update_scope_item(
    scope_item_id: UUID,
    scope_item_in: ScopeItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScopeItemRead:
    item = (
        db.query(ScopeItem)
        .filter(
            ScopeItem.id == scope_item_id,
            ScopeItem.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scope item not found",
        )

    # If updating project_id, verify the target project belongs to this workspace
    if scope_item_in.project_id is not None:
        project = (
            db.query(Project)
            .filter(
                Project.id == scope_item_in.project_id,
                Project.workspace_id == current_user.workspace_id,
            )
            .first()
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target project not found in your workspace",
            )
        item.project_id = scope_item_in.project_id

    if scope_item_in.included_description is not None:
        item.included_description = scope_item_in.included_description.strip()
    if scope_item_in.not_included_description is not None:
        item.not_included_description = scope_item_in.not_included_description.strip()

    db.commit()
    db.refresh(item)
    return ScopeItemRead.model_validate(item)


@router.delete(
    "/{scope_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Scope Item",
    description="Deletes a scope item within the authenticated user's workspace.",
)
def delete_scope_item(
    scope_item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    item = (
        db.query(ScopeItem)
        .filter(
            ScopeItem.id == scope_item_id,
            ScopeItem.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scope item not found",
        )

    db.delete(item)
    db.commit()
    return None
