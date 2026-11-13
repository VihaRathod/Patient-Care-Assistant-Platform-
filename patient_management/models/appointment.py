
import enum

from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Enum,
    String,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class AppointmentType(str, enum.Enum):
    IN_PERSON = "IN_PERSON"
    TELEHEALTH = "TELEHEALTH"


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class Appointment(Base, TimestampMixin):

    __tablename__ = "appointments"

    __table_args__ = (
        CheckConstraint(
            "start_datetime < end_datetime",
            name="check_appointment_time"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    provider_id: Mapped[int] = mapped_column(
        ForeignKey("providers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    appointment_type: Mapped[AppointmentType] = mapped_column(
        Enum(
            AppointmentType,
            name="appointment_type",
            native_enum=False
        ),
        nullable=False
    )

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(
            AppointmentStatus,
            name="appointment_status",
            native_enum=False
        ),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
        index=True
    )

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    room: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Relationships

    patient = relationship(
        "Patient",
        back_populates="appointments"
    )

    provider = relationship(
        "Provider",
        back_populates="appointments"
    )

    visit_note = relationship(
        "VisitNote",
        back_populates="appointment",
        uselist=False,
        cascade="all, delete-orphan"
    )

    prescriptions = relationship(
        "Prescription",
        back_populates="appointment"
    )
