import streamlit as st
import pandas as pd
from components.navigation import create_navigation
from components.inputs import create_neighborhood_inputs, location_picker_widget
from utils.database import get_neighborhood_data
from utils.visualization import create_neighborhood_comparison_chart, create_historical_value_chart
from utils.live_data import (
    get_live_price_history,
    get_live_walk_scores_with_fallback,
    get_live_places_scores,
    live_data_status,
    build_dynamic_neighborhood_from_geo,
    STATE_MEDIAN_HOME_PRICES,
)

st.set_page_config(page_title="Neighborhood Comparison", page_icon="🏘️")


def _estimate_base_price(hood):
    listings = hood.get("property_listings", [])
    if listings:
        prices = [l["price"] for l in listings if isinstance(l.get("price"), (int, float))]
        if prices:
            return sum(prices) / len(prices)
    return 500000


def display_comparison_results(state, city, selected_neighborhoods):
    if not selected_neighborhoods:
        st.warning("Please select at least one neighborhood to compare.")
        return

    neighborhood_data = get_neighborhood_data(city=city, state=state)
    selected_data = [
        dict(hood) for hood in neighborhood_data
        if hood["name"] in selected_neighborhoods
    ]

    if not selected_data:
        st.warning("No data available for the selected neighborhoods.")
        return

    live_sources_active = set()

    for hood in selected_data:
        name = hood["name"]

        live_history = get_live_price_history(city, _estimate_base_price(hood))
        if live_history:
            hood["historical_values"] = live_history
            live_sources_active.add("FRED Case-Shiller (price history)")

        walk = get_live_walk_scores_with_fallback(name)
        if walk:
            if walk.get("walkability") is not None:
                hood["walkability_score"] = walk["walkability"]
            if walk.get("transit") is not None:
                hood["transport_score"] = walk["transit"]
            if walk.get("description"):
                hood["_walk_description"] = walk["description"]
            source_label = walk.get("source", "Walk Score")
            live_sources_active.add(source_label)

        places = get_live_places_scores(name)
        if places:
            for key in ("dining", "nightlife", "shopping", "outdoor"):
                if key in places:
                    hood[f"{key}_score"] = places[key]
            live_sources_active.add("Google Places (dining, nightlife, shopping, outdoor)")

    if live_sources_active:
        st.success(f"📡 Live data: {' · '.join(sorted(live_sources_active))}")
    else:
        st.caption("Showing curated scores. Add API keys to enable live data.")

    _render_comparison(selected_data, live_sources_active)


def display_dynamic_results(neighborhood_dicts):
    """Display comparison for dynamically built neighborhoods."""
    if not neighborhood_dicts:
        return

    live_sources = set()
    for hood in neighborhood_dicts:
        if hood.get("_walk_source"):
            live_sources.add(hood["_walk_source"])
        if hood.get("_places_active"):
            live_sources.add("Google Places (dining, nightlife, shopping, outdoor)")
        if hood.get("_fred_series"):
            live_sources.add("FRED Case-Shiller (price history)")

    if live_sources:
        st.success(f"📡 Live data: {' · '.join(sorted(live_sources))}")
    else:
        st.caption("Showing OpenStreetMap scores. Add API keys to enable additional live data.")

    # Show data notes for dynamic mode
    notes = []
    any_estimated_places = any(not h.get("_places_active") for h in neighborhood_dicts)
    if any_estimated_places:
        notes.append("Dining/nightlife/shopping scores use OpenStreetMap defaults — add a Google Places key for real counts.")
    if any(h.get("property_listings", [{}])[0].get("_estimated") for h in neighborhood_dicts if h.get("property_listings")):
        notes.append("Property prices are state-median estimates. Check Zillow or Realtor.com for live listings.")
    notes.append("School ratings and safety scores use national defaults for custom locations.")
    for note in notes:
        st.caption(f"ℹ️ {note}")

    _render_comparison(neighborhood_dicts, live_sources)


def _render_comparison(selected_data, live_sources_active):
    """Shared rendering: radar, table, historical chart, listings."""
    st.subheader("Neighborhood Radar")
    fig = create_neighborhood_comparison_chart(selected_data)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Score Breakdown")
    rows = []
    for hood in selected_data:
        rows.append({
            "Neighborhood": hood["name"],
            "City / State": f"{hood.get('city', '')}{',' if hood.get('state') else ''} {hood.get('state', '')}".strip(", "),
            "Walkability": hood.get("walkability_score", "—"),
            "Transit": hood.get("transport_score", "—"),
            "Safety": hood.get("safety_score", "—"),
            "Dining": hood.get("dining_score", "—"),
            "Nightlife": hood.get("nightlife_score", "—"),
            "Outdoor": hood.get("outdoor_score", "—"),
            "Shopping": hood.get("shopping_score", "—"),
            "Schools": hood.get("school_rating", "—"),
            "Cost of Living": hood.get("cost_of_living", "—"),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    hist_label = "FRED Case-Shiller Index" if any("FRED" in s for s in live_sources_active) else "Estimated"
    st.subheader(f"Historical Property Values ({hist_label})")
    hist_fig = create_historical_value_chart(selected_data)
    if hist_fig:
        st.plotly_chart(hist_fig, use_container_width=True)
    else:
        st.info("No historical data available for the selected neighborhoods.")

    st.subheader("Property Listings")
    for hood in selected_data:
        listings = hood.get("property_listings", [])
        is_dynamic = hood.get("_is_dynamic", False)
        header = hood["name"]
        if is_dynamic:
            base = STATE_MEDIAN_HOME_PRICES.get(hood.get("state", ""), 350000)
            header += f"  ·  Est. median: ${base:,}"
        with st.expander(header, expanded=False):
            if not listings:
                st.write("No listings available.")
            else:
                if is_dynamic:
                    st.caption("These are price estimates based on state median home prices, not live MLS data.")
                for listing in listings:
                    price = listing.get("price", "N/A")
                    price_str = f"${price:,.0f}" if isinstance(price, (int, float)) else str(price)
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Price", price_str)
                    col2.metric("Beds/Baths", f"{listing.get('beds', '?')} bd / {listing.get('baths', '?')} ba")
                    col3.metric("Sq Ft", f"{listing.get('sqft', '?'):,}" if isinstance(listing.get('sqft'), int) else "?")
                    st.caption(f"📍 {listing.get('address', '')}  ·  {listing.get('type', '')}")
                    st.divider()


def search_tab():
    """
    UI for searching any US location using the 3-phase search-then-confirm picker.
    Up to 3 location slots; at least 1 must be confirmed before comparing.
    """
    st.markdown(
        "Search any US neighborhood, city, or address. "
        "We'll show you matching locations to pick from before fetching any data."
    )

    SLOTS = [
        ("nc_loc_0", "Location 1",           "e.g. South Congress, Austin TX"),
        ("nc_loc_1", "Location 2 (optional)", "e.g. Hyde Park, Chicago IL"),
        ("nc_loc_2", "Location 3 (optional)", "e.g. Capitol Hill, Seattle WA"),
    ]

    confirmed_geos = []
    for key, label, placeholder in SLOTS:
        with st.container(border=True):
            geo = location_picker_widget(key, label=label, placeholder=placeholder)
            if geo:
                confirmed_geos.append(geo)

    st.write("")

    if not confirmed_geos:
        st.info("Confirm at least one location above to enable comparison.")
        return

    if st.button(
        f"Compare {len(confirmed_geos)} Location{'s' if len(confirmed_geos) > 1 else ''}",
        type="primary",
        key="search_compare_btn",
    ):
        neighborhoods = []
        for geo in confirmed_geos:
            label = geo.get("neighborhood", geo.get("display_name", ""))
            with st.spinner(f"Fetching data for {label}…"):
                hood = build_dynamic_neighborhood_from_geo(geo)
            if hood:
                neighborhoods.append(hood)
            else:
                st.error(f"Could not load data for **{label}**.")

        if neighborhoods:
            st.divider()
            display_dynamic_results(neighborhoods)


def curated_tab():
    """UI for the existing curated city/neighborhood dropdowns."""
    state, city, selected_neighborhoods = create_neighborhood_inputs()

    if st.button("Compare Neighborhoods", type="primary", key="curated_btn"):
        if not selected_neighborhoods:
            st.warning("Please select at least one neighborhood.")
        else:
            display_comparison_results(state, city, selected_neighborhoods)


def main():
    create_navigation()

    st.title("Neighborhood Comparison Tool")
    st.write(
        "Compare neighborhoods side-by-side on key metrics. "
        "Search any US location, or browse our curated city list."
    )

    status = live_data_status()
    active = [name for name, on in status.items() if on]
    inactive = [name for name, on in status.items() if not on]

    with st.expander("Live Data Sources", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Active**")
            if active:
                for src in active:
                    st.write(f"✅ {src}")
            else:
                st.write("None yet")
        with col2:
            st.write("**Not configured**")
            for src in inactive:
                st.write(f"⬜ {src}")

    tab1, tab2 = st.tabs(["🔍 Search Any US Location", "📋 Browse Curated Cities"])

    with tab1:
        search_tab()

    with tab2:
        curated_tab()


if __name__ == "__main__":
    main()
