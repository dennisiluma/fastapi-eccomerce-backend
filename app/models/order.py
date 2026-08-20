# app/models/order.py
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .order_item import OrderItem
    from .payment import Payment
    from .user import User


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), default=Decimal("0.00")
    )
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus), default=OrderStatus.PENDING
    )
    shipping_address: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")
    payment: Mapped["Payment | None"] = relationship(
        back_populates="order", uselist=False
    )
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")
