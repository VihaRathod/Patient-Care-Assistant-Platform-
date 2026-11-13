
from sqlalchemy import (
    ForeignKey,
    String,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class PrescriptionItem(Base, TimestampMixin):

    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    prescription_id: Mapped[int] = mapped_column(
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    medication_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    dosage: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    frequency: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    duration_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Relationship

    prescription = relationship(
        "Prescription",
        back_populates="items"
    )
