from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account import Account
from app.schemas.account import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
)
from app.services.account_service import get_account_balance as get_account_bal
# from app.services.account_service import get_transaction_totals, get_transfer_totals

router = APIRouter(
    prefix="/api/accounts",
    tags=["Accounts"],
)

@router.post(
    "",
    response_model=AccountResponse,
    status_code=201,
)

def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
):
    account = Account(
        name=data.name,
        account_type=data.account_type,
        opening_balance=data.opening_balance,
        currency=data.currency.upper(),
    )
    
    if data.account_class not in {"asset", "liability"}:
        raise HTTPException(
            status_code=400,
            detail="Account class must be asset or liability",
        )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@router.get("", response_model=list[AccountResponse])
def get_accounts(
    db: Session = Depends(get_db),
):
    return (
        db.query(Account)
        .filter(Account.is_active.is_(True))
        .order_by(Account.name)
        .all()
    )


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    data: AccountUpdate,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    updates = data.model_dump(exclude_unset=True)

    for key, value in updates.items():
        setattr(account, key, value)

    db.commit()
    db.refresh(account)

    return account


@router.delete("/{account_id}")
def deactivate_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    account.is_active = False

    db.commit()

    return {
        "message": "Account deactivated",
    }


@router.get("/{account_id}/balance")
def get_account_balance(
    account_id: int,
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )
    
    balance = get_account_bal(
        db,
        account,
    )
    
    # income, expenses = get_transaction_totals()
    # transfers_in, transfers_out = get_transfer_totals()

    return {
        "account_id": account.id,
        "account_name": account.name,
        "account_class": account.account_class,
        "currency": account.currency,
        "opening_balance": account.opening_balance,
        # "income": income,
        # "expenses": expenses,
        # "transfers_in": transfers_in,
        # "transfers_out": transfers_out,
        "balance": balance,
    }