# app/models/order_item.py
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .order import Order
    from .product import Product


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    quantity: Mapped[int] = mapped_column(default=1)

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), default=Decimal("0.00")
    )

    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Foreign Keys
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")