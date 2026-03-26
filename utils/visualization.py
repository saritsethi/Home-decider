import plotly.graph_objects as go
import plotly.express as px
import json
from datetime import datetime

def create_cost_comparison_chart(financial_data):
    """Create an interactive cost comparison visualization."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=financial_data['Month'],
        y=financial_data['Cumulative_Buying_Costs'],
        name='Buying Costs',
        line=dict(color='#FF4B4B')
    ))
    
    fig.add_trace(go.Scatter(
        x=financial_data['Month'],
        y=financial_data['Cumulative_Rental_Costs'],
        name='Rental Costs',
        line=dict(color='#1F77B4')
    ))
    
    fig.update_layout(
        title='Cumulative Costs Over Time',
        xaxis_title='Month',
        yaxis_title='Cumulative Costs ($)',
        hovermode='x unified'
    )
    
    return fig

def create_neighborhood_comparison_chart(neighborhood_data):
    """Create radar chart for neighborhood comparison."""
    categories = [
        'Walkability', 'Dining Options', 
        'Public Transport', 'Safety Score',
        'School Rating'
    ]
    
    fig = go.Figure()
    
    for hood in neighborhood_data[:3]:
        fig.add_trace(go.Scatterpolar(
            r=[
                hood['walkability_score'],
                hood.get('dining_score', round(hood['walkability_score'] * 0.8, 1)),
                hood['transport_score'],
                hood.get('safety_score', round(hood['school_rating'] * 0.9, 1)),
                hood['school_rating']
            ],
            theta=categories,
            name=hood['name'],
            fill='toself'
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=True,
        title='Neighborhood Comparison'
    )
    
    return fig

def create_historical_value_chart(neighborhoods):
    """Create line chart showing historical property values for neighborhoods."""
    fig = go.Figure()
    valid_data = False
    
    for hood in neighborhoods:
        try:
            # Parse historical values
            if isinstance(hood['historical_values'], str):
                historical_data = json.loads(hood['historical_values'])
            else:
                historical_data = hood['historical_values']
            
            # Validate data structure
            if not historical_data or not isinstance(historical_data, list):
                continue
                
            dates = []
            values = []
            for point in historical_data:
                try:
                    date = datetime.strptime(point['date'], '%Y-%m-%d')
                    value = float(point['value'])
                    dates.append(date)
                    values.append(value)
                except (ValueError, KeyError):
                    continue
            
            if dates and values:
                valid_data = True
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    name=hood['name'],
                    mode='lines+markers'
                ))
        except Exception as e:
            print(f"Error processing neighborhood {hood.get('name', 'unknown')}: {str(e)}")
            continue
    
    if not valid_data:
        return None
        
    fig.update_layout(
        title='Historical Property Values',
        xaxis_title='Date',
        yaxis_title='Property Value ($)',
        hovermode='x unified',
        showlegend=True
    )
    
    return fig
