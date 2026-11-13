
from sqlalchemy import (
    ForeignKey,
    Integer,
    Time,
    Boolean,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class ProviderAvailability(Base, TimestampMixin):

    __tablename__ = "provider_availability"

    __table_args__ = (
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="check_availability_day"
        ),
        CheckConstraint(
            "start_time < end_time",
            name="check_availability_time"
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

    # Monday = 0, Sunday = 6
    day_of_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    start_time: Mapped[object] = mapped_column(
        Time,
        nullable=False
    )

    end_time: Mapped[object] = mapped_column(
        Time,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationship

    provider = relationship(
        "Provider",
        back_populates="availability"
    )
