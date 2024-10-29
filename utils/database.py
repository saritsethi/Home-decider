import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json
from datetime import datetime, timedelta
import random

# [Previous code remains unchanged until sample_listings]

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
                    'description': 'Elegant corner unit with unobstructed park views, chef\'s kitchen with high-end appliances, marble bathrooms, custom closets, and 24-hour doorman. Steps to Lincoln Park Zoo and lake.'
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
                    'description': 'Contemporary loft-style condo with industrial touches, 11-foot ceilings, exposed brick, chef\'s kitchen, and private terrace. Prime location near restaurants and Blue Line.'
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

# [Rest of the file remains unchanged]
