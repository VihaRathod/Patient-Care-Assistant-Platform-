
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class Provider(Base, TimestampMixin):
    __tablename__ = "providers"

    __table_args__ = (
        CheckConstraint(
            "experience >= 0",
            name="check_provider_experience"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    qualification: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    experience: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    # Relationships

    user = relationship(
        "User",
        back_populates="provider"
    )

    specialties = relationship(
        "ProviderSpecialty",
        back_populates="provider"
    )

    appointments = relationship(
        "Appointment",
        back_populates="provider"
    )

    availability = relationship(
        "ProviderAvailability",
        back_populates="provider"
    )

    time_off = relationship(
        "ProviderTimeOff",
        back_populates="provider"
    )

    prescriptions = relationship(
        "Prescription",
        back_populates="provider"
    )
