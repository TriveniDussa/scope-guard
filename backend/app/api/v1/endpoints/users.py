from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter()


@router.get(
    "",
    response_model=List[UserRead],
    summary="List Workspace Users",
    description="Lists all users in the authenticated user's workspace. Enforces strict tenant isolation.",
)
def list_workspace_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[UserRead]:
    """
    STRICT WORKSPACE ISOLATION:
    Only queries users belonging to the current user's workspace_id.
    """
    users = (
        db.query(User)
        .filter(User.workspace_id == current_user.workspace_id)
        .order_by(User.created_at.desc())
        .all()
    )
    return [UserRead.model_validate(u) for u in users]
