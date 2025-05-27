# streamlit_app/pages/Overview.py

import streamlit as st
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.crud import get_sales_in_range, get_expenses_in_range
import pandas as pd

st.title("📊 Daily Business Overview")

# Setup DB session
session = SessionLocal()

# Time ranges
today = datetime.today().date()
start_of_week = today - timedelta(days=today.weekday())
start_of_month = today.replace(day=1)

def compute_totals(start_date, end_date):
    sales = get_sales_in_range(session, start_date, end_date)
    expenses = get_expenses_in_range(session, start_date, end_date)

    total_sales = sum(s.total_sale for s in sales)
    total_expenses = sum(e.amount for e in expenses)
    net = total_sales - total_expenses

    return total_sales, total_expenses, net

# KPIs
col1, col2, col3 = st.columns(3)
daily_sales, daily_expenses, daily_net = compute_totals(today, today)
weekly_sales, weekly_expenses, weekly_net = compute_totals(start_of_week, today)
monthly_sales, monthly_expenses, monthly_net = compute_totals(start_of_month, today)

col1.metric("📅 Today's Sales", f"{daily_sales:.2f} TRY")
col2.metric("📅 Today's Expenses", f"{daily_expenses:.2f} TRY")
col3.metric("📅 Net Profit", f"{daily_net:.2f} TRY")

# Table: Last 10 Sales
st.subheader("🧾 Last 10 Sales")
sales_data = get_sales_in_range(session, start_of_month, today)
sales_df = pd.DataFrame([{
    "Item": s.item_name,
    "Category": s.category,
    "Qty": s.quantity_sold,
    "Price": s.price_per_unit,
    "Total": s.total_sale,
    "Date": s.timestamp.date()
} for s in sorted(sales_data, key=lambda x: x.timestamp, reverse=True)[:10]])
st.dataframe(sales_df)

# Table: Last 10 Expenses
st.subheader("💸 Last 10 Expenses")
expenses_data = get_expenses_in_range(session, start_of_month, today)
expenses_df = pd.DataFrame([{
    "Type": e.expense_type,
    "Amount": e.amount,
    "Description": e.description,
    "Date": e.timestamp.date()
} for e in sorted(expenses_data, key=lambda x: x.timestamp, reverse=True)[:10]])
st.dataframe(expenses_df)

# Visualization: Daily totals (sales vs expenses)
st.subheader("📈 Daily Sales vs Expenses This Month")

# Prepare daily grouped data
sales_by_day = {}
for s in sales_data:
    date = s.timestamp.date()
    sales_by_day[date] = sales_by_day.get(date, 0) + s.total_sale

expenses_by_day = {}
for e in expenses_data:
    date = e.timestamp.date()
    expenses_by_day[date] = expenses_by_day.get(date, 0) + e.amount

all_dates = sorted(set(sales_by_day.keys()) | set(expenses_by_day.keys()))
chart_df = pd.DataFrame({
    "Date": all_dates,
    "Sales": [sales_by_day.get(d, 0) for d in all_dates],
    "Expenses": [expenses_by_day.get(d, 0) for d in all_dates],
})

st.line_chart(chart_df.set_index("Date"))

session.close()
