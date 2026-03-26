# 🏠 Home Decision Helper

A Streamlit web application that helps users make smarter, data-driven decisions about buying or renting a home. It combines live market data, financial calculators, neighborhood analysis, and a personalized lifestyle quiz to produce a tailored recommendation and downloadable PDF report.

---

## Features

### 1. Rent vs. Buy Calculator
Compare the true long-term cost of renting vs. buying over a 5-year horizon.
- Month-by-month cumulative cost chart
- Factors in home appreciation, opportunity cost of the down payment, property tax, maintenance, insurance (scaled to home value), and annual rent increases
- Division-by-zero safe at 0% interest rate
- Live 30-yr mortgage rate pre-filled from FRED / Freddie Mac

### 2. Mortgage Pre-Qualification Calculator
Estimate how much home you can afford using standard 43% DTI lending guidelines.
- Credit score adjusts the interest rate numerically (0–1.5% premium)
- Shows housing ratio and DTI ratio with pass/fail indicators
- Warns when debts already exceed the 43% limit
- Live 30-yr and 15-yr rates displayed as metrics, pre-filled as defaults

### 3. Neighborhood Comparison Tool
Compare up to 3 neighborhoods side-by-side on a radar chart and score table.
- 10 scored dimensions: walkability, transit, safety, dining, nightlife, outdoor, shopping, schools, cost of living
- 5-year historical property value chart
- Live data automatically overlaid when API keys are configured (Walk Score, Google Places, FRED Case-Shiller)
- Falls back gracefully to curated scores when API keys are absent

### 4. Lifestyle Quiz (3-step)
A guided quiz that generates a personalized neighborhood match report.
- **Step 1** — Family composition (adults, children, total with validation)
- **Step 2** — Financial details (income, savings, target price, down payment, interest rate)
- **Step 3** — Lifestyle preferences (urban/suburban, transport, nightlife, outdoor, quiet, shopping sliders)
- Shows live median 2BR rent for the selected city (BLS CPI estimate)

### 5. Personalized Report
Generated from quiz results with:
- Buy vs. Rent recommendation based on income, savings, and rate
- Top 3 matching neighborhoods scored against lifestyle preferences (0–100, capped)
- Affordability filter: only neighborhoods within budget are shown
- Property listings within each recommended neighborhood
- PDF download with UUID filename (safe for concurrent users)

### 6. My Report
Saved report accessible from the sidebar at any time after completing the quiz.

---

## Live Data Sources

| Source | Key Required | Updates | Powers |
|--------|-------------|---------|--------|
| **FRED / Freddie Mac** | `FRED_API_KEY` (free) | Weekly | 30-yr & 15-yr mortgage rates, Case-Shiller city HPI charts |
| **Google Places API** | `GOOGLE_PLACES_API_KEY` | 7 days | Dining, nightlife, shopping, outdoor scores (place counts within 1 km) |
| **OpenStreetMap / Overpass** | None — always on | 7 days | Walkability & transit scores from real OSM node counts |
| **BLS CPI** | None — always on | Daily | National rent CPI × city median baseline → live 2BR rent estimate |
| **Walk Score API** | `WALK_SCORE_API_KEY` (free tier) | 7 days | Official Walk Score & Transit Score (falls back to Overpass) |
| **RentCast** | `RENTCAST_API_KEY` | Daily | Live market rent by city (falls back to BLS estimate) |

All live data functions use Streamlit caching (24-hour or 7-day TTL) and degrade gracefully — the app works fully without any API keys.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | [Streamlit](https://streamlit.io) |
| Database | PostgreSQL (Neon-backed, via `DATABASE_URL`) |
| PDF Generation | ReportLab |
| Charts | Plotly (line charts, radar charts) |
| HTTP | requests |
| Testing | pytest (69 tests) |

---

## Project Structure

```
main.py                          # Home page — hero section, feature cards, live data status
pages/
  rent_vs_buy.py                 # Rent vs Buy cost comparison calculator
  mortgage_calculator.py         # Mortgage pre-qualification with live rate display
  neighborhood_comparison.py     # Neighborhood radar + historical value chart
  lifestyle_quiz.py              # 3-step quiz: family → finances → lifestyle
  report_display.py              # Personalized report + PDF download
components/
  navigation.py                  # Sidebar navigation (all 6 pages)
  inputs.py                      # Reusable form inputs (financial, neighborhood selectors)
utils/
  database.py                    # DB connection pool, 25-neighborhood data, quiz storage
  financial_calculations.py      # Rent vs buy with appreciation + opportunity cost
  report_generator.py            # Affordability filter, neighborhood matching, PDF generation
  visualization.py               # Plotly charts (cost comparison, radar, historical values)
  live_data.py                   # All live API integrations with graceful fallbacks
tests/
  test_suite.py                  # 69 pytest tests covering all calculations and data integrity
```

---

## Supported Locations

**Illinois**
- Chicago: Lincoln Park, Lake View, Wicker Park
- Evanston: Downtown, South
- Oak Park: Downtown, Frank Lloyd Wright District

**New York**
- New York City: Upper West Side, Harlem, East Village
- Brooklyn: Park Slope, Williamsburg, DUMBO
- Queens: Astoria, Long Island City, Forest Hills

**California**
- San Francisco: Pacific Heights, Mission District, Sunset District
- Los Angeles: Silver Lake, Santa Monica, Eagle Rock
- San Diego: North Park, La Jolla, Hillcrest

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/saritsethi/Home-decider.git
cd Home-decider
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Set the following in your environment or a `.env` file:

```bash
# Required — PostgreSQL database
DATABASE_URL=your_postgres_connection_string

# Optional — enables live mortgage rates and HPI charts
FRED_API_KEY=your_fred_api_key          # free at fred.stlouisfed.org

# Optional — enables real dining/nightlife/shopping scores
GOOGLE_PLACES_API_KEY=your_key          # Google Cloud Console

# Optional — upgrades walkability scores (falls back to OpenStreetMap)
WALK_SCORE_API_KEY=your_key             # free at walkscore.com/professional/api.php

# Optional — upgrades rent estimates (falls back to BLS CPI)
RENTCAST_API_KEY=your_key               # app.rentcast.io
```

### 4. Run the app
```bash
streamlit run main.py
```

### 5. Run the test suite
```bash
pytest tests/test_suite.py -v
```

---

## Test Coverage

69 tests across 7 categories — all passing:

| Category | Tests |
|----------|-------|
| Rent vs Buy calculations | 8 |
| Mortgage pre-qualification | 6 |
| Affordability calculations | 5 |
| Report generation & matching | 12 |
| Neighborhood data integrity | 15 |
| Visualization (Plotly charts) | 8 |
| Input validation & dead code checks | 15 |

---

## API Key Registration Links

| Key | Where to get it | Cost |
|-----|----------------|------|
| `FRED_API_KEY` | [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html) | Free |
| `GOOGLE_PLACES_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/) → Enable Places API | Pay-per-use (free monthly credit) |
| `WALK_SCORE_API_KEY` | [walkscore.com/professional/api.php](https://www.walkscore.com/professional/api.php) | Free up to 5,000/day |
| `RENTCAST_API_KEY` | [app.rentcast.io/app/api-keys](https://app.rentcast.io/app/api-keys) | Free tier available |

---

## License

MIT
