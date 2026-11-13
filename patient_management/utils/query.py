import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Query


def apply_sort(
    query: Query,
    model,
    sort: str | None,
    allowed_fields: set[str]
):
    if not sort:
        return query

    for field in sort.split(","):

        field = field.strip()

        is_desc = field.startswith("desc:")

        field_name = (
            field.replace("desc:", "", 1)
            if is_desc
            else field
        )

        if field_name not in allowed_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sorting by '{field_name}' is not allowed"
            )

        column = getattr(model, field_name)

        if is_desc:
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    return query


def paginate_query(
    query: Query,
    page: int,
    limit: int
):

    total_record = query.count()

    total_pages = (
        math.ceil(total_record / limit)
        if total_record
        else 0
    )

    offset = (page - 1) * limit

    content = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "page_number": page,
        "page_size": limit,
        "total_pages": total_pages,
        "total_record": total_record,
        "content": content
    }