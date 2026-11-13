
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_roles
from models.user import User
from schemas.specialty import (
    SpecialtyCreate,
    SpecialtyUpdate,
    SpecialtyResponse
)
from utils.query import apply_sort, paginate_query

from services.specialty_service import (
    create_specialty,
    get_all_specialties,
    get_specialty_by_id,
    update_specialty,
    delete_specialty
)

from schemas.specialty import SpecialtyResponse
from schemas.pagination import PageResponse


router = APIRouter(
    prefix="/specialties",
    tags=["Specialties"]
)


@router.post("/", response_model=SpecialtyResponse, status_code=201)
def add_specialty(
    data: SpecialtyCreate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    return create_specialty(db, data.model_dump())



@router.get(
    "/",
    response_model=PageResponse[SpecialtyResponse]
)
def list_specialties(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    name: str | None = Query(None, min_length=1),
    sort: str | None = Query(None),

    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    return get_all_specialties(
        db=db,
        page=page,
        limit=limit,
        name=name,
        sort=sort
    )

@router.get("/{specialty_id}", response_model=SpecialtyResponse)
def read_specialty(
    specialty_id: int,
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    return get_specialty_by_id(db, specialty_id)


@router.patch("/{specialty_id}", response_model=SpecialtyResponse)
def edit_specialty(
    specialty_id: int,
    data: SpecialtyUpdate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    specialty = get_specialty_by_id(db, specialty_id)

    return update_specialty(
        db,
        specialty,
        data.model_dump(exclude_unset=True)
    )


@router.delete("/{specialty_id}")
def remove_specialty(
    specialty_id: int,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    specialty = get_specialty_by_id(db, specialty_id)

    return delete_specialty(db, specialty)
