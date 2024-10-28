import streamlit as st
from components.navigation import create_navigation
import numpy as np

st.set_page_config(page_title="Mortgage Pre-Qualification", page_icon="💰")

def calculate_max_mortgage(annual_income, monthly_debts, down_payment, interest_rate, loan_term_years):
    """Calculate maximum mortgage amount based on income and debts."""
    # Monthly income
    monthly_income = annual_income / 12
    
    # Maximum monthly payment based on DTI ratio (43% is standard)
    max_monthly_payment = (monthly_income * 0.43) - monthly_debts
    
    # Convert annual rate to monthly
    monthly_rate = interest_rate / 12 / 100
    
    # Number of payments
    n_payments = loan_term_years * 12
    
    # Maximum mortgage formula: PMT = P * (r(1+r)^n)/((1+r)^n-1)
    # Solving for P (Principal)
    if monthly_rate > 0:
        max_mortgage = max_monthly_payment * (((1 + monthly_rate)**n_payments - 1) / (monthly_rate * (1 + monthly_rate)**n_payments))
    else:
        max_mortgage = max_monthly_payment * n_payments
    
    # Add down payment to get total home price
    max_home_price = max_mortgage + down_payment
    
    return max_home_price, max_mortgage

def main():
    create_navigation()
    
    st.title("Mortgage Pre-Qualification Calculator")
    st.write("""
    Find out how much home you might qualify for based on your income, debts, and other factors.
    This calculator uses standard lending guidelines to estimate your maximum mortgage amount.
    """)
    
    with st.form("mortgage_qualification_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            annual_income = st.number_input(
                "Annual Household Income ($)",
                min_value=0,
                value=60000,
                step=1000,
                help="Combined yearly income before taxes"
            )
            
            monthly_debts = st.number_input(
                "Monthly Debt Payments ($)",
                min_value=0,
                value=500,
                step=100,
                help="Total monthly payments for car loans, credit cards, student loans, etc."
            )
            
            down_payment = st.number_input(
                "Down Payment ($)",
                min_value=0,
                value=20000,
                step=1000,
                help="Amount you plan to pay upfront"
            )
        
        with col2:
            interest_rate = st.number_input(
                "Interest Rate (%)",
                min_value=0.0,
                max_value=15.0,
                value=6.5,
                step=0.1,
                help="Current mortgage interest rate"
            )
            
            loan_term = st.selectbox(
                "Loan Term (Years)",
                options=[15, 20, 30],
                index=2,
                help="Length of the mortgage"
            )
            
            credit_score = st.selectbox(
                "Credit Score Range",
                options=[
                    "Excellent (750+)",
                    "Good (700-749)",
                    "Fair (650-699)",
                    "Poor (below 650)"
                ],
                help="Your credit score affects loan approval and interest rates"
            )
        
        calculate_button = st.form_submit_button("Calculate Pre-Qualification")
    
    if calculate_button:
        max_home_price, max_mortgage = calculate_max_mortgage(
            annual_income,
            monthly_debts,
            down_payment,
            interest_rate,
            loan_term
        )
        
        st.header("Pre-Qualification Results")
        
        # Create three columns for metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Maximum Home Price",
                f"${max_home_price:,.2f}",
                help="The maximum home price you might qualify for"
            )
        
        with col2:
            st.metric(
                "Maximum Mortgage Amount",
                f"${max_mortgage:,.2f}",
                help="The maximum loan amount you might qualify for"
            )
        
        with col3:
            monthly_payment = (max_mortgage * (interest_rate/1200) * (1 + interest_rate/1200)**(loan_term*12)) / ((1 + interest_rate/1200)**(loan_term*12) - 1)
            st.metric(
                "Estimated Monthly Payment",
                f"${monthly_payment:,.2f}",
                help="Estimated principal and interest payment (excluding taxes and insurance)"
            )
        
        # Additional context based on credit score
        st.subheader("Additional Considerations")
        if credit_score == "Excellent (750+)":
            st.success("With your excellent credit score, you're likely to qualify for the best interest rates and loan terms.")
        elif credit_score == "Good (700-749)":
            st.info("Your good credit score should help you qualify for competitive rates, though they may be slightly higher than the best available.")
        elif credit_score == "Fair (650-699)":
            st.warning("With a fair credit score, you may face higher interest rates. Consider improving your credit score before applying.")
        else:
            st.error("A credit score below 650 may make it difficult to qualify for a conventional mortgage. Consider FHA loans or working to improve your credit score.")
        
        # Affordability guidelines
        st.subheader("Affordability Guidelines")
        monthly_income = annual_income / 12
        housing_ratio = monthly_payment / monthly_income * 100
        dti_ratio = (monthly_payment + monthly_debts) / monthly_income * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Housing Ratio",
                f"{housing_ratio:.1f}%",
                help="Monthly payment as percentage of monthly income (should be under 28%)"
            )
        with col2:
            st.metric(
                "Debt-to-Income Ratio",
                f"{dti_ratio:.1f}%",
                help="Total monthly debts as percentage of monthly income (should be under 43%)"
            )

if __name__ == "__main__":
    main()
