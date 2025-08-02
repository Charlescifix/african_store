import streamlit as st
from datetime import datetime
from app.database import SessionLocal
from app.crud import create_sale


st.title("🛒 Record Daily Sale")

# Setup session state
if "show_total_sale" not in st.session_state:
    st.session_state.show_total_sale = False
if "calculated_sale" not in st.session_state:
    st.session_state.calculated_sale = 0.0

with st.form("sales_form"):
    item_name = st.text_input("Item Name")
    category = st.text_input("Category", value="Food")

    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("Price per unit (TRY)", min_value=0.0, step=0.5)
    with col2:
        quantity = st.number_input("Quantity sold", min_value=1, step=1)

    timestamp = st.date_input("Sale Date", value=datetime.today())

    calc_button = st.form_submit_button("🧮 Check Total Sale and Record")

    if calc_button:
        total_sale = price * quantity
        st.session_state.calculated_sale = total_sale
        st.session_state.show_total_sale = True

    if st.session_state.show_total_sale:
        st.markdown(f"### 💰 Total Sale: **{st.session_state.calculated_sale:.2f} TRY**")
        save_button = st.form_submit_button("✅ Confirm and Save Sale")

        if save_button:
            try:
                session = SessionLocal()
                dt = datetime.combine(timestamp, datetime.min.time())
                create_sale(
                    session=session,
                    item_name=item_name,
                    category=category,
                    price_per_unit=price,
                    quantity_sold=quantity,
                    cost=0.0,  # Placeholder; real cost logic will come later
                    timestamp=dt
                )
                st.success("✅ Sale recorded successfully!")
                st.session_state.show_total_sale = False
            except Exception as e:
                st.error(f"❌ Error saving sale: {e}")
            finally:
                session.close()


