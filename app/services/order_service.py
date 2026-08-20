from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ApiException
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderStatusUpdate
from app.services.cart_service import get_user_cart_summary
from app.services.email_service import (
    send_order_status_update_email,
)
from app.services.payment_service import create_stripe_checkout_session


async def process_checkout(db: AsyncSession, user: User) -> dict:

    if not user.address:
        raise ApiException(
            "Delivery Address Is Required, please update your address in the update profile page",
            status.HTTP_406_NOT_ACCEPTABLE,
        )

    cart_items = await get_user_cart_summary(db, user.id)

    if not cart_items["items"]:
        raise ApiException("Cart is empty", status.HTTP_400_BAD_REQUEST)

    order_items = []

    for item in cart_items["items"]:
        product = await db.get(Product, item["product_id"])
        if not product or product.stock_quantity < item["quantity"]:
            raise ApiException(
                f"Stock error: {item['product_name']}", status.HTTP_400_BAD_REQUEST
            )

        # Deduct stock
        product.stock_quantity -= item["quantity"]

        order_items.append(
            OrderItem(
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=product.price,
            )
        )

    new_order = Order(
        user_id=user.id,
        total_price=cart_items["total_price"],
        shipping_address=user.address,
        items=order_items,
    )

    db.add(new_order)

    await db.commit()
    await db.refresh(new_order)

    #Initlilize payment and return a uniqur url to the users where he/she can make payment on 
    checkout_url, session_id = await create_stripe_checkout_session(db=db, order_id=new_order.id)

    return {
        "order": new_order,
        "checkout_url": checkout_url,
        "session_id": session_id,
    }


async def get_orders_of_user(db: AsyncSession, user_id: int) -> list[Order]:

    statement = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )

    result = await db.scalars(statement)
    return list(result.all())


async def get_all_order(db: AsyncSession) -> list[Order]:

    statement = (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.user),
        )
        .order_by(Order.created_at.desc())
    )

    result = await db.scalars(statement)
    return list(result.all())


async def update_order_status(
    db: AsyncSession, order_id: int, status_data: OrderStatusUpdate
) -> Order:
    statement = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product),  # <--- Deep Load
        )
    )
    order = await db.scalar(statement)

    if not order:
        raise ApiException("Order not found", status.HTTP_404_NOT_FOUND)

    order.status = status_data.status

    await db.commit()
    await db.refresh(order)

    await send_order_status_update_email(
        email=order.user.email, name=order.user.name, order=order
    )

    return order
