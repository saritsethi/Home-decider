import streamlit as st
from components.navigation import create_navigation
import json
from utils.visualization import create_neighborhood_comparison_chart
from utils.report_generator import create_pdf_report
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
    else:
        st.warning('Please complete the lifestyle quiz to see neighborhood analysis.')

    # What's Next section
    st.divider()
    st.header("👉 What Would You Like to Do Next?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💰 Calculate Mortgage"):
            # Add mortgage calculator directly in the report
            st.subheader("Calculate Your Mortgage")
            annual_income = st.number_input("Annual Income ($)", min_value=0, value=60000, step=1000)
            down_payment = st.number_input("Down Payment ($)", min_value=0, value=20000, step=1000)
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=6.5, step=0.1)
            loan_term = st.selectbox("Loan Term (Years)", [15, 20, 30], index=2)
            
            if st.button("Calculate Payment"):
                # Calculate monthly payment
                principal = st.session_state.financial_info.get('target_home_price', 300000) - down_payment
                monthly_rate = interest_rate / 12 / 100
                n_payments = loan_term * 12
                monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
                
                st.metric("Monthly Payment", f"${monthly_payment:,.2f}")
                st.metric("Total Loan Amount", f"${principal:,.2f}")
    
    with col2:
        if st.button("🏠 View Properties"):
            if st.session_state.report_data.get('recommended_neighborhoods'):
                st.header("Available Properties")
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
    
    with col3:
        if st.button("🌟 Visualize Your Day"):
            st.header("A Day in Your New Neighborhood")
            for match in st.session_state.report_data['recommended_neighborhoods']:
                hood = match['neighborhood']
                with st.expander(f"Daily Life in {hood['name']}", expanded=True):
                    st.subheader("🍳 Morning Routine")
                    st.write("Breakfast Options:")
                    if 'Lincoln Park' in hood['name']:
                        st.write("- Cafe Vienna: European-style breakfast & pastries")
                        st.write("- Sweet Maple Cafe: Local favorite for pancakes")
                    elif 'Lake View' in hood['name']:
                        st.write("- Ann Sather: Famous for Swedish breakfast")
                        st.write("- Southport Grocery: Fresh baked goods & coffee")
                    else:
                        st.write("- Local cafes and restaurants within walking distance")
                        st.write("- Popular breakfast spots in the area")
                    
                    st.subheader("🚶‍♂️ Family Activities")
                    if 'Lincoln Park' in hood['name']:
                        st.write("- Lincoln Park Zoo: Free admission, open daily")
                        st.write("- North Avenue Beach: Lake Michigan views")
                    elif 'Lake View' in hood['name']:
                        st.write("- Wrigley Field: Cubs games & tours")
                        st.write("- Belmont Harbor: Dog beach & walking paths")
                    else:
                        st.write("- Community parks and recreational areas")
                        st.write("- Local attractions and entertainment venues")
                    
                    st.subheader("🛒 Shopping & Errands")
                    if 'Lincoln Park' in hood['name']:
                        st.write("- Trader Joe's: 667 W Diversey Pkwy")
                        st.write("- Green City Market: Seasonal farmers market")
                    elif 'Lake View' in hood['name']:
                        st.write("- Whole Foods: 3201 N Ashland Ave")
                        st.write("- Jewel-Osco: 3531 N Broadway")
                    else:
                        st.write("- Local grocery stores and supermarkets")
                        st.write("- Shopping centers and retail outlets")
                    
                    st.subheader("🚇 Transportation")
                    if 'Lincoln Park' in hood['name']:
                        st.write("- Red/Brown/Purple Line: Fullerton station")
                        st.write("- Multiple bus routes on Clark & Lincoln")
                    elif 'Lake View' in hood['name']:
                        st.write("- Red/Brown/Purple Line: Belmont station")
                        st.write("- Express buses to downtown on Lake Shore Dr")
                    else:
                        st.write("- Nearby public transit stations")
                        st.write("- Major bus routes and transportation hubs")
                    
                    st.subheader("🌙 Date Night Ideas")
                    if 'Lincoln Park' in hood['name']:
                        st.write("Restaurants:")
                        st.write("- Cafe Ba-Ba-Reeba: Spanish tapas")
                        st.write("- North Pond: Fine dining in the park")
                        st.write("Entertainment:")
                        st.write("- Steppenwolf Theatre")
                        st.write("- Lincoln Hall: Live music venue")
                    elif 'Lake View' in hood['name']:
                        st.write("Restaurants:")
                        st.write("- Southport Corridor restaurants")
                        st.write("- Music Box Theatre: Independent films")
                        st.write("Entertainment:")
                        st.write("- Metro: Historic concert venue")
                        st.write("- Comedy clubs on Broadway")
                    else:
                        st.write("Restaurants:")
                        st.write("- Local dining establishments")
                        st.write("- Popular neighborhood eateries")
                        st.write("Entertainment:")
                        st.write("- Movie theaters and performance venues")
                        st.write("- Local nightlife and entertainment options")

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
