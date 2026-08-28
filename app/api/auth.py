import traceback
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, status

from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.database import db_session
from app.schemas.response import ApiResponse
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenData,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.services.google_auth_service import (
    generate_user_token,
    process_google_callback_workflow,
)
from app.services.user_service import (
    login_user,
    process_forgot_password,
    process_reset_password,
    register_new_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, db: AsyncSession = Depends(db_session)
) -> ApiResponse[UserRead]:

    user = await register_new_user(db=db, user_data=user_data)

    return ApiResponse[UserRead](
        status=status.HTTP_201_CREATED,
        message="User registered succesfullty",
        data=user,
    )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    login_data: UserLogin, db: AsyncSession = Depends(db_session)
) -> ApiResponse[TokenData]:

    token_info = await login_user(db=db, login_data=login_data)

    return ApiResponse[TokenData](
        status=status.HTTP_200_OK,
        message="Login succesfullty",
        data=token_info,
    )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest, db: AsyncSession = Depends(db_session)
) -> ApiResponse[None]:

    print(f"forgot-password called")
    await process_forgot_password(db, request.email)

    return ApiResponse[None](
        status=status.HTTP_200_OK, message="Reset Password Link Sent Successfully"
    )


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest, db: AsyncSession = Depends(db_session)
) -> ApiResponse[None]:

    print(f"reset-password called")
    print(f"code is", request.code)
    await process_reset_password(db, request)

    return ApiResponse[None](
        status=status.HTTP_200_OK, message="Password Reset Successfully"
    )


@router.get("/google")
async def google_reg_login():

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{settings.GOOGLE_REDIRECT_URL}",
        "response_type": "code",
        "scope": "email profile",
        "access_type": "offline",
    }

    auth_url = f"{settings.GOOGLE_AUTH_BASE_URL}?{urlencode(params)}"
    print(f"🔐 Google login initiated")
    print(f"   Redirect URI: {params['redirect_uri']}")

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    request: Request, code: str = None, db: AsyncSession = Depends(db_session)
):
    print(" ✅ Google Callback Received")

    # Catch structural OAuth errors dropped as URL parameters early
    error = request.query_params.get("error")
    if error:
        print(f"❌ Google returned error: {error}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth-error?error={error}")

    if not code:
        print("❌ No authorization code received")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth-error?error=No authorization code"
        )

    try:
        user = await process_google_callback_workflow(db, code)

        # Build app context tracking credentials
        auth_token = await generate_user_token(user)
        print(f"✅ 🔑 JWT token generated for user ID: {user.id}, Role: {user.role}")

        redirect_url = f"{settings.FRONTEND_URL}/auth-success?token={auth_token}&role={user.role.value}"
        print(f" ✅ 🔄 Redirecting to: {redirect_url}")
        return RedirectResponse(url=redirect_url)

    except ValueError as val_err:
        print(f"⚠️ Validation error encountered during OAuth handling: {val_err}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth-error?error={str(val_err)}"
        )
    except Exception as e:
        print(f"❌ ERROR in Google callback pipeline: {str(e)}")
        traceback.print_exc()
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth-error?error=Unexpected authentication fault processing request."
        )
