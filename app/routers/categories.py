from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
)

router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"],
)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=201,
)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
):
    category_type = data.type.lower()

    if category_type not in {"income", "expense"}:
        raise HTTPException(
            status_code=400,
            detail="Category type must be income or expense",
        )

    existing = (
        db.query(Category)
        .filter(
            Category.name == data.name,
            Category.type == category_type,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Category already exists",
        )

    category = Category(
        name=data.name,
        type=category_type,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.get("", response_model=list[CategoryResponse])
def get_categories(
    type: str | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(Category)
        .filter(Category.is_active.is_(True))
    )

    if type:
        category_type = type.lower()

        if category_type not in {"income", "expense"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid category type",
            )

        query = query.filter(
            Category.type == category_type
        )

    return query.order_by(Category.name).all()


@router.delete("/{category_id}")
def deactivate_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    category.is_active = False

    db.commit()

    return {
        "message": "Category deactivated",
    }