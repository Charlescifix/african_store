from sqlalchemy.orm import Session
from app.models import Sale, Expense
from datetime import datetime, timedelta

def get_roi(session: Session, start_date, end_date):
    sales = session.query(Sale).filter(Sale.timestamp >= start_date, Sale.timestamp <= end_date).all()
    expenses = session.query(Expense).filter(Expense.timestamp >= start_date, Expense.timestamp <= end_date).all()

    total_sales = sum([s.total_sale for s in sales])
    total_expenses = sum([e.amount for e in expenses])
    net_profit = total_sales - total_expenses

    roi = (net_profit / total_expenses) * 100 if total_expenses > 0 else 0
    return {
        "sales": total_sales,
        "expenses": total_expenses,
        "net_profit": net_profit,
        "roi": round(roi, 2)
    }
