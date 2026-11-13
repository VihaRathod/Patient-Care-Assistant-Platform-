
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class Specialty(Base, TimestampMixin):

    __tablename__ = "specialties"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # Relationships

    providers = relationship(
        "ProviderSpecialty",
        back_populates="specialty"
    )
