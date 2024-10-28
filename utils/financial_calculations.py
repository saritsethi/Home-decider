import numpy as np
import pandas as pd

def calculate_mortgage_payment(principal, annual_rate, years):
    """Calculate monthly mortgage payment."""
    monthly_rate = annual_rate / 12 / 100
    num_payments = years * 12
    return principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)

def calculate_rent_vs_buy(
    home_price,
    down_payment,
    interest_rate,
    loan_term,
    monthly_rent,
    property_tax_rate,
    maintenance_cost_percent,
    home_appreciation_rate,
    rent_increase_rate,
    investment_return_rate
):
    """Calculate 5-year projection of renting vs buying."""
    
    # Initial calculations
    loan_amount = home_price - down_payment
    monthly_mortgage = calculate_mortgage_payment(loan_amount, interest_rate, loan_term)
    monthly_property_tax = (home_price * property_tax_rate / 100) / 12
    monthly_maintenance = (home_price * maintenance_cost_percent / 100) / 12
    
    # Initialize results DataFrame
    periods = 60  # 5 years
    results = pd.DataFrame(index=range(periods))
    
    # Calculate monthly costs
    results['Month'] = results.index + 1
    results['Monthly_Mortgage'] = monthly_mortgage
    results['Property_Tax'] = monthly_property_tax
    results['Maintenance'] = monthly_maintenance
    
    # Calculate appreciation and equity
    results['Home_Value'] = [home_price * (1 + home_appreciation_rate/100)**(i/12) for i in range(periods)]
    
    # Calculate rental costs
    results['Monthly_Rent'] = [monthly_rent * (1 + rent_increase_rate/100)**(i/12) for i in range(periods)]
    
    # Calculate cumulative costs
    results['Cumulative_Buying_Costs'] = (results['Monthly_Mortgage'] + 
                                        results['Property_Tax'] + 
                                        results['Maintenance']).cumsum()
    
    results['Cumulative_Rental_Costs'] = results['Monthly_Rent'].cumsum()
    
    # Calculate opportunity cost of down payment
    results['Investment_Value'] = [down_payment * (1 + investment_return_rate/100)**(i/12) for i in range(periods)]
    
    return results
