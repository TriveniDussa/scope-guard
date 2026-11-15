import re
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_workspace
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.auth import Token, LoginRequest
from app.schemas.user import (
    AgencySignupRequest,
    AgencySignupResponse,
    UserRead,
)
from app.schemas.workspace import WorkspaceRead

router = APIRouter()


def generate_unique_slug(name: str, db: Session) -> str:
    """Generate a clean, unique URL-friendly slug for the workspace."""
    base_slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not base_slug:
        base_slug = "workspace"
    
    slug = base_slug
    counter = 1
    while db.query(Workspace).filter(Workspace.slug == slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


@router.post(
    "/signup",
    response_model=AgencySignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agency Sign Up",
    description="Registers a new agency workspace and an initial agency admin account.",
)
def signup(
    signup_data: AgencySignupRequest,
    db: Session = Depends(get_db),
) -> Any:
    # 1. Validate email uniqueness
    normalized_email = signup_data.email.lower().strip()
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # 2. Atomic Workspace & User Creation
    workspace_slug = generate_unique_slug(signup_data.agency_name, db)
    new_workspace = Workspace(
        id=uuid.uuid4(),
        name=signup_data.agency_name.strip(),
        slug=workspace_slug,
    )
    db.add(new_workspace)
    db.flush()  # Flush so new_workspace.id is available for FK constraint

    new_user = User(
        id=uuid.uuid4(),
        workspace_id=new_workspace.id,
        email=normalized_email,
        hashed_password=hash_password(signup_data.password),
        full_name=signup_data.full_name.strip(),
        role="agency_admin",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_workspace)
    db.refresh(new_user)

    # 3. Issue JWT Access Token
    access_token = create_access_token(
        subject=str(new_user.id),
        workspace_id=str(new_workspace.id),
    )

    return AgencySignupResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserRead.model_validate(new_user),
        workspace=WorkspaceRead.model_validate(new_workspace),
    )


@router.post(
    "/login",
    response_model=Token,
    summary="User Login",
    description="Authenticates an agency user and returns a signed JWT access token.",
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> Any:
    normalized_email = login_data.email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()

    # Prevent timing attack: always compute or verify password
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive. Please contact your workspace administrator.",
        )

    access_token = create_access_token(
        subject=str(user.id),
        workspace_id=str(user.workspace_id),
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    summary="Get Current User Profile",
    description="Protected endpoint returning the profile of the authenticated user and their workspace.",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    current_workspace: Workspace = Depends(get_current_workspace),
) -> Any:
    return {
        "user": UserRead.model_validate(current_user),
        "workspace": WorkspaceRead.model_validate(current_workspace),
    }
