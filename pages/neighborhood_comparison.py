import streamlit as st
import pandas as pd
from components.navigation import create_navigation
from components.inputs import create_neighborhood_inputs
from utils.database import get_neighborhood_data
from utils.visualization import create_neighborhood_comparison_chart, create_historical_value_chart
from utils.live_data import (
    get_live_price_history,
    get_live_walk_scores,
    get_live_places_scores,
    live_data_status,
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

        walk = get_live_walk_scores(name)
        if walk:
            if walk.get("walkability") is not None:
                hood["walkability_score"] = walk["walkability"]
            if walk.get("transit") is not None:
                hood["transport_score"] = walk["transit"]
            if walk.get("description"):
                hood["_walk_description"] = walk["description"]
            live_sources_active.add("Walk Score (walkability & transit)")

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

    st.subheader("Neighborhood Radar")
    fig = create_neighborhood_comparison_chart(selected_data)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Score Breakdown")
    rows = []
    for hood in selected_data:
        rows.append({
            "Neighborhood": hood["name"],
            "Walkability": hood["walkability_score"],
            "Transit": hood["transport_score"],
            "Safety": hood.get("safety_score", "—"),
            "Dining": hood.get("dining_score", "—"),
            "Nightlife": hood.get("nightlife_score", "—"),
            "Outdoor": hood.get("outdoor_score", "—"),
            "Shopping": hood.get("shopping_score", "—"),
            "Schools": hood["school_rating"],
            "Cost of Living": hood["cost_of_living"],
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    hist_source = "FRED Case-Shiller Index" if "FRED Case-Shiller (price history)" in live_sources_active else "Estimated"
    st.subheader(f"Historical Property Values ({hist_source})")
    hist_fig = create_historical_value_chart(selected_data)
    if hist_fig:
        st.plotly_chart(hist_fig, use_container_width=True)
    else:
        st.info("No historical data available for the selected neighborhoods.")


def main():
    create_navigation()

    st.title("Neighborhood Comparison Tool")
    st.write(
        "Compare neighborhoods side-by-side on key metrics. "
        "Scores update automatically from live sources when API keys are configured."
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

    state, city, selected_neighborhoods = create_neighborhood_inputs()

    if st.button("Compare Neighborhoods", type="primary"):
        if not selected_neighborhoods:
            st.warning("Please select at least one neighborhood.")
        else:
            display_comparison_results(state, city, selected_neighborhoods)


if __name__ == "__main__":
    main()
