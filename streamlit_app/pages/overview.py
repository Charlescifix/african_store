# streamlit_app/pages/Overview.py

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.crud import get_sales_in_range, get_expenses_in_range
import pandas as pd
import numpy as np

st.set_page_config(page_title="Business Overview", layout="wide")

# Custom styling
st.markdown("""
<style>
    .overview-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .insight-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="overview-header"><h1>📊 Business Intelligence Overview</h1><p>Comprehensive analytics and insights for strategic decision making</p></div>',
    unsafe_allow_html=True)

# Setup DB session
session = SessionLocal()

# Sidebar controls
with st.sidebar:
    st.markdown("## 🎛️ Analysis Controls")

    # Analysis period
    analysis_period = st.selectbox(
        "📅 Analysis Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Year to Date", "Custom"],
        index=1
    )

    if analysis_period == "Custom":
        start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
        end_date = st.date_input("End Date", value=datetime.now().date())
    else:
        today = datetime.today().date()
        if analysis_period == "Last 7 Days":
            start_date, end_date = today - timedelta(days=7), today
        elif analysis_period == "Last 30 Days":
            start_date, end_date = today - timedelta(days=30), today
        elif analysis_period == "Last 90 Days":
            start_date, end_date = today - timedelta(days=90), today
        elif analysis_period == "Year to Date":
            start_date, end_date = today.replace(month=1, day=1), today

    # Comparison toggle
    enable_comparison = st.checkbox("📊 Enable Period Comparison", value=True)

    if enable_comparison:
        comparison_days = (end_date - start_date).days
        comparison_start = start_date - timedelta(days=comparison_days)
        comparison_end = start_date - timedelta(days=1)


# Get data
@st.cache_data(ttl=300)
def get_comprehensive_data(start_date, end_date, comp_start=None, comp_end=None):
    # Current period data
    sales = get_sales_in_range(session, start_date, end_date)
    expenses = get_expenses_in_range(session, start_date, end_date)

    current_data = {
        'sales': sales,
        'expenses': expenses,
        'total_sales': sum(s.total_sale for s in sales),
        'total_expenses': sum(e.amount for e in expenses),
    }
    current_data['net_profit'] = current_data['total_sales'] - current_data['total_expenses']

    # Comparison period data
    comparison_data = None
    if comp_start and comp_end:
        comp_sales = get_sales_in_range(session, comp_start, comp_end)
        comp_expenses = get_expenses_in_range(session, comp_start, comp_end)
        comparison_data = {
            'sales': comp_sales,
            'expenses': comp_expenses,
            'total_sales': sum(s.total_sale for s in comp_sales),
            'total_expenses': sum(e.amount for e in comp_expenses),
        }
        comparison_data['net_profit'] = comparison_data['total_sales'] - comparison_data['total_expenses']

    return current_data, comparison_data


current_data, comparison_data = get_comprehensive_data(
    start_date, end_date,
    comparison_start if enable_comparison else None,
    comparison_end if enable_comparison else None
)

# Executive Summary
st.markdown("## 🎯 Executive Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_sales = None
    if comparison_data:
        delta_sales = current_data['total_sales'] - comparison_data['total_sales']
        delta_pct = (delta_sales / comparison_data['total_sales'] * 100) if comparison_data['total_sales'] > 0 else 0
        delta_sales = f"{delta_pct:+.1f}%"

    st.metric("💰 Total Sales", f"{current_data['total_sales']:.2f} TRY", delta=delta_sales)

with col2:
    delta_expenses = None
    if comparison_data:
        delta_expenses = current_data['total_expenses'] - comparison_data['total_expenses']
        delta_pct = (delta_expenses / comparison_data['total_expenses'] * 100) if comparison_data[
                                                                                      'total_expenses'] > 0 else 0
        delta_expenses = f"{delta_pct:+.1f}%"

    st.metric("💸 Total Expenses", f"{current_data['total_expenses']:.2f} TRY", delta=delta_expenses)

with col3:
    delta_profit = None
    if comparison_data:
        delta_profit = current_data['net_profit'] - comparison_data['net_profit']
        if comparison_data['net_profit'] != 0:
            delta_pct = (delta_profit / abs(comparison_data['net_profit']) * 100)
            delta_profit = f"{delta_pct:+.1f}%"
        else:
            delta_profit = "New"

    st.metric("📈 Net Profit", f"{current_data['net_profit']:.2f} TRY", delta=delta_profit)

with col4:
    avg_transaction = current_data['total_sales'] / max(1, len(current_data['sales']))
    delta_avg = None
    if comparison_data:
        comp_avg = comparison_data['total_sales'] / max(1, len(comparison_data['sales']))
        delta_avg = avg_transaction - comp_avg
        delta_pct = (delta_avg / comp_avg * 100) if comp_avg > 0 else 0
        delta_avg = f"{delta_pct:+.1f}%"

    st.metric("🛒 Avg Transaction", f"{avg_transaction:.2f} TRY", delta=delta_avg)

# Advanced Analytics
st.markdown("## 🔬 Advanced Analytics")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Trends", "🎯 Performance", "🔍 Deep Dive", "🚀 Insights", "📊 Forecasting"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        # Daily trend analysis
        daily_sales = {}
        daily_expenses = {}

        for s in current_data['sales']:
            date = s.timestamp.date()
            daily_sales[date] = daily_sales.get(date, 0) + s.total_sale

        for e in current_data['expenses']:
            date = e.timestamp.date()
            daily_expenses[date] = daily_expenses.get(date, 0) + e.amount

        # Create comprehensive daily dataframe
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D').date
        trend_df = pd.DataFrame({
            'Date': all_dates,
            'Sales': [daily_sales.get(d, 0) for d in all_dates],
            'Expenses': [daily_expenses.get(d, 0) for d in all_dates],
        })
        trend_df['Net Profit'] = trend_df['Sales'] - trend_df['Expenses']
        trend_df['Cumulative Sales'] = trend_df['Sales'].cumsum()
        trend_df['Moving Avg (7d)'] = trend_df['Sales'].rolling(window=min(7, len(trend_df))).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend_df['Date'], y=trend_df['Sales'],
                                 name='Daily Sales', line=dict(color='#2E8B57', width=2)))
        fig.add_trace(go.Scatter(x=trend_df['Date'], y=trend_df['Moving Avg (7d)'],
                                 name='7-Day Moving Average', line=dict(color='#FFD700', width=3, dash='dash')))

        fig.update_layout(
            title="📈 Sales Trend Analysis",
            xaxis_title="Date",
            yaxis_title="Sales (TRY)",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Cumulative performance
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=trend_df['Date'], y=trend_df['Cumulative Sales'],
                                  fill='tonexty', name='Cumulative Sales',
                                  line=dict(color='#4169E1')))

        fig2.update_layout(
            title="📊 Cumulative Sales Growth",
            xaxis_title="Date",
            yaxis_title="Cumulative Sales (TRY)"
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)

    with col1:
        # Category performance with detailed metrics
        category_metrics = {}
        for s in current_data['sales']:
            cat = s.category
            if cat not in category_metrics:
                category_metrics[cat] = {
                    'sales': 0, 'quantity': 0, 'transactions': 0,
                    'revenue_share': 0, 'items': set()
                }
            category_metrics[cat]['sales'] += s.total_sale
            category_metrics[cat]['quantity'] += s.quantity_sold
            category_metrics[cat]['transactions'] += 1
            category_metrics[cat]['items'].add(s.item_name)

        # Calculate revenue share
        total_sales = sum(m['sales'] for m in category_metrics.values())
        for cat in category_metrics:
            category_metrics[cat]['revenue_share'] = (
                        category_metrics[cat]['sales'] / total_sales * 100) if total_sales > 0 else 0
            category_metrics[cat]['unique_items'] = len(category_metrics[cat]['items'])

        if category_metrics:
            # Performance heatmap
            cats = list(category_metrics.keys())
            metrics = ['Sales', 'Transactions', 'Avg Transaction', 'Revenue Share %']

            heatmap_data = []
            for cat in cats:
                data = category_metrics[cat]
                avg_transaction = data['sales'] / max(1, data['transactions'])
                heatmap_data.append([
                    data['sales'],
                    data['transactions'],
                    avg_transaction,
                    data['revenue_share']
                ])

            fig3 = go.Figure(data=go.Heatmap(
                z=np.array(heatmap_data).T,
                x=cats,
                y=metrics,
                colorscale='RdYlGn',
                text=np.round(np.array(heatmap_data).T, 2),
                texttemplate="%{text}",
                textfont={"size": 10}
            ))

            fig3.update_layout(title="🎯 Category Performance Heatmap")
            st.plotly_chart(fig3, use_container_width=True)

    with col2:
        # Top performers analysis
        item_performance = {}
        for s in current_data['sales']:
            item = s.item_name
            if item not in item_performance:
                item_performance[item] = {
                    'sales': 0, 'quantity': 0, 'transactions': 0,
                    'category': s.category, 'avg_price': 0
                }
            item_performance[item]['sales'] += s.total_sale
            item_performance[item]['quantity'] += s.quantity_sold
            item_performance[item]['transactions'] += 1
            item_performance[item]['avg_price'] = s.price_per_unit

        # Top 10 items by sales
        top_items = sorted(item_performance.items(), key=lambda x: x[1]['sales'], reverse=True)[:10]

        if top_items:
            items_df = pd.DataFrame([
                {
                    'Item': item[0],
                    'Category': item[1]['category'],
                    'Sales (TRY)': item[1]['sales'],
                    'Quantity Sold': item[1]['quantity'],
                    'Transactions': item[1]['transactions'],
                    'Avg Price': item[1]['avg_price']
                }
                for item in top_items
            ])

            fig4 = px.treemap(
                items_df,
                path=['Category', 'Item'],
                values='Sales (TRY)',
                title="🏆 Top Products by Sales Value",
                color='Sales (TRY)',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig4, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)

    with col1:
        # Hourly analysis
        st.markdown("### ⏰ Peak Hours Analysis")
        hourly_sales = {}
        for s in current_data['sales']:
            hour = s.timestamp.hour
            hourly_sales[hour] = hourly_sales.get(hour, 0) + s.total_sale

        if hourly_sales:
            hours = list(range(24))
            sales_by_hour = [hourly_sales.get(h, 0) for h in hours]

            fig5 = go.Figure()
            fig5.add_trace(go.Bar(
                x=hours,
                y=sales_by_hour,
                name='Sales by Hour',
                marker_color='lightblue',
                text=[f"{s:.0f}" for s in sales_by_hour],
                textposition='auto'
            ))

            # Add peak hour indicator
            peak_hour = max(hourly_sales.items(), key=lambda x: x[1])[0] if hourly_sales else 0
            fig5.add_vline(x=peak_hour, line_dash="dash", line_color="red",
                           annotation_text=f"Peak: {peak_hour}:00")

            fig5.update_layout(
                title="📊 Sales Distribution by Hour",
                xaxis_title="Hour of Day",
                yaxis_title="Sales (TRY)"
            )
            st.plotly_chart(fig5, use_container_width=True)

    with col2:
        # Day of week analysis
        st.markdown("### 📅 Weekly Pattern Analysis")
        weekday_sales = {}
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for s in current_data['sales']:
            weekday = s.timestamp.weekday()
            weekday_sales[weekday] = weekday_sales.get(weekday, 0) + s.total_sale

        if weekday_sales:
            weekday_data = [weekday_sales.get(i, 0) for i in range(7)]

            fig6 = go.Figure()
            fig6.add_trace(go.Scatterpolar(
                r=weekday_data,
                theta=weekday_names,
                fill='toself',
                name='Sales by Weekday'
            ))

            fig6.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, max(weekday_data) if weekday_data else 100])
                ),
                title="🗓️ Weekly Sales Pattern"
            )
            st.plotly_chart(fig6, use_container_width=True)

with tab4:
    # Business insights and recommendations
    st.markdown("### 💡 Key Business Insights")

    # Calculate various metrics for insights
    total_transactions = len(current_data['sales'])
    avg_transaction = current_data['total_sales'] / max(1, total_transactions)
    profit_margin = (current_data['net_profit'] / current_data['total_sales'] * 100) if current_data[
                                                                                            'total_sales'] > 0 else 0

    insights = []

    # Profit margin insight
    if profit_margin > 20:
        insights.append("🟢 **Excellent profit margin** - Your business is highly profitable!")
    elif profit_margin > 10:
        insights.append("🟡 **Good profit margin** - Room for optimization in expense management.")
    else:
        insights.append("🔴 **Low profit margin** - Consider reviewing pricing strategy and cost control.")

    # Transaction size insight
    if avg_transaction > 50:
        insights.append("💰 **High average transaction value** - Customers are making substantial purchases.")
    elif avg_transaction > 25:
        insights.append("📊 **Moderate transaction value** - Consider upselling strategies.")
    else:
        insights.append("📈 **Focus on increasing transaction value** - Bundle products or promote premium items.")

    # Volume insight
    if total_transactions > 100:
        insights.append("🚀 **High transaction volume** - Strong customer traffic!")
    elif total_transactions > 50:
        insights.append("📈 **Moderate transaction volume** - Growing customer base.")
    else:
        insights.append("🎯 **Focus on customer acquisition** - Marketing and promotions needed.")

    for insight in insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

    # Recommendations
    st.markdown("### 🎯 Strategic Recommendations")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📈 Growth Opportunities")
        if category_metrics:
            top_category = max(category_metrics.items(), key=lambda x: x[1]['sales'])[0]
            st.write(f"• **Expand {top_category} category** - Your best performer")

            low_performers = [cat for cat, data in category_metrics.items()
                              if data['revenue_share'] < 10]
            if low_performers:
                st.write(f"• **Review underperforming categories**: {', '.join(low_performers)}")

        if hourly_sales:
            peak_hour = max(hourly_sales.items(), key=lambda x: x[1])[0]
            st.write(f"• **Optimize staffing around {peak_hour}:00** - Peak sales hour")

    with col2:
        st.markdown("#### 💡 Operational Improvements")
        expense_ratio = (current_data['total_expenses'] / current_data['total_sales'] * 100) if current_data[
                                                                                                    'total_sales'] > 0 else 0

        if expense_ratio > 70:
            st.write("• **Cost reduction priority** - Expenses are high relative to sales")
        elif expense_ratio > 50:
            st.write("• **Monitor expense growth** - Keep costs in check")
        else:
            st.write("• **Efficient cost management** - Maintain current expense levels")

        st.write("• **Digital payment options** - Reduce cash handling costs")
        st.write("• **Inventory optimization** - Track fast/slow-moving items")

with tab5:
    # Simple forecasting based on trends
    st.markdown("### 🔮 Sales Forecasting")

    if len(trend_df) > 7:  # Need at least a week of data
        # Simple linear regression for forecasting
        from sklearn.linear_model import LinearRegression
        import numpy as np

        # Prepare data for forecasting
        days = np.arange(len(trend_df)).reshape(-1, 1)
        sales_values = trend_df['Sales'].values

        # Fit model
        model = LinearRegression()
        model.fit(days, sales_values)

        # Predict next 7 days
        future_days = np.arange(len(trend_df), len(trend_df) + 7).reshape(-1, 1)
        future_predictions = model.predict(future_days)

        # Create forecast visualization
        forecast_dates = pd.date_range(start=end_date + timedelta(days=1), periods=7, freq='D')

        fig7 = go.Figure()

        # Historical data
        fig7.add_trace(go.Scatter(
            x=trend_df['Date'],
            y=trend_df['Sales'],
            mode='lines+markers',
            name='Historical Sales',
            line=dict(color='blue')
        ))

        # Forecast
        fig7.add_trace(go.Scatter(
            x=forecast_dates,
            y=future_predictions,
            mode='lines+markers',
            name='Forecast',
            line=dict(color='red', dash='dash')
        ))

        fig7.update_layout(
            title="📈 7-Day Sales Forecast",
            xaxis_title="Date",
            yaxis_title="Predicted Sales (TRY)"
        )
        st.plotly_chart(fig7, use_container_width=True)

        # Forecast summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎯 Next 7 Days Total", f"{sum(future_predictions):.2f} TRY")
        with col2:
            st.metric("📊 Daily Average", f"{np.mean(future_predictions):.2f} TRY")
        with col3:
            current_avg = trend_df['Sales'].mean()
            forecast_avg = np.mean(future_predictions)
            growth = ((forecast_avg - current_avg) / current_avg * 100) if current_avg > 0 else 0
            st.metric("📈 Projected Growth", f"{growth:+.1f}%")
    else:
        st.info("📊 Need at least 7 days of data for reliable forecasting")

# Data Export Section
st.markdown("## 📥 Export Comprehensive Reports")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export Detailed Analysis"):
        # Create comprehensive analysis report
        analysis_data = []

        # Add summary metrics
        analysis_data.append({
            'Report Section': 'Summary',
            'Metric': 'Total Sales',
            'Value': current_data['total_sales'],
            'Period': f"{start_date} to {end_date}"
        })
        analysis_data.append({
            'Report Section': 'Summary',
            'Metric': 'Total Expenses',
            'Value': current_data['total_expenses'],
            'Period': f"{start_date} to {end_date}"
        })
        analysis_data.append({
            'Report Section': 'Summary',
            'Metric': 'Net Profit',
            'Value': current_data['net_profit'],
            'Period': f"{start_date} to {end_date}"
        })

        # Add category breakdown
        if category_metrics:
            for cat, data in category_metrics.items():
                analysis_data.append({
                    'Report Section': 'Category Analysis',
                    'Metric': f'{cat} Sales',
                    'Value': data['sales'],
                    'Period': f"{start_date} to {end_date}"
                })

        analysis_df = pd.DataFrame(analysis_data)
        csv = analysis_df.to_csv(index=False)
        st.download_button(
            label="💾 Download Analysis Report",
            data=csv,
            file_name=f"kika_comprehensive_analysis_{start_date}_to_{end_date}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📈 Export Trend Data"):
        trend_export = trend_df.copy()
        trend_export['Profit Margin %'] = (trend_export['Net Profit'] / trend_export['Sales'] * 100).fillna(0)

        csv = trend_export.to_csv(index=False)
        st.download_button(
            label="💾 Download Trend Data",
            data=csv,
            file_name=f"kika_trends_{start_date}_to_{end_date}.csv",
            mime="text/csv"
        )

with col3:
    if st.button("🎯 Export Performance Metrics"):
        if category_metrics:
            perf_data = []
            for cat, data in category_metrics.items():
                perf_data.append({
                    'Category': cat,
                    'Total Sales (TRY)': data['sales'],
                    'Total Transactions': data['transactions'],
                    'Average Transaction (TRY)': data['sales'] / max(1, data['transactions']),
                    'Revenue Share (%)': data['revenue_share'],
                    'Unique Items': data['unique_items']
                })

            perf_df = pd.DataFrame(perf_data)
            csv = perf_df.to_csv(index=False)
            st.download_button(
                label="💾 Download Performance Data",
                data=csv,
                file_name=f"kika_performance_{start_date}_to_{end_date}.csv",
                mime="text/csv"
            )

# Footer
st.markdown("---")
st.markdown(
    f"*Analysis generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Period: {start_date} to {end_date}*")

session.close()