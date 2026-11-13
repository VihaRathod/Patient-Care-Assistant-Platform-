
from sqlalchemy import (
    ForeignKey,
    Text,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class VisitNote(Base, TimestampMixin):

    __tablename__ = "visit_notes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True
    )

    symptoms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    diagnosis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    treatment_plan: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    follow_up_instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Relationships

    appointment = relationship(
        "Appointment",
        back_populates="visit_note"
    )
