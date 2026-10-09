from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(gt=0,decimal_places=2,)
    transfer_date: date
    description: str | None = None
    reference: str | None = None

class TransferResponse(TransferCreate):
    id: int
