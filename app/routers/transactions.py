from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
)

router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
)

@router.post(
    "",
    response_model=TransactionResponse,
    status_code=201,
)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
):
    if data.type not in {"income", "expense"}:
        raise HTTPException(
            status_code=400,
            detail="Transaction type must be income or expense",
        )

    account = (
        db.query(Account)
        .filter(
            Account.id == data.account_id,
            Account.is_active.is_(True),
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    category = None

    if data.category_id:
        category = (
            db.query(Category)
            .filter(
                Category.id == data.category_id,
                Category.is_active.is_(True),
            )
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found",
            )

        if category.type != data.type:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Category type is '{category.type}', "
                    f"but transaction type is '{data.type}'"
                ),
            )

    transaction = Transaction(
        account_id=data.account_id,
        category_id=data.category_id,
        type=data.type,
        amount=data.amount,
        transaction_date=data.transaction_date,
        description=data.description,
        reference=data.reference,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


@router.get("", response_model=list[TransactionResponse])
def get_transactions(
    account_id: int | None = None,
    type: str | None = None,
    category_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)

    if account_id:
        query = query.filter(
            Transaction.account_id == account_id
        )

    if type:
        if type not in {"income", "expense"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid transaction type",
            )

        query = query.filter(
            Transaction.type == type
        )

    if category_id:
        query = query.filter(
            Transaction.category_id == category_id
        )

    return (
        query
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .all()
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return transaction


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transaction deleted",
    }