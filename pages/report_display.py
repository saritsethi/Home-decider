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
    
    # Historical Property Value Trends
    st.header("📈 Historical Property Value Trends")
    if st.session_state.report_data['recommended_neighborhoods']:
        neighborhoods_for_chart = [match['neighborhood'] for match in st.session_state.report_data['recommended_neighborhoods']]
        fig = create_historical_value_chart(neighborhoods_for_chart)
        st.plotly_chart(fig, use_container_width=True)
    
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
