import streamlit as st
import json
import uuid
from components.navigation import create_navigation
from utils.database import save_quiz_results, get_neighborhood_data

st.set_page_config(page_title="Lifestyle Quiz", page_icon="✨")

def calculate_neighborhood_match(preferences):
    """Calculate neighborhood matches based on user preferences."""
    # Get all neighborhoods from database
    neighborhoods = get_neighborhood_data()
    
    # Calculate match scores for each neighborhood
    matched_neighborhoods = []
    for hood in neighborhoods:
        score = 0
        reasons = []
        
        # Urban/Suburban preference
        urban_score = {
            "Very Urban": 1.0,
            "Somewhat Urban": 0.75,
            "Mixed": 0.5,
            "Somewhat Suburban": 0.25,
            "Very Suburban": 0.0
        }
        urban_factor = urban_score[preferences["housing_type"]]
        density_match = 1 - abs(urban_factor - hood["walkability_score"]/10)
        score += density_match * 25  # 25% weight
        if density_match > 0.7:
            reasons.append(f"Matches your {preferences['housing_type']} lifestyle preference")
        
        # Transport preference
        transport_score = {
            "Walking": hood["walkability_score"],
            "Public Transit": hood["transport_score"],
            "Mix": (hood["walkability_score"] + hood["transport_score"]) / 2,
            "Personal Vehicle": 10 - hood["walkability_score"]  # Inverse of walkability for car preference
        }
        transport_match = transport_score[preferences["transport"]] / 10
        score += transport_match * 25  # 25% weight
        if transport_match > 0.7:
            reasons.append(f"Great {preferences['transport'].lower()} options")
        
        # Nightlife/Shopping importance
        lifestyle_score = (
            (preferences["nightlife"] * hood["walkability_score"] +
             preferences["shopping"] * hood["walkability_score"]) / 
            (preferences["nightlife"] + preferences["shopping"] if (preferences["nightlife"] + preferences["shopping"]) > 0 else 1)
        ) / 10
        score += lifestyle_score * 25  # 25% weight
        if lifestyle_score > 0.7:
            reasons.append("Excellent nightlife and shopping access")
        
        # Outdoor/Quiet preference
        quiet_score = (
            (preferences["outdoor"] * (10 - hood["cost_of_living"]) +
             preferences["quiet"] * (10 - hood["walkability_score"])) /
            (preferences["outdoor"] + preferences["quiet"] if (preferences["outdoor"] + preferences["quiet"]) > 0 else 1)
        ) / 10
        score += quiet_score * 25  # 25% weight
        if quiet_score > 0.7:
            reasons.append("Great for outdoor activities and quiet living")
        
        matched_neighborhoods.append({
            "neighborhood": hood,
            "match_score": round(score, 1),
            "reasons": reasons
        })
    
    # Sort by match score
    return sorted(matched_neighborhoods, key=lambda x: x["match_score"], reverse=True)

def main():
    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
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
        
        # Get neighborhood matches
        matches = calculate_neighborhood_match(preferences)
        
        st.success("🎯 Here are your personalized neighborhood matches!")
        
        # Display top matches with detailed explanations
        for i, match in enumerate(matches[:5]):  # Show top 5 matches
            hood = match["neighborhood"]
            with st.expander(f"#{i+1}: {hood['name']} - {match['match_score']}% Match", expanded=i==0):
                st.write("### Why this neighborhood matches your preferences:")
                for reason in match["reasons"]:
                    st.write(f"- {reason}")
                
                st.write("### Neighborhood Stats:")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Cost of Living", f"{hood['cost_of_living']:.1f}/10")
                    st.metric("Transport Score", f"{hood['transport_score']:.1f}/10")
                with col2:
                    st.metric("School Rating", f"{hood['school_rating']:.1f}/10")
                    st.metric("Walkability", f"{hood['walkability_score']:.1f}/10")

if __name__ == "__main__":
    main()
