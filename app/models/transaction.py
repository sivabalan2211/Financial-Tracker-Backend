from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    # Integer,
    # Column,
    # UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

#     __table_args__ = (
#     UniqueConstraint(
#         "recurring_transaction_id",
#         "transaction_date",
#         name="uq_recurring_transaction_occurrence",
#     ),
# )

    id: Mapped[int] = mapped_column(primary_key=True,index=True,)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"),nullable=False,)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"),nullable=True,)
    type: Mapped[str] = mapped_column(String(20),nullable=False,)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2),nullable=False,)
    transaction_date: Mapped[date] = mapped_column(Date,nullable=False,)
    description: Mapped[str | None] = mapped_column(String(500),nullable=True,)
    reference: Mapped[str | None] = mapped_column(String(100),nullable=True,)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow,nullable=False,)
    updated_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False,)
    account = relationship("Account",back_populates="transactions",)
    category = relationship("Category",back_populates="transactions",)

    # recurring_transaction_id = Column(
    #     Integer,
    #     ForeignKey(
    #         "recurring_transactions.id"
    #     ),
    #     nullable=True,
    # )