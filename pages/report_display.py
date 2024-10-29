import streamlit as st
from components.navigation import create_navigation
import json
from utils.visualization import create_neighborhood_comparison_chart
from utils.report_generator import create_pdf_report
from utils.financial_calculations import calculate_rent_vs_buy
import pandas as pd
import base64
import os

st.set_page_config(page_title="Report Results", page_icon="📊")

# Add CSS for full-width layout
st.markdown('''
    <style>
        .block-container {
            max-width: 100% !important;
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .element-container {
            width: 100% !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            width: 100%;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #fff;
            border-radius: 4px;
            color: #000;
            font-size: 16px;
            font-weight: 400;
            padding: 0px 16px;
            width: 100%;
        }
        .daily-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
            width: 100%;
        }
        .section-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            background-color: #fff;
            height: 100%;
        }
        .stMarkdown {
            width: 100% !important;
        }
        div[data-testid="stHorizontalBlock"] {
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="metric-container"] {
            width: 100% !important;
        }
        .row-widget.stButton {
            width: 100% !important;
        }
    </style>
''', unsafe_allow_html=True)

[Previous content up to the visualization section remains the same...]

    with col3:
        if st.button("🌟 Visualize Your Day", use_container_width=True):
            st.header("A Day in Your New Neighborhood", anchor=False)
            
            # Create tabs for each neighborhood with full width
            if st.session_state.report_data.get('recommended_neighborhoods'):
                st.markdown('<div style="width:100%;">', unsafe_allow_html=True)
                tabs = st.tabs([hood['neighborhood']['name'] for hood in st.session_state.report_data['recommended_neighborhoods']])
                
                for tab, match in zip(tabs, st.session_state.report_data['recommended_neighborhoods']):
                    hood = match['neighborhood']
                    with tab:
                        # Morning Activities
                        st.subheader("🌅 Morning Activities")
                        st.markdown('''
                            <div class="daily-grid">
                                <div class="section-card">
                                    <h5>☕ Breakfast & Coffee</h5>
                        ''', unsafe_allow_html=True)
                        
                        if "Lincoln Park" in hood['name']:
                            st.write("**Sweet Mandy B's**")
                            st.write("📍 1208 W Webster Ave")
                            st.write("- Family-owned bakery")
                            st.write("- Homemade pastries & coffee")
                            st.write("- Opens 7:00 AM daily")
                            st.markdown("---")
                            st.write("**La Colombe Coffee**")
                            st.write("📍 2529 N Clark St")
                            st.write("- Specialty coffee roaster")
                            st.write("- Draft lattes & pastries")
                            st.write("- Opens 6:30 AM")
                        elif "Lake View" in hood['name']:
                            st.write("**Heritage Coffee**")
                            st.write("📍 1325 W Wilson Ave")
                            st.write("- Craft coffee & tea")
                            st.write("- Fresh baked goods")
                            st.write("- Opens 6:00 AM")
                            st.markdown("---")
                            st.write("**The Bageler**")
                            st.write("📍 3732 N Southport Ave")
                            st.write("- Fresh bagels & spreads")
                            st.write("- Breakfast sandwiches")
                            st.write("- Local favorite since 2010")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Fitness Section
                        st.markdown('''
                            <div class="section-card">
                                <h5>🏃‍♂️ Fitness & Recreation</h5>
                        ''', unsafe_allow_html=True)
                        
                        if "Lincoln Park" in hood['name']:
                            st.write("**Lincoln Park Running Path**")
                            st.write("📍 Lakefront Trail")
                            st.write("- 18-mile scenic trail")
                            st.write("- Lake Michigan views")
                            st.write("- Exercise stations")
                            st.markdown("---")
                            st.write("**Lincoln Park Athletic Club**")
                            st.write("📍 1019 W Diversey Pkwy")
                            st.write("- Full-service gym")
                            st.write("- Swimming pool")
                            st.write("- Group fitness classes")
                        elif "Lake View" in hood['name']:
                            st.write("**LA Fitness Lakeview**")
                            st.write("📍 2828 N Clark St")
                            st.write("- Modern gym equipment")
                            st.write("- Personal training")
                            st.write("- Yoga studio")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Parks Section
                        st.markdown('''
                            <div class="section-card">
                                <h5>🌳 Parks & Recreation</h5>
                        ''', unsafe_allow_html=True)
                        
                        if "Lincoln Park" in hood['name']:
                            st.write("**Lincoln Park Zoo**")
                            st.write("📍 2001 N Clark St")
                            st.write("- Free admission")
                            st.write("- 35-acre zoo")
                            st.write("- Nature boardwalk")
                            st.markdown("---")
                            st.write("**North Pond Nature Sanctuary**")
                            st.write("📍 2610 N Cannon Dr")
                            st.write("- Bird watching")
                            st.write("- Walking trails")
                            st.write("- Prairie gardens")
                        elif "Lake View" in hood['name']:
                            st.write("**Belmont Harbor Dog Beach**")
                            st.write("📍 3200 N Lake Shore Dr")
                            st.write("- Off-leash dog area")
                            st.write("- Beach access")
                            st.write("- Sunset views")
                        
                        st.markdown('</div></div>', unsafe_allow_html=True)
                        
                        # Transportation Section
                        st.divider()
                        st.subheader("🚇 Transportation")
                        st.markdown('''
                            <div class="daily-grid">
                                <div class="section-card">
                                    <h5>Public Transit</h5>
                        ''', unsafe_allow_html=True)
                        
                        if "Lincoln Park" in hood['name']:
                            st.write("**Nearest L Stations:**")
                            st.write("- Fullerton (Red/Brown/Purple): 0.2 mi")
                            st.write("- Armitage (Brown/Purple): 0.4 mi")
                            st.markdown("---")
                            st.write("**Bus Routes:**")
                            st.write("- #22 Clark")
                            st.write("- #36 Broadway")
                            st.write("- #74 Fullerton")
                        elif "Lake View" in hood['name']:
                            st.write("**Nearest L Stations:**")
                            st.write("- Belmont (Red/Brown/Purple): 0.3 mi")
                            st.write("- Addison (Red): 0.4 mi")
                            st.markdown("---")
                            st.write("**Bus Routes:**")
                            st.write("- #146 Inner Drive/Michigan Express")
                            st.write("- #22 Clark")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Biking & Walking Section
                        st.markdown('''
                            <div class="section-card">
                                <h5>Biking & Walking</h5>
                        ''', unsafe_allow_html=True)
                        
                        if "Lincoln Park" in hood['name']:
                            st.write("**Divvy Bike Stations:**")
                            st.write("- Clark & Fullerton")
                            st.write("- Lincoln & Diversey")
                            st.markdown("---")
                            st.write("**Walking Paths:**")
                            st.write("- Lakefront Trail access")
                            st.write("- Lincoln Park paths")
                        elif "Lake View" in hood['name']:
                            st.write("**Divvy Bike Stations:**")
                            st.write("- Broadway & Belmont")
                            st.write("- Southport & Addison")
                            st.markdown("---")
                            st.write("**Walking Areas:**")
                            st.write("- Southport Corridor")
                            st.write("- Harbor walkway")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Commute Times Section
                        st.markdown('''
                            <div class="section-card">
                                <h5>Common Commute Times</h5>
                        ''', unsafe_allow_html=True)
                        
                        if "Lincoln Park" in hood['name']:
                            st.write("**By Public Transit:**")
                            st.write("- Loop: 20-25 min")
                            st.write("- O'Hare: 45-50 min")
                            st.write("- River North: 15-20 min")
                            st.markdown("---")
                            st.write("**By Car:**")
                            st.write("- Loop: 12-15 min")
                            st.write("- O'Hare: 25-35 min")
                        elif "Lake View" in hood['name']:
                            st.write("**By Public Transit:**")
                            st.write("- Loop: 25-30 min")
                            st.write("- O'Hare: 50-55 min")
                            st.write("- River North: 20-25 min")
                            st.markdown("---")
                            st.write("**By Car:**")
                            st.write("- Loop: 15-20 min")
                            st.write("- O'Hare: 30-40 min")
                        
                        st.markdown('</div></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # Add feedback section at the very end
    st.divider()
    st.header("📝 Your Feedback")
    feedback_rating = st.slider("How satisfied are you with this analysis? (1-10)", 1, 10, 5)
    if feedback_rating:
        st.write(f"Thank you for your rating of {feedback_rating}/10!")

    # Clean up the temporary PDF file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == "__main__":
    display_report_results()
