import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from app.database import SessionLocal
from app.utils.calculations import get_roi
from app.models import Sale, Expense
from app.crud import get_sales_in_range, get_expenses_in_range

# Page config
st.set_page_config(
    page_title="Kika's Store Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .success-metric {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .warning-metric {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .stSelectbox > div > div {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session
@st.cache_resource
def init_db_session():
    return SessionLocal()


session = init_db_session()

# Header
st.markdown("# 🍲 Kika's Store Business Intelligence Dashboard")
st.markdown("*Real-time insights for your food business success* 📈")

# Sidebar for filters and controls
with st.sidebar:
    st.markdown("## 🎛️ Dashboard Controls")

    # Date range selector
    date_range = st.selectbox(
        "📅 Select Time Period",
        ["Today", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"],
        index=2
    )

    if date_range == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now().date())
    else:
        today = datetime.utcnow().date()
        if date_range == "Today":
            start_date, end_date = today, today
        elif date_range == "Last 7 Days":
            start_date, end_date = today - timedelta(days=7), today
        elif date_range == "Last 30 Days":
            start_date, end_date = today - timedelta(days=30), today
        elif date_range == "Last 90 Days":
            start_date, end_date = today - timedelta(days=90), today

    # Chart type selector
    chart_type = st.selectbox(
        "📊 Primary Chart Type",
        ["Line Chart", "Bar Chart", "Area Chart", "Scatter Plot"]
    )

    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()


# Get data for selected period
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_dashboard_data(start_date, end_date):
    sales_data = get_sales_in_range(session, start_date, end_date)
    expenses_data = get_expenses_in_range(session, start_date, end_date)

    # Calculate metrics
    total_sales = sum(s.total_sale for s in sales_data)
    total_expenses = sum(e.amount for e in expenses_data)
    net_profit = total_sales - total_expenses
    roi = (net_profit / total_expenses * 100) if total_expenses > 0 else 0

    # Prepare daily data
    sales_by_day = {}
    expenses_by_day = {}

    for s in sales_data:
        date = s.timestamp.date()
        sales_by_day[date] = sales_by_day.get(date, 0) + s.total_sale

    for e in expenses_data:
        date = e.timestamp.date()
        expenses_by_day[date] = expenses_by_day.get(date, 0) + e.amount

    return {
        'sales_data': sales_data,
        'expenses_data': expenses_data,
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'roi': roi,
        'sales_by_day': sales_by_day,
        'expenses_by_day': expenses_by_day
    }


data = get_dashboard_data(start_date, end_date)

# KPI Metrics Row
st.markdown("## 🎯 Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="💰 Total Sales",
        value=f"{data['total_sales']:.2f} TRY",
        delta=f"{data['total_sales'] / max(1, len(data['sales_by_day'])):.2f} avg/day"
    )

with col2:
    st.metric(
        label="💸 Total Expenses",
        value=f"{data['total_expenses']:.2f} TRY",
        delta=f"{data['total_expenses'] / max(1, len(data['expenses_by_day'])):.2f} avg/day"
    )

with col3:
    profit_color = "normal" if data['net_profit'] >= 0 else "inverse"
    st.metric(
        label="📈 Net Profit",
        value=f"{data['net_profit']:.2f} TRY",
        delta=f"{data['roi']:.1f}% ROI",
        delta_color=profit_color
    )

with col4:
    avg_transaction = data['total_sales'] / max(1, len(data['sales_data']))
    st.metric(
        label="🛒 Avg Transaction",
        value=f"{avg_transaction:.2f} TRY",
        delta=f"{len(data['sales_data'])} transactions"
    )

with col5:
    # Calculate top selling category
    category_sales = {}
    for s in data['sales_data']:
        category_sales[s.category] = category_sales.get(s.category, 0) + s.total_sale
    top_category = max(category_sales.items(), key=lambda x: x[1])[0] if category_sales else "N/A"
    st.metric(
        label="🏆 Top Category",
        value=top_category,
        delta=f"{max(category_sales.values()) if category_sales else 0:.0f} TRY"
    )

# Main Charts Section
st.markdown("## 📊 Performance Analytics")

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["💹 Trends", "🔍 Analysis", "🏪 Categories", "📋 Recent Activity"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        # Sales vs Expenses Chart
        all_dates = sorted(set(data['sales_by_day'].keys()) | set(data['expenses_by_day'].keys()))
        chart_df = pd.DataFrame({
            'Date': all_dates,
            'Sales': [data['sales_by_day'].get(d, 0) for d in all_dates],
            'Expenses': [data['expenses_by_day'].get(d, 0) for d in all_dates],
            'Net Profit': [data['sales_by_day'].get(d, 0) - data['expenses_by_day'].get(d, 0) for d in all_dates]
        })

        fig = go.Figure()

        if chart_type == "Line Chart":
            fig.add_trace(go.Scatter(x=chart_df['Date'], y=chart_df['Sales'],
                                     name='Sales', line=dict(color='#2E8B57', width=3)))
            fig.add_trace(go.Scatter(x=chart_df['Date'], y=chart_df['Expenses'],
                                     name='Expenses', line=dict(color='#DC143C', width=3)))
            fig.add_trace(go.Scatter(x=chart_df['Date'], y=chart_df['Net Profit'],
                                     name='Net Profit', line=dict(color='#4169E1', width=3)))
        elif chart_type == "Bar Chart":
            fig.add_trace(go.Bar(x=chart_df['Date'], y=chart_df['Sales'], name='Sales', marker_color='#2E8B57'))
            fig.add_trace(go.Bar(x=chart_df['Date'], y=chart_df['Expenses'], name='Expenses', marker_color='#DC143C'))
        elif chart_type == "Area Chart":
            fig.add_trace(go.Scatter(x=chart_df['Date'], y=chart_df['Sales'], fill='tonexty',
                                     name='Sales', fillcolor='rgba(46,139,87,0.3)'))
            fig.add_trace(go.Scatter(x=chart_df['Date'], y=chart_df['Expenses'], fill='tonexty',
                                     name='Expenses', fillcolor='rgba(220,20,60,0.3)'))

        fig.update_layout(
            title="💰 Daily Sales vs Expenses Trend",
            xaxis_title="Date",
            yaxis_title="Amount (TRY)",
            hovermode='x unified',
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Profit Margin Chart
        if len(chart_df) > 0:
            chart_df['Profit Margin %'] = (chart_df['Net Profit'] / chart_df['Sales'] * 100).fillna(0)

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=chart_df['Date'],
                y=chart_df['Profit Margin %'],
                mode='lines+markers',
                line=dict(color='#FFD700', width=3),
                marker=dict(size=8, color='#FFA500'),
                name='Profit Margin %'
            ))

            fig2.update_layout(
                title="📈 Daily Profit Margin Trend",
                xaxis_title="Date",
                yaxis_title="Profit Margin (%)",
                template='plotly_white'
            )
            st.plotly_chart(fig2, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)

    with col1:
        # Sales by Category Pie Chart
        category_sales = {}
        for s in data['sales_data']:
            category_sales[s.category] = category_sales.get(s.category, 0) + s.total_sale

        if category_sales:
            fig3 = px.pie(
                values=list(category_sales.values()),
                names=list(category_sales.keys()),
                title="🍕 Sales Distribution by Category"
            )
            fig3.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig3, use_container_width=True)

    with col2:
        # Expense Type Distribution
        expense_types = {}
        for e in data['expenses_data']:
            expense_types[e.expense_type] = expense_types.get(e.expense_type, 0) + e.amount

        if expense_types:
            fig4 = px.bar(
                x=list(expense_types.keys()),
                y=list(expense_types.values()),
                title="💸 Expenses by Type",
                color=list(expense_types.values()),
                color_continuous_scale='Reds'
            )
            fig4.update_layout(xaxis_title="Expense Type", yaxis_title="Amount (TRY)")
            st.plotly_chart(fig4, use_container_width=True)

with tab3:
    # Category Performance Analysis
    if data['sales_data']:
        category_analysis = {}
        for s in data['sales_data']:
            if s.category not in category_analysis:
                category_analysis[s.category] = {'sales': 0, 'quantity': 0, 'transactions': 0}
            category_analysis[s.category]['sales'] += s.total_sale
            category_analysis[s.category]['quantity'] += s.quantity_sold
            category_analysis[s.category]['transactions'] += 1

        # Create category performance dataframe
        cat_df = pd.DataFrame([
            {
                'Category': cat,
                'Total Sales (TRY)': data['sales'],
                'Total Quantity': data['quantity'],
                'Transactions': data['transactions'],
                'Avg Sale per Transaction': data['sales'] / data['transactions']
            }
            for cat, data in category_analysis.items()
        ])

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🏆 Category Performance")
            st.dataframe(cat_df.round(2), use_container_width=True)

        with col2:
            # Top products
            product_sales = {}
            for s in data['sales_data']:
                product_sales[s.item_name] = product_sales.get(s.item_name, 0) + s.total_sale

            top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:10]

            if top_products:
                fig5 = px.bar(
                    x=[p[1] for p in top_products],
                    y=[p[0] for p in top_products],
                    orientation='h',
                    title="🥇 Top 10 Products by Sales",
                    color=[p[1] for p in top_products],
                    color_continuous_scale='Viridis'
                )
                fig5.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig5, use_container_width=True)

with tab4:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🧾 Recent Sales")
        recent_sales = sorted(data['sales_data'], key=lambda x: x.timestamp, reverse=True)[:10]

        if recent_sales:
            sales_display = []
            for s in recent_sales:
                sales_display.append({
                    'Time': s.timestamp.strftime('%m-%d %H:%M'),
                    'Item': s.item_name,
                    'Category': s.category,
                    'Qty': s.quantity_sold,
                    'Total': f"{s.total_sale:.2f} TRY"
                })

            st.dataframe(pd.DataFrame(sales_display), use_container_width=True)
        else:
            st.info("No recent sales data available")

    with col2:
        st.markdown("### 💸 Recent Expenses")
        recent_expenses = sorted(data['expenses_data'], key=lambda x: x.timestamp, reverse=True)[:10]

        if recent_expenses:
            expenses_display = []
            for e in recent_expenses:
                expenses_display.append({
                    'Time': e.timestamp.strftime('%m-%d %H:%M'),
                    'Type': e.expense_type,
                    'Amount': f"{e.amount:.2f} TRY",
                    'Description': e.description[:30] + "..." if e.description and len(
                        e.description) > 30 else e.description or ""
                })

            st.dataframe(pd.DataFrame(expenses_display), use_container_width=True)
        else:
            st.info("No recent expense data available")

# Download Section
st.markdown("## 📥 Export Data")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Download Sales Data"):
        sales_df = pd.DataFrame([{
            'Date': s.timestamp.strftime('%Y-%m-%d'),
            'Time': s.timestamp.strftime('%H:%M:%S'),
            'Item': s.item_name,
            'Category': s.category,
            'Quantity': s.quantity_sold,
            'Price per Unit': s.price_per_unit,
            'Total Sale': s.total_sale
        } for s in data['sales_data']])

        csv = sales_df.to_csv(index=False)
        st.download_button(
            label="💾 Download Sales CSV",
            data=csv,
            file_name=f"kika_sales_{start_date}_to_{end_date}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("💸 Download Expenses Data"):
        expenses_df = pd.DataFrame([{
            'Date': e.timestamp.strftime('%Y-%m-%d'),
            'Time': e.timestamp.strftime('%H:%M:%S'),
            'Type': e.expense_type,
            'Amount': e.amount,
            'Description': e.description or ''
        } for e in data['expenses_data']])

        csv = expenses_df.to_csv(index=False)
        st.download_button(
            label="💾 Download Expenses CSV",
            data=csv,
            file_name=f"kika_expenses_{start_date}_to_{end_date}.csv",
            mime="text/csv"
        )

with col3:
    if st.button("📈 Download Summary Report"):
        summary_data = {
            'Metric': ['Total Sales', 'Total Expenses', 'Net Profit', 'ROI (%)', 'Total Transactions',
                       'Average Transaction'],
            'Value': [
                f"{data['total_sales']:.2f} TRY",
                f"{data['total_expenses']:.2f} TRY",
                f"{data['net_profit']:.2f} TRY",
                f"{data['roi']:.2f}%",
                len(data['sales_data']),
                f"{data['total_sales'] / max(1, len(data['sales_data'])):.2f} TRY"
            ]
        }

        summary_df = pd.DataFrame(summary_data)
        csv = summary_df.to_csv(index=False)
        st.download_button(
            label="💾 Download Summary CSV",
            data=csv,
            file_name=f"kika_summary_{start_date}_to_{end_date}.csv",
            mime="text/csv"
        )

# Footer with refresh timestamp
st.markdown("---")
st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data range: {start_date} to {end_date}*")

session.close()