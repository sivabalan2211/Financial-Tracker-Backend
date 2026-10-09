from decimal import Decimal
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.transfer import Transfer


def get_transaction_totals(
    db: Session,
    account_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
):
    income_query = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.account_id == account_id,
            Transaction.type == "income",
        )
    )

    expense_query = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.account_id == account_id,
            Transaction.type == "expense",
        )
    )
    
    if start_date:
        income_query = income_query.filter(
            Transaction.transaction_date >= start_date
        )

        expense_query = expense_query.filter(
            Transaction.transaction_date >= start_date
        )

    if end_date:
        income_query = income_query.filter(
            Transaction.transaction_date <= end_date
        )

        expense_query = expense_query.filter(
            Transaction.transaction_date <= end_date
        )

    income = income_query.scalar() or Decimal("0")
    expenses = expense_query.scalar() or Decimal("0")

    return (
        Decimal(str(income)),
        Decimal(str(expenses)),
    )


def get_transfer_totals(
    db: Session,
    account_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
):
    incoming_query = (
        db.query(
            func.coalesce(
                func.sum(Transfer.amount),
                0,
            )
        )
        .filter(
            Transfer.to_account_id == account_id
        )
    )

    outgoing_query = (
        db.query(
            func.coalesce(
                func.sum(Transfer.amount),
                0,
            )
        )
        .filter(
            Transfer.from_account_id == account_id
        )
    )

    if start_date:
        incoming_query = incoming_query.filter(
            Transfer.transfer_date >= start_date
        )

        outgoing_query = outgoing_query.filter(
            Transfer.transfer_date >= start_date
        )

    if end_date:
        incoming_query = incoming_query.filter(
            Transfer.transfer_date <= end_date
        )

        outgoing_query = outgoing_query.filter(
            Transfer.transfer_date <= end_date
        )

    incoming = incoming_query.scalar() or Decimal("0")
    outgoing = outgoing_query.scalar() or Decimal("0")

    return (
        Decimal(str(incoming)),
        Decimal(str(outgoing)),
    )


def get_balance_at_date(
    db: Session,
    account: Account,
    as_of_date: date,
):
    """
    Balance after all activity on or before as_of_date.
    """
    income, expenses = get_transaction_totals(
        db,
        account.id,
        end_date=as_of_date,
    )

    transfers_in, transfers_out = get_transfer_totals(
        db,
        account.id,
        end_date=as_of_date,
    )

    return (
        Decimal(str(account.opening_balance))
        + income
        - expenses
        + transfers_in
        - transfers_out
    )


def get_opening_balance(
    db: Session,
    account: Account,
    start_date: date,
):
    """
    Balance immediately before the statement period.
    """

    previous_day = start_date.fromordinal(
        start_date.toordinal() - 1
    )

    return get_balance_at_date(
        db,
        account,
        previous_day,
    )


def get_period_summary(
    db: Session,
    account: Account,
    start_date: date,
    end_date: date,
):
    income, expenses = get_transaction_totals(
        db,
        account.id,
        start_date=start_date,
        end_date=end_date,
    )

    transfers_in, transfers_out = get_transfer_totals(
        db,
        account.id,
        start_date=start_date,
        end_date=end_date,
    )

    opening_balance = get_opening_balance(
        db,
        account,
        start_date,
    )

    closing_balance = (
        opening_balance
        + income
        - expenses
        + transfers_in
        - transfers_out
    )

    return {
        "opening_balance": opening_balance,
        "income": income,
        "expenses": expenses,
        "transfers_in": transfers_in,
        "transfers_out": transfers_out,
        "net_cash_flow": (
            income
            - expenses
            + transfers_in
            - transfers_out
        ),
        "closing_balance": closing_balance,
    }


def get_account_balance(
    db: Session,
    account: Account,
):
    return get_balance_at_date(
        db,
        account,
        date.today(),
    )


def get_all_account_balances(
    db: Session,
):
    accounts = (
        db.query(Account)
        .filter(Account.is_active.is_(True))
        .order_by(Account.name)
        .all()
    )

    return [
        {
            "account": account,
            "balance": get_account_balance(
                db,
                account,
            ),
        }
        for account in accounts
    ]


def get_net_worth(
    db: Session,
):
    account_balances = get_all_account_balances(db)

    assets = Decimal("0")
    liabilities = Decimal("0")

    for item in account_balances:
        account = item["account"]
        balance = item["balance"]

        if account.account_class == "asset":
            assets += balance
        elif account.account_class == "liability":
            liabilities += balance

    return {
        "assets": assets,
        "liabilities": liabilities,
        "net_worth": assets - liabilities,
    }

