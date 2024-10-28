import streamlit as st
import pandas as pd
from components.navigation import create_navigation
from components.inputs import create_neighborhood_inputs
from utils.database import get_neighborhood_data
from utils.visualization import create_neighborhood_comparison_chart

st.set_page_config(page_title="Neighborhood Comparison", page_icon="🏘️")

def display_comparison_results(state, city, selected_neighborhoods):
    """Display neighborhood comparison results."""
    if not selected_neighborhoods:
        st.warning("Please select at least one neighborhood to compare.")
        return
        
    # Get neighborhood data
    neighborhood_data = get_neighborhood_data(city=city, state=state)
    
    # Filter for selected neighborhoods
    selected_data = [
        hood for hood in neighborhood_data 
        if hood['name'] in selected_neighborhoods
    ]
    
    if selected_data:
        # Create visualization
        fig = create_neighborhood_comparison_chart(selected_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed metrics table
        st.subheader("Detailed Metrics")
        metrics_df = pd.DataFrame(selected_data)
        st.dataframe(
            metrics_df[['name', 'cost_of_living', 'school_rating', 
                       'transport_score', 'walkability_score']],
            hide_index=True
        )
    else:
        st.warning("No data available for the selected neighborhoods.")

def main():
    create_navigation()
    
    st.title("Neighborhood Comparison Tool")
    st.write("""
    Compare different neighborhoods based on key metrics like cost of living,
    school ratings, transportation access, and walkability.
    """)
    
    # Get user inputs
    state, city, selected_neighborhoods = create_neighborhood_inputs()
    
    # Add Compare button
    if st.button("Compare Neighborhoods", type="primary"):
        display_comparison_results(state, city, selected_neighborhoods)

if __name__ == "__main__":
    main()
