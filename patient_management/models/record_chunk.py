
from sqlalchemy import (
    ForeignKey,
    String,
    Integer,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin


class RecordChunk(Base, TimestampMixin):

    __tablename__ = "record_chunks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # VISIT_NOTE, PRESCRIPTION, etc.
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # ID of the original record
    source_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # Actual text content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Numerical embedding representation
    embedding: Mapped[list[float] | None] = mapped_column(
        JSON,
        nullable=True
    )
