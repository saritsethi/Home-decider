import streamlit as st
from components.navigation import create_navigation
import json
from utils.visualization import create_historical_value_chart, create_neighborhood_comparison_chart
from utils.report_generator import create_pdf_report
import pandas as pd
import plotly.express as px
import base64
import os

st.set_page_config(page_title="Report Results", page_icon="📊")

def get_pdf_download_link(pdf_path, link_text="Download PDF Report"):
    """Generate a link to download the PDF file."""
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="home_decision_report.pdf">{link_text}</a>'
    return href

def display_report_results():
    if 'report_data' not in st.session_state:
        st.warning("Please complete the lifestyle quiz first!")
        st.page_link("pages/lifestyle_quiz.py", label="Take the Quiz", icon="✨")
        return

    create_navigation()
    st.title("Your Personalized Home Recommendations")
    
    # Generate PDF report
    pdf_path = create_pdf_report(
        st.session_state.report_data,
        st.session_state.financial_info,
        st.session_state.preferences
    )
    
    # Add download button at the top
    st.markdown(
        get_pdf_download_link(pdf_path),
        unsafe_allow_html=True
    )
    
    # Add narrative summary
    st.markdown("### Summary of Recommendations")
    
    # Get key metrics for the narrative
    max_home_price = st.session_state.report_data['max_home_price']
    monthly_mortgage = st.session_state.financial_info.get('target_home_price', 0) * 0.8 * 0.005
    current_rent = st.session_state.financial_info.get('current_monthly_rent', 0)
    recommendation = st.session_state.report_data['rent_vs_buy_recommendation'].upper()
    
    # Create narrative
    st.markdown(f'''
    Based on your financial profile and preferences, here are our key recommendations:
    
    - **Housing Budget**: You can afford a home up to ${max_home_price:,.2f}, based on your income, savings, and current expenses.
    
    - **Buy vs Rent**: We recommend you **{recommendation}** because:
        - Monthly mortgage payment would be approximately ${monthly_mortgage:,.2f}
        - Your current monthly rent is ${current_rent:,.2f}
        - {'The cost of buying (including maintenance and taxes) would be higher than renting.' if recommendation == 'RENT' else 'Buying would build equity while keeping monthly costs manageable.'}
    
    - **Neighborhood Matches**: We've identified neighborhoods that match your lifestyle preferences, prioritizing:
        - School quality for your family
        - Safety ratings
        - Your preferred transportation options
        - Local amenities that match your interests
    
    Below you'll find detailed analysis of costs, neighborhood trends, and specific recommendations.
    ''')
    
    st.divider()  # Add visual separator before detailed sections
    
    # Financial Analysis Section
    st.header('💰 Financial Analysis')
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            'Maximum Home Price',
            f'${st.session_state.report_data["max_home_price"]:,.2f}'
        )
        st.metric(
            'Monthly Mortgage Payment',
            f'${st.session_state.financial_info["target_home_price"] * 0.8 * 0.005:,.2f}'
        )
    
    with col2:
        st.metric(
            'Current Monthly Rent',
            f'${st.session_state.financial_info["current_monthly_rent"]:,.2f}'
        )
        recommendation = st.session_state.report_data['rent_vs_buy_recommendation'].upper()
        st.success(f'Recommendation: {recommendation}')
    
    # Neighborhood Analysis
    st.header('🏘️ Neighborhood Analysis')
    if st.session_state.report_data['recommended_neighborhoods']:
        neighborhoods = [match['neighborhood'] for match in st.session_state.report_data['recommended_neighborhoods']]
        
        # Create tabs for different views
        trend_tabs = st.tabs(['Value Trends', 'Growth Rates', 'Market Analysis'])
        
        with trend_tabs[0]:
            fig = create_historical_value_chart(neighborhoods)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning('Historical property value data is not available.')
        
        with trend_tabs[1]:
            growth_data = []
            for hood in neighborhoods:
                historical_data = hood['historical_values'] if isinstance(hood['historical_values'], list) else json.loads(hood['historical_values'])
                if len(historical_data) >= 2:
                    start_value = historical_data[0]['value']
                    end_value = historical_data[-1]['value']
                    growth_rate = ((end_value - start_value) / start_value) * 100
                    growth_data.append({
                        'Neighborhood': hood['name'],
                        'Growth Rate': growth_rate
                    })
            
            if growth_data:
                growth_df = pd.DataFrame(growth_data)
                fig = px.bar(growth_df, x='Neighborhood', y='Growth Rate',
                            title='5-Year Growth Rates by Neighborhood')
                st.plotly_chart(fig, use_container_width=True)
        
        with trend_tabs[2]:
            for hood in neighborhoods:
                with st.expander(f'{hood["name"]} Market Analysis'):
                    historical_data = hood['historical_values'] if isinstance(hood['historical_values'], list) else json.loads(hood['historical_values'])
                    if len(historical_data) >= 2:
                        start_value = historical_data[0]['value']
                        end_value = historical_data[-1]['value']
                        annual_growth = (((end_value / start_value) ** (1/5)) - 1) * 100
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric('Current Average Value', f'${end_value:,.2f}')
                            st.metric('5-Year Price Change', f'${end_value - start_value:,.2f}')
                        with col2:
                            st.metric('Annual Growth Rate', f'{annual_growth:.1f}%')
                            st.metric('Cost of Living Score', f'{hood["cost_of_living"]}/10')

    # Clean up the temporary PDF file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == "__main__":
    display_report_results()
