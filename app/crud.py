from sqlalchemy.orm import Session
from app.models import Sale, Expense
from datetime import datetime

# -----------------------------
# 💰 SALES FUNCTIONS
# -----------------------------

def create_sale(
    session: Session,
    item_name: str,
    category: str,
    price_per_unit: float,
    quantity_sold: int,
    cost: float,
    timestamp: datetime = None
):
    """
    Inserts a new sales record into the database.
    Calculates total_sale and profit automatically.
    """
    total_sale = price_per_unit * quantity_sold
    profit = total_sale - cost

    sale = Sale(
        item_name=item_name,
        category=category,
        price_per_unit=price_per_unit,
        quantity_sold=quantity_sold,
        total_sale=total_sale,
        cost=cost,
        profit=profit,
        timestamp=timestamp or datetime.utcnow()
    )

    session.add(sale)
    session.commit()
    session.refresh(sale)
    return sale

def get_recent_sales(session: Session, limit: int = 10):
    """
    Fetches the most recent sales up to the specified limit.
    """
    return session.query(Sale).order_by(Sale.timestamp.desc()).limit(limit).all()


# -----------------------------
# 🧾 EXPENSES FUNCTIONS
# -----------------------------

def create_expense(
    session: Session,
    expense_type: str,
    amount: float,
    description: str = None,
    timestamp: datetime = None
):
    """
    Inserts a new expense record into the database.
    """
    expense = Expense(
        expense_type=expense_type,
        amount=amount,
        description=description,
        timestamp=timestamp or datetime.utcnow()
    )

    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense

def get_recent_expenses(session: Session, limit: int = 10):
    """
    Fetches the most recent expenses up to the specified limit.
    """
    return session.query(Expense).order_by(Expense.timestamp.desc()).limit(limit).all()


# -----------------------------
# 📅 FILTERED QUERY HELPERS
# -----------------------------

def get_sales_in_range(session: Session, start_date, end_date):
    """
    Returns all sales between start_date and end_date.
    """
    return session.query(Sale).filter(Sale.timestamp >= start_date, Sale.timestamp <= end_date).all()

def get_expenses_in_range(session: Session, start_date, end_date):
    """
    Returns all expenses between start_date and end_date.
    """
    return session.query(Expense).filter(Expense.timestamp >= start_date, Expense.timestamp <= end_date).all()
