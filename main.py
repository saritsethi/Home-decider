import streamlit as st
from components.navigation import create_navigation
from utils.database import init_database

st.set_page_config(
    page_title="Home Decision Helper",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def create_feature_container(title, description, page_path):
    """Create a styled container for feature links."""
    with st.container():
        st.subheader(title)
        st.write(description)
        st.page_link(page_path, label=f"Go to {title}", use_container_width=True)

def main():
    # Initialize database
    init_database()
    
    # Set up navigation
    create_navigation()
    
    # Main page content
    st.title("🏠 Home Decision Helper")
    st.write("""
    Welcome to your comprehensive home decision-making tool! This application will help you:
    
    * Compare renting vs. buying costs
    * Analyze and compare neighborhoods
    * Get personalized lifestyle-based recommendations
    """)
    
    # Quick access cards using containers
    col1, col2, col3 = st.columns(3)
    
    with col1:
        create_feature_container(
            "Rent vs. Buy Calculator",
            "Compare the financial implications of renting versus buying",
            "pages/rent_vs_buy.py"
        )
    
    with col2:
        create_feature_container(
            "Neighborhood Comparison",
            "Analyze and compare different neighborhoods",
            "pages/neighborhood_comparison.py"
        )
    
    with col3:
        create_feature_container(
            "Lifestyle Quiz",
            "Get personalized neighborhood recommendations",
            "pages/lifestyle_quiz.py"
        )

if __name__ == "__main__":
    main()
