import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.utils.calculations import get_roi
from app.models import Sale, Expense

st.set_page_config(page_title="Kika Stores Food Dashboard", layout="wide")
st.title("🍲 Kika's Store Food Business Tracker")

session = SessionLocal()

# Time ranges
today = datetime.utcnow().date()
week_ago = today - timedelta(days=7)
month_ago = today - timedelta(days=30)

# ROI KPIs
daily_stats = get_roi(session, today, today)
weekly_stats = get_roi(session, week_ago, today)
monthly_stats = get_roi(session, month_ago, today)

col1, col2, col3, col4 = st.columns(4)
col1.metric("📅 Today's Net Profit (TRY)", f"{daily_stats['net_profit']:.2f}")
col2.metric("📆 Weekly ROI (%)", f"{weekly_stats['roi']:.2f}")
col3.metric("📆 Monthly Sales (TRY)", f"{monthly_stats['sales']:.2f}")
col4.metric("📆 Monthly Expenses (TRY)", f"{monthly_stats['expenses']:.2f}")

# Recent Sales Log
st.subheader("🧾 Recent Sales")
sales_rows = session.query(Sale).order_by(Sale.timestamp.desc()).limit(10).all()
for row in sales_rows:
    st.write(f"{row.timestamp.strftime('%Y-%m-%d %H:%M')} — {row.item_name}: {row.quantity_sold} x {row.price_per_unit} = {row.total_sale} TRY")

# Recent Expenses Log
st.subheader("💸 Recent Expenses")
expense_rows = session.query(Expense).order_by(Expense.timestamp.desc()).limit(10).all()
for exp in expense_rows:
    desc = f" ({exp.description})" if exp.description else ""
    st.write(f"{exp.timestamp.strftime('%Y-%m-%d %H:%M')} — {exp.expense_type}: {exp.amount:.2f} TRY{desc}")

session.close()
