import numpy as np
import pandas as pd

def calculate_monthly_ownership_costs(home_price):
    # Property tax (annual rate of 1.2% divided by 12)
    monthly_property_tax = (home_price * 0.012) / 12
    # HOA fees
    monthly_hoa = 500
    # Insurance
    monthly_insurance = 100
    # Maintenance (2% annual divided by 12)
    monthly_maintenance = (home_price * 0.02) / 12
    
    return {
        'property_tax': monthly_property_tax,
        'hoa': monthly_hoa,
        'insurance': monthly_insurance,
        'maintenance': monthly_maintenance,
        'total': monthly_property_tax + monthly_hoa + monthly_insurance + monthly_maintenance
    }

def calculate_rent_vs_buy(home_price, down_payment, interest_rate, loan_term, monthly_rent):
    # Calculate mortgage payment
    loan_amount = home_price - down_payment
    monthly_rate = interest_rate / 12 / 100
    n_payments = loan_term * 12
    monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    
    # Get additional ownership costs
    ownership_costs = calculate_monthly_ownership_costs(home_price)
    total_monthly_ownership = monthly_mortgage + ownership_costs['total']
    
    # Calculate 5-year comparison
    months = 60
    buying_costs = []
    renting_costs = []
    rent_amounts = []
    
    # Assume 3% annual rent increase
    for month in range(months):
        rent_increase = (1 + 0.03)**(month/12)
        current_rent = monthly_rent * rent_increase
        rent_amounts.append(current_rent)
        
        # Accumulate costs
        renting_costs.append(current_rent)
        buying_costs.append(total_monthly_ownership)
    
    # Calculate cumulative costs
    cumulative_buying = sum(buying_costs)
    cumulative_renting = sum(rent_amounts)
    
    # Find break-even rent
    break_even_rent = total_monthly_ownership
    
    return {
        'monthly_mortgage': monthly_mortgage,
        'monthly_ownership_costs': ownership_costs,
        'total_monthly_ownership': total_monthly_ownership,
        'five_year_buying_cost': cumulative_buying,
        'five_year_renting_cost': cumulative_renting,
        'break_even_rent': break_even_rent
    }

def calculate_mortgage_payment(principal, annual_rate, years):
    """Calculate monthly mortgage payment."""
    monthly_rate = annual_rate / 12 / 100
    num_payments = years * 12
    return principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
