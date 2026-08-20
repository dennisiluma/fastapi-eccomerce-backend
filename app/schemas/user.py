from pydantic import EmailStr

from app.models.user import UserRole
from app.schemas.schema_base import SchemaBaseModel


class UserCreate(SchemaBaseModel):
    email: EmailStr
    password: str
    name: str
    role: UserRole | None = UserRole.CUSTOMER


class UserRead(SchemaBaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    active: bool
    profile_picture: str | None = None
    address: str | None = None


class UserLogin(SchemaBaseModel):
    email: EmailStr
    password: str


class TokenData(SchemaBaseModel):
    token: str
    type: str = "bearer"
    user: UserRead


class UserUpdate(SchemaBaseModel):
    name: str | None = None
    address: str | None = None


class PasswordUpdate(SchemaBaseModel):
    old_password: str
    new_password: str


class ForgotPasswordRequest(SchemaBaseModel):
    email: EmailStr


class ResetPasswordRequest(SchemaBaseModel):
    code: str
    password: str
