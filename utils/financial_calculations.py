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

def calculate_rent_vs_buy(home_price, down_payment, interest_rate, loan_term, monthly_rent,
                          property_tax_rate=1.2, maintenance_cost_percent=1.0,
                          home_appreciation_rate=3.0, rent_increase_rate=2.0,
                          investment_return_rate=7.0):
    loan_amount = home_price - down_payment
    monthly_rate = interest_rate / 12 / 100
    n_payments = loan_term * 12
    monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)

    monthly_property_tax = (home_price * property_tax_rate / 100) / 12
    monthly_insurance = 100
    monthly_hoa = 500
    monthly_maintenance = (home_price * maintenance_cost_percent / 100) / 12

    months = 60
    month_list = []
    cumulative_buying = []
    cumulative_renting = []
    total_buy = 0
    total_rent = 0

    for month in range(1, months + 1):
        buy_cost = monthly_mortgage + monthly_property_tax + monthly_insurance + monthly_hoa + monthly_maintenance
        total_buy += buy_cost

        rent_increase = (1 + rent_increase_rate / 100) ** ((month - 1) / 12)
        current_rent = monthly_rent * rent_increase
        total_rent += current_rent

        month_list.append(month)
        cumulative_buying.append(total_buy)
        cumulative_renting.append(total_rent)

    df = pd.DataFrame({
        'Month': month_list,
        'Cumulative_Buying_Costs': cumulative_buying,
        'Cumulative_Rental_Costs': cumulative_renting
    })
    return df

def calculate_mortgage_payment(principal, annual_rate, years):
    """Calculate monthly mortgage payment."""
    monthly_rate = annual_rate / 12 / 100
    num_payments = years * 12
    return principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
