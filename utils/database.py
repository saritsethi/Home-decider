import os
import random
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import pool
from datetime import datetime, timedelta
import streamlit as st


@st.cache_resource
def get_connection_pool():
    try:
        connection_pool = pool.SimpleConnectionPool(
            1, 20,
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


@st.cache_data(ttl=3600)
def generate_historical_values(base_price):
    """Generate deterministic historical property values seeded by base price."""
    rng = random.Random(int(base_price))
    values = []
    date = datetime.now() - timedelta(days=5 * 365)
    price = base_price * 0.75

    for _ in range(20):
        values.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": round(price, 2)
        })
        date += timedelta(days=90)
        growth_rate = 1.02 + (rng.random() - 0.5) * 0.01
        price *= growth_rate

    return json.dumps(values)


def init_database():
    db_pool = get_connection_pool()
    conn = None
    cur = None
    try:
        conn = db_pool.getconn()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                session_id TEXT PRIMARY KEY,
                preferences JSONB,
                user_info JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        return True
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            db_pool.putconn(conn)


@st.cache_data(ttl=3600)
def get_available_states():
    return ["Illinois", "New York", "California"]


@st.cache_data(ttl=3600)
def get_available_cities(state=None):
    cities = {
        "Illinois": ["Chicago", "Evanston", "Oak Park"],
        "New York": ["New York City", "Brooklyn", "Queens"],
        "California": ["San Francisco", "Los Angeles", "San Diego"]
    }
    return cities.get(state, []) if state else []


@st.cache_data(ttl=3600)
def get_neighborhood_data(city=None, state=None):
    if not city:
        return []

    neighborhoods = {
        "Chicago": [
            {
                "name": "Lincoln Park",
                "cost_of_living": 8, "school_rating": 9, "transport_score": 8, "walkability_score": 9,
                "safety_score": 8, "nightlife_score": 8, "dining_score": 9, "outdoor_score": 8,
                "quiet_score": 3, "shopping_score": 7,
                "historical_values": generate_historical_values(500000),
                "property_listings": [
                    {"address": "2143 N Sheffield Ave", "price": 849000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 2100, "year_built": 2019, "description": "Stunning contemporary townhome with hardwood floors, gourmet kitchen, spacious primary suite, attached garage, and private rooftop deck."},
                    {"address": "1920 N Lincoln Park West", "price": 1249000, "bedrooms": 4, "bathrooms": 3, "sqft": 2800, "year_built": 2015, "description": "Elegant corner unit with unobstructed park views, chef's kitchen, marble bathrooms, custom closets, and 24-hour doorman."}
                ]
            },
            {
                "name": "Lake View",
                "cost_of_living": 7, "school_rating": 8, "transport_score": 9, "walkability_score": 8,
                "safety_score": 7, "nightlife_score": 9, "dining_score": 8, "outdoor_score": 6,
                "quiet_score": 3, "shopping_score": 7,
                "historical_values": generate_historical_values(450000),
                "property_listings": [
                    {"address": "3550 N Lake Shore Dr", "price": 899000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 1900, "year_built": 2017, "description": "Luxury high-rise with breathtaking lake views, custom kitchen, quartz countertops, spa-like bathrooms, and fitness center."},
                    {"address": "1658 W Addison St", "price": 679000, "bedrooms": 3, "bathrooms": 2, "sqft": 1650, "year_built": 2012, "description": "Sun-filled corner unit near Wrigley Field, open concept living, renovated kitchen, hardwood floors, and private outdoor space."}
                ]
            },
            {
                "name": "Wicker Park",
                "cost_of_living": 7, "school_rating": 7, "transport_score": 8, "walkability_score": 9,
                "safety_score": 6, "nightlife_score": 9, "dining_score": 9, "outdoor_score": 5,
                "quiet_score": 3, "shopping_score": 8,
                "historical_values": generate_historical_values(420000),
                "property_listings": [
                    {"address": "1540 N Damen Ave", "price": 599000, "bedrooms": 2, "bathrooms": 2, "sqft": 1400, "year_built": 2018, "description": "Modern condo in the heart of Wicker Park with rooftop deck, in-unit laundry, and steps from top restaurants."},
                    {"address": "2020 W Pierce Ave", "price": 725000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 1850, "year_built": 2020, "description": "New construction townhome with open floor plan, designer finishes, private garage, and landscaped backyard."}
                ]
            }
        ],
        "Evanston": [
            {
                "name": "Downtown Evanston",
                "cost_of_living": 7, "school_rating": 9, "transport_score": 8, "walkability_score": 9,
                "safety_score": 8, "nightlife_score": 5, "dining_score": 7, "outdoor_score": 6,
                "quiet_score": 6, "shopping_score": 7,
                "historical_values": generate_historical_values(400000),
                "property_listings": [
                    {"address": "1570 Sherman Ave", "price": 425000, "bedrooms": 2, "bathrooms": 2, "sqft": 1200, "year_built": 2010, "description": "Bright condo near Northwestern University with lake views, updated kitchen, and walking distance to shops and transit."},
                    {"address": "820 Church St", "price": 675000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 2000, "year_built": 2005, "description": "Spacious townhome with finished basement, two-car garage, and excellent school district access."}
                ]
            },
            {
                "name": "South Evanston",
                "cost_of_living": 6, "school_rating": 8, "transport_score": 7, "walkability_score": 7,
                "safety_score": 8, "nightlife_score": 3, "dining_score": 5, "outdoor_score": 6,
                "quiet_score": 8, "shopping_score": 5,
                "historical_values": generate_historical_values(350000),
                "property_listings": [
                    {"address": "2200 Main St", "price": 375000, "bedrooms": 3, "bathrooms": 1.5, "sqft": 1600, "year_built": 1995, "description": "Charming single-family home with large yard, updated bathrooms, and quiet tree-lined street."},
                    {"address": "1845 Dodge Ave", "price": 310000, "bedrooms": 2, "bathrooms": 1, "sqft": 1100, "year_built": 1985, "description": "Affordable starter home with hardwood floors, new roof, and close to parks and schools."}
                ]
            }
        ],
        "Oak Park": [
            {
                "name": "Downtown Oak Park",
                "cost_of_living": 7, "school_rating": 8, "transport_score": 8, "walkability_score": 8,
                "safety_score": 8, "nightlife_score": 4, "dining_score": 6, "outdoor_score": 6,
                "quiet_score": 7, "shopping_score": 6,
                "historical_values": generate_historical_values(380000),
                "property_listings": [
                    {"address": "150 S Oak Park Ave", "price": 450000, "bedrooms": 3, "bathrooms": 2, "sqft": 1800, "year_built": 2000, "description": "Historic district home with original woodwork, updated kitchen, wrap-around porch, and easy CTA access."},
                    {"address": "625 Lake St", "price": 389000, "bedrooms": 2, "bathrooms": 2, "sqft": 1350, "year_built": 2012, "description": "Modern condo with open layout, stainless appliances, balcony, one block from Green Line station."}
                ]
            },
            {
                "name": "Frank Lloyd Wright District",
                "cost_of_living": 8, "school_rating": 9, "transport_score": 7, "walkability_score": 8,
                "safety_score": 9, "nightlife_score": 3, "dining_score": 5, "outdoor_score": 7,
                "quiet_score": 8, "shopping_score": 5,
                "historical_values": generate_historical_values(450000),
                "property_listings": [
                    {"address": "333 Forest Ave", "price": 725000, "bedrooms": 4, "bathrooms": 3, "sqft": 2600, "year_built": 1920, "description": "Beautifully preserved Prairie-style home with period details, chef's kitchen renovation, mature landscaping, and top-rated schools."},
                    {"address": "210 N Kenilworth Ave", "price": 549000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 2100, "year_built": 1935, "description": "Classic brick home in historic neighborhood with updated systems, hardwood floors, and finished attic."}
                ]
            }
        ],
        "New York City": [
            {
                "name": "Upper West Side",
                "cost_of_living": 9, "school_rating": 9, "transport_score": 10, "walkability_score": 10,
                "safety_score": 8, "nightlife_score": 7, "dining_score": 9, "outdoor_score": 8,
                "quiet_score": 4, "shopping_score": 8,
                "historical_values": generate_historical_values(950000),
                "property_listings": [
                    {"address": "210 W 78th St", "price": 1450000, "bedrooms": 2, "bathrooms": 2, "sqft": 1200, "year_built": 2018, "description": "Pre-war charm meets modern luxury with Central Park views, doorman building, renovated kitchen, and washer/dryer in unit."},
                    {"address": "350 W 85th St", "price": 899000, "bedrooms": 1, "bathrooms": 1, "sqft": 850, "year_built": 2005, "description": "Bright one-bedroom with high ceilings, exposed brick, and steps from Riverside Park."}
                ]
            },
            {
                "name": "Harlem",
                "cost_of_living": 6, "school_rating": 7, "transport_score": 9, "walkability_score": 8,
                "safety_score": 6, "nightlife_score": 7, "dining_score": 7, "outdoor_score": 6,
                "quiet_score": 5, "shopping_score": 6,
                "historical_values": generate_historical_values(550000),
                "property_listings": [
                    {"address": "280 W 135th St", "price": 650000, "bedrooms": 2, "bathrooms": 1.5, "sqft": 1100, "year_built": 2016, "description": "New development condo with chef's kitchen, private balcony, fitness center, and vibrant neighborhood culture."},
                    {"address": "45 W 125th St", "price": 495000, "bedrooms": 1, "bathrooms": 1, "sqft": 750, "year_built": 2020, "description": "Modern one-bedroom near Apollo Theater with floor-to-ceiling windows, in-unit laundry, and rooftop terrace."}
                ]
            },
            {
                "name": "East Village",
                "cost_of_living": 8, "school_rating": 7, "transport_score": 10, "walkability_score": 10,
                "safety_score": 7, "nightlife_score": 10, "dining_score": 10, "outdoor_score": 5,
                "quiet_score": 2, "shopping_score": 8,
                "historical_values": generate_historical_values(750000),
                "property_listings": [
                    {"address": "120 E 7th St", "price": 875000, "bedrooms": 2, "bathrooms": 1, "sqft": 950, "year_built": 2010, "description": "Renovated walkup with exposed brick, chef's kitchen, surrounded by the best dining and nightlife in the city."},
                    {"address": "330 E 6th St", "price": 625000, "bedrooms": 1, "bathrooms": 1, "sqft": 650, "year_built": 2000, "description": "Cozy one-bedroom with high ceilings, original details, and Tompkins Square Park at your doorstep."}
                ]
            }
        ],
        "Brooklyn": [
            {
                "name": "Park Slope",
                "cost_of_living": 8, "school_rating": 9, "transport_score": 9, "walkability_score": 9,
                "safety_score": 8, "nightlife_score": 6, "dining_score": 8, "outdoor_score": 8,
                "quiet_score": 5, "shopping_score": 7,
                "historical_values": generate_historical_values(850000),
                "property_listings": [
                    {"address": "450 5th Ave", "price": 1100000, "bedrooms": 3, "bathrooms": 2, "sqft": 1600, "year_built": 2015, "description": "Stunning brownstone floor-through with original moldings, chef's kitchen, private garden, and steps from Prospect Park."},
                    {"address": "725 Union St", "price": 789000, "bedrooms": 2, "bathrooms": 1.5, "sqft": 1200, "year_built": 2008, "description": "Sun-drenched condo with modern finishes, in-unit washer/dryer, and top-rated PS 321 school district."}
                ]
            },
            {
                "name": "Williamsburg",
                "cost_of_living": 8, "school_rating": 7, "transport_score": 8, "walkability_score": 9,
                "safety_score": 7, "nightlife_score": 9, "dining_score": 9, "outdoor_score": 5,
                "quiet_score": 3, "shopping_score": 8,
                "historical_values": generate_historical_values(700000),
                "property_listings": [
                    {"address": "100 N 3rd St", "price": 925000, "bedrooms": 2, "bathrooms": 2, "sqft": 1100, "year_built": 2019, "description": "Luxury waterfront condo with Manhattan skyline views, rooftop pool, concierge, and steps from the L train."},
                    {"address": "250 Bedford Ave", "price": 675000, "bedrooms": 1, "bathrooms": 1, "sqft": 800, "year_built": 2017, "description": "Trendy loft-style apartment with soaring ceilings, oversized windows, surrounded by galleries and restaurants."}
                ]
            },
            {
                "name": "DUMBO",
                "cost_of_living": 9, "school_rating": 8, "transport_score": 8, "walkability_score": 9,
                "safety_score": 8, "nightlife_score": 6, "dining_score": 7, "outdoor_score": 7,
                "quiet_score": 5, "shopping_score": 6,
                "historical_values": generate_historical_values(900000),
                "property_listings": [
                    {"address": "50 Main St", "price": 1350000, "bedrooms": 2, "bathrooms": 2, "sqft": 1300, "year_built": 2020, "description": "Converted warehouse loft with Brooklyn Bridge views, 12-foot ceilings, designer finishes, and doorman building."},
                    {"address": "85 Jay St", "price": 975000, "bedrooms": 1, "bathrooms": 1, "sqft": 900, "year_built": 2018, "description": "Modern luxury one-bedroom with stunning East River views, chef's kitchen, and full-service amenities."}
                ]
            }
        ],
        "Queens": [
            {
                "name": "Astoria",
                "cost_of_living": 6, "school_rating": 7, "transport_score": 8, "walkability_score": 8,
                "safety_score": 7, "nightlife_score": 6, "dining_score": 8, "outdoor_score": 6,
                "quiet_score": 5, "shopping_score": 6,
                "historical_values": generate_historical_values(450000),
                "property_listings": [
                    {"address": "25-10 30th Ave", "price": 525000, "bedrooms": 2, "bathrooms": 1, "sqft": 1000, "year_built": 2015, "description": "Bright corner condo with balcony, updated kitchen, diverse dining scene, and quick N/W train access to Manhattan."},
                    {"address": "31-50 Steinway St", "price": 449000, "bedrooms": 1, "bathrooms": 1, "sqft": 750, "year_built": 2012, "description": "Modern one-bedroom near Astoria Park with rooftop access, in-unit laundry, and East River views."}
                ]
            },
            {
                "name": "Long Island City",
                "cost_of_living": 7, "school_rating": 7, "transport_score": 9, "walkability_score": 8,
                "safety_score": 7, "nightlife_score": 5, "dining_score": 6, "outdoor_score": 6,
                "quiet_score": 5, "shopping_score": 5,
                "historical_values": generate_historical_values(600000),
                "property_listings": [
                    {"address": "5-25 46th Ave", "price": 750000, "bedrooms": 2, "bathrooms": 2, "sqft": 1100, "year_built": 2021, "description": "Brand new luxury tower with panoramic Manhattan views, resort-style amenities, one stop from Midtown."},
                    {"address": "10-50 Jackson Ave", "price": 595000, "bedrooms": 1, "bathrooms": 1, "sqft": 800, "year_built": 2019, "description": "Sleek modern condo near MoMA PS1 with floor-to-ceiling windows, chef's kitchen, and concierge service."}
                ]
            },
            {
                "name": "Forest Hills",
                "cost_of_living": 6, "school_rating": 8, "transport_score": 7, "walkability_score": 7,
                "safety_score": 8, "nightlife_score": 4, "dining_score": 6, "outdoor_score": 6,
                "quiet_score": 7, "shopping_score": 6,
                "historical_values": generate_historical_values(500000),
                "property_listings": [
                    {"address": "108-20 Queens Blvd", "price": 475000, "bedrooms": 2, "bathrooms": 1.5, "sqft": 1100, "year_built": 2000, "description": "Pre-war co-op with Art Deco details, doorman building, lush garden courtyard, and express train to Penn Station."},
                    {"address": "65-25 Austin St", "price": 550000, "bedrooms": 2, "bathrooms": 2, "sqft": 1200, "year_built": 2010, "description": "Renovated apartment near Austin Street shops with modern kitchen, hardwood floors, and great school district."}
                ]
            }
        ],
        "San Francisco": [
            {
                "name": "Pacific Heights",
                "cost_of_living": 10, "school_rating": 9, "transport_score": 7, "walkability_score": 8,
                "safety_score": 8, "nightlife_score": 5, "dining_score": 7, "outdoor_score": 7,
                "quiet_score": 6, "shopping_score": 7,
                "historical_values": generate_historical_values(1200000),
                "property_listings": [
                    {"address": "2450 Broadway St", "price": 1850000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 2200, "year_built": 2015, "description": "Stunning Victorian with Golden Gate Bridge views, gourmet kitchen, private garden, and classic San Francisco charm."},
                    {"address": "1920 Divisadero St", "price": 1295000, "bedrooms": 2, "bathrooms": 2, "sqft": 1500, "year_built": 2018, "description": "Modern condo with panoramic bay views, open floor plan, high-end finishes, and shared roof deck."}
                ]
            },
            {
                "name": "Mission District",
                "cost_of_living": 7, "school_rating": 6, "transport_score": 9, "walkability_score": 9,
                "safety_score": 5, "nightlife_score": 8, "dining_score": 10, "outdoor_score": 5,
                "quiet_score": 3, "shopping_score": 7,
                "historical_values": generate_historical_values(800000),
                "property_listings": [
                    {"address": "3200 24th St", "price": 895000, "bedrooms": 2, "bathrooms": 1, "sqft": 1100, "year_built": 2010, "description": "Vibrant neighborhood condo with BART access, sunny exposure, modern finishes, and world-class dining at your door."},
                    {"address": "1450 Valencia St", "price": 749000, "bedrooms": 1, "bathrooms": 1, "sqft": 800, "year_built": 2016, "description": "Stylish one-bedroom with private patio, in-unit laundry, surrounded by the best cafes and shops."}
                ]
            },
            {
                "name": "Sunset District",
                "cost_of_living": 6, "school_rating": 8, "transport_score": 6, "walkability_score": 6,
                "safety_score": 8, "nightlife_score": 3, "dining_score": 5, "outdoor_score": 8,
                "quiet_score": 8, "shopping_score": 5,
                "historical_values": generate_historical_values(950000),
                "property_listings": [
                    {"address": "1840 Judah St", "price": 1100000, "bedrooms": 3, "bathrooms": 2, "sqft": 1800, "year_built": 1960, "description": "Classic single-family home with ocean breezes, large backyard, updated kitchen, and close to Golden Gate Park."},
                    {"address": "2250 Noriega St", "price": 875000, "bedrooms": 2, "bathrooms": 1, "sqft": 1200, "year_built": 1955, "description": "Cozy Outer Sunset home with garage, new windows, family-friendly neighborhood, and N-Judah Muni access."}
                ]
            }
        ],
        "Los Angeles": [
            {
                "name": "Silver Lake",
                "cost_of_living": 7, "school_rating": 7, "transport_score": 5, "walkability_score": 7,
                "safety_score": 6, "nightlife_score": 7, "dining_score": 8, "outdoor_score": 7,
                "quiet_score": 5, "shopping_score": 7,
                "historical_values": generate_historical_values(850000),
                "property_listings": [
                    {"address": "2830 Sunset Blvd", "price": 975000, "bedrooms": 2, "bathrooms": 2, "sqft": 1400, "year_built": 2019, "description": "Mid-century modern home with hillside views, open floor plan, designer kitchen, walking distance to the reservoir."},
                    {"address": "1545 Hyperion Ave", "price": 799000, "bedrooms": 2, "bathrooms": 1.5, "sqft": 1200, "year_built": 2015, "description": "Stylish bungalow with private yard, updated interiors, steps from Sunset Junction shops and restaurants."}
                ]
            },
            {
                "name": "Santa Monica",
                "cost_of_living": 9, "school_rating": 9, "transport_score": 7, "walkability_score": 9,
                "safety_score": 8, "nightlife_score": 6, "dining_score": 8, "outdoor_score": 9,
                "quiet_score": 5, "shopping_score": 8,
                "historical_values": generate_historical_values(1100000),
                "property_listings": [
                    {"address": "1425 Ocean Ave", "price": 1650000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 1900, "year_built": 2020, "description": "Ocean-view luxury condo with resort amenities, chef's kitchen, private balcony, and steps from the beach and pier."},
                    {"address": "820 14th St", "price": 1195000, "bedrooms": 2, "bathrooms": 2, "sqft": 1350, "year_built": 2017, "description": "Bright modern condo near Montana Avenue shops with high ceilings, hardwood floors, and two parking spaces."}
                ]
            },
            {
                "name": "Eagle Rock",
                "cost_of_living": 5, "school_rating": 7, "transport_score": 5, "walkability_score": 6,
                "safety_score": 7, "nightlife_score": 4, "dining_score": 6, "outdoor_score": 7,
                "quiet_score": 7, "shopping_score": 5,
                "historical_values": generate_historical_values(650000),
                "property_listings": [
                    {"address": "4620 Eagle Rock Blvd", "price": 725000, "bedrooms": 3, "bathrooms": 2, "sqft": 1600, "year_built": 2000, "description": "Charming craftsman home with mountain views, updated kitchen, spacious backyard, and growing arts district."},
                    {"address": "1935 Colorado Blvd", "price": 599000, "bedrooms": 2, "bathrooms": 1, "sqft": 1100, "year_built": 1985, "description": "Affordable starter home with character, hardwood floors, detached garage, and near Occidental College."}
                ]
            }
        ],
        "San Diego": [
            {
                "name": "North Park",
                "cost_of_living": 6, "school_rating": 7, "transport_score": 6, "walkability_score": 8,
                "safety_score": 7, "nightlife_score": 7, "dining_score": 8, "outdoor_score": 6,
                "quiet_score": 5, "shopping_score": 6,
                "historical_values": generate_historical_values(650000),
                "property_listings": [
                    {"address": "3025 University Ave", "price": 699000, "bedrooms": 2, "bathrooms": 2, "sqft": 1200, "year_built": 2018, "description": "Modern condo in trendy North Park with craft brewery scene, farmers market, and walkable neighborhood vibe."},
                    {"address": "4140 30th St", "price": 575000, "bedrooms": 1, "bathrooms": 1, "sqft": 850, "year_built": 2015, "description": "Charming one-bedroom with private patio, updated finishes, surrounded by the best local restaurants."}
                ]
            },
            {
                "name": "La Jolla",
                "cost_of_living": 9, "school_rating": 10, "transport_score": 5, "walkability_score": 7,
                "safety_score": 9, "nightlife_score": 4, "dining_score": 7, "outdoor_score": 9,
                "quiet_score": 7, "shopping_score": 6,
                "historical_values": generate_historical_values(1100000),
                "property_listings": [
                    {"address": "7550 Eads Ave", "price": 1495000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 2000, "year_built": 2016, "description": "Coastal luxury condo with ocean views, gourmet kitchen, spa-like bathrooms, and steps from La Jolla Cove."},
                    {"address": "850 Prospect St", "price": 1125000, "bedrooms": 2, "bathrooms": 2, "sqft": 1400, "year_built": 2012, "description": "Village location with panoramic ocean views, modern finishes, rooftop terrace, and world-class dining nearby."}
                ]
            },
            {
                "name": "Hillcrest",
                "cost_of_living": 6, "school_rating": 7, "transport_score": 7, "walkability_score": 9,
                "safety_score": 7, "nightlife_score": 7, "dining_score": 8, "outdoor_score": 6,
                "quiet_score": 5, "shopping_score": 7,
                "historical_values": generate_historical_values(550000),
                "property_listings": [
                    {"address": "3780 Park Blvd", "price": 525000, "bedrooms": 2, "bathrooms": 1, "sqft": 950, "year_built": 2010, "description": "Vibrant urban living near Balboa Park with walkable dining, updated kitchen, and strong community feel."},
                    {"address": "1450 University Ave", "price": 449000, "bedrooms": 1, "bathrooms": 1, "sqft": 700, "year_built": 2008, "description": "Cozy condo with balcony, modern appliances, surrounded by shops, cafes, and the famous farmers market."}
                ]
            }
        ]
    }
    return neighborhoods.get(city, [])


def save_quiz_results(session_id, preferences, user_info):
    db_pool = get_connection_pool()
    conn = None
    cur = None
    try:
        conn = db_pool.getconn()
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
            db_pool.putconn(conn)
