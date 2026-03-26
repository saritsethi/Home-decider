"""
Live data integrations for the Home Decision Helper.
Each function degrades gracefully to None when its API key is unavailable.
Data sources:
  - FRED API        : Live 30yr/15yr mortgage rates + Case-Shiller city HPI
  - Walk Score API  : Real walkability and transit scores per neighborhood
  - Google Places   : Real dining, nightlife, shopping, outdoor scores
  - RentCast API    : Live median market rent by city
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


def live_data_status():
    """Return a dict of {source_name: is_active} for all integrations."""
    return {
        "FRED (mortgage rates & price history)": bool(os.environ.get("FRED_API_KEY")),
        "Walk Score (walkability & transit)":    bool(os.environ.get("WALK_SCORE_API_KEY")),
        "Google Places (dining, nightlife, shopping)": bool(os.environ.get("GOOGLE_PLACES_API_KEY")),
        "RentCast (market rents)":               bool(os.environ.get("RENTCAST_API_KEY")),
    }
