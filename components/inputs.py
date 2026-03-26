import streamlit as st
from utils.database import get_available_states, get_available_cities, get_neighborhood_data
from utils.live_data import get_live_mortgage_rates, search_locations


def location_picker_widget(key, label="Location", placeholder="e.g. South Congress, Austin TX"):
    """
    A reusable 3-phase search-then-confirm location picker widget.

    Phases:
      "search"      — text input + Search button
      "suggestions" — radio list of up to 5 geocoding candidates + Confirm/Back buttons
      "confirmed"   — green confirmation chip + Change button

    Uses Streamlit session state keys prefixed with `key`.
    Returns the confirmed geo dict when the user has confirmed, else None.
    Each geo dict: {lat, lon, display_name, city, state, neighborhood}
    """
    phase_key       = f"{key}_phase"
    query_key       = f"{key}_query"
    suggestions_key = f"{key}_suggestions"
    geo_key         = f"{key}_geo"

    if phase_key not in st.session_state:
        st.session_state[phase_key] = "search"

    phase = st.session_state[phase_key]

    # ── Phase 1: search ──────────────────────────────────────────────────────
    if phase == "search":
        col1, col2 = st.columns([5, 1])
        with col1:
            query = st.text_input(label, placeholder=placeholder, key=query_key)
        with col2:
            st.write("")
            st.write("")
            search_clicked = st.button("Search", key=f"{key}_search_btn", use_container_width=True)

        if search_clicked:
            if not query.strip():
                st.warning("Please enter a location before searching.")
            else:
                with st.spinner(f'Searching for "{query.strip()}"…'):
                    candidates = search_locations(query.strip(), limit=5)
                if candidates:
                    st.session_state[suggestions_key] = candidates
                    st.session_state[phase_key] = "suggestions"
                    st.rerun()
                else:
                    st.error(
                        f"No results found for **{query.strip()}**. "
                        "Try being more specific, e.g. \"Montrose, Houston TX\" or "
                        "\"Capitol Hill, Seattle WA\"."
                    )
        return None

    # ── Phase 2: pick from candidates ────────────────────────────────────────
    elif phase == "suggestions":
        candidates = st.session_state.get(suggestions_key, [])
        if not candidates:
            st.session_state[phase_key] = "search"
            st.rerun()
            return None

        display_names = [c["display_name"] for c in candidates]
        st.caption(f"**{len(candidates)} result(s) found — pick the correct one:**")
        selected_name = st.radio(
            label,
            display_names,
            key=f"{key}_radio",
            label_visibility="collapsed",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Use this location", type="primary", key=f"{key}_confirm_btn",
                         use_container_width=True):
                idx = display_names.index(selected_name)
                st.session_state[geo_key] = candidates[idx]
                st.session_state[phase_key] = "confirmed"
                st.rerun()
        with col2:
            if st.button("Back — search again", key=f"{key}_back_btn",
                         use_container_width=True):
                st.session_state[phase_key] = "search"
                st.rerun()
        return None

    # ── Phase 3: confirmed ────────────────────────────────────────────────────
    else:
        geo = st.session_state.get(geo_key)
        if not geo:
            st.session_state[phase_key] = "search"
            st.rerun()
            return None

        display = geo["display_name"]
        short = display if len(display) <= 90 else display[:87] + "…"
        col1, col2 = st.columns([5, 1])
        with col1:
            st.success(f"📍 {short}")
        with col2:
            if st.button("Change", key=f"{key}_change_btn", use_container_width=True):
                st.session_state[phase_key] = "search"
                for k in (query_key, suggestions_key, geo_key):
                    st.session_state.pop(k, None)
                st.rerun()
        return geo


def create_financial_inputs():
    """Create standardized financial input fields for the Rent vs Buy calculator."""
    live_rates = get_live_mortgage_rates()
    default_rate = live_rates["rate_30yr"] if live_rates else 6.5

    if live_rates:
        st.caption(
            f"📡 Live 30-yr rate: **{live_rates['rate_30yr']:.2f}%** "
            f"(Freddie Mac, as of {live_rates['as_of']}) — pre-filled below."
        )

    with st.form("financial_inputs"):
        home_price = st.number_input("Home Purchase Price ($)", min_value=0, value=300000, step=1000)
        down_payment = st.number_input("Down Payment ($)", min_value=0, value=60000, step=1000)
        interest_rate = st.number_input(
            "Interest Rate (%)", min_value=0.0, value=float(default_rate), step=0.1,
            help="Pre-filled from live Freddie Mac data when FRED key is configured."
        )
        monthly_rent = st.number_input("Monthly Rent ($)", min_value=0, value=2000, step=100)

        col1, col2 = st.columns(2)
        with col1:
            property_tax_rate = st.number_input("Property Tax Rate (%)", min_value=0.0, value=1.2, step=0.1)
            maintenance_cost_percent = st.number_input(
                "Annual Maintenance Cost (%)", min_value=0.0, value=1.0, step=0.1,
                help="Typically 1-2% of home value per year. Include HOA fees here if applicable."
            )

        with col2:
            home_appreciation_rate = st.number_input("Home Appreciation Rate (%)", min_value=0.0, value=3.0, step=0.1)
            rent_increase_rate = st.number_input("Annual Rent Increase (%)", min_value=0.0, value=2.0, step=0.1)

        submit_button = st.form_submit_button("Calculate")

        return (submit_button, {
            "home_price": home_price,
            "down_payment": down_payment,
            "interest_rate": interest_rate,
            "monthly_rent": monthly_rent,
            "property_tax_rate": property_tax_rate,
            "maintenance_cost_percent": maintenance_cost_percent,
            "home_appreciation_rate": home_appreciation_rate,
            "rent_increase_rate": rent_increase_rate
        })


def create_neighborhood_inputs():
    """Create standardized neighborhood comparison inputs."""
    states = get_available_states()
    state = st.selectbox("Select State", states)

    cities = get_available_cities(state)
    city = st.selectbox("Select City", cities)

    neighborhoods_data = get_neighborhood_data(city=city, state=state)
    available_neighborhoods = (
        [n["name"] for n in neighborhoods_data] if neighborhoods_data
        else ["No neighborhoods available"]
    )

    neighborhoods = st.multiselect(
        "Select Neighborhoods to Compare",
        available_neighborhoods,
        max_selections=3
    )
    return state, city, neighborhoods
