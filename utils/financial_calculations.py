import pandas as pd


def calculate_rent_vs_buy(home_price, down_payment, interest_rate, loan_term, monthly_rent,
                          property_tax_rate=1.2, maintenance_cost_percent=1.0,
                          home_appreciation_rate=3.0, rent_increase_rate=2.0,
                          investment_return_rate=7.0):
    loan_amount = home_price - down_payment
    monthly_rate = interest_rate / 12 / 100
    n_payments = loan_term * 12

    if monthly_rate > 0:
        monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    else:
        monthly_mortgage = loan_amount / n_payments if n_payments > 0 else 0

    monthly_property_tax = (home_price * property_tax_rate / 100) / 12
    monthly_insurance = (home_price * 0.001) / 12
    monthly_maintenance = (home_price * maintenance_cost_percent / 100) / 12

    monthly_opportunity_cost = down_payment * ((1 + investment_return_rate / 100) ** (1 / 12) - 1)

    months = 60
    month_list = []
    cumulative_buying = []
    cumulative_renting = []
    total_buy = 0
    total_rent = 0
    current_home_value = home_price

    for month in range(1, months + 1):
        monthly_appreciation = current_home_value * ((1 + home_appreciation_rate / 100) ** (1 / 12) - 1)
        current_home_value *= (1 + home_appreciation_rate / 100) ** (1 / 12)

        gross_buy_cost = (monthly_mortgage + monthly_property_tax +
                          monthly_insurance + monthly_maintenance + monthly_opportunity_cost)
        net_buy_cost = gross_buy_cost - monthly_appreciation
        total_buy += net_buy_cost

        rent_increase = (1 + rent_increase_rate / 100) ** ((month - 1) / 12)
        current_rent = monthly_rent * rent_increase
        total_rent += current_rent

        month_list.append(month)
        cumulative_buying.append(total_buy)
        cumulative_renting.append(total_rent)

    return pd.DataFrame({
        'Month': month_list,
        'Cumulative_Buying_Costs': cumulative_buying,
        'Cumulative_Rental_Costs': cumulative_renting
    })
