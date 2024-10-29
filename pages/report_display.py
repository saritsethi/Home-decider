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
                        # Morning Activities
                        st.subheader("🌅 Morning")
                        morning_col1, morning_col2 = st.columns(2)
                        with morning_col1:
                            st.markdown("##### Breakfast & Coffee")
                            if "Lincoln Park" in hood['name']:
                                st.write("☕ **Sweet Mandy B's**")
                                st.write("- Local bakery & cafe")
                                st.write("- Known for fresh pastries")
                                st.write("- Opens 7:00 AM")
                                
                                st.write("☕ **Elaine's Coffee Call**")
                                st.write("- Cozy neighborhood spot")
                                st.write("- Artisanal coffee")
                                st.write("- Fresh baked goods")
                            elif "Lake View" in hood['name']:
                                st.write("☕ **Intelligentsia Coffee**")
                                st.write("- Premium coffee roaster")
                                st.write("- Specialty drinks")
                                st.write("- Opens 6:30 AM")
                                
                                st.write("☕ **Ann Sather**")
                                st.write("- Famous cinnamon rolls")
                                st.write("- Swedish breakfast")
                                st.write("- Family friendly")
                            else:
                                st.write("Local cafes and breakfast spots")
                                
                        with morning_col2:
                            st.markdown("##### Morning Exercise")
                            if "Lincoln Park" in hood['name']:
                                st.write("🏃‍♂️ **Lincoln Park Trail**")
                                st.write("- 18-mile lakefront path")
                                st.write("- Popular for morning jogs")
                                st.write("- Beautiful lake views")
                            elif "Lake View" in hood['name']:
                                st.write("🏃‍♂️ **Belmont Harbor Running Path**")
                                st.write("- Scenic harbor views")
                                st.write("- 3-mile loop")
                                st.write("- Exercise stations")
                            else:
                                st.write("Local parks and running trails")

                        # Daily Activities
                        st.subheader("☀️ Daytime")
                        day_col1, day_col2 = st.columns(2)
                        with day_col1:
                            st.markdown("##### Shopping & Errands")
                            if "Lincoln Park" in hood['name']:
                                st.write("🛒 **Trader Joe's**")
                                st.write("- 667 W Diversey Pkwy")
                                st.write("- Full grocery selection")
                                st.write("- Parking available")
                                
                                st.write("🛒 **Green City Market**")
                                st.write("- Local farmers market")
                                st.write("- Wed & Sat mornings")
                                st.write("- Fresh produce & artisanal goods")
                            elif "Lake View" in hood['name']:
                                st.write("🛒 **Whole Foods Market**")
                                st.write("- 3201 N Ashland Ave")
                                st.write("- Organic & local products")
                                st.write("- Hot food bar")
                            else:
                                st.write("Local grocery stores and markets")

                        with day_col2:
                            st.markdown("##### Recreation")
                            if "Lincoln Park" in hood['name']:
                                st.write("🦁 **Lincoln Park Zoo**")
                                st.write("- Free admission")
                                st.write("- Open daily")
                                st.write("- Family friendly")
                                
                                st.write("🎨 **Chicago History Museum**")
                                st.write("- Local history exhibits")
                                st.write("- Interactive displays")
                                st.write("- Family programs")
                            elif "Lake View" in hood['name']:
                                st.write("⚾ **Wrigley Field**")
                                st.write("- Historic baseball stadium")
                                st.write("- Stadium tours available")
                                st.write("- Year-round events")
                            else:
                                st.write("Local attractions and activities")

                        # Evening Options
                        st.subheader("🌙 Evening")
                        evening_col1, evening_col2 = st.columns(2)
                        with evening_col1:
                            st.markdown("##### Dining")
                            if "Lincoln Park" in hood['name']:
                                st.write("🍝 **Cafe Ba-Ba-Reeba!**")
                                st.write("- Spanish tapas")
                                st.write("- Lively atmosphere")
                                st.write("- Great for groups")
                                
                                st.write("🍷 **North Pond**")
                                st.write("- Fine dining")
                                st.write("- Park views")
                                st.write("- Special occasion spot")
                            elif "Lake View" in hood['name']:
                                st.write("🍣 **Tango Sur**")
                                st.write("- Argentine steakhouse")
                                st.write("- BYOB")
                                st.write("- Intimate setting")
                            else:
                                st.write("Local restaurants and eateries")

                        with evening_col2:
                            st.markdown("##### Entertainment")
                            if "Lincoln Park" in hood['name']:
                                st.write("🎭 **Steppenwolf Theatre**")
                                st.write("- World-class performances")
                                st.write("- Modern venue")
                                st.write("- Student discounts")
                                
                                st.write("🎵 **Lincoln Hall**")
                                st.write("- Live music venue")
                                st.write("- Intimate shows")
                                st.write("- Full bar")
                            elif "Lake View" in hood['name']:
                                st.write("🎬 **Music Box Theatre**")
                                st.write("- Independent films")
                                st.write("- Historic venue")
                                st.write("- Special events")
                            else:
                                st.write("Local entertainment venues")

                        # Transportation
                        st.divider()
                        st.subheader("🚇 Getting Around")
                        transport_col1, transport_col2 = st.columns(2)
                        with transport_col1:
                            st.metric("Walk Score", f"{hood['walkability_score']}/10")
                            st.write("**Nearest Transit:**")
                            if "Lincoln Park" in hood['name']:
                                st.write("- Fullerton Station (Red/Brown/Purple): 0.2 mi")
                                st.write("- Clark/Lincoln Bus: 0.1 mi")
                                st.write("- Divvy Bike Station: 0.1 mi")
                            elif "Lake View" in hood['name']:
                                st.write("- Belmont Station (Red/Brown/Purple): 0.3 mi")
                                st.write("- Addison Station (Red): 0.4 mi")
                                st.write("- Multiple bus routes on Clark")
                            else:
                                st.write("Local transit options")
                                
                        with transport_col2:
                            st.metric("Transit Score", f"{hood['transport_score']}/10")
                            st.write("**Common Commute Times:**")
                            if "Lincoln Park" in hood['name']:
                                st.write("- Downtown: 15-20 min")
                                st.write("- O'Hare Airport: 45-50 min")
                                st.write("- Medical District: 25-30 min")
                            elif "Lake View" in hood['name']:
                                st.write("- Downtown: 20-25 min")
                                st.write("- O'Hare Airport: 50-55 min")
                                st.write("- River North: 15-20 min")
                            else:
                                st.write("Estimated commute times")

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
