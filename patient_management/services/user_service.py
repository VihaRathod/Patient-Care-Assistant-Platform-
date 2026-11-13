
from sqlalchemy.orm import Session

from models.user import User, UserRole
from models.patient import Patient

from schemas.auth import PatientRegisterRequest

from utils.password import hash_password


def create_patient_user(
    db: Session,
    user_data: PatientRegisterRequest
):

    # 1. Check whether email already exists

    existing_user = (
        db.query(User)
        .filter(
            User.email == user_data.email
        )
        .first()
    )

    if existing_user:
        return None, "Email already registered"

    try:

        # 2. Create User

        user = User(
            email=user_data.email,

            password_hash=hash_password(
                user_data.password
            ),

            role=UserRole.PATIENT,

            is_active=True
        )

        db.add(user)

        # Generate user.id before creating Patient

        db.flush()

        # 3. Create Patient profile

        patient = Patient(
            user_id=user.id,

            first_name=user_data.first_name,

            last_name=user_data.last_name,

            date_of_birth=user_data.date_of_birth,

            gender=user_data.gender,

            phone=user_data.phone,

            address=user_data.address
        )

        db.add(patient)

        # 4. Save both records

        db.commit()

        db.refresh(user)

        return user, None

    except Exception:

        db.rollback()

        raise
