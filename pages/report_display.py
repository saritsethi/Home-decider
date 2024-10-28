import streamlit as st
from components.navigation import create_navigation
import json
from utils.visualization import create_historical_value_chart

st.set_page_config(page_title="Report Results", page_icon="📊")

def display_report_results():
    if 'report_data' not in st.session_state:
        st.warning("Please complete the lifestyle quiz first!")
        st.page_link("pages/lifestyle_quiz.py", label="Take the Quiz", icon="✨")
        return

    create_navigation()
    st.title("Your Personalized Home Recommendations")
    
    # Financial Analysis Section
    st.header("💰 Financial Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Maximum Home Price",
            f"${st.session_state.report_data['max_home_price']:,.2f}"
        )
        st.metric(
            "Monthly Mortgage Payment",
            f"${st.session_state.financial_info.get('target_home_price', 0) * 0.8 * 0.005:,.2f}"
        )
    
    with col2:
        st.metric(
            "Current Monthly Rent",
            f"${st.session_state.financial_info.get('current_monthly_rent', 0):,.2f}"
        )
        recommendation = st.session_state.report_data['rent_vs_buy_recommendation'].upper()
        st.success(f"Recommendation: {recommendation}")
    
    # Detailed Financial Analysis
    st.header("📊 Detailed Financial Analysis")
    
    # Maximum Home Price Breakdown
    st.subheader("Maximum Home Price Analysis")
    monthly_income = st.session_state.financial_info.get('annual_income', 0) / 12
    max_monthly_payment = monthly_income * 0.28  # 28% DTI ratio
    max_price_from_income = max_monthly_payment * 200  # Rough estimate based on monthly payment
    max_price_from_savings = st.session_state.financial_info.get('savings', 0) * 5  # 20% down payment

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Monthly Income", f"${monthly_income:,.2f}")
        st.metric("Max Monthly Payment (28% DTI)", f"${max_monthly_payment:,.2f}")
    with col2:
        st.metric("Max Price (Income-based)", f"${max_price_from_income:,.2f}")
        st.metric("Max Price (Savings-based)", f"${max_price_from_savings:,.2f}")

    # Rent vs Buy Analysis
    st.subheader("Rent vs Buy Analysis")
    target_home_price = st.session_state.financial_info.get('target_home_price', 0)
    monthly_mortgage = target_home_price * 0.8 * 0.005
    property_tax = target_home_price * 0.015 / 12
    insurance = 150  # Estimated monthly insurance
    maintenance = target_home_price * 0.01 / 12
    total_monthly_cost = monthly_mortgage + property_tax + insurance + maintenance
    
    # Create comparison table
    comparison_data = {
        "Category": ["Monthly Cost", "5-Year Total Cost", "Building Equity?", "Maintenance Required?"],
        "Renting": [
            f"${st.session_state.financial_info.get('current_monthly_rent', 0):,.2f}",
            f"${st.session_state.financial_info.get('current_monthly_rent', 0) * 60:,.2f}",
            "No",
            "No"
        ],
        "Buying": [
            f"${total_monthly_cost:,.2f}",
            f"${total_monthly_cost * 60:,.2f}",
            "Yes",
            "Yes"
        ]
    }
    st.table(comparison_data)

    # Historical Property Value Trends
    st.header("📈 Neighborhood Value Trends")
    if st.session_state.report_data['recommended_neighborhoods']:
        # Create tabs for different trend views
        trend_tabs = st.tabs(["Value Trends", "Growth Rates", "Market Analysis"])
        
        with trend_tabs[0]:
            # Historical value trends chart
            neighborhoods_for_chart = [match['neighborhood'] for match in st.session_state.report_data['recommended_neighborhoods']]
            fig = create_historical_value_chart(neighborhoods_for_chart)
            st.plotly_chart(fig, use_container_width=True)
        
        with trend_tabs[1]:
            # Calculate and display growth rates
            st.subheader("5-Year Growth Rates")
            for match in st.session_state.report_data['recommended_neighborhoods']:
                hood = match['neighborhood']
                historical_data = hood['historical_values'] if isinstance(hood['historical_values'], list) else json.loads(hood['historical_values'])
                if len(historical_data) >= 2:
                    start_value = historical_data[0]['value']
                    end_value = historical_data[-1]['value']
                    growth_rate = ((end_value - start_value) / start_value) * 100
                    st.metric(
                        f"{hood['name']}",
                        f"{growth_rate:.1f}%",
                        delta=f"${end_value - start_value:,.2f}"
                    )
        
        with trend_tabs[2]:
            # Market analysis
            st.subheader("Market Analysis")
            for match in st.session_state.report_data['recommended_neighborhoods']:
                hood = match['neighborhood']
                with st.expander(f"{hood['name']} Market Analysis"):
                    historical_data = hood['historical_values'] if isinstance(hood['historical_values'], list) else json.loads(hood['historical_values'])
                    if len(historical_data) >= 2:
                        recent_value = historical_data[-1]['value']
                        yearly_growth = (((recent_value / historical_data[0]['value']) ** (1/5)) - 1) * 100
                        
                        st.metric("Current Average Value", f"${recent_value:,.2f}")
                        st.metric("Annual Growth Rate", f"{yearly_growth:.1f}%")
                        st.metric("Price per Walkability Point", 
                                f"${(recent_value / hood['walkability_score']):,.2f}")
    
    # Neighborhood Recommendations
    st.header("🏘️ Recommended Neighborhoods")
    if st.session_state.report_data['recommended_neighborhoods']:
        for idx, match in enumerate(st.session_state.report_data['recommended_neighborhoods']):
            with st.expander(f"#{idx+1}: {match['neighborhood']['name']} - {match['match_score']}% Match", expanded=idx==0):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Why this neighborhood?")
                    for reason in match['reasons']:
                        st.write(f"✓ {reason}")
                
                with col2:
                    st.markdown("### Key Statistics")
                    st.metric("Cost of Living", f"{match['neighborhood']['cost_of_living']}/10")
                    st.metric("School Rating", f"{match['neighborhood']['school_rating']}/10")
                    st.metric("Transport Score", f"{match['neighborhood']['transport_score']}/10")
                    st.metric("Walkability", f"{match['neighborhood']['walkability_score']}/10")
    else:
        st.warning("No matching neighborhoods found based on your preferences.")

if __name__ == "__main__":
    display_report_results()
