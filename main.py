import streamlit as st
from components.navigation import create_navigation
from utils.database import init_database

st.set_page_config(
    page_title="Home Decision Helper",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    # Quick access cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.card(
            title="Rent vs. Buy Calculator",
            text="Compare the financial implications of renting versus buying",
            on_click=lambda: st.switch_page("pages/rent_vs_buy.py")
        )
    
    with col2:
        st.card(
            title="Neighborhood Comparison",
            text="Analyze and compare different neighborhoods",
            on_click=lambda: st.switch_page("pages/neighborhood_comparison.py")
        )
    
    with col3:
        st.card(
            title="Lifestyle Quiz",
            text="Get personalized neighborhood recommendations",
            on_click=lambda: st.switch_page("pages/lifestyle_quiz.py")
        )

if __name__ == "__main__":
    main()
