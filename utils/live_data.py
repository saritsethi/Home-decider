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
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    all_tasks = [
        (category, place_type)
        for category, types in category_types.items()
        for place_type in types
    ]
    counts = {cat: 0 for cat in category_types}

    def _fetch(category, place_type):
        try:
            resp = requests.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params={"location": location, "radius": 1000, "type": place_type, "key": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            return category, len(resp.json().get("results", []))
        except Exception:
            return category, 0

    with ThreadPoolExecutor(max_workers=len(all_tasks)) as executor:
        futures = {executor.submit(_fetch, cat, ptype): (cat, ptype) for cat, ptype in all_tasks}
        for future in as_completed(futures):
            cat, n = future.result()
            counts[cat] += n

    scores = {cat: min(10.0, round(n / 2.0, 1)) for cat, n in counts.items()}
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


# ── US-wide expansion: geocoding + dynamic neighborhood builder ───────────────

# Median home prices by state (2024 estimates, Zillow/Census ACS)
STATE_MEDIAN_HOME_PRICES = {
    "Alabama": 215000, "Alaska": 355000, "Arizona": 365000, "Arkansas": 195000,
    "California": 680000, "Colorado": 495000, "Connecticut": 370000, "Delaware": 330000,
    "Florida": 415000, "Georgia": 320000, "Hawaii": 820000, "Idaho": 395000,
    "Illinois": 285000, "Indiana": 245000, "Iowa": 215000, "Kansas": 230000,
    "Kentucky": 220000, "Louisiana": 225000, "Maine": 360000, "Maryland": 415000,
    "Massachusetts": 570000, "Michigan": 245000, "Minnesota": 320000, "Mississippi": 190000,
    "Missouri": 230000, "Montana": 415000, "Nebraska": 250000, "Nevada": 395000,
    "New Hampshire": 445000, "New Jersey": 475000, "New Mexico": 290000, "New York": 420000,
    "North Carolina": 325000, "North Dakota": 255000, "Ohio": 235000, "Oklahoma": 220000,
    "Oregon": 460000, "Pennsylvania": 290000, "Rhode Island": 435000, "South Carolina": 305000,
    "South Dakota": 295000, "Tennessee": 345000, "Texas": 315000, "Utah": 495000,
    "Vermont": 390000, "Virginia": 385000, "Washington": 535000, "West Virginia": 180000,
    "Wisconsin": 275000, "Wyoming": 340000,
}

# Median 2BR monthly rent by state (2024 estimates)
STATE_MEDIAN_RENT = {
    "Alabama": 1100, "Alaska": 1500, "Arizona": 1650, "Arkansas": 1000,
    "California": 2800, "Colorado": 1950, "Connecticut": 1700, "Delaware": 1600,
    "Florida": 1900, "Georgia": 1600, "Hawaii": 2800, "Idaho": 1500,
    "Illinois": 1550, "Indiana": 1200, "Iowa": 1050, "Kansas": 1100,
    "Kentucky": 1100, "Louisiana": 1150, "Maine": 1500, "Maryland": 1950,
    "Massachusetts": 2400, "Michigan": 1200, "Minnesota": 1500, "Mississippi": 1000,
    "Missouri": 1150, "Montana": 1400, "Nebraska": 1150, "Nevada": 1700,
    "New Hampshire": 1800, "New Jersey": 2200, "New Mexico": 1300, "New York": 2200,
    "North Carolina": 1500, "North Dakota": 1150, "Ohio": 1150, "Oklahoma": 1100,
    "Oregon": 1800, "Pennsylvania": 1400, "Rhode Island": 1800, "South Carolina": 1450,
    "South Dakota": 1150, "Tennessee": 1500, "Texas": 1550, "Utah": 1700,
    "Vermont": 1600, "Virginia": 1800, "Washington": 2100, "West Virginia": 900,
    "Wisconsin": 1300, "Wyoming": 1300,
}

# Map each state to its nearest Case-Shiller metro FRED series
STATE_TO_FRED_SERIES = {
    "Alabama": "ATXRSA", "Alaska": "SFXRSA", "Arizona": "PHXXRSA",
    "Arkansas": "DAXRSA", "California": "SFXRSA", "Colorado": "DNXRSA",
    "Connecticut": "NYXRSA", "Delaware": "PHXRSA", "Florida": "TPXRSA",
    "Georgia": "ATXRSA", "Hawaii": "SFXRSA", "Idaho": "PDXRSA",
    "Illinois": "CHXRSA", "Indiana": "CHXRSA", "Iowa": "CHXRSA",
    "Kansas": "DAXRSA", "Kentucky": "CHXRSA", "Louisiana": "DAXRSA",
    "Maine": "BOXRSA", "Maryland": "DCXRSA", "Massachusetts": "BOXRSA",
    "Michigan": "DTXRSA", "Minnesota": "MNXRSA", "Mississippi": "ATXRSA",
    "Missouri": "CHXRSA", "Montana": "PDXRSA", "Nebraska": "MNXRSA",
    "Nevada": "LVXRSA", "New Hampshire": "BOXRSA", "New Jersey": "NYXRSA",
    "New Mexico": "DAXRSA", "New York": "NYXRSA", "North Carolina": "CHAXRSA",
    "North Dakota": "MNXRSA", "Ohio": "CLEXRSA", "Oklahoma": "DAXRSA",
    "Oregon": "PDXRSA", "Pennsylvania": "PHXRSA", "Rhode Island": "BOXRSA",
    "South Carolina": "CHAXRSA", "South Dakota": "MNXRSA", "Tennessee": "ATXRSA",
    "Texas": "DAXRSA", "Utah": "DNXRSA", "Vermont": "BOXRSA",
    "Virginia": "DCXRSA", "Washington": "WDXRSA", "West Virginia": "DCXRSA",
    "Wisconsin": "MNXRSA", "Wyoming": "DNXRSA",
}

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_HEADERS = {"User-Agent": "HomeDecisionHelper/1.0 (contact@homedecisionhelper.app)"}


def _parse_nominatim_result(r, fallback_name=""):
    """Parse a single Nominatim result dict into our standard geo dict."""
    addr = r.get("address", {})
    city = (addr.get("city") or addr.get("town") or
            addr.get("village") or addr.get("county", ""))
    state = addr.get("state", "")
    neighborhood = (addr.get("neighbourhood") or addr.get("suburb") or
                    fallback_name.split(",")[0].strip())
    return {
        "lat": float(r["lat"]),
        "lon": float(r["lon"]),
        "display_name": r.get("display_name", fallback_name),
        "city": city,
        "state": state,
        "neighborhood": neighborhood,
    }


@st.cache_data(ttl=86400 * 30)
def search_locations(query, limit=5):
    """
    Search for up to `limit` US locations matching `query` using Nominatim.
    No API key required. Returns a list of geo dicts (may be empty).
    Cached for 30 days.
    Each dict: {lat, lon, display_name, city, state, neighborhood}
    """
    try:
        resp = requests.get(
            _NOMINATIM_URL,
            params={"q": query + ", USA", "format": "json", "limit": limit,
                    "countrycodes": "us", "addressdetails": 1},
            headers=_NOMINATIM_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        return [_parse_nominatim_result(r, query) for r in results]
    except Exception:
        return []


@st.cache_data(ttl=86400 * 30)
def geocode_location(query):
    """
    Geocode any US address/neighborhood/city using Nominatim — returns the single
    best match as a geo dict, or None. Cached for 30 days.
    """
    results = search_locations(query, limit=1)
    return results[0] if results else None


@st.cache_data(ttl=86400 * 7)
def get_overpass_walk_scores_by_coords(lat, lon):
    """
    Fetch walkability and transit scores from Overpass API using explicit coordinates.
    No API key required. Cached for 7 days.
    Returns dict: {walkability, transit, source} on 0–10 scale, or None.
    """
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


@st.cache_data(ttl=86400 * 7)
def get_live_places_scores_by_coords(lat, lon):
    """
    Fetch dining, nightlife, shopping, outdoor scores from Google Places API
    using explicit coordinates. Cached for 7 days.
    Returns dict: {dining, nightlife, shopping, outdoor} on 0–10 scale, or None.
    """
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return None
    location = f"{lat},{lon}"
    category_types = {
        "dining":    ["restaurant", "cafe"],
        "nightlife": ["bar", "night_club"],
        "shopping":  ["shopping_mall", "clothing_store", "grocery_or_supermarket"],
        "outdoor":   ["park"],
    }
    all_tasks = [
        (category, place_type)
        for category, types in category_types.items()
        for place_type in types
    ]
    counts = {cat: 0 for cat in category_types}

    def _fetch2(category, place_type):
        try:
            resp = requests.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params={"location": location, "radius": 1000, "type": place_type, "key": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            return category, len(resp.json().get("results", []))
        except Exception:
            return category, 0

    with ThreadPoolExecutor(max_workers=len(all_tasks)) as executor:
        futures = {executor.submit(_fetch2, cat, ptype): (cat, ptype) for cat, ptype in all_tasks}
        for future in as_completed(futures):
            cat, n = future.result()
            counts[cat] += n

    scores = {cat: min(10.0, round(n / 2.0, 1)) for cat, n in counts.items()}
    return scores if scores else None


@st.cache_data(ttl=86400)
def get_live_price_history_by_series(series_id, base_price):
    """
    Fetch 5-year home price history from any FRED Case-Shiller series, scaled to base_price.
    Returns JSON string or None.
    """
    from datetime import datetime, timedelta
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


def _generate_estimated_listings(base_price, neighborhood_name, state):
    """Generate 3 price-realistic estimated property listings for any US location."""
    import random
    rng = random.Random(hash(f"{neighborhood_name}{state}"))
    listing_types = [("Single Family", 3, 2, 1800), ("Condo", 2, 2, 1100), ("Townhouse", 3, 2, 1500)]
    listings = []
    for i, (ltype, beds, baths, sqft) in enumerate(listing_types):
        factor = rng.uniform(0.88, 1.15)
        price = round(base_price * factor / 1000) * 1000
        address_num = rng.randint(100, 9999)
        street = rng.choice(["Main St", "Oak Ave", "Maple Dr", "Park Blvd", "Cedar Ln"])
        listings.append({
            "address": f"{address_num} {street}, {neighborhood_name}",
            "price": price,
            "beds": beds,
            "baths": baths,
            "sqft": sqft + rng.randint(-200, 300),
            "type": ltype,
            "_estimated": True,
        })
    return listings


def _build_neighborhood_from_geo(geo):
    """
    Internal: build a neighborhood profile dict from a pre-resolved geo dict.
    Shared by both build_dynamic_neighborhood and build_dynamic_neighborhood_from_geo.
    """
    lat, lon = geo["lat"], geo["lon"]
    state = geo["state"]
    city = geo["city"]
    neighborhood_name = geo["neighborhood"]

    # Walkability and transit from Overpass (always available)
    walk = get_overpass_walk_scores_by_coords(lat, lon) or {}
    walkability = walk.get("walkability", 5.0)
    transit = walk.get("transit", 5.0)

    # Dining/nightlife/shopping/outdoor from Google Places (optional)
    places = get_live_places_scores_by_coords(lat, lon) or {}
    dining = places.get("dining", 5.0)
    nightlife = places.get("nightlife", 5.0)
    shopping = places.get("shopping", 5.0)
    outdoor = places.get("outdoor", 5.0)

    # quiet is inverse of nightlife on a 0-10 scale
    quiet = round(max(0.0, 10.0 - nightlife), 1)

    # Base price from state median
    base_price = STATE_MEDIAN_HOME_PRICES.get(state, 350000)

    # Cost of living on 1-10 scale, derived from state median price
    cost_of_living = min(10.0, max(1.0, round((base_price - 150000) / 65000, 1)))

    # FRED historical price data using nearest metro series for this state
    fred_series = STATE_TO_FRED_SERIES.get(state)
    historical_values = None
    if fred_series:
        historical_values = get_live_price_history_by_series(fred_series, base_price)

    # Fallback: generate deterministic historical values
    if not historical_values:
        from utils.database import generate_historical_values
        historical_values = generate_historical_values(base_price)

    # Rent estimate from state baseline
    rent_estimate = STATE_MEDIAN_RENT.get(state, 1500)

    # Property listings (estimated from state median)
    listings = _generate_estimated_listings(base_price, neighborhood_name, state)

    return {
        "name": neighborhood_name,
        "city": city,
        "state": state,
        "walkability_score": walkability,
        "transport_score": transit,
        "school_rating": 6.5,
        "cost_of_living": cost_of_living,
        "safety_score": 6.0,
        "nightlife_score": nightlife,
        "dining_score": dining,
        "outdoor_score": outdoor,
        "quiet_score": quiet,
        "shopping_score": shopping,
        "property_listings": listings,
        "historical_values": historical_values,
        "_is_dynamic": True,
        "_geo": geo,
        "_rent_estimate": rent_estimate,
        "_walk_source": walk.get("source", "OpenStreetMap"),
        "_places_active": bool(places),
        "_fred_series": fred_series,
        "_search_query": geo.get("display_name", neighborhood_name),
    }


@st.cache_data(ttl=3600)
def build_dynamic_neighborhood_from_geo(geo):
    """
    Build a neighborhood profile from a pre-resolved geo dict (e.g. from
    search_locations). Skips geocoding entirely — use this after the user
    has confirmed their location selection.
    Returns a neighborhood dict or None.
    """
    if not geo:
        return None
    return _build_neighborhood_from_geo(geo)


@st.cache_data(ttl=3600)
def build_dynamic_neighborhood(search_query):
    """
    Build a neighborhood profile for any US location by geocoding `search_query`
    and then fetching live scores. Returns a neighborhood dict or None.
    """
    geo = geocode_location(search_query)
    if not geo:
        return None
    return _build_neighborhood_from_geo(geo)
