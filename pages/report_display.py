import streamlit as st
from components.navigation import create_navigation
import json
from utils.visualization import create_neighborhood_comparison_chart
from utils.report_generator import create_pdf_report
from utils.financial_calculations import calculate_rent_vs_buy
import pandas as pd
import base64
import os

st.set_page_config(page_title="Report Results", page_icon="📊")

# Optimized CSS
st.markdown('''
    <style>
        /* Optimized layout styles */
        .block-container { max-width: 100% !important; padding: 2rem; }
        .element-container, .stTabs { width: 100% !important; }
        .stTab { width: 100%; }
        [data-testid="stHorizontalBlock"] { width: 100%; gap: 2rem; }
        .stMarkdown { width: 100% !important; }
        
        /* Grid layout */
        .daily-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
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

def display_report_results():
    if 'report_data' not in st.session_state:
        st.warning("Please complete the lifestyle quiz first!")
        st.page_link("pages/lifestyle_quiz.py", label="Take the Quiz", icon="✨")
        return

    with st.spinner('Loading report...'):
        create_navigation()
        st.title("Your Personalized Home Recommendations")
        
        # Financial Recommendation Section
        st.header('💡 Financial Recommendation')
        recommendation = st.session_state.report_data['rent_vs_buy_recommendation'].upper()
        st.info(f'Based on your financial profile, we recommend you {recommendation}.')

        # Key Financial Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                'Maximum Home Price',
                f'${st.session_state.report_data["max_home_price"]:,.2f}',
                help='Based on your income and savings'
            )
        with col2:
            st.metric(
                'Down Payment Available',
                f'${st.session_state.financial_info["down_payment"]:,.2f}',
                help='From your provided financial information'
            )
        with col3:
            monthly_income = st.session_state.financial_info['annual_income'] / 12
            st.metric(
                'Monthly Income',
                f'${monthly_income:,.2f}',
                help='Your monthly household income'
            )

        # Narrative Summary
        st.header('📝 Analysis Summary')
        for match in st.session_state.report_data['recommended_neighborhoods']:
            st.subheader(f'{match["neighborhood"]["name"]} - {match["match_score"]}% Match')
            st.write('Why this neighborhood?')
            for reason in match['reasons']:
                st.markdown(f'• {reason}')
            st.divider()
        
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

        # What's Next section with optimized tabs
        st.divider()
        st.header("👉 What Would You Like to Do Next?")
        
        # Use two tabs instead of three as per manager's request
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
                for match in st.session_state.report_data['recommended_neighborhoods']:
                    hood = match['neighborhood']
                    listings = hood.get('property_listings', [])
                    if isinstance(listings, str):
                        listings = json.loads(listings)
                    
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

    # Clean up the temporary PDF file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == "__main__":
    display_report_results()
