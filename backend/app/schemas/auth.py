from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    workspace_id: str
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
