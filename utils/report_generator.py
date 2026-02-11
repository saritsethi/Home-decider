import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
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

def create_pdf_report(report_data, family_info, preferences):
    """Generate a downloadable PDF report with all analysis results."""
    # Create a temporary file path for the PDF
    output_path = "temp_report.pdf"
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12
    )
    
    # Title
    story.append(Paragraph("Your Personalized Home Decision Report", title_style))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(f"""
    Based on your financial profile and preferences, we recommend you {report_data['rent_vs_buy_recommendation'].upper()}.
    Your maximum affordable home price is ${report_data['max_home_price']:,.2f}.
    """, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Financial Analysis
    story.append(Paragraph("Financial Analysis", heading_style))
    financial_data = [
        ["Metric", "Value"],
        ["Annual Income", f"${family_info['annual_income']:,.2f}"],
        ["Monthly Income", f"${family_info['annual_income']/12:,.2f}"],
        ["Total Savings", f"${family_info['savings']:,.2f}"],
        ["Current Monthly Rent", f"${family_info.get('current_monthly_rent', 0):,.2f}"],
        ["Target Home Price", f"${family_info.get('target_home_price', 0):,.2f}"],
        ["Down Payment", f"${family_info.get('down_payment', 0):,.2f}"]
    ]
    
    t = Table(financial_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    
    # Neighborhood Recommendations
    story.append(Paragraph("Recommended Neighborhoods", heading_style))
    for match in report_data['recommended_neighborhoods']:
        hood = match['neighborhood']
        story.append(Paragraph(f"{hood['name']} - {match['match_score']}% Match", styles['Heading3']))
        
        # Create a table for neighborhood metrics
        metrics_data = [
            ["Metric", "Score"],
            ["Cost of Living", f"{hood['cost_of_living']}/10"],
            ["School Rating", f"{hood['school_rating']}/10"],
            ["Transport Score", f"{hood['transport_score']}/10"],
            ["Walkability", f"{hood['walkability_score']}/10"]
        ]
        
        t = Table(metrics_data)
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ]))
        story.append(t)
        story.append(Spacer(1, 10))
        
        # Add match reasons
        story.append(Paragraph("Why this neighborhood?", styles['Heading4']))
        for reason in match['reasons']:
            story.append(Paragraph(f"• {reason}", styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Add available properties if any
        if 'property_listings' in hood:
            listings = json.loads(hood['property_listings']) if isinstance(hood['property_listings'], str) else hood['property_listings']
            if listings:
                story.append(Paragraph("Available Properties:", styles['Heading4']))
                for listing in listings:
                    story.append(Paragraph(
                        f"${listing['price']:,} - {listing['bedrooms']}bd/{listing['bathrooms']}ba, "
                        f"{listing['sqft']} sqft, Built {listing['year_built']}", 
                        styles['Normal']
                    ))
        story.append(Spacer(1, 20))
    
    # Build the PDF
    doc.build(story)
    return output_path
