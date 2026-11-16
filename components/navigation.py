import streamlit as st


def create_navigation():
    """Create consistent navigation sidebar."""
    # QA fix Nov 15 2026: hide Streamlit default nav.
    # App has its own custom sidebar nav below,
    # so the built-in list duplicated it. Runs on
    # every page via create_navigation().
    # QA fix Nov 15 2026: bottom padding so the
    # footer / last content is not cut off.
    st.markdown("<style>[data-testid=stSidebarNav],[data-testid=stSidebarNavItems],[data-testid=stSidebarNavSeparator]{display:none!important}.block-container{padding-bottom:6rem!important}</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.title("Navigation")

        st.page_link("main.py", label="Home", icon="🏠")
        st.page_link("pages/rent_vs_buy.py", label="Rent vs Buy Calculator", icon="🧮")
        st.page_link("pages/mortgage_calculator.py", label="Mortgage Calculator", icon="💰")
        st.page_link("pages/neighborhood_comparison.py", label="Compare Neighborhoods", icon="🏘️")
        st.page_link("pages/lifestyle_quiz.py", label="Lifestyle Quiz", icon="✨")
        st.page_link("pages/report_display.py", label="My Report", icon="📊")
