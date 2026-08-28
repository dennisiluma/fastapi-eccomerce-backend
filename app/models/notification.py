# app/models/notification.py
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class NotificationType(str, Enum):
    WELCOME = "welcome"
    ORDER_UPDATE = "order_update"
    PAYMENT_UPDATE = "payment_update"
    PROMOTIONAL = "promotional"
    SECURITY = "security"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Destination email i.e. where you want to send the mail to
    recipient_email: Mapped[str] = mapped_column(String, index=True)

    # Content of the notification
    title: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)

    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType), default=NotificationType.ORDER_UPDATE
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
