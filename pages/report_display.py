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
        
        # Display only historical value chart
        if neighborhoods:
            st.subheader('Historical Property Values')
            fig = create_historical_value_chart(neighborhoods)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning('Historical property value data is not available.')
    else:
        st.warning('Please complete the lifestyle quiz to see neighborhood analysis.')
    
    # Add feedback section
    st.divider()
    st.header("📝 Your Feedback")
    feedback_rating = st.slider("How satisfied are you with this analysis? (1-10)", 1, 10, 5)
    if feedback_rating:
        st.write(f"Thank you for your rating of {feedback_rating}/10!")

    # What's Next section
    st.divider()
    st.header("👉 What Would You Like to Do Next?")
    st.write("Choose your next step in your home search journey:")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💰 Calculate Mortgage"):
            # Add mortgage calculator form directly in the report
            st.subheader("Mortgage Pre-Qualification")
            annual_income = st.number_input("Annual Income ($)", value=st.session_state.financial_info.get('annual_income', 60000))
            monthly_debts = st.number_input("Monthly Debts ($)", value=500)
            down_payment = st.number_input("Down Payment ($)", value=st.session_state.financial_info.get('down_payment', 20000))
            interest_rate = st.number_input("Interest Rate (%)", value=6.5, step=0.1)
            
            if st.button("Calculate"):
                # Calculate maximum mortgage amount
                monthly_income = annual_income / 12
                max_monthly_payment = (monthly_income * 0.43) - monthly_debts
                monthly_rate = interest_rate / 12 / 100
                n_payments = 30 * 12  # 30-year mortgage
                
                if monthly_rate > 0:
                    max_mortgage = max_monthly_payment * (((1 + monthly_rate)**n_payments - 1) / (monthly_rate * (1 + monthly_rate)**n_payments))
                else:
                    max_mortgage = max_monthly_payment * n_payments
                
                max_home_price = max_mortgage + down_payment
                
                st.metric("Maximum Home Price", f"${max_home_price:,.2f}")
                st.metric("Maximum Monthly Payment", f"${max_monthly_payment:,.2f}")
        st.caption("Get pre-qualified and calculate your monthly payments")
    
    with col2:
        if st.button("🏠 See Neighborhood Listings"):
            st.header("Available Properties")
            for match in st.session_state.report_data['recommended_neighborhoods']:
                hood = match['neighborhood']
                listings = hood.get('property_listings', [])
                if isinstance(listings, str):
                    listings = json.loads(listings)
                
                if listings:
                    st.subheader(f"Properties in {hood['name']}")
                    for listing in listings:
                        with st.expander(f"${listing['price']:,} - {listing['bedrooms']}bd/{listing['bathrooms']}ba"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Square Feet", f"{listing['sqft']:,}")
                                st.metric("Year Built", listing['year_built'])
                            with col2:
                                st.metric("Price/sqft", f"${listing['price']/listing['sqft']:,.2f}")
                            st.write(listing['description'])
        st.caption("View available properties in your matched neighborhoods")
    
    with col3:
        if st.button("🌟 Visualize Your Day"):
            st.header("A Day in Your New Neighborhood")
            for match in st.session_state.report_data['recommended_neighborhoods']:
                hood = match['neighborhood']
                with st.expander(f"Daily Life in {hood['name']}", expanded=True):
                    st.subheader("🍳 Morning Routine")
                    # Customize based on neighborhood location
                    if 'Lincoln Park' in hood['name']:
                        st.write("Breakfast Options:")
                        st.write("- Cafe Vienna: European-style breakfast & pastries")
                        st.write("- Sweet Maple Cafe: Local favorite for pancakes")
                    elif 'Lake View' in hood['name']:
                        st.write("Breakfast Options:")
                        st.write("- Ann Sather: Famous for Swedish breakfast")
                        st.write("- Southport Grocery: Fresh baked goods & coffee")
                    
                    st.subheader("🚶‍♂️ Family Activities")
                    if 'Lincoln Park' in hood['name']:
                        st.write("- Lincoln Park Zoo: Free admission, open daily")
                        st.write("- North Avenue Beach: Lake Michigan views")
                    elif 'Lake View' in hood['name']:
                        st.write("- Wrigley Field: Cubs games & tours")
                        st.write("- Belmont Harbor: Dog beach & walking paths")
                    
                    st.subheader("🛒 Shopping & Errands")
                    if 'Lincoln Park' in hood['name']:
                        st.write("- Trader Joe's: 667 W Diversey Pkwy")
                        st.write("- Green City Market: Seasonal farmers market")
                    elif 'Lake View' in hood['name']:
                        st.write("- Whole Foods: 3201 N Ashland Ave")
                        st.write("- Jewel-Osco: 3531 N Broadway")
                    
                    st.subheader("🚇 Transportation")
                    if 'Lincoln Park' in hood['name']:
                        st.write("- Red/Brown/Purple Line: Fullerton station")
                        st.write("- Multiple bus routes on Clark & Lincoln")
                    elif 'Lake View' in hood['name']:
                        st.write("- Red/Brown/Purple Line: Belmont station")
                        st.write("- Express buses to downtown on Lake Shore Dr")
                    
                    st.subheader("🌙 Date Night Ideas")
                    if 'Lincoln Park' in hood['name']:
                        st.write("- Restaurants:")
                        st.write("  • Cafe Ba-Ba-Reeba: Spanish tapas")
                        st.write("  • North Pond: Fine dining in the park")
                        st.write("- Entertainment:")
                        st.write("  • Steppenwolf Theatre")
                        st.write("  • Lincoln Hall: Live music venue")
                    elif 'Lake View' in hood['name']:
                        st.write("- Restaurants:")
                        st.write("  • Southport Corridor restaurants")
                        st.write("  • Music Box Theatre: Independent films")
                        st.write("- Entertainment:")
                        st.write("  • Metro: Historic concert venue")
                        st.write("  • Comedy clubs on Broadway")
        st.caption("Experience a typical day in your potential new neighborhood")

    # Clean up the temporary PDF file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == "__main__":
    display_report_results()
