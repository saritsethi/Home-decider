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

# Add CSS for full-width layout
st.markdown('''
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }
        .element-container {
            width: 100%;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #fff;
            border-radius: 4px;
            color: #000;
            font-size: 16px;
            font-weight: 400;
            padding: 0px 16px;
        }
        .daily-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 20px 0;
        }
        .section-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            background-color: #fff;
        }
    </style>
''', unsafe_allow_html=True)

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
            try:
                with st.form(key="mortgage_calc"):
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
                        monthly_income = annual_income / 12
                        max_monthly_payment = (monthly_income * 0.43) - monthly_debts
                        monthly_rate = interest_rate / 12 / 100
                        n_payments = 30 * 12
                        
                        max_mortgage = max_monthly_payment * (((1 + monthly_rate)**n_payments - 1) / (monthly_rate * (1 + monthly_rate)**n_payments))
                        max_home_price = max_mortgage + down_payment
                        
                        st.metric("Maximum Home Price", f"${max_home_price:,.2f}")
                        st.metric("Maximum Monthly Payment", f"${max_monthly_payment:,.2f}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    
    with col2:
        if st.button("🏠 View Properties", use_container_width=True):
            try:
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
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    with col3:
        if st.button("🌟 Visualize Your Day", use_container_width=True):
            st.header("A Day in Your New Neighborhood", anchor=False)
            
            # Create tabs for each neighborhood
            if st.session_state.report_data.get('recommended_neighborhoods'):
                tabs = st.tabs([hood['neighborhood']['name'] for hood in st.session_state.report_data['recommended_neighborhoods']])
                
                for tab, match in zip(tabs, st.session_state.report_data['recommended_neighborhoods']):
                    hood = match['neighborhood']
                    with tab:
                        # Create grid layout for each section
                        st.markdown('''
                            <style>
                                .daily-grid {
                                    display: grid;
                                    grid-template-columns: repeat(3, 1fr);
                                    gap: 20px;
                                    margin: 20px 0;
                                }
                                .section-card {
                                    border: 1px solid #ddd;
                                    border-radius: 10px;
                                    padding: 20px;
                                }
                            </style>
                        ''', unsafe_allow_html=True)
                        
                        # Morning Section
                        st.subheader("🌅 Morning Activities")
                        st.markdown('<div class="daily-grid">', unsafe_allow_html=True)
                        
                        # Breakfast & Coffee Column
                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown("##### ☕ Breakfast & Coffee")
                        if "Lincoln Park" in hood['name']:
                            st.write("**Sweet Mandy B's**")
                            st.write("📍 1208 W Webster Ave")
                            st.write("- Family-owned bakery")
                            st.write("- Homemade pastries & coffee")
                            st.write("- Opens 7:00 AM daily")
                            st.markdown("---")
                            st.write("**La Colombe Coffee**")
                            st.write("📍 2529 N Clark St")
                            st.write("- Specialty coffee roaster")
                            st.write("- Draft lattes & pastries")
                            st.write("- Opens 6:30 AM")
                        elif "Lake View" in hood['name']:
                            st.write("**Heritage Coffee**")
                            st.write("📍 1325 W Wilson Ave")
                            st.write("- Craft coffee & tea")
                            st.write("- Fresh baked goods")
                            st.write("- Opens 6:00 AM")
                            st.markdown("---")
                            st.write("**The Bageler**")
                            st.write("📍 3732 N Southport Ave")
                            st.write("- Fresh bagels & spreads")
                            st.write("- Breakfast sandwiches")
                            st.write("- Local favorite since 2010")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Exercise Column
                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown("##### 🏃‍♂️ Fitness & Recreation")
                        if "Lincoln Park" in hood['name']:
                            st.write("**Lincoln Park Running Path**")
                            st.write("📍 Lakefront Trail")
                            st.write("- 18-mile scenic trail")
                            st.write("- Lake Michigan views")
                            st.write("- Exercise stations")
                            st.markdown("---")
                            st.write("**Lincoln Park Athletic Club**")
                            st.write("📍 1019 W Diversey Pkwy")
                            st.write("- Full-service gym")
                            st.write("- Swimming pool")
                            st.write("- Group fitness classes")
                        elif "Lake View" in hood['name']:
                            st.write("**LA Fitness Lakeview**")
                            st.write("📍 2828 N Clark St")
                            st.write("- Modern gym equipment")
                            st.write("- Personal training")
                            st.write("- Yoga studio")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Parks Column
                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown("##### 🌳 Parks & Recreation")
                        if "Lincoln Park" in hood['name']:
                            st.write("**Lincoln Park Zoo**")
                            st.write("📍 2001 N Clark St")
                            st.write("- Free admission")
                            st.write("- 35-acre zoo")
                            st.write("- Nature boardwalk")
                            st.markdown("---")
                            st.write("**North Pond Nature Sanctuary**")
                            st.write("📍 2610 N Cannon Dr")
                            st.write("- Bird watching")
                            st.write("- Walking trails")
                            st.write("- Prairie gardens")
                        elif "Lake View" in hood['name']:
                            st.write("**Belmont Harbor Dog Beach**")
                            st.write("📍 3200 N Lake Shore Dr")
                            st.write("- Off-leash dog area")
                            st.write("- Beach access")
                            st.write("- Sunset views")
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Add other sections (Daytime, Evening, Transportation) similarly...
                        
                        # Transportation
                        st.divider()
                        st.subheader("🚇 Transportation")
                        st.markdown('<div class="daily-grid">', unsafe_allow_html=True)
                        
                        # Public Transit Column
                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown("##### Public Transit")
                        if "Lincoln Park" in hood['name']:
                            st.write("**Nearest L Stations:**")
                            st.write("- Fullerton (Red/Brown/Purple): 0.2 mi")
                            st.write("- Armitage (Brown/Purple): 0.4 mi")
                            st.markdown("---")
                            st.write("**Bus Routes:**")
                            st.write("- #22 Clark")
                            st.write("- #36 Broadway")
                            st.write("- #74 Fullerton")
                        elif "Lake View" in hood['name']:
                            st.write("**Nearest L Stations:**")
                            st.write("- Belmont (Red/Brown/Purple): 0.3 mi")
                            st.write("- Addison (Red): 0.4 mi")
                            st.markdown("---")
                            st.write("**Bus Routes:**")
                            st.write("- #146 Inner Drive/Michigan Express")
                            st.write("- #22 Clark")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Bike & Walk Column
                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown("##### Biking & Walking")
                        if "Lincoln Park" in hood['name']:
                            st.write("**Divvy Bike Stations:**")
                            st.write("- Clark & Fullerton")
                            st.write("- Lincoln & Diversey")
                            st.markdown("---")
                            st.write("**Walking Paths:**")
                            st.write("- Lakefront Trail access")
                            st.write("- Lincoln Park paths")
                        elif "Lake View" in hood['name']:
                            st.write("**Divvy Bike Stations:**")
                            st.write("- Broadway & Belmont")
                            st.write("- Southport & Addison")
                            st.markdown("---")
                            st.write("**Walking Areas:**")
                            st.write("- Southport Corridor")
                            st.write("- Harbor walkway")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Commute Times Column
                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown("##### Common Commute Times")
                        if "Lincoln Park" in hood['name']:
                            st.write("**By Public Transit:**")
                            st.write("- Loop: 20-25 min")
                            st.write("- O'Hare: 45-50 min")
                            st.write("- River North: 15-20 min")
                            st.markdown("---")
                            st.write("**By Car:**")
                            st.write("- Loop: 12-15 min")
                            st.write("- O'Hare: 25-35 min")
                        elif "Lake View" in hood['name']:
                            st.write("**By Public Transit:**")
                            st.write("- Loop: 25-30 min")
                            st.write("- O'Hare: 50-55 min")
                            st.write("- River North: 20-25 min")
                            st.markdown("---")
                            st.write("**By Car:**")
                            st.write("- Loop: 15-20 min")
                            st.write("- O'Hare: 30-40 min")
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

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
