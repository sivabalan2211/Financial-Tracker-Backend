
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    account_type: str = Field(min_length=1,max_length=30,)
    opening_balance: Decimal = Field(default=Decimal("0.00"),decimal_places=2,)
    currency: str = Field(default="INR",min_length=3,max_length=3,)

class AccountCreate(AccountBase):
    account_class: str = "asset"

class AccountUpdate(BaseModel):
    name: str | None = None
    account_type: str | None = None
    is_active: bool | None = None

class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
