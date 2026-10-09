from decimal import Decimal
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.transfer import Transfer

from app.services.account_service import (
    get_all_account_balances,
    get_net_worth,
)

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


def transaction_total(
    db: Session,
    transaction_type: str,
):
    return (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.type == transaction_type
        )
        .scalar()
    )


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
):
    accounts = (
        db.query(Account)
        .filter(Account.is_active.is_(True))
        .order_by(Account.name)
        .all()
    )

    total_income = transaction_total(
        db,
        "income",
    )

    total_expenses = transaction_total(
        db,
        "expense",
    )

    account_data = []

    total_assets = Decimal("0")
    total_liabilities = Decimal("0")

    for account in accounts:
        income = (
            db.query(
                func.coalesce(
                    func.sum(Transaction.amount),
                    0,
                )
            )
            .filter(
                Transaction.account_id == account.id,
                Transaction.type == "income",
            )
            .scalar()
        )

        expenses = (
            db.query(
                func.coalesce(
                    func.sum(Transaction.amount),
                    0,
                )
            )
            .filter(
                Transaction.account_id == account.id,
                Transaction.type == "expense",
            )
            .scalar()
        )

        transfers_in = (
            db.query(
                func.coalesce(
                    func.sum(Transfer.amount),
                    0,
                )
            )
            .filter(
                Transfer.to_account_id == account.id,
            )
            .scalar()
        )

        transfers_out = (
            db.query(
                func.coalesce(
                    func.sum(Transfer.amount),
                    0,
                )
            )
            .filter(
                Transfer.from_account_id == account.id,
            )
            .scalar()
        )

        balance = (
            account.opening_balance
            + Decimal(str(income))
            - Decimal(str(expenses))
            + Decimal(str(transfers_in))
            - Decimal(str(transfers_out))
        )

        if account.account_class == "asset":
            total_assets += balance
        else:
            total_liabilities += balance

        account_data.append(
            {
                "id": account.id,
                "name": account.name,
                "account_type": account.account_type,
                "account_class": account.account_class,
                "currency": account.currency,
                "balance": balance,
            }
        )

    recent_transactions = (
        db.query(Transaction)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .limit(10)
        .all()
    )

    recent_data = []

    for transaction in recent_transactions:
        recent_data.append(
            {
                "id": transaction.id,
                "account_id": transaction.account_id,
                "category_id": transaction.category_id,
                "type": transaction.type,
                "amount": transaction.amount,
                "transaction_date": transaction.transaction_date,
                "description": transaction.description,
                "reference": transaction.reference,
            }
        )

    net_worth = (
        total_assets
        - total_liabilities
    )

    net_cash_flow = (
        Decimal(str(total_income))
        - Decimal(str(total_expenses))
    )

    account_balances = get_all_account_balances(db)

    account_data = []

    for item in account_balances:
        account = item["account"]
        balance = item["balance"]

    account_data.append(
        {
            "id": account.id,
            "name": account.name,
            "account_type": account.account_type,
            "account_class": account.account_class,
            "currency": account.currency,
            "balance": balance,
        }
    )

    net_worth_data = get_net_worth(db)

    total_assets = net_worth_data["assets"]
    total_liabilities = net_worth_data["liabilities"]
    net_worth = net_worth_data["net_worth"]

    return {
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "net_worth": net_worth,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": net_cash_flow,
        "accounts": account_data,
        "recent_transactions": recent_data,
    }

@router.get("/overview")
def dashboard_overview(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    summary = get_report_summary_data(
        db,
        start_date,
        end_date,
    )

    accounts = get_all_account_balances(db)
    net_worth = get_net_worth(db)

    return {
        "summary": summary,
        "accounts": [
            {
                "id": item["account"].id,
                "name": item["account"].name,
                "balance": item["balance"],
                "currency": item["account"].currency,
            }
            for item in accounts
        ],
        "net_worth": net_worth,
    }
