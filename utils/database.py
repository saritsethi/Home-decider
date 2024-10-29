import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json
from datetime import datetime, timedelta
import random

def get_db_connection():
    """Create a database connection using environment variables."""
    return psycopg2.connect(
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD'],
        host=os.environ['PGHOST'],
        port=os.environ['PGPORT'],
        database=os.environ['PGDATABASE']
    )

def generate_historical_values(base_price):
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
    """Initialize database tables if they don't exist."""
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Create quiz_results table with family_info column
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id SERIAL PRIMARY KEY,
            session_id TEXT NOT NULL,
            preferences JSONB,
            family_info JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create neighborhoods table with historical data
    cur.execute("""
        CREATE TABLE IF NOT EXISTS neighborhoods (
            id SERIAL PRIMARY KEY,
            state TEXT NOT NULL,
            city TEXT NOT NULL,
            name TEXT NOT NULL,
            cost_of_living FLOAT,
            school_rating FLOAT,
            transport_score FLOAT,
            walkability_score FLOAT,
            historical_values JSONB DEFAULT '[]'::jsonb,
            property_listings JSONB DEFAULT '[]'::jsonb
        )
    """)
    
    # Add historical_values column if it doesn't exist
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'neighborhoods' AND column_name = 'historical_values'
            ) THEN
                ALTER TABLE neighborhoods ADD COLUMN historical_values JSONB DEFAULT '[]'::jsonb;
            END IF;
        END $$;
    """)

    # Add property_listings column if it doesn't exist
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'neighborhoods' AND column_name = 'property_listings'
            ) THEN
                ALTER TABLE neighborhoods ADD COLUMN property_listings JSONB DEFAULT '[]'::jsonb;
            END IF;
        END $$;
    """)
    
    # Insert sample data if table is empty
    cur.execute("SELECT COUNT(*) FROM neighborhoods")
    count = cur.fetchone()[0]
    
    if count == 0:
        # Sample listings for each neighborhood
        sample_listings = {
            'Lincoln Park': [
                {
                    'address': '2143 N Sheffield Ave',
                    'price': 849000,
                    'bedrooms': 3,
                    'bathrooms': 2.5,
                    'sqft': 2100,
                    'year_built': 2019,
                    'description': 'Stunning contemporary townhome featuring hardwood floors throughout, gourmet kitchen with stainless steel appliances, spacious primary suite, attached garage, and private rooftop deck. Walking distance to parks and restaurants.'
                },
                {
                    'address': '1920 N Lincoln Park West',
                    'price': 1249000,
                    'bedrooms': 4,
                    'bathrooms': 3,
                    'sqft': 2800,
                    'year_built': 2015,
                    'description': 'Elegant corner unit with unobstructed park views, chef's kitchen with high-end appliances, marble bathrooms, custom closets, and 24-hour doorman. Steps to Lincoln Park Zoo and lake.'
                },
                {
                    'address': '2238 N Racine Ave',
                    'price': 725000,
                    'bedrooms': 2,
                    'bathrooms': 2,
                    'sqft': 1450,
                    'year_built': 2010,
                    'description': 'Charming vintage condo in prime location, fully renovated with modern finishes, in-unit laundry, balcony, and deeded parking space. Close to DePaul University.'
                }
            ],
            'Lake View': [
                {
                    'address': '3550 N Lake Shore Dr',
                    'price': 899000,
                    'bedrooms': 3,
                    'bathrooms': 2.5,
                    'sqft': 1900,
                    'year_built': 2017,
                    'description': 'Luxury high-rise unit with breathtaking lake views, custom kitchen cabinets, quartz countertops, spa-like bathrooms, and building amenities including fitness center and roof deck.'
                },
                {
                    'address': '1658 W Addison St',
                    'price': 679000,
                    'bedrooms': 3,
                    'bathrooms': 2,
                    'sqft': 1650,
                    'year_built': 2012,
                    'description': 'Sun-filled corner unit near Wrigley Field, open concept living area, renovated kitchen, hardwood floors, and private outdoor space. Great investment opportunity.'
                },
                {
                    'address': '3845 N Southport Ave',
                    'price': 599000,
                    'bedrooms': 2,
                    'bathrooms': 2,
                    'sqft': 1200,
                    'year_built': 2016,
                    'description': 'Modern condo in the heart of Southport Corridor, floor-to-ceiling windows, custom built-ins, premium finishes, and garage parking included. Steps to shopping and dining.'
                }
            ],
            'Wicker Park': [
                {
                    'address': '1722 W Division St',
                    'price': 785000,
                    'bedrooms': 3,
                    'bathrooms': 2,
                    'sqft': 1850,
                    'year_built': 2018,
                    'description': 'Contemporary loft-style condo with industrial touches, 11-foot ceilings, exposed brick, chef's kitchen, and private terrace. Prime location near restaurants and Blue Line.'
                },
                {
                    'address': '1515 N Wood St',
                    'price': 949000,
                    'bedrooms': 4,
                    'bathrooms': 3.5,
                    'sqft': 2400,
                    'year_built': 2020,
                    'description': 'Luxurious single-family home with high-end finishes, custom millwork, gourmet kitchen, primary suite with walk-in closet, and landscaped yard with deck.'
                }
            ],
            'West Loop': [
                {
                    'address': '1040 W Madison St',
                    'price': 1150000,
                    'bedrooms': 3,
                    'bathrooms': 2.5,
                    'sqft': 2200,
                    'year_built': 2021,
                    'description': 'Ultra-luxury residence in premier building, floor-to-ceiling windows, custom Italian kitchen, smart home features, and world-class amenities including pool and fitness center.'
                },
                {
                    'address': '123 S Green St',
                    'price': 899000,
                    'bedrooms': 2,
                    'bathrooms': 2,
                    'sqft': 1600,
                    'year_built': 2019,
                    'description': 'Designer finishes throughout this stunning corner unit, waterfall quartz island, wine fridge, custom closets, and balcony with skyline views. Steps to Restaurant Row.'
                }
            ]
        }
        
        sample_data = [
            ('IL', 'Chicago', 'Lincoln Park', 8.5, 9.0, 8.5, 9.0, generate_historical_values(800000), json.dumps(sample_listings['Lincoln Park'])),
            ('IL', 'Chicago', 'Wicker Park', 8.0, 8.5, 9.0, 9.0, generate_historical_values(650000), json.dumps(sample_listings['Wicker Park'])),
            ('IL', 'Chicago', 'Lake View', 8.5, 8.5, 9.0, 8.5, generate_historical_values(700000), json.dumps(sample_listings['Lake View'])),
            ('IL', 'Chicago', 'West Loop', 9.0, 8.0, 9.0, 9.5, generate_historical_values(900000), json.dumps(sample_listings['West Loop']))
        ]
        
        cur.executemany("""
            INSERT INTO neighborhoods 
            (state, city, name, cost_of_living, school_rating, transport_score, walkability_score, historical_values, property_listings)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, sample_data)
    
    cur.close()
    conn.close()

def get_available_states():
    """Get list of all unique states from the neighborhoods table."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT DISTINCT state FROM neighborhoods ORDER BY state")
    states = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return states if states else ["No states available"]

def get_available_cities(state=None):
    """Get list of all unique cities, optionally filtered by state."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    if state and state != "No states available":
        cur.execute(
            "SELECT DISTINCT city FROM neighborhoods WHERE state = %s ORDER BY city",
            (state,)
        )
    else:
        cur.execute("SELECT DISTINCT city FROM neighborhoods ORDER BY city")
    
    cities = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return cities if cities else ["No cities available"]

def get_neighborhood_data(city=None, state=None):
    """Retrieve neighborhood data, optionally filtered by city and state."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    if state and city:
        cur.execute("""
            SELECT id, state, city, name, cost_of_living, school_rating, 
                   transport_score, walkability_score, historical_values, property_listings
            FROM neighborhoods 
            WHERE state = %s AND city = %s
        """, (state, city))
    elif state:
        cur.execute("""
            SELECT id, state, city, name, cost_of_living, school_rating, 
                   transport_score, walkability_score, historical_values, property_listings
            FROM neighborhoods 
            WHERE state = %s
        """, (state,))
    elif city:
        cur.execute("""
            SELECT id, state, city, name, cost_of_living, school_rating, 
                   transport_score, walkability_score, historical_values, property_listings
            FROM neighborhoods 
            WHERE city = %s
        """, (city,))
    else:
        cur.execute("""
            SELECT id, state, city, name, cost_of_living, school_rating, 
                   transport_score, walkability_score, historical_values, property_listings
            FROM neighborhoods
        """)
    
    columns = ['id', 'state', 'city', 'name', 'cost_of_living', 'school_rating', 
               'transport_score', 'walkability_score', 'historical_values', 'property_listings']
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return results

def save_quiz_results(session_id, preferences, family_info=None):
    """Save quiz results to database."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        """
        INSERT INTO quiz_results (session_id, preferences, family_info) 
        VALUES (%s, %s, %s)
        """,
        (session_id, preferences, family_info)
    )
    
    conn.commit()
    cur.close()
    conn.close()
