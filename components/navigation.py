import streamlit as st

def create_navigation():
    """Create consistent navigation sidebar."""
    with st.sidebar:
        st.title("Navigation")
        
        st.page_link("main.py", label="Home", icon="🏠")
        st.page_link("pages/rent_vs_buy.py", label="Rent vs Buy Calculator", icon="🧮")
        st.page_link("pages/mortgage_calculator.py", label="Mortgage Calculator", icon="💰")
        st.page_link("pages/neighborhood_comparison.py", label="Compare Neighborhoods", icon="🏘️")
        st.page_link("pages/lifestyle_quiz.py", label="Lifestyle Quiz", icon="✨")
