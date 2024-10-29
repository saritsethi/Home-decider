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
            max-width: 100% !important;
            padding: 2rem;
        }
        .element-container, .stTabs {
            width: 100% !important;
        }
        .stTab {
            width: 100%;
        }
        [data-testid="stHorizontalBlock"] {
            width: 100%;
            gap: 2rem;
        }
        .stMarkdown {
            width: 100% !important;
        }
        .daily-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .section-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            background-color: #fff;
            height: 100%;
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
    
    # Use full width tabs instead of columns
    tabs = st.tabs(["💰 Mortgage Calculator", "🏠 Property Listings", "🌟 Daily Life"])
    
    with tabs[0]:
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
                monthly_income = annual_income / 12
                max_monthly_payment = (monthly_income * 0.43) - monthly_debts
                monthly_rate = interest_rate / 12 / 100
                n_payments = 30 * 12
                
                max_mortgage = max_monthly_payment * (((1 + monthly_rate)**n_payments - 1) / (monthly_rate * (1 + monthly_rate)**n_payments))
                max_home_price = max_mortgage + down_payment
                
                st.metric("Maximum Home Price", f"${max_home_price:,.2f}")
                st.metric("Maximum Monthly Payment", f"${max_monthly_payment:,.2f}")
    
    with tabs[1]:
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
    
    with tabs[2]:
        st.header("A Day in Your New Neighborhood")
        if st.session_state.report_data.get('recommended_neighborhoods'):
            neighborhood_tabs = st.tabs([hood['neighborhood']['name'] for hood in st.session_state.report_data['recommended_neighborhoods']])
            
            for ntab, match in zip(neighborhood_tabs, st.session_state.report_data['recommended_neighborhoods']):
                hood = match['neighborhood']
                with ntab:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🌅 Morning")
                        st.markdown("##### ☕ Coffee & Breakfast")
                        if "Lincoln Park" in hood['name']:
                            st.write("**Sweet Mandy B's**")
                            st.write("📍 1208 W Webster Ave")
                            st.write("- Family-owned bakery")
                            st.write("- Opens 7:00 AM")
                            
                            st.write("**La Colombe**")
                            st.write("📍 2529 N Clark St")
                            st.write("- Specialty coffee")
                            st.write("- Opens 6:30 AM")
                        elif "Lake View" in hood['name']:
                            st.write("**Heritage Coffee**")
                            st.write("📍 1325 W Wilson Ave")
                            st.write("- Craft coffee & tea")
                            st.write("- Opens 6:00 AM")
                            
                            st.write("**The Bageler**")
                            st.write("📍 3732 N Southport Ave")
                            st.write("- Fresh bagels")
                            st.write("- Local favorite")
                    
                    with col2:
                        st.subheader("🌅 Recreation")
                        st.markdown("##### 🏃‍♂️ Fitness")
                        if "Lincoln Park" in hood['name']:
                            st.write("**Lincoln Park Trail**")
                            st.write("📍 Lakefront Trail")
                            st.write("- 18-mile path")
                            st.write("- Lake views")
                            
                            st.write("**Lincoln Park Athletic Club**")
                            st.write("📍 1019 W Diversey")
                            st.write("- Full gym")
                            st.write("- Pool access")
                        elif "Lake View" in hood['name']:
                            st.write("**LA Fitness**")
                            st.write("📍 2828 N Clark")
                            st.write("- Modern equipment")
                            st.write("- Yoga studio")
                    
                    st.divider()
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        st.subheader("🌇 Evening")
                        st.markdown("##### 🍽️ Dining")
                        if "Lincoln Park" in hood['name']:
                            st.write("**North Pond**")
                            st.write("📍 2610 N Cannon Dr")
                            st.write("- Fine dining")
                            st.write("- Park views")
                            
                            st.write("**Pequod's Pizza**")
                            st.write("📍 2207 N Clybourn")
                            st.write("- Deep dish pizza")
                            st.write("- Local favorite")
                        elif "Lake View" in hood['name']:
                            st.write("**Tango Sur**")
                            st.write("📍 3763 N Southport")
                            st.write("- Steakhouse")
                            st.write("- BYOB")
                    
                    with col4:
                        st.subheader("🚇 Transit")
                        if "Lincoln Park" in hood['name']:
                            st.write("**L Stations:**")
                            st.write("- Fullerton (0.2 mi)")
                            st.write("- Armitage (0.4 mi)")
                            st.write("**Bus Routes:**")
                            st.write("- #22 Clark")
                            st.write("- #36 Broadway")
                        elif "Lake View" in hood['name']:
                            st.write("**L Stations:**")
                            st.write("- Belmont (0.3 mi)")
                            st.write("- Addison (0.4 mi)")
                            st.write("**Bus Routes:**")
                            st.write("- #146 Express")
                            st.write("- #22 Clark")

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
