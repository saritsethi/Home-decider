# Home Decision Helper

## Overview
A Streamlit-based web application that helps users make informed decisions about buying or renting a home. It provides financial calculators, neighborhood comparisons, a lifestyle quiz, and personalized PDF reports.

## Recent Changes (2026-03-26)
Comprehensive 25-bug audit completed and all issues fixed:

**Critical fixes:**
- Database no longer drops `quiz_results` table on restart (changed to `CREATE TABLE IF NOT EXISTS`)
- Division by zero at 0% interest rate guarded in all mortgage/rent-vs-buy calculations
- Division by zero at $0 income guarded in Mortgage Calculator
- Negative mortgage warning shown when debts exceed 43% of income
- PDF reports now use UUID filenames to prevent concurrent-user race conditions

**Calculation fixes:**
- Home appreciation and opportunity cost of down payment now fully included in Rent vs Buy comparison
- Affordability filter in report generator now compares listing prices to budget (not a no-op formula)
- All lifestyle quiz sliders (nightlife, shopping, outdoor, quiet, housing type) now directly influence neighborhood matching
- Match scores are always 0-100 (fixed denominator scaling)
- Quiz report uses the user's actual interest rate (was hardcoded at 6%)
- Monthly expenses now subtract from income before calculating affordability
- Credit score in Mortgage Calculator now adjusts the interest rate numerically (0–1.5% premium)

**Data quality fixes:**
- All 27 neighborhoods now have 6 real scored fields: `safety_score`, `nightlife_score`, `dining_score`, `outdoor_score`, `quiet_score`, `shopping_score`
- Historical property values are now deterministic (seeded by base price), not random
- Home insurance scales with home value (0.1%/yr) instead of hardcoded $100/mo
- HOA hardcode removed; maintenance % field help text now mentions HOA inclusion

**UX fixes:**
- "My Report" page added to sidebar navigation
- Current rent defaults to $1,800 (was $0 which biased recommendation to RENT)
- Family size validated: adults + children must equal total
- Down payment > home price now shows an error
- Property listing expanders default to collapsed
- Radar chart uses real `dining_score` and `safety_score` values

**Dead code removed:**
- `calculate_monthly_ownership_costs()` removed
- `calculate_mortgage_payment()` removed
- `get_db_connection()` removed
- `numpy` import removed from `mortgage_calculator.py`

## Live Data Integrations (`utils/live_data.py`)

### Always Active (no key required)
- **OpenStreetMap / Overpass API** — Real walkability & transit scores per neighborhood (counts amenities + transit stops within 1 km, 7-day cache)
- **BLS CPI API** — National rent CPI (series `CUSR0000SEHA`) × city baseline median 2BR rents → live rent estimate (24-hr cache)

### Key-Activated
- **FRED API** (`FRED_API_KEY`) — Live 30-yr/15-yr Freddie Mac mortgage rates + Case-Shiller city HPI history (24-hr cache)
- **Google Places API** (`GOOGLE_PLACES_API_KEY`) — Real dining, nightlife, shopping, outdoor scores from place counts in 1 km radius (7-day cache)
- **Walk Score API** (`WALK_SCORE_API_KEY`) — Walk Score + Transit Score (7-day cache; falls back to Overpass when absent)
- **RentCast API** (`RENTCAST_API_KEY`) — Live median market rent by city (24-hr cache; falls back to BLS estimate when absent)

### Fallback Chain
- Walkability/transit: Walk Score API → Overpass API (always works)
- Market rent: RentCast → BLS CPI estimate (always works)

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
  navigation.py                  # Sidebar navigation (all 6 pages including My Report)
  inputs.py                      # Reusable form input components
utils/
  database.py                    # DB connection pool, neighborhood data, quiz storage
  financial_calculations.py      # Rent vs buy with appreciation + opportunity cost
  report_generator.py            # Affordability calc, neighborhood matching, PDF generation
  visualization.py               # Plotly charts (cost comparison, radar, historical values)
```

### Neighborhood Scores (all 27 neighborhoods have these fields)
Each neighborhood carries: `walkability_score`, `transport_score`, `school_rating`,
`cost_of_living`, `safety_score`, `nightlife_score`, `dining_score`, `outdoor_score`,
`quiet_score`, `shopping_score` — all on a 0–10 scale.

### Supported Locations
- **Illinois**: Chicago (Lincoln Park, Lake View, Wicker Park), Evanston (Downtown, South), Oak Park (Downtown, Frank Lloyd Wright District)
- **New York**: NYC (Upper West Side, Harlem, East Village), Brooklyn (Park Slope, Williamsburg, DUMBO), Queens (Astoria, Long Island City, Forest Hills)
- **California**: San Francisco (Pacific Heights, Mission District, Sunset District), Los Angeles (Silver Lake, Santa Monica, Eagle Rock), San Diego (North Park, La Jolla, Hillcrest)

## User Preferences
- None recorded yet.
