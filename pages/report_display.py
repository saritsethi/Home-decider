import streamlit as st
from components.navigation import create_navigation
import json
import os
from utils.report_generator import create_pdf_report
from utils.visualization import create_historical_value_chart

st.set_page_config(page_title="Report Results", page_icon="📊")

def display_report_results():
    """Display the report results in a structured format."""
    if 'report_data' not in st.session_state:
        st.warning("Please complete the lifestyle quiz first!")
        st.page_link("pages/lifestyle_quiz.py", label="Take the Quiz", icon="✨")
        return

    create_navigation()
    report_data = st.session_state.report_data
    preferences = st.session_state.preferences

    st.title("🎯 Your Personalized Recommendations")
    
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
            historical_data = hood['historical_values'] if isinstance(hood['historical_values'], list) else json.loads(hood['historical_values'])
            if len(historical_data) >= 2:
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
    
    # PDF Generation outside of any form
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

if __name__ == "__main__":
    display_report_results()
