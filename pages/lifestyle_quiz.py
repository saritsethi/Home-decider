import streamlit as st
import json
import uuid
import os
from components.navigation import create_navigation
from utils.database import save_quiz_results, get_neighborhood_data
from utils.report_generator import generate_integrated_report, create_pdf_report

st.set_page_config(page_title="Lifestyle Quiz", page_icon="✨")

def calculate_neighborhood_match(preferences):
    """Calculate neighborhood matches based on user preferences."""
    # Get all neighborhoods
    neighborhoods = get_neighborhood_data()
    
    matches = []
    for hood in neighborhoods:
        match_score = 0
        reasons = []
        
        # Calculate urban/suburban match
        urban_scores = {
            "Very Urban": 10,
            "Somewhat Urban": 7.5,
            "Mixed": 5,
            "Somewhat Suburban": 2.5,
            "Very Suburban": 0
        }
        urban_match = 10 - abs(urban_scores[preferences['housing_type']] - hood['walkability_score'])
        match_score += urban_match
        
        # Transport preference match
        transport_scores = {
            "Walking": hood['walkability_score'],
            "Public Transit": hood['transport_score'],
            "Mix": (hood['walkability_score'] + hood['transport_score']) / 2,
            "Personal Vehicle": 10 - hood['transport_score']/2
        }
        transport_match = transport_scores[preferences['transport']]
        match_score += transport_match
        
        # Calculate historical value trend
        historical_data = json.loads(hood['historical_values'])
        if len(historical_data) >= 2:
            start_value = historical_data[0]['value']
            end_value = historical_data[-1]['value']
            appreciation = ((end_value - start_value) / start_value) * 100
            if appreciation > 15:  # More than 15% appreciation in 5 years
                match_score += 10
                reasons.append(f"Strong property value growth: {appreciation:.1f}% over 5 years")
        
        # Lifestyle matches
        if preferences['nightlife'] > 7:
            nightlife_match = hood['walkability_score']
            match_score += nightlife_match
            if nightlife_match > 7:
                reasons.append("Great nightlife and entertainment options")
        
        if preferences['shopping'] > 7:
            shopping_match = hood['walkability_score']
            match_score += shopping_match
            if shopping_match > 7:
                reasons.append("Excellent shopping accessibility")
        
        if preferences['outdoor'] > 7:
            outdoor_match = 10 - hood['cost_of_living']/2
            match_score += outdoor_match
            if outdoor_match > 7:
                reasons.append("Good access to outdoor activities")
        
        if preferences['quiet'] > 7:
            quiet_match = 10 - hood['walkability_score']/2
            match_score += quiet_match
            if quiet_match > 7:
                reasons.append("Quiet and peaceful environment")
        
        # Normalize score to percentage
        final_score = int((match_score / 60) * 100)  # 60 is max possible score (including appreciation)
        
        # Add to matches if score is above 50%
        if final_score >= 50:
            matches.append({
                "neighborhood": hood,
                "match_score": final_score,
                "reasons": reasons
            })
    
    # Sort by match score
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return matches

def initialize_session_state():
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'family_info' not in st.session_state:
        st.session_state.family_info = {}
    if 'financial_info' not in st.session_state:
        st.session_state.financial_info = {}

def display_family_info():
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

def display_financial_info():
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

def display_lifestyle_preferences():
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

def display_current_step():
    if st.session_state.current_step == 1:
        display_family_info()
    elif st.session_state.current_step == 2:
        display_financial_info()
    else:
        display_lifestyle_preferences()

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
    
    display_report_results(report_data, preferences)

def display_report_results(report_data, preferences):
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
            
            # Display historical value trend
            historical_data = json.loads(hood['historical_values'])
            if len(historical_data) >= 2:
                from utils.visualization import create_historical_value_chart
                fig = create_historical_value_chart([hood])
                st.plotly_chart(fig, use_container_width=True)
            
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
    initialize_session_state()
    create_navigation()
    
    st.title("Find Your Perfect Home")
    steps = ["Family Information", "Financial Details", "Lifestyle Preferences"]
    st.progress((st.session_state.current_step - 1) / len(steps))
    st.subheader(f"Step {st.session_state.current_step}: {steps[st.session_state.current_step-1]}")
    
    if st.session_state.current_step > 1:
        if st.button("← Back"):
            st.session_state.current_step -= 1
            st.rerun()

    display_current_step()

if __name__ == "__main__":
    main()
