import streamlit as st
import json
import uuid
from components.navigation import create_navigation
from utils.database import get_available_states, get_available_cities, get_neighborhood_data, save_quiz_results
from utils.report_generator import generate_integrated_report

st.set_page_config(page_title="Lifestyle Quiz", page_icon="✨")


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
        col1, col2 = st.columns(2)
        with col1:
            family_size = st.number_input("Number of family members", min_value=1, value=2)
            adults = st.number_input("Number of adults", min_value=1, value=2)
            children = st.number_input("Number of children", min_value=0, value=0)

        if st.form_submit_button("Next"):
            if adults + children != family_size:
                st.error("Number of adults + children must equal total family members.")
            else:
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

        annual_income = st.number_input("Annual Household Income ($)", min_value=0, value=75000, step=1000)
        savings = st.number_input("Total Savings ($)", min_value=0, value=50000, step=1000)

        st.subheader("Current Housing Situation")
        current_monthly_rent = st.number_input(
            "Current Monthly Rent ($)", min_value=0, value=1800, step=100,
            help="Enter 0 if you currently own or live rent-free"
        )
        monthly_expenses = st.number_input(
            "Other Monthly Expenses ($)", min_value=0, value=2000, step=100,
            help="Car payments, loans, subscriptions — not including rent"
        )

        st.subheader("Home Buying Preferences")
        target_home_price = st.number_input("Target Home Purchase Price ($)", min_value=0, value=400000, step=10000)
        down_payment_percent = st.slider("Down Payment Percentage", min_value=3, max_value=50, value=20)
        interest_rate = st.number_input(
            "Expected Interest Rate (%)", min_value=0.0, max_value=15.0, value=6.5, step=0.1,
            help="Current 30-year fixed rates are typically 6-8%"
        )

        if st.form_submit_button("Next"):
            if annual_income <= 0:
                st.error("Please enter a valid annual income.")
            else:
                down_payment = target_home_price * (down_payment_percent / 100)
                st.session_state.financial_info = {
                    "annual_income": annual_income,
                    "savings": savings,
                    "current_monthly_rent": current_monthly_rent,
                    "monthly_expenses": monthly_expenses,
                    "target_home_price": target_home_price,
                    "down_payment": down_payment,
                    "down_payment_percent": down_payment_percent,
                    "interest_rate": interest_rate
                }
                st.session_state.current_step = 3
                st.rerun()


def display_lifestyle_preferences():
    with st.form("neighborhood_preferences_form"):
        st.subheader("Location Preferences")

        states = get_available_states()
        state = st.selectbox("Select State", states, key='state_selector')

        if state and state != st.session_state.get('selected_state'):
            st.session_state.selected_state = state
            if 'selected_city' in st.session_state:
                del st.session_state.selected_city

        filtered_cities = get_available_cities(state=state)
        city = st.selectbox("Select City", filtered_cities, key='city_selector')

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
            nightlife = st.slider("How important is nightlife & entertainment?", 0, 10, 5)
            shopping = st.slider("How important is shopping access?", 0, 10, 5)
        with col2:
            outdoor = st.slider("How important are outdoor activities & parks?", 0, 10, 5)
            quiet = st.slider("How important is a quiet neighborhood?", 0, 10, 5)

        if st.form_submit_button("Generate Report"):
            combined_info = {
                **st.session_state.family_info,
                **st.session_state.financial_info
            }

            preferences = {
                "state": state,
                "city": city,
                "housing_type": housing_type,
                "transport": transport,
                "nightlife": nightlife,
                "shopping": shopping,
                "outdoor": outdoor,
                "quiet": quiet
            }

            st.session_state.preferences = preferences

            matches = get_neighborhood_data(city=city, state=state)

            st.session_state.report_data = generate_integrated_report(
                preferences,
                combined_info,
                matches
            )

            save_quiz_results(
                st.session_state.session_id,
                json.dumps(preferences),
                json.dumps(combined_info)
            )

            st.switch_page("pages/report_display.py")


def main():
    create_navigation()
    initialize_session_state()

    st.title("Find Your Perfect Home")
    steps = ["Family Information", "Financial Details", "Lifestyle Preferences"]
    st.progress((st.session_state.current_step - 1) / len(steps))
    st.write(f"Step {st.session_state.current_step} of {len(steps)}: {steps[st.session_state.current_step - 1]}")

    if st.session_state.current_step > 1:
        if st.button("← Back"):
            st.session_state.current_step -= 1
            st.rerun()

    if st.session_state.current_step == 1:
        display_family_info()
    elif st.session_state.current_step == 2:
        display_financial_info()
    else:
        display_lifestyle_preferences()


if __name__ == "__main__":
    main()
