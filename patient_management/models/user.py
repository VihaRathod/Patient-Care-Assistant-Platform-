
import enum

from sqlalchemy import (
    String,
    Boolean,
    Enum,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


# User roles
class UserRole(str, enum.Enum):
    PATIENT = "PATIENT"
    PROVIDER = "PROVIDER"
    ADMIN = "ADMIN"


class User(Base, TimestampMixin):

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Login email
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    # Hashed password
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # User role
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        default=UserRole.PATIENT,
        nullable=False
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationships

    patient = relationship(
        "Patient",
        back_populates="user",
        uselist=False
    )

    provider = relationship(
        "Provider",
        back_populates="user",
        uselist=False
    )
