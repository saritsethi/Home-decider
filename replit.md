# Home Decision Helper

## Overview
A Streamlit-based web application that helps users make informed decisions about buying or renting a home. It provides financial calculators, neighborhood comparisons, a lifestyle quiz, and personalized PDF reports.

## Recent Changes
- 2026-02-11: Fixed Rent vs Buy calculator function signature mismatch (was passing 10 args to 5-param function). Now returns a DataFrame with Month, Cumulative_Buying_Costs, Cumulative_Rental_Costs columns.
- 2026-02-11: Expanded neighborhood data from only Chicago (2 neighborhoods) to all 9 supported cities across 3 states with 2-3 neighborhoods each.
- 2026-02-11: Wired up the historical property value chart to display in Neighborhood Comparison and Report Display pages.

## Project Architecture
- **Framework**: Streamlit (Python)
- **Database**: PostgreSQL (Neon-backed) for storing quiz results
- **PDF Generation**: ReportLab
- **Visualizations**: Plotly (line charts, radar charts)

### File Structure
```
main.py                          # Home page with hero section and feature cards
pages/
  rent_vs_buy.py                 # Rent vs Buy cost comparison calculator
  mortgage_calculator.py         # Mortgage pre-qualification calculator
  neighborhood_comparison.py     # Compare neighborhoods with radar + historical charts
  lifestyle_quiz.py              # 3-step quiz: family, finances, lifestyle preferences
  report_display.py              # Personalized report with PDF download
components/
  navigation.py                  # Sidebar navigation
  inputs.py                      # Reusable form input components
utils/
  database.py                    # DB connection pool, neighborhood data, quiz storage
  financial_calculations.py      # Rent vs buy, mortgage payment calculations
  report_generator.py            # Affordability calc, neighborhood matching, PDF generation
  visualization.py               # Plotly charts (cost comparison, radar, historical values)
```

### Supported Locations
- **Illinois**: Chicago (Lincoln Park, Lake View, Wicker Park), Evanston (Downtown, South), Oak Park (Downtown, Frank Lloyd Wright District)
- **New York**: NYC (Upper West Side, Harlem, East Village), Brooklyn (Park Slope, Williamsburg, DUMBO), Queens (Astoria, Long Island City, Forest Hills)
- **California**: San Francisco (Pacific Heights, Mission District, Sunset District), Los Angeles (Silver Lake, Santa Monica, Eagle Rock), San Diego (North Park, La Jolla, Hillcrest)

## User Preferences
- None recorded yet.
