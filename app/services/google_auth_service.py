import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.services.email_service import send_welcome_email


async def process_google_callback_workflow(db: AsyncSession, code: str) -> User:

    print("🔄 Exchanging code for access token...")

    token_data = await exchange_code_for_token(code)

    access_token = token_data.get("access_token")

    if not access_token:
        raise ValueError(
            f"Failed to get access token from Google response: {token_data}"
        )

    print("✅ Access token obtained")

    print("🔄 Fetching user info...")

    user_info = await get_user_info(access_token)

    print(f"📧 User email: {user_info.get('email')}")

    if not user_info.get("email"):
        raise ValueError("Google user profile payload missing verified email key.")

    # Sync with DB engine
    user = await get_or_create_user_from_google(db, user_info)

    await send_welcome_email(user.email, user.name)

    return user


async def get_or_create_user_from_google(db: AsyncSession, user_data: dict) -> User:
    """Get existing user or create new one from Google data"""
    email = user_data.get("email")
    name = user_data.get("name")
    picture = user_data.get("picture")

    print(f"Processing Google user data - Email: {email}, Name: {name}")

    if not email:
        raise Exception("No email provided by Google")

    statement = select(User).where(User.email == email)
    user = await db.scalar(statement)

    if not user:

        user = User(
            email=email,
            name=name or email.split("@")[0],
            hashed_password=None,
            role=UserRole.CUSTOMER,
            profile_picture=picture,
            active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✅ Created new user: {email} (ID: {user.id})")
    else:
        print(f"✅ Found existing user: {email} (ID: {user.id})")

    return user


async def get_user_info(access_token: str) -> dict:
    """Get user info from Google using access token"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()


async def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token"""

    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URL,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        return response.json()


async def generate_user_token(user: User) -> str:
    return create_access_token(data={"sub": str(user.id), "role": user.role})
