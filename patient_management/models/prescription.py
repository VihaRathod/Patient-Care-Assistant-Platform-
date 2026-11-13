
import enum

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Enum,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class PrescriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Prescription(Base, TimestampMixin):

    __tablename__ = "prescriptions"

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

    # Nullable because prescriptions can exist
    # without being linked to an appointment.
    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    issued_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    status: Mapped[PrescriptionStatus] = mapped_column(
        Enum(PrescriptionStatus, name="prescription_status",
             native_enum=False),
        default=PrescriptionStatus.ACTIVE,
        nullable=False
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # Relationships

    patient = relationship(
        "Patient",
        back_populates="prescriptions"
    )

    provider = relationship(
        "Provider",
        back_populates="prescriptions"
    )

    appointment = relationship(
        "Appointment",
        back_populates="prescriptions"
    )

    items = relationship(
        "PrescriptionItem",
        back_populates="prescription",
        cascade="all, delete-orphan"
    )
