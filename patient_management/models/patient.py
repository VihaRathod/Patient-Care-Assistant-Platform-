
from datetime import date

from sqlalchemy import (
    String,
    Date,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

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

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    gender: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # Relationships

    user = relationship(
        "User",
        back_populates="patient"
    )

    appointments = relationship(
        "Appointment",
        back_populates="patient"
    )

    prescriptions = relationship(
        "Prescription",
        back_populates="patient"
    )

    allergies = relationship(
        "PatientAllergy",
        back_populates="patient"
    )
    


