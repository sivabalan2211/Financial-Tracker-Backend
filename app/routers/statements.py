from datetime import date
from decimal import Decimal
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.database import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.transfer import Transfer
from app.services.account_service import get_account_balance, get_period_summary

router = APIRouter(
    prefix="/api/statements",
    tags=["Statements"],
)


def money(value, currency="INR"):
    symbol = {
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
    }.get(currency, currency + " ")

    return f"{symbol}{float(value):,.2f}"


@router.get("/account/{account_id}/pdf")
def generate_account_statement(
    account_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date",
        )

    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    # --------------------------------------------------
    # Transactions within statement period
    # --------------------------------------------------

    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.account_id == account_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .order_by(
            Transaction.transaction_date.asc(),
            Transaction.id.asc(),
        )
        .all()
    )

    # --------------------------------------------------
    # Opening balance
    #
    # Current balance minus activity during period.
    # --------------------------------------------------

    current_balance = get_account_balance(
        db,
        account,
    )

    period_income = Decimal("0")
    period_expenses = Decimal("0")

    for transaction in transactions:
        if transaction.type == "income":
            period_income += transaction.amount
        else:
            period_expenses += transaction.amount

    transfers_in = (
        db.query(Transfer)
        .filter(
            Transfer.to_account_id == account_id,
            Transfer.transfer_date >= start_date,
            Transfer.transfer_date <= end_date,
        )
        .all()
    )

    transfers_out = (
        db.query(Transfer)
        .filter(
            Transfer.from_account_id == account_id,
            Transfer.transfer_date >= start_date,
            Transfer.transfer_date <= end_date,
        )
        .all()
    )

    transfer_in_total = sum(
        (t.amount for t in transfers_in),
        Decimal("0"),
    )

    transfer_out_total = sum(
        (t.amount for t in transfers_out),
        Decimal("0"),
    )

    period_net = (
        period_income
        - period_expenses
        + transfer_in_total
        - transfer_out_total
    )

    closing_balance = (
        current_balance
    )

    opening_balance = (
        closing_balance - period_net
    )

    summary = get_period_summary(
        db,
        account,
        start_date,
        end_date,
    )

    opening_balance = summary["opening_balance"]
    period_income = summary["income"]
    period_expenses = summary["expenses"]
    transfer_in_total = summary["transfers_in"]
    transfer_out_total = summary["transfers_out"]
    closing_balance = summary["closing_balance"]

    # --------------------------------------------------
    # PDF
    # --------------------------------------------------

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"{account.name} Statement",
        author="Financial Tracker",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "StatementTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=20,
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#334155"),
    )

    story = []

    # --------------------------------------------------
    # Header
    # --------------------------------------------------

    story.append(
        Paragraph(
            "FINANCIAL STATEMENT",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"{account.name} · "
            f"{start_date.strftime('%d %b %Y')} - "
            f"{end_date.strftime('%d %b %Y')}",
            subtitle_style,
        )
    )

    # --------------------------------------------------
    # Account information
    # --------------------------------------------------

    account_data = [
        ["Account", account.name],
        ["Type", account.account_type.replace("_", " ").title()],
        ["Class", account.account_class.title()],
        ["Currency", account.currency],
        ["Statement Period",
         f"{start_date} to {end_date}"],
    ]

    account_table = Table(
        account_data,
        colWidths=[45 * mm, 130 * mm],
    )

    account_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#f1f5f9"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#334155"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#e2e8f0"),
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(account_table)
    story.append(Spacer(1, 10))

    # --------------------------------------------------
    # Balance summary
    # --------------------------------------------------

    story.append(
        Paragraph(
            "Balance Summary",
            heading_style,
        )
    )

    summary_data = [
        ["Opening Balance", money(
            opening_balance,
            account.currency,
        )],
        ["Total Income", money(
            period_income,
            account.currency,
        )],
        ["Total Expenses", money(
            period_expenses,
            account.currency,
        )],
        ["Transfers In", money(
            transfer_in_total,
            account.currency,
        )],
        ["Transfers Out", money(
            transfer_out_total,
            account.currency,
        )],
        ["Closing Balance", money(
            closing_balance,
            account.currency,
        )],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[90 * mm, 85 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#e2e8f0"),
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica",
                ),
                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold",
                ),
                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.HexColor("#f8fafc"),
                ),
            ]
        )
    )

    story.append(summary_table)

    # --------------------------------------------------
    # Transactions
    # --------------------------------------------------

    story.append(
        Paragraph(
            "Transactions",
            heading_style,
        )
    )

    transaction_rows = [
        [
            "Date",
            "Description",
            "Type",
            "Income",
            "Expense",
        ]
    ]

    for transaction in transactions:
        income = (
            money(
                transaction.amount,
                account.currency,
            )
            if transaction.type == "income"
            else ""
        )

        expense = (
            money(
                transaction.amount,
                account.currency,
            )
            if transaction.type == "expense"
            else ""
        )

        transaction_rows.append(
            [
                transaction.transaction_date.strftime(
                    "%d/%m/%Y"
                ),
                transaction.description
                or "Transaction",
                transaction.type.title(),
                income,
                expense,
            ]
        )

    if len(transaction_rows) == 1:
        transaction_rows.append(
            [
                "-",
                "No transactions in this period",
                "-",
                "-",
                "-",
            ]
        )

    transaction_table = Table(
        transaction_rows,
        repeatRows=1,
        colWidths=[
            25 * mm,
            65 * mm,
            25 * mm,
            30 * mm,
            30 * mm,
        ],
    )

    transaction_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0f172a"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#e2e8f0"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#f8fafc"),
                    ],
                ),
                (
                    "ALIGN",
                    (3, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(transaction_table)

    # --------------------------------------------------
    # Footer
    # --------------------------------------------------

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Generated by Financial Tracker",
            subtitle_style,
        )
    )

    document.build(story)

    buffer.seek(0)

    filename = (
        f"{account.name.replace(' ', '_')}_"
        f"{start_date}_{end_date}.pdf"
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )

@router.get("/account/{account_id}")
def get_account_statement(
    account_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date",
        )

    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    summary = get_period_summary(
        db,
        account,
        start_date,
        end_date,
    )

    return {
        "account": {
            "id": account.id,
            "name": account.name,
            "type": account.account_type,
            "class": account.account_class,
            "currency": account.currency,
        },
        "period": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "summary": summary,
    }