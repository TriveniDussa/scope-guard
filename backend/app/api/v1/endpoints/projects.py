import uuid
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.client import Client
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter()


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Project",
    description="Creates a new project. Ensures client belongs to the authenticated user's workspace.",
)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectRead:
    # 1. Enforce that client belongs to the user's workspace
    client = (
        db.query(Client)
        .filter(
            Client.id == project_in.client_id,
            Client.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found in your workspace",
        )

    # 2. Create project
    new_project = Project(
        id=uuid.uuid4(),
        workspace_id=current_user.workspace_id,
        client_id=project_in.client_id,
        name=project_in.name.strip(),
        status=project_in.status.value,
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return ProjectRead.model_validate(new_project)


@router.get(
    "",
    response_model=List[ProjectRead],
    summary="List Projects",
    description="Lists all projects within the authenticated user's workspace. Optionally filter by client or status.",
)
def list_projects(
    client_id: Optional[UUID] = Query(None, description="Filter by client ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Active or Done)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ProjectRead]:
    query = db.query(Project).filter(Project.workspace_id == current_user.workspace_id)

    if client_id is not None:
        query = query.filter(Project.client_id == client_id)
    if status_filter is not None:
        # Match case-insensitively to Active / Done
        normalized_status = status_filter.strip().capitalize()
        query = query.filter(Project.status == normalized_status)

    projects = query.order_by(Project.created_at.desc()).all()
    return [ProjectRead.model_validate(p) for p in projects]


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get Project by ID",
    description="Retrieves a single project within the authenticated user's workspace.",
)
def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectRead:
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return ProjectRead.model_validate(project)


@router.put(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Update Project",
    description="Updates a project. Enforces workspace isolation and client validation.",
)
def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectRead:
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # If updating client_id, verify new client belongs to current user's workspace
    if project_in.client_id is not None:
        client = (
            db.query(Client)
            .filter(
                Client.id == project_in.client_id,
                Client.workspace_id == current_user.workspace_id,
            )
            .first()
        )
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New client not found in your workspace",
            )
        project.client_id = project_in.client_id

    if project_in.name is not None:
        project.name = project_in.name.strip()
    if project_in.status is not None:
        project.status = project_in.status.value

    db.commit()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Project",
    description="Deletes a project within the authenticated user's workspace.",
)
def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    db.delete(project)
    db.commit()
    return None
