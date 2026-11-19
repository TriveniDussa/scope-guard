import uuid
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.scope_item import ScopeItem
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter()


def build_task_read(task: Task, db: Session) -> TaskRead:
    """Helper to populate related project name and scope item summary."""
    project_name = None
    scope_item_summary = None

    if task.project:
        project_name = task.project.name
    else:
        p = db.query(Project).filter(Project.id == task.project_id).first()
        if p:
            project_name = p.name

    if task.scope_item:
        scope_item_summary = task.scope_item.included_description[:100]
    else:
        s = db.query(ScopeItem).filter(ScopeItem.id == task.scope_item_id).first()
        if s:
            scope_item_summary = s.included_description[:100]

    return TaskRead(
        id=task.id,
        workspace_id=task.workspace_id,
        project_id=task.project_id,
        scope_item_id=task.scope_item_id,
        title=task.title,
        due_date=task.due_date,
        status=task.status,
        project_name=project_name,
        scope_item_summary=scope_item_summary,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Task",
    description="Creates a task linked to a project and scope item within the user's workspace.",
)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskRead:
    # 1. Verify project exists in the user's workspace
    project = (
        db.query(Project)
        .filter(
            Project.id == task_in.project_id,
            Project.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in your workspace",
        )

    # 2. Verify scope item exists in the user's workspace
    scope_item = (
        db.query(ScopeItem)
        .filter(
            ScopeItem.id == task_in.scope_item_id,
            ScopeItem.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not scope_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scope item not found in your workspace",
        )

    # 3. Verify scope item belongs to the specified project
    if scope_item.project_id != task_in.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scope item does not belong to the specified project",
        )

    new_task = Task(
        id=uuid.uuid4(),
        workspace_id=current_user.workspace_id,
        project_id=task_in.project_id,
        scope_item_id=task_in.scope_item_id,
        title=task_in.title.strip(),
        due_date=task_in.due_date,
        status=task_in.status.value,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return build_task_read(new_task, db)


@router.get(
    "",
    response_model=List[TaskRead],
    summary="List Tasks",
    description="Lists all tasks in the user's workspace. Supports optional filters by project, scope item, or status.",
)
def list_tasks(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    scope_item_id: Optional[UUID] = Query(None, description="Filter by scope item ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (To do, Doing, Done)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TaskRead]:
    query = db.query(Task).filter(Task.workspace_id == current_user.workspace_id)

    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    if scope_item_id is not None:
        query = query.filter(Task.scope_item_id == scope_item_id)
    if status_filter is not None:
        clean_status = status_filter.strip().lower()
        if clean_status in ("to do", "todo"):
            query = query.filter(Task.status == "To do")
        elif clean_status in ("doing", "in_progress"):
            query = query.filter(Task.status == "Doing")
        elif clean_status == "done":
            query = query.filter(Task.status == "Done")
        else:
            query = query.filter(Task.status == status_filter)

    tasks = query.order_by(Task.created_at.desc()).all()
    return [build_task_read(t, db) for t in tasks]


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Get Task by ID",
    description="Retrieves a specific task by ID within the authenticated user's workspace.",
)
def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskRead:
    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return build_task_read(task, db)


@router.put(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update Task",
    description="Updates a task's title, status, due date, project, or scope item.",
)
def update_task(
    task_id: UUID,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskRead:
    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    target_project_id = task_in.project_id if task_in.project_id is not None else task.project_id
    target_scope_item_id = task_in.scope_item_id if task_in.scope_item_id is not None else task.scope_item_id

    # If project or scope item are being updated, re-validate their relationship
    if task_in.project_id is not None or task_in.scope_item_id is not None:
        project = (
            db.query(Project)
            .filter(
                Project.id == target_project_id,
                Project.workspace_id == current_user.workspace_id,
            )
            .first()
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found in your workspace",
            )

        scope_item = (
            db.query(ScopeItem)
            .filter(
                ScopeItem.id == target_scope_item_id,
                ScopeItem.workspace_id == current_user.workspace_id,
            )
            .first()
        )
        if not scope_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scope item not found in your workspace",
            )

        if scope_item.project_id != target_project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scope item does not belong to the specified project",
            )

        task.project_id = target_project_id
        task.scope_item_id = target_scope_item_id

    if task_in.title is not None:
        task.title = task_in.title.strip()
    if task_in.due_date is not None:
        task.due_date = task_in.due_date
    if task_in.status is not None:
        task.status = task_in.status.value

    db.commit()
    db.refresh(task)
    return build_task_read(task, db)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Task",
    description="Deletes a task within the user's workspace.",
)
def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    db.delete(task)
    db.commit()
    return None
