from typing import Any

from fastapi import APIRouter, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import db_session
from app.api.dependencies import get_current_admin
from app.models.user import User
from app.schemas.response import ApiResponse
from app.services.report_service import get_dashboard_stats

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def get_dashboard_report(
    db: AsyncSession = Depends(db_session),
      _: User = Depends(get_current_admin)
) -> ApiResponse[dict[str, Any]]:

    stats = await get_dashboard_stats(db)

    return ApiResponse[dict[str, Any]](
        status=status.HTTP_200_OK,
        message="Dashboard statistics retrieved successfully",
        data=stats,
    )
