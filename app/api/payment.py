from fastapi import APIRouter, status, Depends
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import db_session
from app.schemas.order import OrderRead
from app.schemas.response import ApiResponse
from app.services.payment_service import fullfil_order_payment, cancel_order_payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/confirm", status_code=status.HTTP_200_OK)
async def confirm_payment(
    session_id: str, db: AsyncSession = Depends(db_session)
) -> ApiResponse[OrderRead]:

    order = await fullfil_order_payment(db, session_id)

    return ApiResponse[OrderRead](
        status=status.HTTP_200_OK,
        message="Payment verified and order is now being processed.",
        data=OrderRead.model_validate(order),
    )


@router.get("/cancel", status_code=status.HTTP_200_OK)
async def cancel_payment(
    session_id: str, db: AsyncSession = Depends(db_session)
) -> ApiResponse[OrderRead]:
    order = await cancel_order_payment(db, session_id)

    return ApiResponse[OrderRead](
        status=status.HTTP_200_OK,
        message="Payment was cancelled. You can try paying again from your order history.",
        data=OrderRead.model_validate(order),
    )
