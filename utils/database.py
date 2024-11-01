import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json
from datetime import datetime, timedelta
import random
import streamlit as st
import logging

@st.cache_resource
def get_db_connection():
    """Create a cached database connection using environment variables."""
    return psycopg2.connect(
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD'],
        host=os.environ['PGHOST'],
        port=os.environ['PGPORT'],
        database=os.environ['PGDATABASE']
    )

@st.cache_data(ttl=3600)
def generate_historical_values(base_price):
    """Generate cached historical property values."""
    values = []
    date = datetime.now() - timedelta(days=5*365)
    price = base_price * 0.75  # Start 25% lower than current
    
    for _ in range(20):  # Quarterly for 5 years
        values.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": round(price, 2)
        })
        date += timedelta(days=90)
        # Add some variability to price growth
        growth_rate = 1.02 + (random.random() - 0.5) * 0.01
        price *= growth_rate
    
    return json.dumps(values)

def init_database():
    try:
        conn = get_db_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logging.info('Database connection established successfully')
        return True
    except Exception as e:
        logging.error(f'Database connection error: {str(e)}')
        return False

@st.cache_data(ttl=3600)
def get_available_states():
    return ['Illinois', 'California', 'New York']

@st.cache_data(ttl=3600)
def get_available_cities(state=None):
    cities = {
        'Illinois': ['Chicago', 'Evanston', 'Oak Park'],
        'California': ['San Francisco', 'Los Angeles', 'San Diego'],
        'New York': ['New York City', 'Brooklyn', 'Queens']
    }
    return cities.get(state, [])

@st.cache_data(ttl=3600)
def get_neighborhood_data(city=None, state=None):
    neighborhoods = []
    if city == 'Chicago':
        neighborhoods = [
            {
                'name': 'Lincoln Park',
                'cost_of_living': 8.5,
                'school_rating': 9.0,
                'transport_score': 8.5,
                'walkability_score': 9.0,
                'historical_values': generate_historical_values(1000000),
                'property_listings': json.dumps([
                    {
                        'address': '2143 N Sheffield Ave',
                        'price': 849000,
                        'bedrooms': 3,
                        'bathrooms': 2.5,
                        'sqft': 2100,
                        'year_built': 2019,
                        'description': 'Stunning contemporary townhome'
                    }
                ])
            },
            {
                'name': 'Lake View',
                'cost_of_living': 7.5,
                'school_rating': 8.0,
                'transport_score': 9.0,
                'walkability_score': 8.5,
                'historical_values': generate_historical_values(800000),
                'property_listings': json.dumps([
                    {
                        'address': '3550 N Lake Shore Dr',
                        'price': 899000,
                        'bedrooms': 3,
                        'bathrooms': 2.5,
                        'sqft': 1900,
                        'year_built': 2017,
                        'description': 'Luxury high-rise unit'
                    }
                ])
            }
        ]
    return neighborhoods

@st.cache_data(ttl=3600)
def save_quiz_results(session_id, preferences, family_info):
    return True  # Mock implementation
