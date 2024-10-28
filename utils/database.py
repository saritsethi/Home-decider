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
            historical_values JSONB DEFAULT '[]'::jsonb
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
    
    # Insert sample data if table is empty
    cur.execute("SELECT COUNT(*) FROM neighborhoods")
    count = cur.fetchone()[0]
    
    if count == 0:
        sample_data = [
            ('IL', 'Chicago', 'Lincoln Park', 8.5, 9.0, 8.5, 9.0, generate_historical_values(800000)),
            ('IL', 'Chicago', 'Wicker Park', 8.0, 8.5, 9.0, 9.0, generate_historical_values(650000)),
            ('IL', 'Chicago', 'Lake View', 8.5, 8.5, 9.0, 8.5, generate_historical_values(700000)),
            ('IL', 'Chicago', 'West Loop', 9.0, 8.0, 9.0, 9.5, generate_historical_values(900000))
        ]
        
        cur.executemany("""
            INSERT INTO neighborhoods 
            (state, city, name, cost_of_living, school_rating, transport_score, walkability_score, historical_values)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
                   transport_score, walkability_score, historical_values
            FROM neighborhoods 
            WHERE state = %s AND city = %s
        """, (state, city))
    elif state:
        cur.execute("""
            SELECT id, state, city, name, cost_of_living, school_rating, 
                   transport_score, walkability_score, historical_values
            FROM neighborhoods 
            WHERE state = %s
        """, (state,))
    elif city:
        cur.execute("""
            SELECT id, state, city, name, cost_of_living, school_rating, 
                   transport_score, walkability_score, historical_values
            FROM neighborhoods 
            WHERE city = %s
        """, (city,))
    else:
        cur.execute("""
            SELECT id, state, city, name, cost_of_living, school_rating, 
                   transport_score, walkability_score, historical_values
            FROM neighborhoods
        """)
    
    columns = ['id', 'state', 'city', 'name', 'cost_of_living', 'school_rating', 
               'transport_score', 'walkability_score', 'historical_values']
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
