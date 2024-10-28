import streamlit as st
from utils.database import get_available_states, get_available_cities, get_neighborhood_data

def create_financial_inputs():
    """Create standardized financial input fields."""
    with st.form("financial_inputs"):
        home_price = st.number_input("Home Purchase Price ($)", min_value=0, value=300000, step=1000)
        down_payment = st.number_input("Down Payment ($)", min_value=0, value=60000, step=1000)
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=4.5, step=0.1)
        monthly_rent = st.number_input("Monthly Rent ($)", min_value=0, value=2000, step=100)
        
        col1, col2 = st.columns(2)
        with col1:
            property_tax_rate = st.number_input("Property Tax Rate (%)", min_value=0.0, value=1.2, step=0.1)
            maintenance_cost_percent = st.number_input("Annual Maintenance Cost (%)", min_value=0.0, value=1.0, step=0.1)
        
        with col2:
            home_appreciation_rate = st.number_input("Home Appreciation Rate (%)", min_value=0.0, value=3.0, step=0.1)
            rent_increase_rate = st.number_input("Annual Rent Increase (%)", min_value=0.0, value=2.0, step=0.1)
        
        submit_button = st.form_submit_button("Calculate")
        
        return (submit_button, {
            "home_price": home_price,
            "down_payment": down_payment,
            "interest_rate": interest_rate,
            "monthly_rent": monthly_rent,
            "property_tax_rate": property_tax_rate,
            "maintenance_cost_percent": maintenance_cost_percent,
            "home_appreciation_rate": home_appreciation_rate,
            "rent_increase_rate": rent_increase_rate
        })

def create_neighborhood_inputs():
    """Create standardized neighborhood comparison inputs."""
    # Get available states
    states = get_available_states()
    state = st.selectbox("Select State", states)
    
    # Get cities for selected state
    cities = get_available_cities(state)
    city = st.selectbox("Select City", cities)
    
    # Get neighborhoods for selected city and state
    neighborhoods_data = get_neighborhood_data(city=city, state=state)
    available_neighborhoods = [n['name'] for n in neighborhoods_data] if neighborhoods_data else ["No neighborhoods available"]
    
    neighborhoods = st.multiselect(
        "Select Neighborhoods to Compare",
        available_neighborhoods,
        max_selections=3
    )
    return state, city, neighborhoods
