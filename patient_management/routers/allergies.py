
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_roles
from models.user import User

from schemas.allergy import (
    AllergyCreate,
    AllergyUpdate,
    AllergyResponse
)
from fastapi import APIRouter, Depends, Query
from schemas.pagination import PageResponse
from services.allergy_service import (
    create_allergy,
    get_all_allergies,
    get_allergy_by_id,
    update_allergy,
    delete_allergy
)


router = APIRouter(
    prefix="/allergies",
    tags=["Allergies"]
)


@router.post("/", response_model=AllergyResponse, status_code=201)
def add_allergy(
    data: AllergyCreate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    return create_allergy(db, data.model_dump())


@router.get(
    "/",
    response_model=PageResponse[AllergyResponse]
)
def list_allergies(

    page: int = Query(
        1,
        ge=1
    ),

    limit: int = Query(
        10,
        ge=1,
        le=100
    ),

    name: str | None = Query(None),

    description: str | None = Query(None),

    sort: str | None = Query(None),

    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),

    db: Session = Depends(get_db)
):

    return get_all_allergies(
        db=db,
        page=page,
        limit=limit,
        name=name,
        description=description,
        sort=sort
    )


@router.get("/{allergy_id}", response_model=AllergyResponse)
def read_allergy(
    allergy_id: int,
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    return get_allergy_by_id(db, allergy_id)


@router.patch("/{allergy_id}", response_model=AllergyResponse)
def edit_allergy(
    allergy_id: int,
    data: AllergyUpdate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    allergy = get_allergy_by_id(db, allergy_id)

    return update_allergy(
        db,
        allergy,
        data.model_dump(exclude_unset=True)
    )


@router.delete("/{allergy_id}")
def remove_allergy(
    allergy_id: int,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    allergy = get_allergy_by_id(db, allergy_id)

    return delete_allergy(db, allergy)
