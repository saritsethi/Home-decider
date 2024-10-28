import streamlit as st
from components.navigation import create_navigation
from utils.database import init_database

st.set_page_config(
    page_title="Home Decision Helper",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    # Initialize database
    init_database()
    
    # Set up navigation
    create_navigation()
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">🏠 Find Your Perfect Home</div>
        <div class="hero-subtitle">Make smarter decisions with our comprehensive home analysis tools</div>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # Quick Start Guide
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <h3>Ready to get started?</h3>
        <p>Choose any tool above or take our lifestyle quiz for personalized recommendations.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
