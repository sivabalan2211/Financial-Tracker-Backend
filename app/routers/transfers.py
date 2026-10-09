from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account import Account
from app.models.transfer import Transfer
from app.schemas.transfer import (
    TransferCreate,
    TransferResponse,
)

router = APIRouter(
    prefix="/api/transfers",
    tags=["Transfers"],
)


@router.post(
    "",
    response_model=TransferResponse,
    status_code=201,
)
def create_transfer(
    data: TransferCreate,
    db: Session = Depends(get_db),
):
    if data.from_account_id == data.to_account_id:
        raise HTTPException(
            status_code=400,
            detail="Source and destination accounts must be different",
        )

    source = (
        db.query(Account)
        .filter(
            Account.id == data.from_account_id,
            Account.is_active.is_(True),
        )
        .first()
    )

    if not source:
        raise HTTPException(
            status_code=404,
            detail="Source account not found",
        )

    destination = (
        db.query(Account)
        .filter(
            Account.id == data.to_account_id,
            Account.is_active.is_(True),
        )
        .first()
    )

    if not destination:
        raise HTTPException(
            status_code=404,
            detail="Destination account not found",
        )

    transfer = Transfer(
        from_account_id=data.from_account_id,
        to_account_id=data.to_account_id,
        amount=data.amount,
        transfer_date=data.transfer_date,
        description=data.description,
        reference=data.reference,
    )

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    return transfer


@router.get("", response_model=list[TransferResponse])
def get_transfers(
    account_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Transfer)

    if account_id:
        query = query.filter(
            (Transfer.from_account_id == account_id)
            | (Transfer.to_account_id == account_id)
        )

    return (
        query
        .order_by(
            Transfer.transfer_date.desc(),
            Transfer.id.desc(),
        )
        .all()
    )


@router.delete("/{transfer_id}")
def delete_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
):
    transfer = (
        db.query(Transfer)
        .filter(Transfer.id == transfer_id)
        .first()
    )

    if not transfer:
        raise HTTPException(
            status_code=404,
            detail="Transfer not found",
        )

    db.delete(transfer)
    db.commit()

    return {
        "message": "Transfer deleted",
    }