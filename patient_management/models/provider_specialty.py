
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class ProviderSpecialty(Base, TimestampMixin):

    __tablename__ = "provider_specialties"

    __table_args__ = (
        UniqueConstraint(
            "provider_id",
            "specialty_id",
            name="uq_provider_specialty"
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

    specialty_id: Mapped[int] = mapped_column(
        ForeignKey("specialties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships

    provider = relationship(
        "Provider",
        back_populates="specialties"
    )

    specialty = relationship(
        "Specialty",
        back_populates="providers"
    )
