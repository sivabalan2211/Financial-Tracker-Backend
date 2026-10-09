from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(primary_key=True,index=True,)
    from_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"),nullable=False,)
    to_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"),nullable=False,)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2),nullable=False,)
    transfer_date: Mapped[date] = mapped_column(Date,nullable=False,)
    description: Mapped[str | None] = mapped_column(String(500),nullable=True,)
    reference: Mapped[str | None] = mapped_column(String(100),nullable=True,)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow,nullable=False,)
    