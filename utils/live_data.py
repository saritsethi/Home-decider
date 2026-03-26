"""
Live data integrations for the Home Decision Helper.
Each function degrades gracefully to None when its API key is unavailable.
Data sources:
  - FRED API        : Live 30yr/15yr mortgage rates + Case-Shiller city HPI
  - Walk Score API  : Real walkability and transit scores per neighborhood (optional key)
  - Overpass API    : Real walkability & transit from OpenStreetMap — NO KEY REQUIRED
  - Google Places   : Real dining, nightlife, shopping, outdoor scores
  - RentCast API    : Live median market rent by city (optional key)
  - BLS API         : National rent CPI + city baselines for rent estimates — NO KEY REQUIRED
"""

import os
import json
import requests
from datetime import datetime, timedelta
import streamlit as st


# ── FRED series identifiers ───────────────────────────────────────────────────
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

CITY_HPI_SERIES = {
    "Chicago": "CHXRSA",       "Evanston": "CHXRSA",    "Oak Park": "CHXRSA",
    "New York City": "NYXRSA", "Brooklyn": "NYXRSA",    "Queens": "NYXRSA",
    "San Francisco": "SFXRSA",
    "Los Angeles": "LXXRSA",
    "San Diego": "SDXRSA",
}

STATE_ABBREVS = {"Illinois": "IL", "New York": "NY", "California": "CA"}

# ── Neighborhood geographic coordinates ──────────────────────────────────────
NEIGHBORHOOD_COORDS = {
    "Lincoln Park":               {"lat": 41.9214, "lon": -87.6351, "address": "Lincoln Park, Chicago, IL"},
    "Lake View":                  {"lat": 41.9484, "lon": -87.6547, "address": "Lake View, Chicago, IL"},
    "Wicker Park":                {"lat": 41.9085, "lon": -87.6771, "address": "Wicker Park, Chicago, IL"},
    "Downtown Evanston":          {"lat": 42.0451, "lon": -87.6877, "address": "Downtown, Evanston, IL"},
    "South Evanston":             {"lat": 42.0123, "lon": -87.6776, "address": "South Evanston, IL"},
    "Downtown Oak Park":          {"lat": 41.8850, "lon": -87.7845, "address": "Downtown, Oak Park, IL"},
    "Frank Lloyd Wright District":{"lat": 41.8860, "lon": -87.7978, "address": "Frank Lloyd Wright District, Oak Park, IL"},
    "Upper West Side":            {"lat": 40.7870, "lon": -73.9754, "address": "Upper West Side, New York, NY"},
    "Harlem":                     {"lat": 40.8116, "lon": -73.9465, "address": "Harlem, New York, NY"},
    "East Village":               {"lat": 40.7265, "lon": -73.9815, "address": "East Village, New York, NY"},
    "Park Slope":                 {"lat": 40.6782, "lon": -73.9775, "address": "Park Slope, Brooklyn, NY"},
    "Williamsburg":               {"lat": 40.7081, "lon": -73.9571, "address": "Williamsburg, Brooklyn, NY"},
    "DUMBO":                      {"lat": 40.7033, "lon": -73.9881, "address": "DUMBO, Brooklyn, NY"},
    "Astoria":                    {"lat": 40.7721, "lon": -73.9302, "address": "Astoria, Queens, NY"},
    "Long Island City":           {"lat": 40.7447, "lon": -73.9485, "address": "Long Island City, Queens, NY"},
    "Forest Hills":               {"lat": 40.7178, "lon": -73.8448, "address": "Forest Hills, Queens, NY"},
    "Pacific Heights":            {"lat": 37.7925, "lon": -122.4382, "address": "Pacific Heights, San Francisco, CA"},
    "Mission District":           {"lat": 37.7599, "lon": -122.4148, "address": "Mission District, San Francisco, CA"},
    "Sunset District":            {"lat": 37.7558, "lon": -122.4832, "address": "Sunset District, San Francisco, CA"},
    "Silver Lake":                {"lat": 34.0874, "lon": -118.2743, "address": "Silver Lake, Los Angeles, CA"},
    "Santa Monica":               {"lat": 34.0195, "lon": -118.4912, "address": "Santa Monica, CA"},
    "Eagle Rock":                 {"lat": 34.1397, "lon": -118.2102, "address": "Eagle Rock, Los Angeles, CA"},
    "North Park":                 {"lat": 32.7484, "lon": -117.1299, "address": "North Park, San Diego, CA"},
    "La Jolla":                   {"lat": 32.8328, "lon": -117.2713, "address": "La Jolla, San Diego, CA"},
    "Hillcrest":                  {"lat": 32.7470, "lon": -117.1602, "address": "Hillcrest, San Diego, CA"},
}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _fred_fetch(series_id, **params):
    """Raw FRED API call. Returns list of observations or None on any failure."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        return None
    try:
        resp = requests.get(FRED_BASE, params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            **params,
        }, timeout=10)
        resp.raise_for_status()
        return resp.json().get("observations", [])
    except Exception:
        return None


# ── Public API functions ──────────────────────────────────────────────────────

@st.cache_data(ttl=86400)
def get_live_mortgage_rates():
    """
    Fetch current 30-year and 15-year fixed mortgage rates from FRED.
    Returns dict with keys: rate_30yr, rate_15yr (optional), as_of — or None.
    Cached for 24 hours.
    """
    obs_30 = _fred_fetch("MORTGAGE30US", sort_order="desc", limit=1)
    if not obs_30:
        return None

    obs_15 = _fred_fetch("MORTGAGE15US", sort_order="desc", limit=1)
    result = {}

    if obs_30[0]["value"] != ".":
        result["rate_30yr"] = float(obs_30[0]["value"])
        result["as_of"] = obs_30[0]["date"]

    if obs_15 and obs_15[0]["value"] != ".":
        result["rate_15yr"] = float(obs_15[0]["value"])

    return result if result else None


@st.cache_data(ttl=86400)
def get_live_price_history(city, base_price):
    """
    Fetch 5-year city-level home price history from FRED Case-Shiller indices,
    scaled to the neighborhood's base_price. Returns JSON string or None.
    Cached for 24 hours.
    """
    series_id = CITY_HPI_SERIES.get(city)
    if not series_id:
        return None

    five_years_ago = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
    obs = _fred_fetch(series_id, observation_start=five_years_ago, sort_order="asc")

    if not obs or len(obs) < 2:
        return None

    valid = [(o["date"], float(o["value"])) for o in obs if o["value"] != "."]
    if len(valid) < 2:
        return None

    anchor = valid[-1][1]
    history = [
        {"date": date, "value": round(base_price * (idx / anchor), 2)}
        for date, idx in valid
    ]
    return json.dumps(history)


@st.cache_data(ttl=86400 * 7)
def get_live_walk_scores(neighborhood_name):
    """
    Fetch Walk Score and Transit Score for a neighborhood.
    Returns dict: {walkability, transit, description} on 0–10 scale, or None.
    Cached for 7 days (scores don't change often).
    """
    api_key = os.environ.get("WALK_SCORE_API_KEY")
    coords = NEIGHBORHOOD_COORDS.get(neighborhood_name)
    if not api_key or not coords:
        return None
    try:
        resp = requests.get("https://api.walkscore.com/score", params={
            "format": "json",
            "address": coords["address"],
            "lat": coords["lat"],
            "lon": coords["lon"],
            "transit": 1,
            "wsapikey": api_key,
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        walk = data.get("walkscore")
        transit_info = data.get("transit", {})
        transit = transit_info.get("score") if isinstance(transit_info, dict) else None

        return {
            "walkability": round(walk / 10, 1) if walk is not None else None,
            "transit": round(transit / 10, 1) if transit is not None else None,
            "description": data.get("description", ""),
        }
    except Exception:
        return None


@st.cache_data(ttl=86400 * 7)
def get_live_places_scores(neighborhood_name):
    """
    Use Google Places Nearby Search to count restaurants, bars, shops, and parks
    within 1 km, converting counts into 0–10 scores.
    Returns dict: {dining, nightlife, shopping, outdoor} or None.
    Cached for 7 days.
    """
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    coords = NEIGHBORHOOD_COORDS.get(neighborhood_name)
    if not api_key or not coords:
        return None

    location = f"{coords['lat']},{coords['lon']}"
    category_types = {
        "dining":    ["restaurant", "cafe"],
        "nightlife": ["bar", "night_club"],
        "shopping":  ["shopping_mall", "clothing_store", "grocery_or_supermarket"],
        "outdoor":   ["park"],
    }

    scores = {}
    for category, types in category_types.items():
        total = 0
        for place_type in types:
            try:
                resp = requests.get(
                    "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                    params={"location": location, "radius": 1000, "type": place_type, "key": api_key},
                    timeout=10,
                )
                resp.raise_for_status()
                total += len(resp.json().get("results", []))
            except Exception:
                pass
        scores[category] = min(10.0, round(total / 2.0, 1))

    return scores if scores else None


@st.cache_data(ttl=86400)
def get_live_market_rent(city, state):
    """
    Fetch median 2-bedroom monthly rent from RentCast.
    Returns float or None.
    Cached for 24 hours.
    """
    api_key = os.environ.get("RENTCAST_API_KEY")
    if not api_key:
        return None
    state_abbrev = STATE_ABBREVS.get(state, state[:2].upper())
    try:
        resp = requests.get(
            "https://api.rentcast.io/v1/markets",
            params={"city": city, "state": state_abbrev, "propertyType": "Apartment"},
            headers={"X-Api-Key": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        rent = data.get("rent", {})
        return rent.get("twoBedroomAvgRent") or rent.get("averageRent")
    except Exception:
        return None


# ── City rent baselines (2024/25 median 2BR, sourced from Census ACS & Zillow) ──
_CITY_MEDIAN_2BR_RENT = {
    "Chicago": 1950,       "Evanston": 1800,       "Oak Park": 1700,
    "New York City": 3200, "Brooklyn": 2800,        "Queens": 2300,
    "San Francisco": 3400, "Los Angeles": 2800,     "San Diego": 2700,
}

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_BLS_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/CUSR0000SEHA"


@st.cache_data(ttl=86400 * 7)
def get_overpass_walk_scores(neighborhood_name):
    """
    Fetch walkability and transit scores from OpenStreetMap via the Overpass API.
    No API key required. Counts transit stops and walkable amenities within 1 km.
    Returns dict: {walkability, transit} on 0–10 scale, or None on failure.
    Cached for 7 days.
    """
    coords = NEIGHBORHOOD_COORDS.get(neighborhood_name)
    if not coords:
        return None

    lat, lon = coords["lat"], coords["lon"]
    query = (
        f"[out:json][timeout:25];"
        f"("
        f"node[\"public_transport\"=\"stop_position\"](around:1000,{lat},{lon});"
        f"node[\"highway\"=\"bus_stop\"](around:1000,{lat},{lon});"
        f"node[\"railway\"=\"station\"](around:1000,{lat},{lon});"
        f"node[\"railway\"=\"stop\"](around:1000,{lat},{lon});"
        f"node[\"amenity\"~\"restaurant|cafe|bar|supermarket|pharmacy\"](around:1000,{lat},{lon});"
        f"node[\"shop\"](around:1000,{lat},{lon});"
        f"node[\"leisure\"=\"park\"](around:1000,{lat},{lon});"
        f");"
        f"out tags;"
    )
    try:
        resp = requests.post(_OVERPASS_URL, data={"data": query}, timeout=30)
        resp.raise_for_status()
        if not resp.text.strip():
            return None
        elements = resp.json().get("elements", [])
        if not elements:
            return None

        transit_tags = {"public_transport", "highway", "railway"}
        transit_count = sum(
            1 for e in elements
            if any(k in e.get("tags", {}) for k in transit_tags)
            and (
                e.get("tags", {}).get("public_transport") == "stop_position"
                or e.get("tags", {}).get("highway") == "bus_stop"
                or e.get("tags", {}).get("railway") in ("station", "stop")
            )
        )
        amenity_count = len(elements) - transit_count

        return {
            "walkability": min(10.0, round(amenity_count / 15.0, 1)),
            "transit":     min(10.0, round(transit_count / 3.0, 1)),
            "source":      "OpenStreetMap (Overpass)",
        }
    except Exception:
        return None


@st.cache_data(ttl=86400)
def get_bls_rent_estimate(city):
    """
    Estimate current median 2BR rent using BLS national rent CPI (no API key required)
    scaled against a city-specific 2024/25 median rent baseline from Census ACS.
    Returns float or None.
    Cached for 24 hours.
    """
    baseline = _CITY_MEDIAN_2BR_RENT.get(city)
    if not baseline:
        return None
    try:
        resp = requests.get(_BLS_URL, timeout=15)
        resp.raise_for_status()
        series_data = resp.json().get("Results", {}).get("series", [{}])[0].get("data", [])
        if len(series_data) < 13:
            return baseline

        current = series_data[0]
        current_cpi = float(current["value"])
        year_ago = next(
            (d for d in series_data
             if int(d["year"]) == int(current["year"]) - 1
             and d["period"] == current["period"]),
            None,
        )
        if not year_ago:
            return baseline

        yoy_factor = current_cpi / float(year_ago["value"])
        return round(baseline * yoy_factor, -1)
    except Exception:
        return baseline


def get_live_walk_scores_with_fallback(neighborhood_name):
    """
    Try Walk Score API first (if key present), then fall back to Overpass (no key needed).
    Returns dict: {walkability, transit, source, description?} or None.
    """
    ws = get_live_walk_scores(neighborhood_name)
    if ws:
        ws["source"] = "Walk Score API"
        return ws
    return get_overpass_walk_scores(neighborhood_name)


def get_live_market_rent_with_fallback(city, state):
    """
    Try RentCast first (if key present), then fall back to BLS CPI estimate (no key needed).
    Returns float or None.
    """
    rent = get_live_market_rent(city, state)
    if rent:
        return rent, "RentCast"
    estimate = get_bls_rent_estimate(city)
    if estimate:
        return estimate, "BLS CPI estimate"
    return None, None


def live_data_status():
    """Return a dict of {source_name: is_active} for all integrations."""
    return {
        "FRED (mortgage rates & price history)": bool(os.environ.get("FRED_API_KEY")),
        "OpenStreetMap / Overpass (walkability)": True,
        "BLS CPI (rent estimates)":              True,
        "Walk Score (walkability & transit)":    bool(os.environ.get("WALK_SCORE_API_KEY")),
        "Google Places (dining, nightlife, shopping)": bool(os.environ.get("GOOGLE_PLACES_API_KEY")),
        "RentCast (live market rents)":          bool(os.environ.get("RENTCAST_API_KEY")),
    }
