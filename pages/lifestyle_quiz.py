import streamlit as st
import json
from components.navigation import create_navigation
from utils.database import save_quiz_results

st.set_page_config(page_title="Lifestyle Quiz", page_icon="✨")

def main():
    create_navigation()
    
    st.title("Lifestyle Preference Quiz")
    st.write("""
    Take this quick quiz to get personalized neighborhood recommendations
    based on your lifestyle preferences.
    """)
    
    # Quiz questions
    with st.form("lifestyle_quiz"):
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
        # Save quiz results
        preferences = {
            "housing_type": housing_type,
            "transport": transport,
            "nightlife": nightlife,
            "shopping": shopping,
            "outdoor": outdoor,
            "quiet": quiet
        }
        
        save_quiz_results(st.session_state.session_id, json.dumps(preferences))
        
        # Generate recommendations
        st.success("Based on your preferences, we recommend:")
        
        if housing_type in ["Very Urban", "Somewhat Urban"]:
            st.write("🌆 Urban neighborhoods with:")
            st.write("- High walkability scores")
            st.write("- Excellent public transportation")
            st.write("- Active nightlife and entertainment")
        else:
            st.write("🏡 Suburban areas with:")
            st.write("- More space and quieter streets")
            st.write("- Better parking availability")
            st.write("- Proximity to parks and nature")
        
        # Show matching neighborhoods
        st.subheader("Matching Neighborhoods")
        st.write("Here are some neighborhoods that match your preferences:")
        
        # This would be replaced with actual database queries based on preferences
        example_matches = [
            {"name": "Sample Neighborhood 1", "match_score": 95},
            {"name": "Sample Neighborhood 2", "match_score": 88},
            {"name": "Sample Neighborhood 3", "match_score": 82},
        ]
        
        for match in example_matches:
            st.metric(
                match["name"],
                f"{match['match_score']}% Match"
            )

if __name__ == "__main__":
    main()
