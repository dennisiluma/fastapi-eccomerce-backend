
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User, UserRole


async def get_dashboard_stats(db: AsyncSession) -> dict:

    # Get total products
    total_products = (await db.scalar(select(func.count()).select_from(Product))) or 0

    # Get total categories
    total_categories = (
        await db.scalar(select(func.count()).select_from(Category))
    ) or 0

    # Get total orders
    total_orders = (await db.scalar(select(func.count()).select_from(Order))) or 0

    # Get total users
    total_users = (await db.scalar(select(func.count()).select_from(User))) or 0

    # Get total revenue
    total_revenue_stmt = select(func.sum(Order.total_price)).where(
        Order.status.in_(
            [OrderStatus.DELIVERED, OrderStatus.PROCESSING, OrderStatus.SHIPPED]
        )
    )
    total_revenue = (await db.scalar(total_revenue_stmt)) or Decimal("0.00")

    # Orders by status
    orders_by_status_stmt = select(Order.status, func.count(Order.id)).group_by(
        Order.status
    )
    orders_by_status_result = await db.execute(orders_by_status_stmt)
    orders_by_status = {
        status: count for status, count in orders_by_status_result.all()
    }

    # Users by role
    users_by_role_stmt = select(User.role, func.count(User.id)).group_by(User.role)
    users_by_role_result = await db.execute(users_by_role_stmt)
    users_by_role = {role: count for role, count in users_by_role_result.all()}

    # Low stock products (stock <= 5)
    low_stock_stmt = (
        select(func.count()).select_from(Product).where(Product.stock_quantity <= 5)
    )
    low_stock_products = (await db.scalar(low_stock_stmt)) or 0

    # Out of stock products (stock == 0)
    out_of_stock_stmt = (
        select(func.count()).select_from(Product).where(Product.stock_quantity == 0)
    )
    out_of_stock_products = (await db.scalar(out_of_stock_stmt)) or 0

    # Recent orders (last 7 days using timezone-aware UTC datetime)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_orders_stmt = (
        select(func.count())
        .select_from(Order)
        .where(Order.created_at >= seven_days_ago)
    )
    recent_orders = (await db.scalar(recent_orders_stmt)) or 0

    return {
        "totalProducts": total_products,
        "totalCategories": total_categories,
        "totalOrders": total_orders,
        "totalUsers": total_users,
        "totalRevenue": float(total_revenue),
        "breakdown": {
            "orders_by_status": {
                "pending": orders_by_status.get(OrderStatus.PENDING, 0),
                "processing": orders_by_status.get(OrderStatus.PROCESSING, 0),
                "shipped": orders_by_status.get(OrderStatus.SHIPPED, 0),
                "delivered": orders_by_status.get(OrderStatus.DELIVERED, 0),
                "cancelled": orders_by_status.get(OrderStatus.CANCELLED, 0),
            },
            "users_by_role": {
                "admin": users_by_role.get(UserRole.ADMIN, 0),
                "customer": users_by_role.get(UserRole.CUSTOMER, 0),
                "delivery": users_by_role.get(UserRole.DELIVERY, 0),
            },
            "inventory_status": {
                "low_stock_products": low_stock_products,
                "out_of_stock_products": out_of_stock_products,
            },
            "recent_orders_last_7_days": recent_orders,
        },
    }
