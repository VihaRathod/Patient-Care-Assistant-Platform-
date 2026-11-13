
from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Text,
    UniqueConstraint
)

from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin


class Notification(Base, TimestampMixin):

    __tablename__ = "notifications"

    __table_args__ = (
        UniqueConstraint(
            "appointment_id",
            "notification_type",
            name="uq_appointment_notification_type"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # External IDs: no foreign keys to Patient Management
    patient_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    appointment_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    recipient_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
