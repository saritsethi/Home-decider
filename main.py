import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

try:
    # Set page config first
    st.set_page_config(
        page_title='Home Decision Helper',
        page_icon='🏠',
        layout='wide',
        initial_sidebar_state='expanded'
    )
    
    # Import other dependencies
    from components.navigation import create_navigation
    from utils.database import init_database
    
    # Custom CSS for hover effects and styling
    st.markdown("""
    <style>
        .feature-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #e9ecef;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        .feature-title {
            font-size: 1.3rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .feature-description {
            font-size: 1rem;
            color: #6c757d;
        }
        .hero-section {
            text-align: center;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }
        .hero-title {
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .hero-subtitle {
            font-size: 1.2rem;
            color: #6c757d;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

    def create_feature_container(icon, title, description, page_path):
        """Create a styled container for feature links with enhanced visuals."""
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <div class="feature-title">{title}</div>
            <div class="feature-description">{description}</div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link(page_path, label="Get Started →", use_container_width=True)

    def main():
        # Initialize database with error handling
        try:
            init_database()
            logging.info('Database initialized successfully')
        except Exception as e:
            logging.error(f'Database initialization error: {str(e)}')
            st.error('Unable to initialize database. Please try again.')
            return
        
        # Set up navigation
        create_navigation()
        
        # Hero Section
        st.markdown("""
        <div class="hero-section">
            <div class="hero-title">🏠 Find Your Perfect Home</div>
            <div class="hero-subtitle">Make smarter decisions with our comprehensive home analysis tools</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Introduction Section
        st.markdown('''
        <div style="text-align: center; padding: 2rem 0;">
            <h2>How It Works</h2>
            <p style="font-size: 1.2rem; color: #6c757d; margin: 1rem 0;">
                Our comprehensive quiz helps you make informed decisions about your next home:
            </p>
            <ol style="text-align: left; max-width: 600px; margin: 0 auto; font-size: 1.1rem;">
                <li>Share your family details and preferences</li>
                <li>Tell us about your financial situation</li>
                <li>Choose your lifestyle preferences</li>
            </ol>
            <div style="margin: 2rem 0;">
                <a href="/lifestyle_quiz" target="_self" style="
                    background-color: #FF4B4B;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: bold;
                    font-size: 1.2rem;
                    transition: background-color 0.3s ease;
                ">Take the Quiz →</a>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Feature Cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_feature_container(
                "💰",
                "Rent vs. Buy",
                "Calculate and compare your long-term housing costs",
                "pages/rent_vs_buy.py"
            )
        
        with col2:
            create_feature_container(
                "🏘️",
                "Neighborhood Finder",
                "Discover and compare the perfect neighborhood",
                "pages/neighborhood_comparison.py"
            )
        
        with col3:
            create_feature_container(
                "✨",
                "Lifestyle Match",
                "Get personalized neighborhood recommendations",
                "pages/lifestyle_quiz.py"
            )

    if __name__ == "__main__":
        main()
        
except Exception as e:
    logging.error(f'Application startup error: {str(e)}')
    st.error('Unable to start application. Please try again.')
