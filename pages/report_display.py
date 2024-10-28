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
        
        # Create tabs for trends and analysis
        if neighborhoods:
            trend_tabs = st.tabs(['Value Trends', 'Growth Rates', 'Market Analysis'])
            
            with trend_tabs[0]:
                st.subheader('Historical Property Values')
                fig = create_historical_value_chart(neighborhoods)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning('Historical property value data is not available.')
            
            with trend_tabs[1]:
                st.subheader('Growth Rate Analysis')
                growth_data = []
                for hood in neighborhoods:
                    try:
                        historical_data = hood['historical_values'] if isinstance(hood['historical_values'], list) else json.loads(hood['historical_values'])
                        if len(historical_data) >= 2:
                            start_value = float(historical_data[0]['value'])
                            end_value = float(historical_data[-1]['value'])
                            growth_rate = ((end_value - start_value) / start_value) * 100
                            annual_growth = ((1 + growth_rate/100) ** (1/5) - 1) * 100
                            growth_data.append({
                                'Neighborhood': hood['name'],
                                'Total Growth Rate': growth_rate,
                                'Annual Growth Rate': annual_growth,
                                'Value Change': end_value - start_value
                            })
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        st.warning(f'Could not process growth data for {hood.get("name", "unknown")}')
                        continue
                
                if growth_data:
                    for data in growth_data:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                f"{data['Neighborhood']} - Total Growth",
                                f"{data['Total Growth Rate']:.1f}%",
                                delta=f"${data['Value Change']:,.2f}"
                            )
                        with col2:
                            st.metric(
                                "Annual Growth Rate",
                                f"{data['Annual Growth Rate']:.1f}%"
                            )
                else:
                    st.warning('No growth rate data available.')
            
            with trend_tabs[2]:
                st.subheader('Market Analysis')
                for hood in neighborhoods:
                    with st.expander(f"{hood['name']} Market Analysis", expanded=True):
                        try:
                            historical_data = hood['historical_values'] if isinstance(hood['historical_values'], list) else json.loads(hood['historical_values'])
                            if len(historical_data) >= 2:
                                recent_value = float(historical_data[-1]['value'])
                                start_value = float(historical_data[0]['value'])
                                yearly_growth = (((recent_value / start_value) ** (1/5)) - 1) * 100
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Current Average Value", f"${recent_value:,.2f}")
                                    st.metric("5-Year Start Value", f"${start_value:,.2f}")
                                with col2:
                                    st.metric("Annual Growth Rate", f"{yearly_growth:.1f}%")
                                    st.metric("Cost of Living Score", f"{hood['cost_of_living']}/10")
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            st.error(f'Could not analyze market data for {hood.get("name", "unknown")}')
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
            st.switch_page("pages/mortgage_calculator.py")
        st.caption("Get pre-qualified and calculate your monthly payments")
    
    with col2:
        if st.button("🏠 See Neighborhood Listings"):
            # Display property listings for recommended neighborhoods
            st.header("Available Properties")
            for match in st.session_state.report_data['recommended_neighborhoods']:
                hood = match['neighborhood']
                if 'property_listings' in hood:
                    listings = json.loads(hood['property_listings']) if isinstance(hood['property_listings'], str) else hood['property_listings']
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
                    st.write("Breakfast Options:")
                    st.write("- Local Cafe: 'Morning Brew' - Known for artisanal coffee and fresh pastries")
                    st.write("- Family Diner: 'Sunrise Kitchen' - Popular weekend brunch spot")
                    
                    st.subheader("🚶‍♂️ Family Activities")
                    st.write("Walking Routes:")
                    st.write("- Community Park Trail: Perfect for morning walks")
                    st.write("- Riverside Path: Scenic route for evening strolls")
                    
                    st.subheader("🛒 Shopping & Errands")
                    st.write("Grocery Options:")
                    st.write("- Whole Foods Market: 10-minute walk")
                    st.write("- Local Farmers Market: Weekend mornings")
                    
                    st.subheader("🚇 Transportation")
                    st.write("Public Transit:")
                    st.write(f"- Nearest Bus Stop: {hood['name']} Central")
                    st.write("- Metro Station: 5-minute walk to Green Line")
                    
                    st.subheader("🌙 Date Night Ideas")
                    st.write("Restaurant Recommendations:")
                    st.write("- 'The Bistro' - Romantic Italian dining")
                    st.write("- 'Sushi Star' - Popular fusion restaurant")
                    st.write("Entertainment:")
                    st.write("- Local Theater: Weekly shows and performances")
                    st.write("- Wine Bar: 'Vintage Room' with live jazz")
        st.caption("Experience a typical day in your potential new neighborhood")

    # Clean up the temporary PDF file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == "__main__":
    display_report_results()
