import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_db_connection():
    """Create a database connection using environment variables."""
    return psycopg2.connect(
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD'],
        host=os.environ['PGHOST'],
        port=os.environ['PGPORT'],
        database=os.environ['PGDATABASE']
    )

def init_database():
    """Initialize database tables if they don't exist."""
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Create neighborhoods table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS neighborhoods (
            id SERIAL PRIMARY KEY,
            city TEXT NOT NULL,
            name TEXT NOT NULL,
            cost_of_living FLOAT,
            school_rating FLOAT,
            transport_score FLOAT,
            walkability_score FLOAT
        )
    """)
    
    # Create quiz_results table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id SERIAL PRIMARY KEY,
            session_id TEXT NOT NULL,
            preferences JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.close()
    conn.close()

def save_quiz_results(session_id, preferences):
    """Save quiz results to database."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "INSERT INTO quiz_results (session_id, preferences) VALUES (%s, %s)",
        (session_id, preferences)
    )
    
    conn.commit()
    cur.close()
    conn.close()

def get_neighborhood_data(city=None):
    """Retrieve neighborhood data, optionally filtered by city."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    if city:
        cur.execute("SELECT * FROM neighborhoods WHERE city = %s", (city,))
    else:
        cur.execute("SELECT * FROM neighborhoods")
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results
