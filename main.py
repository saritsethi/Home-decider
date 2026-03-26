import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

@st.cache_resource
def init_cached_database():
    """Cached database initialization."""
    from utils.database import init_database
    init_database()
    return True

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
    
    # Optimized CSS with combined selectors and minimal transitions
    st.markdown("""
    <style>
        /* Combined card styles */
        .feature-card, .section-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #e9ecef;
            transition: all 0.2s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        /* Combined text styles */
        .feature-title, .hero-title {
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .feature-title { font-size: 1.3rem; }
        .hero-title { font-size: 3rem; }
        /* Combined description styles */
        .feature-description, .hero-subtitle {
            color: #6c757d;
        }
        .feature-description { font-size: 1rem; }
        .hero-subtitle { font-size: 1.2rem; }
        /* Icon styles */
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        /* Section styles */
        .hero-section {
            text-align: center;
            padding: 2rem 0;
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
        # Initialize database with caching and error handling
        try:
            with st.spinner('Initializing application...'):
                init_success = init_cached_database()
                if init_success:
                    logging.info('Database initialized successfully')
                else:
                    raise Exception("Database initialization failed")
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
                    transition: background-color 0.2s ease;
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

        st.divider()
        from utils.live_data import live_data_status, get_live_mortgage_rates
        status = live_data_status()
        _always_on_names = {"OpenStreetMap / Overpass (walkability)", "BLS CPI (rent estimates)"}
        always_on = [name for name, on in status.items() if on and name in _always_on_names]
        key_active = [name for name, on in status.items() if on and name not in _always_on_names]

        rates = get_live_mortgage_rates()
        rate_str = f" · 30-yr fixed: **{rates['rate_30yr']:.2f}%**" if rates else ""

        lines = []
        if always_on:
            lines.append(f"**Always on:** {', '.join(always_on)}")
        if key_active:
            lines.append(f"**API-powered:** {', '.join(key_active)}{rate_str}")
        if lines:
            st.success("📡 Live data · " + " · ".join(lines))
        else:
            st.caption("📊 Running on curated data. Add API keys to enable live mortgage rates, walk scores, and market rents.")

    if __name__ == "__main__":
        main()
        
except Exception as e:
    logging.error(f'Application startup error: {str(e)}')
    st.error('Unable to start application. Please try again.')
