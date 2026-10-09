from sqlalchemy.orm import Session

from app.models.category import Category


DEFAULT_CATEGORIES = [
    # Income
    ("Salary", "income"),
    ("Freelance", "income"),
    ("Business", "income"),
    ("Interest", "income"),
    ("Investment", "income"),
    ("Parents", "income"),
    ("Other Income", "income"),

    # Expenses
    ("Food", "expense"),
    ("Groceries", "expense"),
    ("Rent", "expense"),
    ("Utilities", "expense"),
    ("Transportation", "expense"),
    ("Fuel", "expense"),
    ("Shopping", "expense"),
    ("Healthcare", "expense"),
    ("Education", "expense"),
    ("Entertainment", "expense"),
    ("Travel", "expense"),
    ("Insurance", "expense"),
    ("Subscriptions", "expense"),
    ("Personal Care", "expense"),
    ("Other Expense", "expense"),
]


def seed_default_categories(db: Session):
    for name, category_type in DEFAULT_CATEGORIES:
        existing = (
            db.query(Category)
            .filter(
                Category.name == name,
                Category.type == category_type,
            )
            .first()
        )

        if not existing:
            db.add(
                Category(
                    name=name,
                    type=category_type,
                )
            )

    db.commit()
