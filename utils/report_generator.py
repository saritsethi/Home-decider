import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from utils.financial_calculations import calculate_rent_vs_buy
import json
from datetime import datetime

def calculate_affordability(annual_income, savings, monthly_expenses):
    """Calculate maximum affordable home price based on financial situation."""
    monthly_income = annual_income / 12
    max_monthly_payment = monthly_income * 0.28  # 28% DTI ratio
    
    # Factor in property tax (1.5%) and insurance ($150/month)
    monthly_pti = max_monthly_payment * 0.8  # 80% of payment for principal & interest
    max_price_from_income = (monthly_pti * 12 * 20) / (1 + 0.015)  # Adjust for property tax
    
    # Calculate max price based on down payment (20%)
    max_price_from_savings = savings * 5  # 20% down payment
    
    return min(max_price_from_income, max_price_from_savings)

def generate_integrated_report(preferences, family_info, neighborhoods):
    """Generate comprehensive report with recommendations."""
    max_home_price = calculate_affordability(
        family_info['annual_income'],
        family_info['savings'],
        family_info.get('monthly_expenses', 0)
    )
    
    # Calculate monthly costs for rent vs buy recommendation
    monthly_income = family_info['annual_income'] / 12
    max_monthly_payment = monthly_income * 0.28
    monthly_mortgage = family_info['target_home_price'] * 0.8 * 0.005
    total_monthly_cost = monthly_mortgage + (family_info['target_home_price'] * 0.015 / 12) + 150
    
    rent_vs_buy = 'buy' if total_monthly_cost < max_monthly_payment and total_monthly_cost < family_info['current_monthly_rent'] * 1.2 else 'rent'
    
    # Enhanced neighborhood matching for families
    matches = []
    for hood in neighborhoods:
        match_score = 0
        reasons = []
        
        # School rating weight increased for families with children
        school_weight = 2.0 if family_info.get('children', 0) > 0 else 1.0
        school_score = hood['school_rating'] * school_weight
        match_score += school_score
        if school_score > 7:
            reasons.append(f"Excellent schools (Rating: {hood['school_rating']}/10)")
        
        # Safety score (estimated from school rating if not available)
        safety_score = hood.get('safety_score', hood['school_rating'] * 0.9)
        match_score += safety_score
        if safety_score > 7:
            reasons.append("Safe neighborhood for families")
        
        # Family-friendly amenities (based on walkability and transport)
        amenities_score = (hood['walkability_score'] + hood['transport_score']) / 2
        match_score += amenities_score
        if amenities_score > 7:
            reasons.append("Great family amenities and accessibility")
        
        # Transport accessibility
        transport_scores = {
            "Walking": hood['walkability_score'],
            "Public Transit": hood['transport_score'],
            "Mix": (hood['walkability_score'] + hood['transport_score']) / 2,
            "Personal Vehicle": 10 - hood['transport_score']/2
        }
        transport_match = transport_scores[preferences['transport']]
        match_score += transport_match
        
        # Calculate historical value trend
        historical_data = hood['historical_values'] if isinstance(hood['historical_values'], list) else json.loads(hood['historical_values'])
        if len(historical_data) >= 2:
            start_value = historical_data[0]['value']
            end_value = historical_data[-1]['value']
            appreciation = ((end_value - start_value) / start_value) * 100
            if appreciation > 15:
                match_score += 10
                reasons.append(f"Strong property value growth: {appreciation:.1f}% over 5 years")
        
        # Filter based on affordability
        if hood['cost_of_living'] * max_home_price / 10 <= max_home_price:
            final_score = int((match_score / 50) * 100)  # 50 is max possible score
            if final_score >= 60:  # Increased threshold for better matches
                matches.append({
                    "neighborhood": hood,
                    "match_score": final_score,
                    "reasons": reasons
                })
    
    # Sort matches by score and limit to top matches
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return {
        'max_home_price': max_home_price,
        'recommended_neighborhoods': matches[:3],  # Limit to top 3
        'rent_vs_buy_recommendation': rent_vs_buy
    }

def create_pdf_report(output_path, report_data, family_info, preferences):
    """Generate a PDF report with all recommendations and analysis."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    story.append(Paragraph("Your Personalized Home Decision Report", title_style))
    story.append(Spacer(1, 20))
    
    # Add remaining PDF generation code...
    # [Previous PDF generation code remains unchanged]
    
    doc.build(story)
    return output_path
