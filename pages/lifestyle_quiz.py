import streamlit as st
import json
import uuid
import os
from components.navigation import create_navigation
from utils.database import save_quiz_results, get_neighborhood_data
from utils.report_generator import calculate_neighborhood_match, generate_integrated_report, create_pdf_report

st.set_page_config(page_title="Lifestyle Quiz", page_icon="✨")

def generate_and_display_report(family_info, financial_info, preferences):
    """Generate and display comprehensive report with all recommendations."""
    # Save quiz results
    save_quiz_results(
        st.session_state.session_id,
        json.dumps(preferences),
        json.dumps({**family_info, **financial_info})
    )
    
    # Get neighborhood matches
    matches = calculate_neighborhood_match(preferences)
    
    # Generate integrated report
    report_data = generate_integrated_report(
        preferences,
        {**family_info, **financial_info},
        matches
    )
    
    display_report_results(report_data)

def display_report_results(report_data):
    """Display the report results in a structured format."""
    st.success("🎯 Here are your personalized recommendations!")
    
    # Financial Summary
    st.subheader("Financial Analysis")
    st.write(f"Based on your financial information:")
    st.write(f"- Maximum affordable home price: ${report_data['max_home_price']:,.2f}")
    st.write(f"- Recommendation: {report_data['rent_vs_buy_recommendation'].upper()}")
    
    # Display filtered and prioritized neighborhood matches
    st.subheader("Recommended Neighborhoods")
    for i, match in enumerate(report_data['recommended_neighborhoods']):
        hood = match["neighborhood"]
        with st.expander(f"#{i+1}: {hood['name']} - {match['match_score']}% Match", expanded=i==0):
            st.write("### Why this neighborhood matches your needs:")
            for reason in match["reasons"]:
                st.write(f"- {reason}")
            
            if st.session_state.family_info['children'] > 0:
                st.write(f"- School Rating: {hood['school_rating']:.1f}/10 (Great for families with children!)")
            
            st.write("### Neighborhood Stats:")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Cost of Living", f"{hood['cost_of_living']:.1f}/10")
                st.metric("Transport Score", f"{hood['transport_score']:.1f}/10")
            with col2:
                st.metric("School Rating", f"{hood['school_rating']:.1f}/10")
                st.metric("Walkability", f"{hood['walkability_score']:.1f}/10")
    
    # Generate and offer PDF download
    if st.button("Generate Detailed PDF Report"):
        pdf_path = f"temp_report_{st.session_state.session_id}.pdf"
        create_pdf_report(pdf_path, report_data, st.session_state.family_info, preferences)
        
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name="home_decision_report.pdf",
                mime="application/pdf"
            )
        
        os.remove(pdf_path)

def main():
    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    create_navigation()
    
    st.title("Lifestyle Preference Quiz")
    
    # Progress indicator
    steps = ["Family Information", "Financial Details", "Neighborhood Preferences"]
    st.progress((st.session_state.current_step - 1) / len(steps))
    st.write(f"Step {st.session_state.current_step} of {len(steps)}: {steps[st.session_state.current_step-1]}")
    
    # Navigation - Back button
    if st.session_state.current_step > 1:
        if st.button("← Back"):
            st.session_state.current_step -= 1
            st.rerun()
    
    # Step 1: Family Information
    if st.session_state.current_step == 1:
        with st.form("family_info_form"):
            st.subheader("Family Information")
            family_size = st.number_input("Number of family members", min_value=1, value=1)
            adults = st.number_input("Number of adults", min_value=1, value=1)
            children = st.number_input("Number of children", min_value=0, value=0)
            if st.form_submit_button("Next"):
                st.session_state.family_info = {
                    "family_size": family_size,
                    "adults": adults,
                    "children": children
                }
                st.session_state.current_step = 2
                st.rerun()
    
    # Step 2: Financial Details
    elif st.session_state.current_step == 2:
        with st.form("financial_details_form"):
            st.subheader("Financial Information")
            annual_income = st.number_input("Annual Household Income ($)", min_value=0, value=50000, step=1000)
            savings = st.number_input("Total Savings ($)", min_value=0, value=10000, step=1000)
            monthly_expenses = st.number_input("Monthly Expenses ($)", min_value=0, value=2000, step=100)
            if st.form_submit_button("Next"):
                st.session_state.financial_info = {
                    "annual_income": annual_income,
                    "savings": savings,
                    "monthly_expenses": monthly_expenses
                }
                st.session_state.current_step = 3
                st.rerun()
    
    # Step 3: Neighborhood Preferences
    else:
        with st.form("neighborhood_preferences_form"):
            st.subheader("Neighborhood Preferences")
            housing_type = st.select_slider(
                "Do you prefer urban or suburban living?",
                options=["Very Urban", "Somewhat Urban", "Mixed", "Somewhat Suburban", "Very Suburban"]
            )
            transport = st.select_slider(
                "How do you prefer to get around?",
                options=["Walking", "Public Transit", "Mix", "Personal Vehicle"]
            )
            
            col1, col2 = st.columns(2)
            with col1:
                nightlife = st.slider("How important is nightlife?", 0, 10, 5)
                shopping = st.slider("How important is shopping access?", 0, 10, 5)
            with col2:
                outdoor = st.slider("How important are outdoor activities?", 0, 10, 5)
                quiet = st.slider("How important is a quiet neighborhood?", 0, 10, 5)
            
            if st.form_submit_button("Generate Report"):
                preferences = {
                    "housing_type": housing_type,
                    "transport": transport,
                    "nightlife": nightlife,
                    "shopping": shopping,
                    "outdoor": outdoor,
                    "quiet": quiet
                }
                
                generate_and_display_report(
                    st.session_state.family_info,
                    st.session_state.financial_info,
                    preferences
                )

if __name__ == "__main__":
    main()
