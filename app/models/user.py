# app/models/user.py
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base



if TYPE_CHECKING:
    from .cart import Cart
    from .order import Order
    from .review import Review


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    DELIVERY = "DELIVERY"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    name: Mapped[str] = mapped_column(String, index=True)
    profile_picture: Mapped[str | None] = mapped_column(String, default=None)
    address: Mapped[str | None] = mapped_column(String, default=None)

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), default=UserRole.CUSTOMER, index=True
    )

    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    # One-to-many relationships
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user")

    # One-to-one relationship
    cart: Mapped["Cart | None"] = relationship(back_populates="user", uselist=False)
