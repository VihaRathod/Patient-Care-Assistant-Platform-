"""Create repeatable local data for the Appointment Concierge demo.

Run from ``patient_management`` after applying Alembic migrations:
``python3 scripts/seed_appointment_agent_demo.py``.
It is idempotent and is intended only for local development.
"""

from datetime import date, time

from database.connection import SessionLocal
from models.patient import Patient
from models.provider import Provider
from models.provider_availability import ProviderAvailability
from models.provider_specialty import ProviderSpecialty
from models.specialty import Specialty
from models.user import User, UserRole
from utils.password import hash_password


PASSWORD = "DemoPass123!"


def get_or_create_user(db, email: str, role: UserRole) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        email=email,
        password_hash=hash_password(PASSWORD),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_specialty(db, name: str, description: str) -> Specialty:
    specialty = db.query(Specialty).filter(Specialty.name == name).first()
    if not specialty:
        specialty = Specialty(name=name, description=description)
        db.add(specialty)
        db.flush()
    return specialty


def get_or_create_provider(db, email: str, first_name: str, last_name: str) -> Provider:
    user = get_or_create_user(db, email, UserRole.PROVIDER)
    provider = db.query(Provider).filter(Provider.user_id == user.id).first()
    if not provider:
        provider = Provider(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            qualification="MBBS, MD",
            experience=8,
            phone="9000000000",
        )
        db.add(provider)
        db.flush()
    return provider


def ensure_provider_schedule(db, provider: Provider) -> None:
    # Daily 09:00–17:00 schedules make the sample usable on any day of week.
    for day in range(7):
        exists = db.query(ProviderAvailability).filter(
            ProviderAvailability.provider_id == provider.id,
            ProviderAvailability.day_of_week == day,
            ProviderAvailability.start_time == time(9, 0),
            ProviderAvailability.end_time == time(17, 0),
        ).first()
        if not exists:
            db.add(ProviderAvailability(
                provider_id=provider.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_active=True,
            ))


def ensure_specialty(db, provider: Provider, specialty: Specialty) -> None:
    exists = db.query(ProviderSpecialty).filter(
        ProviderSpecialty.provider_id == provider.id,
        ProviderSpecialty.specialty_id == specialty.id,
    ).first()
    if not exists:
        db.add(ProviderSpecialty(provider_id=provider.id, specialty_id=specialty.id))


def main() -> None:
    db = SessionLocal()
    try:
        get_or_create_user(db, "demo.admin@example.com", UserRole.ADMIN)
        patient_user = get_or_create_user(db, "demo.patient@example.com", UserRole.PATIENT)
        if not db.query(Patient).filter(Patient.user_id == patient_user.id).first():
            db.add(Patient(
                user_id=patient_user.id,
                first_name="Priya",
                last_name="Patel",
                date_of_birth=date(1994, 5, 12),
                gender="Female",
                phone="9000000001",
                address="Demo address",
            ))

        general = get_or_create_specialty(db, "General Medicine", "General adult health appointments")
        pulmonary = get_or_create_specialty(db, "Pulmonology", "Respiratory-system appointments")
        asha = get_or_create_provider(db, "dr.asha@example.com", "Asha", "Sharma")
        rohan = get_or_create_provider(db, "dr.rohan@example.com", "Rohan", "Mehta")
        ensure_specialty(db, asha, general)
        ensure_specialty(db, rohan, pulmonary)
        ensure_specialty(db, rohan, general)
        ensure_provider_schedule(db, asha)
        ensure_provider_schedule(db, rohan)
        db.commit()
        print("Appointment Concierge demo data is ready.")
        print("Patient login: demo.patient@example.com / DemoPass123!")
        print("Provider login: dr.asha@example.com / DemoPass123!")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
