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

def get_pdf_download_link(pdf_path, link_text="Download PDF Report"):
    """Generate a link to download the PDF file."""
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="home_decision_report.pdf">{link_text}</a>'
    return href

def display_property_listings(neighborhood):
    """Display property listings for a neighborhood."""
    if 'property_listings' in neighborhood:
        listings = neighborhood['property_listings']
        if isinstance(listings, str):
            listings = json.loads(listings)
        
        if listings:
            st.markdown("#### 🏠 Available Properties")
            for listing in listings:
                with st.expander(f"${listing['price']:,} - {listing['bedrooms']}bd/{listing['bathrooms']}ba"):
                    st.write(f"**Address**: {listing['address']}")
                    st.write(f"**Square Feet**: {listing['sqft']}")
                    st.write(f"**Year Built**: {listing['year_built']}")
                    st.write(f"**Description**: {listing['description']}")

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
    st.header('💰 Cost Analysis')
    
    # Get cost analysis
    costs = calculate_rent_vs_buy(
        st.session_state.financial_info['target_home_price'],
        st.session_state.financial_info['down_payment'],
        4.5,  # Assumed interest rate
        30,   # 30-year mortgage
        st.session_state.financial_info['current_monthly_rent']
    )
    
    # Monthly costs comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Buying Costs")
        st.metric("Mortgage Payment", f"${costs['monthly_mortgage']:,.2f}")
        st.metric("Property Tax", f"${costs['monthly_ownership_costs']['property_tax']:,.2f}")
        st.metric("HOA Fees", f"${costs['monthly_ownership_costs']['hoa']:,.2f}")
        st.metric("Insurance", f"${costs['monthly_ownership_costs']['insurance']:,.2f}")
        st.metric("Maintenance", f"${costs['monthly_ownership_costs']['maintenance']:,.2f}")
        st.metric("Total Monthly Cost", f"${costs['total_monthly_ownership']:,.2f}", "Buying")
    
    with col2:
        st.subheader("Monthly Renting Costs")
        st.metric("Current Rent", f"${st.session_state.financial_info['current_monthly_rent']:,.2f}")
        st.metric("Break-even Rent", f"${costs['break_even_rent']:,.2f}")
        st.write("*Renting is more affordable if your rent stays below the break-even amount")
    
    # 5-year comparison
    st.subheader("5-Year Cost Comparison")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total 5-Year Buying Cost", f"${costs['five_year_buying_cost']:,.2f}")
    with col2:
        st.metric("Total 5-Year Renting Cost", f"${costs['five_year_renting_cost']:,.2f}")
        difference = costs['five_year_renting_cost'] - costs['five_year_buying_cost']
        st.metric("Cost Difference", f"${abs(difference):,.2f}", 
                 f"{'Renting costs more' if difference > 0 else 'Buying costs more'}")
    
    # Neighborhood Analysis
    st.header('🏘️ Neighborhood Analysis')
    if st.session_state.report_data.get('recommended_neighborhoods'):
        # Display each recommended neighborhood
        for match in st.session_state.report_data['recommended_neighborhoods']:
            hood = match['neighborhood']
            st.subheader(f"{hood['name']} - {match['match_score']}% Match")
            
            # Display match reasons
            st.markdown("#### Why this neighborhood?")
            for reason in match['reasons']:
                st.markdown(f"- {reason}")
            
            # Create columns for metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("School Rating", f"{hood['school_rating']}/10")
                st.metric("Transport Score", f"{hood['transport_score']}/10")
            with col2:
                st.metric("Walkability", f"{hood['walkability_score']}/10")
                st.metric("Cost of Living", f"{hood['cost_of_living']}/10")
            
            # Display property listings
            display_property_listings(hood)
            
            st.divider()
        
        # Create radar chart comparing neighborhoods
        if neighborhoods := [match['neighborhood'] for match in st.session_state.report_data['recommended_neighborhoods']]:
            st.subheader("Neighborhood Comparison")
            
            # Create and display radar chart
            radar_fig = create_neighborhood_comparison_chart(neighborhoods)
            if radar_fig:
                st.plotly_chart(radar_fig, use_container_width=True)
            else:
                st.warning("Could not create neighborhood comparison visualization.")
    else:
        st.warning('Please complete the lifestyle quiz to see neighborhood analysis.')

    # What's Next Section
    st.header("🎯 What's Next?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 💰 Get Pre-Qualified
        Ready to take the next step? Use our mortgage calculator to estimate your monthly payments and get pre-qualified.
        """)
        st.page_link("pages/mortgage_calculator.py", label="Calculate Mortgage", icon="💰")
    
    with col2:
        st.markdown("""
        ### 🔍 Compare More Areas
        Want to explore other neighborhoods? Use our comparison tool to find the perfect match.
        """)
        st.page_link("pages/neighborhood_comparison.py", label="Compare Areas", icon="🏘️")
    
    with col3:
        st.markdown("""
        ### 📊 Rent vs Buy Analysis
        Still deciding between renting and buying? Get a detailed cost comparison.
        """)
        st.page_link("pages/rent_vs_buy.py", label="Compare Costs", icon="🧮")

    # Add feedback section at the very end
    st.divider()
    st.header("📝 Your Feedback")
    feedback_rating = st.slider("How satisfied are you with this analysis? (1-10)", 1, 10, 5)
    if feedback_rating:
        st.write(f"Thank you for your rating of {feedback_rating}/10!")

    # Clean up the temporary PDF file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == "__main__":
    display_report_results()
