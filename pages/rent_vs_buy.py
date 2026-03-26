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
    Compare the true financial cost of renting versus buying over a 5-year period.
    The buying cost accounts for mortgage, taxes, insurance, maintenance, and the opportunity
    cost of your down payment — offset by home equity gained through appreciation.
    """)

    submitted, inputs = create_financial_inputs()

    if submitted:
        if inputs["home_price"] <= 0:
            st.error("Please enter a valid home price greater than $0.")
            return
        if inputs["down_payment"] >= inputs["home_price"]:
            st.error("Down payment must be less than the home price.")
            return
        if inputs["monthly_rent"] <= 0:
            st.error("Please enter a valid monthly rent amount.")
            return

        results = calculate_rent_vs_buy(
            inputs["home_price"],
            inputs["down_payment"],
            inputs["interest_rate"],
            30,
            inputs["monthly_rent"],
            inputs["property_tax_rate"],
            inputs["maintenance_cost_percent"],
            inputs["home_appreciation_rate"],
            inputs["rent_increase_rate"],
            7.0
        )

        st.subheader("5-Year Net Cost Comparison")
        st.caption("Buying costs are net of equity gained through appreciation. Includes opportunity cost of down payment.")
        fig = create_cost_comparison_chart(results)
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Net Buying Cost (5yr)", f"${results['Cumulative_Buying_Costs'].iloc[-1]:,.2f}")

        with col2:
            st.metric("Total Rental Cost (5yr)", f"${results['Cumulative_Rental_Costs'].iloc[-1]:,.2f}")

        with col3:
            difference = (results['Cumulative_Buying_Costs'].iloc[-1] -
                          results['Cumulative_Rental_Costs'].iloc[-1])
            st.metric(
                "5-Year Difference",
                f"${abs(difference):,.2f}",
                f"{'Buying costs more' if difference > 0 else 'Renting costs more'}"
            )


if __name__ == "__main__":
    main()
