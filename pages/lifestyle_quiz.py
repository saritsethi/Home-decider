def display_lifestyle_preferences():
    with st.form("neighborhood_preferences_form"):
        st.subheader("Location Preferences")
        
        # Get all states
        states = get_available_states()
        state = st.selectbox("Select State", states, key='state_selector')
        
        # Get cities filtered by state
        if state and state != st.session_state.get('selected_state'):
            st.session_state.selected_state = state
            # Clear previous city selection
            if 'selected_city' in st.session_state:
                del st.session_state.selected_city
        
        # Get cities for selected state
        filtered_cities = get_available_cities(state=state)
        city = st.selectbox("Select City", filtered_cities, key='city_selector')
        
        st.subheader("Neighborhood Preferences")
        housing_type = st.select_slider(
            "Do you prefer urban or suburban living?",
            options=["Very Urban", "Somewhat Urban", "Mixed", "Somewhat Suburban", "Very Suburban"]
        )
        transport = st.select_slider(
            "How do you prefer to get around?",
            options=["Walking", "Public Transit", "Mix", "Personal Vehicle"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            nightlife = st.slider("How important is nightlife?", 0, 10, 5)
            shopping = st.slider("How important is shopping access?", 0, 10, 5)
        with col2:
            outdoor = st.slider("How important are outdoor activities?", 0, 10, 5)
            quiet = st.slider("How important is a quiet neighborhood?", 0, 10, 5)
        
        if st.form_submit_button("Generate Report"):
            # Combine all info before generating report
            combined_info = {
                **st.session_state.family_info,
                **st.session_state.financial_info
            }
            
            preferences = {
                "state": state,
                "city": city,
                "housing_type": housing_type,
                "transport": transport,
                "nightlife": nightlife,
                "shopping": shopping,
                "outdoor": outdoor,
                "quiet": quiet
            }
            
            # Save preferences to session state
            st.session_state.preferences = preferences
            
            # Get neighborhood matches
            matches = get_neighborhood_data(city=city, state=state)
            
            # Generate and store report data with combined info
            st.session_state.report_data = generate_integrated_report(
                preferences,
                combined_info,
                matches  # Pass matches directly without wrapping
            )
            
            # Save quiz results
            save_quiz_results(
                st.session_state.session_id,
                json.dumps(preferences),
                json.dumps(combined_info)
            )
            
            # Switch to report page
            st.switch_page("pages/report_display.py")
