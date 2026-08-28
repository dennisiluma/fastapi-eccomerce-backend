from datetime import datetime, timezone
import email
from os import name
from pathlib import Path
import secrets
import string

from pwdlib import PasswordHash
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, status
from app.core.config import settings
from app.core.exceptions import ApiException
from app.core.security import create_access_token
from app.models.reset_code import ResetCode
from app.models.user import User
from app.schemas.user import (
    PasswordUpdate,
    ResetPasswordRequest,
    TokenData,
    UserCreate,
    UserLogin,
    UserUpdate,
)
from app.services.email_service import send_reset_password_email, send_welcome_email
from app.services.upload_service import upload_file, upload_to_s3

password_hasher = PasswordHash.recommended()


async def register_new_user(db: AsyncSession, user_data: UserCreate):

    statement = select(User).where(User.email == user_data.email)
    existing_user = await db.scalar(statement)

    if existing_user:
        raise ApiException(
            message="User with this email already existis",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    hashed_password = password_hasher.hash(user_data.password)

    user_object = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        role=user_data.role,
    )

    db.add(user_object)
    await db.commit()
    await db.refresh(user_object)

    await send_welcome_email(user_object.email, user_object.name)
    return user_object


async def login_user(db: AsyncSession, login_data: UserLogin) -> TokenData:

    # 1. Find user
    statement = select(User).where(User.email == login_data.email)
    user = await db.scalar(statement)

    # 2. Check if user exists
    if not user:
        raise ApiException(
            message="Invalid email or password",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 3. Check if user authenticated via OAuth 2.0 (no password set)
    if not user.hashed_password:
        raise ApiException(
            message="You authenticated via OAuth 2.0. Please log in with your social provider.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 4. Verify password
    if not password_hasher.verify(login_data.password, user.hashed_password):
        raise ApiException(
            message="Invalid email or password",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    token = create_access_token(data={"sub": str(user.id), "role": user.role})

    return TokenData(token=token, user=user)


async def process_forgot_password(db: AsyncSession, email: str) -> bool:
    # 1. Verify user exists
    statement = select(User).where(User.email == email)
    user = await db.scalar(statement)

    if not user:
        raise ApiException(
            "User with this email not found", status_code=status.HTTP_404_NOT_FOUND
        )

    # 2. Generate a UNIQUE 6-character code
    unique_code = False
    code = ""

    while not unique_code:
        # Generate random uppercase 6-char string
        code = "".join(
            secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)
        )

        # Check if this code already exists in the ResetCode table
        code_statement = select(ResetCode).where(ResetCode.code == code)
        existing_code = await db.scalar(code_statement)

        if not existing_code:
            unique_code = True

    # 3. Save to DB
    reset_entry = ResetCode(email=email, code=code)
    db.add(reset_entry)
    await db.commit()

    print(f"DEBUG: Saved code '{code}' for email '{email}' to database.")

    reset_url = f"{settings.RESET_PASSWORD_URL}{code}"

    await send_reset_password_email(
        email=email, name=user.name, code=code, reset_url=reset_url
    )
    return True


async def process_reset_password(
    db: AsyncSession, reset_data: ResetPasswordRequest
) -> bool:
    # 1. Find the code and check expiry
    statement = select(ResetCode).where(ResetCode.code == reset_data.code)
    reset_entry = await db.scalar(statement)

    if not reset_entry:
        print(f"DEBUG: Reset code '{reset_data.code}' not found in database.")
        raise ApiException(
            "Invalid reset code", status_code=status.HTTP_400_BAD_REQUEST
        )

    print(
        f"DEBUG: Found code. Expires at: {reset_entry.expires_at}, Current time: {datetime.now(timezone.utc)}"
    )

    # Ensure safety against naive/aware datetime comparison issues
    current_time = datetime.now(timezone.utc)
    expiry_time = reset_entry.expires_at

    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=timezone.utc)

    if current_time > expiry_time:
        print(f"DEBUG: Code has expired.")
        raise ApiException(
            "Reset code has expired", status_code=status.HTTP_400_BAD_REQUEST
        )

    # 2. Find the user
    user_stmt = select(User).where(User.email == reset_entry.email)
    user = await db.scalar(user_stmt)

    if not user:
        print(f"DEBUG: User with email {reset_entry.email} no longer exists.")
        raise ApiException(
            "User no longer exists", status_code=status.HTTP_404_NOT_FOUND
        )

    # 3. Update Password
    user.hashed_password = password_hasher.hash(reset_data.password)

    # 4. Cleanup: Delete ALL reset codes for this email
    await db.execute(delete(ResetCode).where(ResetCode.email == reset_entry.email))

    await db.commit()
    return True


async def get_all_users(db: AsyncSession) -> list[User]:
    statement = select(User).order_by(desc(User.id))
    result = await db.scalars(statement)
    return list(result.all())


async def update_user_profile(
    db: AsyncSession, user: User, update_data: UserUpdate
) -> User:
    if update_data.name:
        user.name = update_data.name

    if update_data.address:
        user.address = update_data.address

    await db.commit()
    await db.refresh(user)
    return user


async def change_user_password(
    db: AsyncSession, user: User, password_data: PasswordUpdate
) -> bool:
    # 1. Verify old password
    if not password_hasher.verify(password_data.old_password, user.hashed_password):
        raise ApiException(
            "Old password is incorrect", status_code=status.HTTP_400_BAD_REQUEST
        )

    # 2. Hash and update
    user.hashed_password = password_hasher.hash(password_data.new_password)
    await db.commit()
    return True


async def upload_profile_pix(db: AsyncSession, user: User, file: UploadFile) -> str:

    upload_dir = Path("uploads/profile")

    image_path = await upload_to_s3(file=file, upload_dir=upload_dir)

    user.profile_picture = image_path

    await db.commit()
    await db.refresh(user)

    return image_path
