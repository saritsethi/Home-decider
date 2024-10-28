import streamlit as st
from components.navigation import create_navigation
from components.inputs import create_neighborhood_inputs
from utils.database import get_neighborhood_data
from utils.visualization import create_neighborhood_comparison_chart

st.set_page_config(page_title="Neighborhood Comparison", page_icon="🏘️")

def main():
    create_navigation()
    
    st.title("Neighborhood Comparison Tool")
    st.write("""
    Compare different neighborhoods based on key metrics like cost of living,
    school ratings, transportation access, and walkability.
    """)
    
    # Get user inputs
    city, selected_neighborhoods = create_neighborhood_inputs()
    
    if selected_neighborhoods:
        # Get neighborhood data
        neighborhood_data = get_neighborhood_data(city)
        
        # Filter for selected neighborhoods
        selected_data = [
            hood for hood in neighborhood_data 
            if hood['name'] in selected_neighborhoods
        ]
        
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

if __name__ == "__main__":
    main()
