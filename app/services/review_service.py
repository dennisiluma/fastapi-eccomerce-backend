from fastapi import status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApiException
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate


async def create_product_review(
    db: AsyncSession, user: User, review_data: ReviewCreate
) -> Review:

    # 1. Fetch the specific OrderItem for this user, order, and product
    statement = (
        select(OrderItem)
        .join(Order)
        .where(
            and_(
                Order.id == review_data.order_id,
                Order.user_id == user.id,
                Order.status == OrderStatus.DELIVERED,
                OrderItem.product_id == review_data.product_id,
            )
        )
    )

    order_item = await db.scalar(statement)

    if not order_item:
        raise ApiException(
            "You can only review products from delivered orders belonging to you.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 2. Check if this specific order item has already been reviewed
    if order_item.is_reviewed:
        raise ApiException(
            "You have already reviewed this product for this order.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 3. Create Review
    new_review = Review(
        rating=review_data.rating,
        comment=review_data.comment,
        product_id=review_data.product_id,
        user_id=user.id,
        username=user.name,
    )

    order_item.is_reviewed = True

    db.add(new_review)
    db.add(order_item)

    await db.commit()
    await db.refresh(new_review)
    return new_review


async def get_average_rating(db: AsyncSession, product_id: int) -> dict:

    statement = select(
        func.avg(Review.rating).label("average"),
        func.count(Review.id).label("count"),
    ).where(Review.product_id == product_id)

    result = await db.execute(statement)
    stats = result.first()

    average = round(float(stats.average), 1) if stats and stats.average else 0.0
    total_reviews = stats.count if stats else 0

    return {"average_rating": average, "total_reviews": total_reviews}
