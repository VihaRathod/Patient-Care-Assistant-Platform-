
import enum

from sqlalchemy import (
    ForeignKey,
    Enum,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class AllergySeverity(str, enum.Enum):
    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"


class PatientAllergy(Base, TimestampMixin):

    __tablename__ = "patient_allergies"

    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "allergy_id",
            name="uq_patient_allergy"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    allergy_id: Mapped[int] = mapped_column(
        ForeignKey("allergies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    severity: Mapped[AllergySeverity] = mapped_column(
        Enum(
            AllergySeverity,
            name="allergy_severity",
            native_enum=False
        ),
        nullable=False
    )

    reaction: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # Relationships

    patient = relationship(
        "Patient",
        back_populates="allergies"
    )

    allergy = relationship(
        "Allergy",
        back_populates="patients"
    )
