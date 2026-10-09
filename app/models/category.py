from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    # __table_args__ = (
    #     UniqueConstraint(
    #         "name",
    #         "type",
    #         name="uq_category_name_type",
    #     ),
    # )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100),nullable=False,)
    type: Mapped[str] = mapped_column(String(20),nullable=False,)
    is_active: Mapped[bool] = mapped_column(Boolean,default=True,nullable=False,)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow,nullable=False,)
    transactions = relationship("Transaction",back_populates="category",)
    