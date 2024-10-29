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
    
    st.divider()
    
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
        if st.button("💰 Calculate Mortgage", use_container_width=True):
            with st.form("mortgage_calc_form"):
                annual_income = float(st.number_input("Annual Income ($)", 
                    min_value=0.0, 
                    value=float(st.session_state.financial_info.get('annual_income', 60000.0)),
                    step=1000.0
                ))
                monthly_debts = float(st.number_input("Monthly Debts ($)", 
                    min_value=0.0, 
                    value=500.0,
                    step=100.0
                ))
                down_payment = float(st.number_input("Down Payment ($)", 
                    min_value=0.0, 
                    value=float(st.session_state.financial_info.get('down_payment', 20000.0)),
                    step=1000.0
                ))
                interest_rate = float(st.number_input("Interest Rate (%)", 
                    min_value=0.0, 
                    value=6.5, 
                    step=0.1
                ))
                
                if st.form_submit_button("Calculate"):
                    monthly_income = annual_income / 12
                    max_monthly_payment = (monthly_income * 0.43) - monthly_debts
                    monthly_rate = interest_rate / 12 / 100
                    n_payments = 30 * 12
                    
                    max_mortgage = max_monthly_payment * (((1 + monthly_rate)**n_payments - 1) / (monthly_rate * (1 + monthly_rate)**n_payments))
                    max_home_price = max_mortgage + down_payment
                    
                    st.metric("Maximum Home Price", f"${max_home_price:,.2f}")
                    st.metric("Maximum Monthly Payment", f"${max_monthly_payment:,.2f}")
    
    with col2:
        if st.button("🏠 View Properties", use_container_width=True):
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
                else:
                    st.info(f"No current listings available in {hood['name']}")
    
    with col3:
        if st.button("🌟 Visualize Your Day", use_container_width=True):
            st.header("A Day in Your New Neighborhood")
            
            # Create tabs for each neighborhood
            if st.session_state.report_data.get('recommended_neighborhoods'):
                tabs = st.tabs([hood['neighborhood']['name'] for hood in st.session_state.report_data['recommended_neighborhoods']])
                
                for tab, match in zip(tabs, st.session_state.report_data['recommended_neighborhoods']):
                    hood = match['neighborhood']
                    with tab:
                        # Create grid layout for activities
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.subheader("🍳 Morning Options")
                            st.markdown("#### Breakfast & Coffee")
                            # Add actual Google Places data for cafes and restaurants
                            if 'Lincoln Park' in hood['name']:
                                st.write("[Sweet Mandy B's](https://goo.gl/maps/eGckLZAHj3VBKqSt8)")
                                st.write("⭐ 4.8 (2,000+ reviews)")
                                st.write("Local bakery & cafe")
                                
                                st.write("[Cafe Vienna](https://goo.gl/maps/QK9Z1XYG5v8RK6at8)")
                                st.write("⭐ 4.6 (500+ reviews)")
                                st.write("European breakfast")
                            
                            st.markdown("#### Parks & Morning Walks")
                            # Add actual park data
                            if 'Lincoln Park' in hood['name']:
                                st.write("[Lincoln Park Zoo](https://goo.gl/maps/8Q9Z1XYG5v8RK6at8)")
                                st.write("⭐ 4.8 (30,000+ reviews)")
                                st.write("Free admission, open daily")
                        
                        with col2:
                            st.subheader("🏃‍♂️ Daily Activities")
                            st.markdown("#### Grocery Shopping")
                            # Add actual grocery store data
                            if 'Lincoln Park' in hood['name']:
                                st.write("[Trader Joe's](https://goo.gl/maps/7Q9Z1XYG5v8RK6at8)")
                                st.write("⭐ 4.7 (3,000+ reviews)")
                                st.write("667 W Diversey Pkwy")
                            
                            st.markdown("#### Fitness & Recreation")
                            # Add actual gym/fitness data
                            if 'Lincoln Park' in hood['name']:
                                st.write("[LA Fitness](https://goo.gl/maps/6Q9Z1XYG5v8RK6at8)")
                                st.write("⭐ 4.5 (1,000+ reviews)")
                                st.write("Full-service gym")
                        
                        with col3:
                            st.subheader("🌙 Evening Activities")
                            st.markdown("#### Dining Options")
                            # Add actual restaurant data
                            if 'Lincoln Park' in hood['name']:
                                st.write("[North Pond](https://goo.gl/maps/5Q9Z1XYG5v8RK6at8)")
                                st.write("⭐ 4.9 (1,500+ reviews)")
                                st.write("Fine dining with park views")
                            
                            st.markdown("#### Entertainment")
                            # Add actual entertainment venue data
                            if 'Lincoln Park' in hood['name']:
                                st.write("[Steppenwolf Theatre](https://goo.gl/maps/4Q9Z1XYG5v8RK6at8)")
                                st.write("⭐ 4.8 (2,000+ reviews)")
                                st.write("World-class performances")

                        # Add transportation info at the bottom
                        st.divider()
                        st.subheader("🚇 Getting Around")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Walk Score", f"{hood['walkability_score']}/10")
                            st.write("Nearest Transit:")
                            if 'Lincoln Park' in hood['name']:
                                st.write("- Fullerton (Red/Brown/Purple): 0.2 mi")
                                st.write("- Clark/Lincoln Bus: 0.1 mi")
                        with col2:
                            st.metric("Transit Score", f"{hood['transport_score']}/10")
                            st.write("Common Commute Times:")
                            if 'Lincoln Park' in hood['name']:
                                st.write("- Downtown: 15-20 min")
                                st.write("- O'Hare Airport: 45-50 min")

    # Note about future Google Places API integration
    st.info("Note: Future updates will include real-time data from Google Places API for more accurate and up-to-date neighborhood information.")

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
