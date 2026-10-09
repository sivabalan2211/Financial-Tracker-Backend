from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100),nullable=False,)
    account_type: Mapped[str] = mapped_column(String(30),nullable=False,)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2),default=0,nullable=False,)
    currency: Mapped[str] = mapped_column(String(3),default="INR",nullable=False,)
    is_active: Mapped[bool] = mapped_column(Boolean,default=True,nullable=False,)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow,nullable=False,)
    updated_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False,)
    transactions = relationship("Transaction",back_populates="account",)
    account_class: Mapped[str] = mapped_column(String(20),nullable=False,default="asset",)
