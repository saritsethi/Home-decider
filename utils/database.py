import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import pool
import json
from datetime import datetime, timedelta
import random
import streamlit as st

# Create a connection pool
@st.cache_resource
def get_connection_pool():
    try:
        connection_pool = pool.SimpleConnectionPool(
            1, 20,  # min, max connections
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            host=os.environ['PGHOST'],
            port=os.environ['PGPORT'],
            database=os.environ['PGDATABASE']
        )
        return connection_pool
    except Exception as e:
        st.error(f"Failed to create connection pool: {str(e)}")
        raise e

# Update get_db_connection to use pool
@st.cache_resource
def get_db_connection():
    try:
        pool = get_connection_pool()
        return pool.getconn()
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        raise e

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
    pool = get_connection_pool()
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Drop existing table if it exists
        cur.execute("DROP TABLE IF EXISTS quiz_results")
        
        # Create table with correct schema
        cur.execute(
            """
            CREATE TABLE quiz_results (
                session_id TEXT PRIMARY KEY,
                preferences JSONB,
                user_info JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        return True
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            pool.putconn(conn)

@st.cache_data(ttl=3600)
def get_available_states():
    """Get list of available states."""
    return ["Illinois", "New York", "California"]

@st.cache_data(ttl=3600)
def get_available_cities(state=None):
    """Get list of available cities for a state."""
    cities = {
        "Illinois": ["Chicago", "Evanston", "Oak Park"],
        "New York": ["New York City", "Brooklyn", "Queens"],
        "California": ["San Francisco", "Los Angeles", "San Diego"]
    }
    return cities.get(state, []) if state else []

@st.cache_data(ttl=3600)
def get_neighborhood_data(city=None, state=None):
    """Get neighborhood data for a city."""
    if not city:
        return []
        
    neighborhoods = {
        "Chicago": [
            {
                "name": "Lincoln Park",
                "cost_of_living": 8,
                "school_rating": 9,
                "transport_score": 8,
                "walkability_score": 9,
                "historical_values": generate_historical_values(500000),
                "property_listings": [
                    {
                        "address": "2143 N Sheffield Ave",
                        "price": 849000,
                        "bedrooms": 3,
                        "bathrooms": 2.5,
                        "sqft": 2100,
                        "year_built": 2019,
                        "description": "Stunning contemporary townhome featuring hardwood floors throughout, gourmet kitchen with stainless steel appliances, spacious primary suite, attached garage, and private rooftop deck. Walking distance to parks and restaurants."
                    },
                    {
                        "address": "1920 N Lincoln Park West",
                        "price": 1249000,
                        "bedrooms": 4,
                        "bathrooms": 3,
                        "sqft": 2800,
                        "year_built": 2015,
                        "description": "Elegant corner unit with unobstructed park views, chef's kitchen with high-end appliances, marble bathrooms, custom closets, and 24-hour doorman. Steps to Lincoln Park Zoo and lake."
                    }
                ]
            },
            {
                "name": "Lake View",
                "cost_of_living": 7,
                "school_rating": 8,
                "transport_score": 9,
                "walkability_score": 8,
                "historical_values": generate_historical_values(450000),
                "property_listings": [
                    {
                        "address": "3550 N Lake Shore Dr",
                        "price": 899000,
                        "bedrooms": 3,
                        "bathrooms": 2.5,
                        "sqft": 1900,
                        "year_built": 2017,
                        "description": "Luxury high-rise unit with breathtaking lake views, custom kitchen cabinets, quartz countertops, spa-like bathrooms, and building amenities including fitness center and roof deck."
                    },
                    {
                        "address": "1658 W Addison St",
                        "price": 679000,
                        "bedrooms": 3,
                        "bathrooms": 2,
                        "sqft": 1650,
                        "year_built": 2012,
                        "description": "Sun-filled corner unit near Wrigley Field, open concept living area, renovated kitchen, hardwood floors, and private outdoor space. Great investment opportunity."
                    }
                ]
            }
        ]
    }
    return neighborhoods.get(city, [])

def save_quiz_results(session_id, preferences, user_info):
    pool = get_connection_pool()
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        cur = conn.cursor()
        
        cur.execute(
            """
            INSERT INTO quiz_results (session_id, preferences, user_info)
            VALUES (%s, %s::jsonb, %s::jsonb)
            ON CONFLICT (session_id) DO UPDATE
            SET preferences = EXCLUDED.preferences,
                user_info = EXCLUDED.user_info
            """, 
            (session_id, preferences, user_info)
        )
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Error saving quiz results: {str(e)}")
        raise e
    finally:
        if cur:
            cur.close()
        if conn:
            pool.putconn(conn)  # Return connection to pool
