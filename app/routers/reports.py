from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.transfer import Transfer
from app.services.account_service import get_all_account_balances


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)


@router.get("/summary")
def get_report_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    account_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Transaction).filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
    )

    if account_id:
        query = query.filter(
            Transaction.account_id == account_id
        )

    transactions = query.all()

    total_income = Decimal("0")
    total_expenses = Decimal("0")

    for transaction in transactions:
        if transaction.type == "income":
            total_income += transaction.amount
        elif transaction.type == "expense":
            total_expenses += transaction.amount

    net_cash_flow = (
        total_income - total_expenses
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "account_id": account_id,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": net_cash_flow,
        "transaction_count": len(transactions),
    }


@router.get("/categories")
def get_category_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    type: str = Query("expense"),
    account_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Category.id,
            Category.name,
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            ).label("total"),
        )
        .join(
            Transaction,
            Transaction.category_id == Category.id,
        )
        .filter(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.type == type,
        )
        .group_by(
            Category.id,
            Category.name,
        )
        .order_by(
            func.sum(Transaction.amount).desc()
        )
    )

    if account_id:
        query = query.filter(
            Transaction.account_id == account_id
        )

    results = query.all()

    return [
        {
            "category_id": row.id,
            "category_name": row.name,
            "total": row.total,
        }
        for row in results
    ]


@router.get("/monthly")
def get_monthly_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    account_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Transaction).filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
    )

    if account_id:
        query = query.filter(
            Transaction.account_id == account_id
        )

    transactions = query.all()

    monthly = {}

    for transaction in transactions:
        month = transaction.transaction_date.strftime(
            "%Y-%m"
        )

        if month not in monthly:
            monthly[month] = {
                "month": month,
                "income": Decimal("0"),
                "expenses": Decimal("0"),
            }

        if transaction.type == "income":
            monthly[month]["income"] += (
                transaction.amount
            )
        else:
            monthly[month]["expenses"] += (
                transaction.amount
            )

    result = []

    for month in sorted(monthly):
        income = monthly[month]["income"]
        expenses = monthly[month]["expenses"]

        result.append(
            {
                "month": month,
                "income": income,
                "expenses": expenses,
                "net_cash_flow": income - expenses,
            }
        )

    return result


@router.get("/accounts")
def get_account_report(
    db: Session = Depends(get_db),
):
    account_balances = get_all_account_balances(db)

    assets = []
    liabilities = []

    for item in account_balances:
        account = item["account"]
        balance = item["balance"]

        data = {
            "account_id": account.id,
            "account_name": account.name,
            "account_type": account.account_type,
            "account_class": account.account_class,
            "currency": account.currency,
            "balance": balance,
        }

        if account.account_class == "asset":
            assets.append(data)
        else:
            liabilities.append(data)

    total_assets = sum(
        (
            item["balance"]
            for item in assets
        ),
        Decimal("0"),
    )

    total_liabilities = sum(
        (
            item["balance"]
            for item in liabilities
        ),
        Decimal("0"),
    )

    return {
        "assets": assets,
        "liabilities": liabilities,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "net_worth": (
            total_assets - total_liabilities
        ),
    }