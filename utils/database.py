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
    
    # Insert sample neighborhood data
    cur.execute("SELECT COUNT(*) FROM neighborhoods")
    count = cur.fetchone()[0]
    
    if count == 0:
        sample_data = [
            ('San Francisco', 'Mission District', 8.5, 7.0, 9.0, 9.5),
            ('San Francisco', 'Pacific Heights', 9.5, 8.5, 7.5, 8.0),
            ('New York', 'Brooklyn Heights', 8.0, 8.5, 9.0, 9.0),
            ('New York', 'Upper West Side', 9.0, 9.0, 9.5, 9.0),
            ('Chicago', 'Lincoln Park', 7.5, 8.0, 8.5, 8.5),
            ('Chicago', 'Wicker Park', 7.0, 7.5, 8.5, 9.0),
            ('Austin', 'South Congress', 6.5, 7.0, 7.0, 8.0),
            ('Austin', 'Domain', 7.0, 8.0, 6.5, 7.0)
        ]
        
        cur.executemany("""
            INSERT INTO neighborhoods 
            (city, name, cost_of_living, school_rating, transport_score, walkability_score)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, sample_data)
    
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
    
    columns = ['id', 'city', 'name', 'cost_of_living', 'school_rating', 'transport_score', 'walkability_score']
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return results

def get_available_cities():
    """Get list of all unique cities from the neighborhoods table."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT DISTINCT city FROM neighborhoods ORDER BY city")
    cities = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return cities if cities else ["No cities available"]
