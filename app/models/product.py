# app/models/product.py
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .category import Category
    from .order_item import OrderItem
    from .review import Review


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), default=Decimal("0.00")
    )
    stock_quantity: Mapped[int] = mapped_column(default=0)

    image_url: Mapped[str | None] = mapped_column(String, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    # Foreign Key
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    # Relationships
    category: Mapped["Category"] = relationship(back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")

    # Cascading delete-orphan on reviews
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
