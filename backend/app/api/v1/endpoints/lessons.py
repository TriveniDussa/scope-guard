from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.lesson import Lesson
from app.models.project import Project
from app.models.user import User
from app.schemas.lesson import LessonRead

router = APIRouter()


def build_lesson_read(lesson: Lesson, db: Session) -> LessonRead:
    """Helper to populate project name onto the LessonRead response."""
    project_name = None
    if lesson.project:
        project_name = lesson.project.name
    else:
        p = db.query(Project).filter(Project.id == lesson.project_id).first()
        if p:
            project_name = p.name

    return LessonRead(
        id=lesson.id,
        workspace_id=lesson.workspace_id,
        project_id=lesson.project_id,
        request_id=lesson.request_id,
        ai_answer=lesson.ai_answer,
        correct_result=lesson.correct_result,
        correction_reason=lesson.correction_reason,
        project_name=project_name,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


@router.get(
    "",
    response_model=List[LessonRead],
    summary="List Lessons Learned",
    description="Retrieves agency correction lessons strictly within the authenticated user's workspace. Optionally filter by project_id.",
)
def list_lessons(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[LessonRead]:
    query = db.query(Lesson).filter(Lesson.workspace_id == current_user.workspace_id)

    if project_id is not None:
        query = query.filter(Lesson.project_id == project_id)

    lessons = query.order_by(Lesson.created_at.desc()).all()
    return [build_lesson_read(lesson, db) for lesson in lessons]


@router.get(
    "/{lesson_id}",
    response_model=LessonRead,
    summary="Get Lesson by ID",
    description="Retrieves an individual lesson by ID strictly within the authenticated user's workspace.",
)
def get_lesson(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonRead:
    lesson = (
        db.query(Lesson)
        .filter(
            Lesson.id == lesson_id,
            Lesson.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    return build_lesson_read(lesson, db)
