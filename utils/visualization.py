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
    categories = ['Cost of Living', 'School Rating', 'Transport Score', 'Walkability']
    
    fig = go.Figure()
    
    for hood in neighborhood_data:
        fig.add_trace(go.Scatterpolar(
            r=[hood['cost_of_living'], hood['school_rating'], 
               hood['transport_score'], hood['walkability_score']],
            theta=categories,
            name=hood['name'],
            fill='toself'
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=True
    )
    
    return fig

def create_historical_value_chart(neighborhoods):
    """Create line chart showing historical property values for neighborhoods."""
    fig = go.Figure()
    
    for hood in neighborhoods:
        # Parse historical values from JSON
        historical_data = json.loads(hood['historical_values'])
        dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in historical_data]
        values = [d['value'] for d in historical_data]
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            name=f"{hood['name']} ({hood['city']}, {hood['state']})",
            mode='lines+markers'
        ))
    
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
