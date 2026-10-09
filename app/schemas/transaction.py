from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class TransactionCreate(BaseModel):
    account_id: int
    category_id: int | None = None
    type: str = Field(description="income or expense",)
    amount: Decimal = Field(gt=0,decimal_places=2,)
    transaction_date: date
    description: str | None = None
    reference: str | None = None

class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    category_id: int | None
    type: str
    amount: Decimal
    transaction_date: date
    description: str | None
    reference: str | None
