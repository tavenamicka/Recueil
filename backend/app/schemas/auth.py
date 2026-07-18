from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole, UserStatus


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str
    new_password: str


class MessageResponse(BaseModel):
    message: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    approved_at: Optional[datetime] = None


class PasswordResetRequestOut(BaseModel):
    id: int
    user_id: int
    user_email: str
    status: UserStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    items: List[UserOut]


class PasswordResetListResponse(BaseModel):
    items: List[PasswordResetRequestOut]
