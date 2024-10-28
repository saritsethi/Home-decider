import streamlit as st
from components.navigation import create_navigation
from components.inputs import create_financial_inputs
from utils.financial_calculations import calculate_rent_vs_buy
from utils.visualization import create_cost_comparison_chart

st.set_page_config(page_title="Rent vs Buy Calculator", page_icon="🧮")

def main():
    create_navigation()
    
    st.title("Rent vs Buy Calculator")
    st.write("""
    Compare the financial implications of renting versus buying a home over a 5-year period.
    Enter your financial details below to get started.
    """)
    
    # Get financial inputs
    submitted, inputs = create_financial_inputs()
    
    if submitted:
        # Calculate financial projection
        results = calculate_rent_vs_buy(
            inputs["home_price"],
            inputs["down_payment"],
            inputs["interest_rate"],
            30,  # Fixed 30-year mortgage
            inputs["monthly_rent"],
            inputs["property_tax_rate"],
            inputs["maintenance_cost_percent"],
            inputs["home_appreciation_rate"],
            inputs["rent_increase_rate"],
            7.0  # Assumed investment return rate
        )
        
        # Display results
        st.subheader("5-Year Cost Comparison")
        fig = create_cost_comparison_chart(results)
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Buying Costs",
                f"${results['Cumulative_Buying_Costs'].iloc[-1]:,.2f}"
            )
        
        with col2:
            st.metric(
                "Total Rental Costs",
                f"${results['Cumulative_Rental_Costs'].iloc[-1]:,.2f}"
            )
        
        with col3:
            difference = (results['Cumulative_Buying_Costs'].iloc[-1] - 
                        results['Cumulative_Rental_Costs'].iloc[-1])
            st.metric(
                "Buy vs Rent Difference",
                f"${abs(difference):,.2f}",
                f"{'Buying costs more' if difference > 0 else 'Renting costs more'}"
            )

if __name__ == "__main__":
    main()
