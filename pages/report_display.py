import streamlit as st
from components.navigation import create_navigation
import json
from utils.visualization import create_neighborhood_comparison_chart
from utils.report_generator import create_pdf_report
from utils.financial_calculations import calculate_rent_vs_buy
import pandas as pd
import base64
import os

st.set_page_config(page_title="Report Results", page_icon="📊", layout="wide")

# Optimized CSS
st.markdown('''
    <style>
        /* Optimized layout styles */
        .block-container { max-width: 100% !important; padding: 2rem; }
        .element-container, .stTabs { width: 100% !important; }
        .stTab { width: 100%; }
        [data-testid="stHorizontalBlock"] { width: 100%; gap: 2rem; }
        .stMarkdown { width: 100% !important; }
        
        /* Card styles */
        .section-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            background-color: #fff;
            height: 100%;
            transition: all 0.2s ease;
        }
    </style>
''', unsafe_allow_html=True)

@st.cache_data
def get_pdf_download_link(pdf_path, link_text="Download PDF Report"):
    """Generate a cached link to download the PDF file."""
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="home_decision_report.pdf">{link_text}</a>'
    return href

@st.cache_data
def calculate_mortgage_prequalification(annual_income, monthly_debts, down_payment, interest_rate):
    """Calculate cached mortgage pre-qualification results."""
    monthly_income = annual_income / 12
    max_monthly_payment = (monthly_income * 0.43) - monthly_debts
    monthly_rate = interest_rate / 12 / 100
    n_payments = 30 * 12
    
    max_mortgage = max_monthly_payment * (((1 + monthly_rate)**n_payments - 1) / (monthly_rate * (1 + monthly_rate)**n_payments))
    max_home_price = max_mortgage + down_payment
    
    return max_home_price, max_monthly_payment

def initialize_session_state():
    """Initialize session state with default values if not present."""
    if 'report_data' not in st.session_state:
        st.session_state.report_data = None
    if 'financial_info' not in st.session_state:
        st.session_state.financial_info = {}
    if 'preferences' not in st.session_state:
        st.session_state.preferences = {}

def display_report_results():
    # Initialize session state
    initialize_session_state()
    
    # Create navigation
    create_navigation()
    
    if not st.session_state.report_data:
        st.warning("Please complete the lifestyle quiz first!")
        st.page_link("pages/lifestyle_quiz.py", label="Take the Quiz", icon="✨")
        return

    with st.spinner('Loading report...'):
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

        # Financial Analysis Section
        st.divider()
        st.header("💰 Financial Analysis")

        # Display rent vs buy recommendation
        st.subheader("Rent vs Buy Recommendation")
        recommendation = st.session_state.report_data['rent_vs_buy_recommendation'].upper()
        st.info(f"Based on your financial profile, we recommend you {recommendation}.")

        # Display financial metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Maximum Home Price", f"${st.session_state.report_data['max_home_price']:,.2f}")
        with col2:
            st.metric("Annual Income", f"${st.session_state.financial_info['annual_income']:,.2f}")
        with col3:
            st.metric("Total Savings", f"${st.session_state.financial_info['savings']:,.2f}")

        # Neighborhood Comparison Section
        st.divider()
        st.header("🏘️ Neighborhood Analysis")

        # Display recommended neighborhoods
        if 'recommended_neighborhoods' in st.session_state.report_data:
            for match in st.session_state.report_data['recommended_neighborhoods']:
                hood = match['neighborhood']
                with st.expander(f"{hood['name']} - {match['match_score']}% Match", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("School Rating", f"{hood['school_rating']}/10")
                        st.metric("Transport Score", f"{hood['transport_score']}/10")
                    
                    with col2:
                        st.metric("Walkability", f"{hood['walkability_score']}/10")
                        st.metric("Cost of Living", f"{hood['cost_of_living']}/10")
                    
                    if match.get('reasons'):
                        st.subheader("Why This Neighborhood?")
                        for reason in match['reasons']:
                            st.write(f"• {reason}")

        # What's Next section with optimized tabs
        st.divider()
        st.header("👉 What Would You Like to Do Next?")
        
        tab_mortgage, tab_listings = st.tabs(["💰 Mortgage Calculator", "🏠 Property Listings"])
        
        with tab_mortgage:
            with st.spinner('Loading mortgage calculator...'):
                st.subheader("Mortgage Pre-Qualification")
                with st.form(key="mortgage_calc"):
                    col1, col2 = st.columns(2)
                    with col1:
                        annual_income = st.number_input(
                            "Annual Income ($)",
                            min_value=0.0,
                            value=float(st.session_state.financial_info.get('annual_income', 60000.0)),
                            step=1000.0,
                            format="%.2f"
                        )
                        monthly_debts = st.number_input(
                            "Monthly Debts ($)",
                            min_value=0.0,
                            value=500.0,
                            step=100.0,
                            format="%.2f"
                        )
                    with col2:
                        down_payment = st.number_input(
                            "Down Payment ($)",
                            min_value=0.0,
                            value=float(st.session_state.financial_info.get('down_payment', 20000.0)),
                            step=1000.0,
                            format="%.2f"
                        )
                        interest_rate = st.number_input(
                            "Interest Rate (%)",
                            min_value=0.0,
                            value=6.5,
                            step=0.1,
                            format="%.1f"
                        )
                    
                    submit_calc = st.form_submit_button("Calculate")
                    
                    if submit_calc:
                        max_home_price, max_monthly_payment = calculate_mortgage_prequalification(
                            annual_income, monthly_debts, down_payment, interest_rate
                        )
                        st.metric("Maximum Home Price", f"${max_home_price:,.2f}")
                        st.metric("Maximum Monthly Payment", f"${max_monthly_payment:,.2f}")
        
        with tab_listings:
            with st.spinner('Loading property listings...'):
                st.subheader("Available Properties")
                if 'recommended_neighborhoods' in st.session_state.report_data:
                    for match in st.session_state.report_data['recommended_neighborhoods']:
                        hood = match['neighborhood']
                        listings = hood.get('property_listings', [])
                        if isinstance(listings, str):
                            try:
                                listings = json.loads(listings)
                            except json.JSONDecodeError:
                                listings = []
                        
                        if listings:
                            st.subheader(f"Properties in {hood['name']}")
                            for listing in listings:
                                with st.expander(f"${listing['price']:,} - {listing['bedrooms']}bd/{listing['bathrooms']}ba", expanded=True):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Square Feet", f"{listing['sqft']:,}")
                                        st.metric("Year Built", listing['year_built'])
                                    with col2:
                                        st.metric("Price/sqft", f"${listing['price']/listing['sqft']:,.2f}")
                                    st.write(listing['description'])
                else:
                    st.warning("No neighborhood recommendations available. Please complete the lifestyle quiz.")

        # Clean up the temporary PDF file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    display_report_results()
