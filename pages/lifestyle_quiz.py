import streamlit as st
import json
import uuid
import os
from components.navigation import create_navigation
from utils.database import save_quiz_results, get_neighborhood_data
from utils.report_generator import calculate_neighborhood_match, generate_integrated_report, create_pdf_report

st.set_page_config(page_title="Lifestyle Quiz", page_icon="✨")

def main():
    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    create_navigation()
    
    st.title("Lifestyle Preference Quiz")
    st.write("""
    Take this quick quiz to get personalized neighborhood recommendations
    based on your lifestyle preferences and family needs.
    """)
    
    # Quiz form
    with st.form("lifestyle_quiz"):
        # Family Information Section
        st.subheader("Family Information")
        col1, col2 = st.columns(2)
        with col1:
            family_size = st.number_input("Number of family members", min_value=1, value=1)
            adults = st.number_input("Number of adults", min_value=1, value=1)
            children = st.number_input("Number of children", min_value=0, value=0)
        with col2:
            annual_income = st.number_input("Annual Household Income ($)", min_value=0, value=50000, step=1000)
            savings = st.number_input("Total Savings ($)", min_value=0, value=10000, step=1000)
            monthly_expenses = st.number_input("Monthly Expenses ($)", min_value=0, value=2000, step=100)
        
        st.subheader("Housing Preferences")
        housing_type = st.select_slider(
            "Do you prefer urban or suburban living?",
            options=["Very Urban", "Somewhat Urban", "Mixed", "Somewhat Suburban", "Very Suburban"]
        )
        
        st.subheader("Transportation")
        transport = st.select_slider(
            "How do you prefer to get around?",
            options=["Walking", "Public Transit", "Mix", "Personal Vehicle"]
        )
        
        st.subheader("Lifestyle")
        col1, col2 = st.columns(2)
        with col1:
            nightlife = st.slider("How important is nightlife?", 0, 10, 5)
            shopping = st.slider("How important is shopping access?", 0, 10, 5)
        
        with col2:
            outdoor = st.slider("How important are outdoor activities?", 0, 10, 5)
            quiet = st.slider("How important is a quiet neighborhood?", 0, 10, 5)
        
        submitted = st.form_submit_button("Get Recommendations")
    
    if submitted:
        # Prepare data
        preferences = {
            "housing_type": housing_type,
            "transport": transport,
            "nightlife": nightlife,
            "shopping": shopping,
            "outdoor": outdoor,
            "quiet": quiet
        }
        
        family_info = {
            "family_size": family_size,
            "adults": adults,
            "children": children,
            "annual_income": annual_income,
            "savings": savings,
            "monthly_expenses": monthly_expenses
        }
        
        # Save quiz results with family information
        save_quiz_results(
            st.session_state.session_id,
            json.dumps(preferences),
            json.dumps(family_info)
        )
        
        # Get neighborhood matches
        matches = calculate_neighborhood_match(preferences)
        
        # Generate integrated report
        report_data = generate_integrated_report(preferences, family_info, matches)
        
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
                
                # Additional family-specific information
                if children > 0:
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
            # Create temporary file for PDF
            pdf_path = f"temp_report_{st.session_state.session_id}.pdf"
            create_pdf_report(pdf_path, report_data, family_info, preferences)
            
            # Read PDF file and create download button
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name="home_decision_report.pdf",
                    mime="application/pdf"
                )
            
            # Clean up temporary file
            os.remove(pdf_path)

if __name__ == "__main__":
    main()
