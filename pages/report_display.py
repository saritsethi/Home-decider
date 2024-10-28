import streamlit as st
from components.navigation import create_navigation
import json
from utils.visualization import create_historical_value_chart, create_neighborhood_comparison_chart
import pandas as pd
import plotly.express as px

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
    
    # Historical Property Value Trends
    st.header("📈 Neighborhood Value Trends")
    if st.session_state.report_data['recommended_neighborhoods']:
        # Create tabs for different trend views
        trend_tabs = st.tabs(["Value Trends", "Growth Rates", "Market Analysis"])
        
        with trend_tabs[0]:
            # Historical value trends chart
            neighborhoods_for_chart = [match['neighborhood'] for match in st.session_state.report_data['recommended_neighborhoods']]
            fig = create_historical_value_chart(neighborhoods_for_chart)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Historical property value data is not available for these neighborhoods.")
        
        with trend_tabs[1]:
            st.subheader("Property Value Growth Analysis")
            growth_data = []
            
            for match in st.session_state.report_data['recommended_neighborhoods']:
                hood = match['neighborhood']
                historical_data = hood['historical_values'] if isinstance(hood['historical_values'], list) else json.loads(hood['historical_values'])
                if len(historical_data) >= 2:
                    start_value = historical_data[0]['value']
                    end_value = historical_data[-1]['value']
                    total_growth = ((end_value - start_value) / start_value) * 100
                    years = 5
                    annual_growth = ((1 + total_growth/100) ** (1/years) - 1) * 100
                    
                    growth_data.append({
                        'Neighborhood': hood['name'],
                        'Annual Growth Rate': annual_growth,
                        'Total Value Change': end_value - start_value,
                        'Starting Value': start_value,
                        'Current Value': end_value
                    })
            
            if growth_data:
                for data in growth_data:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            f"{data['Neighborhood']} - Annual Growth",
                            f"{data['Annual Growth Rate']:.1f}%",
                            delta=f"${data['Total Value Change']:,.2f}"
                        )
                    with col2:
                        st.metric(
                            "Value Change",
                            f"${data['Current Value']:,.2f}",
                            delta=f"From ${data['Starting Value']:,.2f}"
                        )
        
        with trend_tabs[2]:
            # Market analysis
            st.subheader("Market Analysis")
            for match in st.session_state.report_data['recommended_neighborhoods']:
                hood = match['neighborhood']
                with st.expander(f"{hood['name']} Market Analysis", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        historical_data = hood['historical_values'] if isinstance(hood['historical_values'], list) else json.loads(hood['historical_values'])
                        if len(historical_data) >= 2:
                            recent_value = historical_data[-1]['value']
                            start_value = historical_data[0]['value']
                            yearly_growth = (((recent_value / start_value) ** (1/5)) - 1) * 100
                            
                            st.metric("Current Average Value", f"${recent_value:,.2f}")
                            st.metric("5-Year Start Value", f"${start_value:,.2f}")
                            st.metric("Annual Growth Rate", f"{yearly_growth:.1f}%")
                    
                    with col2:
                        st.metric("Cost of Living Score", f"{hood['cost_of_living']}/10")
                        st.metric("Price per Walkability Point", f"${(recent_value / hood['walkability_score']):,.2f}")
                        st.metric("Price per School Rating Point", f"${(recent_value / hood['school_rating']):,.2f}")
    
    # Neighborhood Recommendations
    st.header("🏘️ Recommended Neighborhoods")
    if st.session_state.report_data['recommended_neighborhoods']:
        # Add neighborhood comparison chart
        fig = create_neighborhood_comparison_chart([match['neighborhood'] for match in st.session_state.report_data['recommended_neighborhoods']])
        st.plotly_chart(fig, use_container_width=True)
        
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
