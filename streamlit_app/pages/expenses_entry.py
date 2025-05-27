import streamlit as st
from datetime import datetime
from app.database import SessionLocal
from app.crud import create_expense

st.title("💸 Record Daily Expense")

with st.form("expense_form"):
    expense_type = st.text_input("Expense Type", placeholder="e.g. Transport, Items, Electricity")
    amount = st.number_input("Amount (TRY)", min_value=0.0, step=1.0)
    description = st.text_area("Description (optional)", placeholder="More details if needed...")
    timestamp = st.date_input("Expense Date", value=datetime.today())

    submitted = st.form_submit_button("✅ Save Expense")
    if submitted:
        try:
            session = SessionLocal()
            dt = datetime.combine(timestamp, datetime.min.time())
            create_expense(
                session=session,
                expense_type=expense_type,
                amount=amount,
                description=description,
                timestamp=dt
            )
            st.success("✅ Expense recorded successfully!")
        except Exception as e:
            st.error(f"❌ Error saving expense: {e}")
        finally:
            session.close()
