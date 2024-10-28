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
    
    for hood in neighborhood_data[:3]:  # Only top 3
        fig.add_trace(go.Scatterpolar(
            r=[
                hood['walkability_score'],
                hood.get('dining_score', hood['walkability_score'] * 0.8),  # Estimate if not available
                hood['transport_score'],
                hood.get('safety_score', hood['school_rating'] * 0.9),  # Estimate if not available
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

def parse_historical_values(historical_values):
    """Safely parse historical values from either string or list format."""
    try:
        if isinstance(historical_values, str):
            data = json.loads(historical_values)
        elif isinstance(historical_values, list):
            data = historical_values
        else:
            return None
        
        # Validate data structure
        if not all(isinstance(d, dict) and 'date' in d and 'value' in d for d in data):
            return None
            
        return data
    except (json.JSONDecodeError, TypeError):
        return None

def create_historical_value_chart(neighborhoods):
    """Create line chart showing historical property values for neighborhoods."""
    fig = go.Figure()
    
    try:
        for hood in neighborhoods:
            historical_data = parse_historical_values(hood['historical_values'])
            if not historical_data:
                continue
                
            try:
                dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in historical_data]
                values = [d['value'] for d in historical_data]
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    name=f"{hood['name']} ({hood.get('city', '')})",
                    mode='lines+markers'
                ))
            except (ValueError, KeyError):
                continue
        
        if len(fig.data) == 0:
            # If no valid data was added, return None
            return None
            
        fig.update_layout(
            title='Historical Property Values by Neighborhood',
            xaxis_title='Date',
            yaxis_title='Property Value ($)',
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    except Exception as e:
        print(f"Error generating historical value chart: {str(e)}")
        return None
