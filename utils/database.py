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
    
    # Backup existing data
    cur.execute("SELECT * FROM neighborhoods") if table_exists(cur, 'neighborhoods') else None
    existing_data = cur.fetchall() if table_exists(cur, 'neighborhoods') else []
    
    # Drop and recreate neighborhoods table with new schema
    if table_exists(cur, 'neighborhoods'):
        cur.execute("DROP TABLE neighborhoods")
    
    # Create neighborhoods table with state column
    cur.execute("""
        CREATE TABLE IF NOT EXISTS neighborhoods (
            id SERIAL PRIMARY KEY,
            state TEXT NOT NULL,
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
            ('CA', 'San Francisco', 'Mission District', 8.5, 7.0, 9.0, 9.5),
            ('CA', 'San Francisco', 'Pacific Heights', 9.5, 8.5, 7.5, 8.0),
            ('CA', 'Los Angeles', 'Santa Monica', 9.0, 8.0, 8.0, 9.0),
            ('CA', 'Los Angeles', 'Silver Lake', 8.0, 7.5, 7.5, 8.5),
            ('NY', 'New York', 'Brooklyn Heights', 8.0, 8.5, 9.0, 9.0),
            ('NY', 'New York', 'Upper West Side', 9.0, 9.0, 9.5, 9.0),
            ('IL', 'Chicago', 'Lincoln Park', 7.5, 8.0, 8.5, 8.5),
            ('IL', 'Chicago', 'Wicker Park', 7.0, 7.5, 8.5, 9.0),
            ('TX', 'Austin', 'South Congress', 6.5, 7.0, 7.0, 8.0),
            ('TX', 'Austin', 'Domain', 7.0, 8.0, 6.5, 7.0),
            ('TX', 'Dallas', 'Uptown', 7.5, 8.0, 7.0, 8.5),
            ('TX', 'Dallas', 'Bishop Arts', 7.0, 7.5, 7.5, 8.0)
        ]
        
        cur.executemany("""
            INSERT INTO neighborhoods 
            (state, city, name, cost_of_living, school_rating, transport_score, walkability_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, sample_data)
    
    cur.close()
    conn.close()

def table_exists(cur, table_name):
    """Check if a table exists in the database."""
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        )
    """, (table_name,))
    return cur.fetchone()[0]

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
    
    if state:
        cur.execute("SELECT DISTINCT city FROM neighborhoods WHERE state = %s ORDER BY city", (state,))
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
        cur.execute("SELECT * FROM neighborhoods WHERE state = %s AND city = %s", (state, city))
    elif state:
        cur.execute("SELECT * FROM neighborhoods WHERE state = %s", (state,))
    elif city:
        cur.execute("SELECT * FROM neighborhoods WHERE city = %s", (city,))
    else:
        cur.execute("SELECT * FROM neighborhoods")
    
    columns = ['id', 'state', 'city', 'name', 'cost_of_living', 'school_rating', 'transport_score', 'walkability_score']
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return results
