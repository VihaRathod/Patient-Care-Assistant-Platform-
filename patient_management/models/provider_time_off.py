
from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    DateTime,
    String,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class ProviderTimeOff(Base, TimestampMixin):

    __tablename__ = "provider_time_off"

    __table_args__ = (
        CheckConstraint(
            "start_datetime < end_datetime",
            name="check_time_off_range"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    provider_id: Mapped[int] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # Relationship

    provider = relationship(
        "Provider",
        back_populates="time_off"
    )
