import streamlit as st
from components.navigation import create_navigation
from utils.live_data import get_live_mortgage_rates

st.set_page_config(page_title="Mortgage Pre-Qualification", page_icon="💰")

CREDIT_RATE_ADJUSTMENTS = {
    "Excellent (750+)": 0.0,
    "Good (700-749)": 0.25,
    "Fair (650-699)": 0.75,
    "Poor (below 650)": 1.5
}


def calculate_max_mortgage(annual_income, monthly_debts, down_payment, interest_rate, loan_term_years):
    monthly_income = annual_income / 12
    max_monthly_payment = (monthly_income * 0.43) - monthly_debts
    monthly_rate = interest_rate / 12 / 100
    n_payments = loan_term_years * 12

    if monthly_rate > 0:
        max_mortgage = max_monthly_payment * (
            ((1 + monthly_rate)**n_payments - 1) / (monthly_rate * (1 + monthly_rate)**n_payments)
        )
    else:
        max_mortgage = max_monthly_payment * n_payments

    max_home_price = max_mortgage + down_payment
    return max_home_price, max_mortgage


def main():
    create_navigation()

    st.title("Mortgage Pre-Qualification Calculator")
    st.write(
        "Find out how much home you might qualify for based on your income, debts, and credit score. "
        "Uses standard 43% debt-to-income lending guidelines."
    )

    live_rates = get_live_mortgage_rates()
    if live_rates:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Live 30-yr Fixed Rate", f"{live_rates['rate_30yr']:.2f}%")
        with col2:
            if "rate_15yr" in live_rates:
                st.metric("Live 15-yr Fixed Rate", f"{live_rates['rate_15yr']:.2f}%")
        with col3:
            st.caption(f"📡 Source: FRED / Freddie Mac\nAs of {live_rates['as_of']}")
        default_rate = live_rates["rate_30yr"]
    else:
        default_rate = 6.5

    with st.form("mortgage_qualification_form"):
        col1, col2 = st.columns(2)

        with col1:
            annual_income = st.number_input(
                "Annual Household Income ($)", min_value=0, value=60000, step=1000,
                help="Combined yearly income before taxes"
            )
            monthly_debts = st.number_input(
                "Monthly Debt Payments ($)", min_value=0, value=500, step=100,
                help="Car loans, credit cards, student loans, etc."
            )
            down_payment = st.number_input(
                "Down Payment ($)", min_value=0, value=20000, step=1000,
                help="Amount you plan to pay upfront"
            )

        with col2:
            interest_rate = st.number_input(
                "Interest Rate (%)", min_value=0.0, max_value=15.0,
                value=float(default_rate), step=0.1,
                help="Base rate before credit score adjustment. Live rate auto-filled from FRED when key is configured."
            )
            loan_term = st.selectbox(
                "Loan Term (Years)", options=[15, 20, 30], index=2
            )
            credit_score = st.selectbox(
                "Credit Score Range",
                options=list(CREDIT_RATE_ADJUSTMENTS.keys()),
                help="Your credit score adjusts the interest rate numerically"
            )

        calculate_button = st.form_submit_button("Calculate Pre-Qualification")

    if calculate_button:
        if annual_income <= 0:
            st.error("Please enter a valid annual income greater than $0.")
            return

        monthly_income = annual_income / 12
        max_monthly_available = (monthly_income * 0.43) - monthly_debts

        if max_monthly_available <= 0:
            st.error(
                "Your monthly debt payments already exceed 43% of your monthly income. "
                "You may not qualify for a conventional mortgage. Consider reducing existing debts first."
            )
            return

        rate_adjustment = CREDIT_RATE_ADJUSTMENTS[credit_score]
        adjusted_rate = interest_rate + rate_adjustment

        max_home_price, max_mortgage = calculate_max_mortgage(
            annual_income, monthly_debts, down_payment, adjusted_rate, loan_term
        )

        st.header("Pre-Qualification Results")

        if rate_adjustment > 0:
            st.info(
                f"Your base rate of {interest_rate:.2f}% has been adjusted to "
                f"**{adjusted_rate:.2f}%** based on your credit score. "
                f"Improving your credit could save you significantly over the life of the loan."
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Maximum Home Price", f"${max_home_price:,.0f}")
        with col2:
            st.metric("Maximum Mortgage", f"${max_mortgage:,.0f}")
        with col3:
            monthly_rate_calc = adjusted_rate / 1200
            n = loan_term * 12
            if monthly_rate_calc > 0:
                monthly_payment = (max_mortgage * monthly_rate_calc * (1 + monthly_rate_calc)**n) / \
                                  ((1 + monthly_rate_calc)**n - 1)
            else:
                monthly_payment = max_mortgage / n
            st.metric("Est. Monthly Payment", f"${monthly_payment:,.0f}")

        st.subheader("Affordability Ratios")
        monthly_income = annual_income / 12
        housing_ratio = monthly_payment / monthly_income * 100
        dti_ratio = (monthly_payment + monthly_debts) / monthly_income * 100

        col1, col2 = st.columns(2)
        with col1:
            color = "normal" if housing_ratio <= 28 else "inverse"
            st.metric("Housing Ratio", f"{housing_ratio:.1f}%",
                      "✓ Within 28% guideline" if housing_ratio <= 28 else "⚠ Above 28% guideline",
                      delta_color=color)
        with col2:
            color = "normal" if dti_ratio <= 43 else "inverse"
            st.metric("Debt-to-Income Ratio", f"{dti_ratio:.1f}%",
                      "✓ Within 43% limit" if dti_ratio <= 43 else "⚠ Above 43% limit",
                      delta_color=color)

        st.subheader("Credit Score Impact")
        if credit_score == "Excellent (750+)":
            st.success("Excellent credit — you qualify for the best available rates.")
        elif credit_score == "Good (700-749)":
            st.info(f"Good credit adds a 0.25% rate premium (+${(monthly_payment * 0.25 / 100 * n):,.0f} over the loan term).")
        elif credit_score == "Fair (650-699)":
            st.warning(f"Fair credit adds a 0.75% rate premium. Improving your score before applying could save thousands.")
        else:
            st.error("A score below 650 adds a 1.5% premium and may limit loan options. Consider FHA loans or credit improvement strategies.")


if __name__ == "__main__":
    main()
