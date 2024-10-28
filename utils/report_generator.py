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
    max_monthly_payment = monthly_income * 0.28
    available_monthly_payment = max_monthly_payment - monthly_expenses
    max_price_from_income = (available_monthly_payment * 12 * 20)
    max_price_from_savings = savings * 5
    return min(max_price_from_income, max_price_from_savings)

def generate_integrated_report(preferences, family_info, neighborhoods):
    """Generate comprehensive report with recommendations."""
    # neighborhoods is now a direct list, not wrapped in a match structure
    max_home_price = calculate_affordability(
        family_info['annual_income'],
        family_info['savings'],
        family_info['monthly_expenses']
    )
    
    # Calculate matches for each neighborhood
    matches = []
    for hood in neighborhoods:
        match_score = 0
        reasons = []
        
        # Urban/suburban match
        urban_scores = {
            "Very Urban": 10,
            "Somewhat Urban": 7.5,
            "Mixed": 5,
            "Somewhat Suburban": 2.5,
            "Very Suburban": 0
        }
        urban_match = 10 - abs(urban_scores[preferences['housing_type']] - hood['walkability_score'])
        match_score += urban_match
        
        # Transport preference match
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
            if appreciation > 15:  # More than 15% appreciation in 5 years
                match_score += 10
                reasons.append(f"Strong property value growth: {appreciation:.1f}% over 5 years")
        
        # Lifestyle matches
        if preferences['nightlife'] > 7:
            nightlife_match = hood['walkability_score']
            match_score += nightlife_match
            if nightlife_match > 7:
                reasons.append("Great nightlife and entertainment options")
        
        if preferences['shopping'] > 7:
            shopping_match = hood['walkability_score']
            match_score += shopping_match
            if shopping_match > 7:
                reasons.append("Excellent shopping accessibility")
        
        if preferences['outdoor'] > 7:
            outdoor_match = 10 - hood['cost_of_living']/2
            match_score += outdoor_match
            if outdoor_match > 7:
                reasons.append("Good access to outdoor activities")
        
        if preferences['quiet'] > 7:
            quiet_match = 10 - hood['walkability_score']/2
            match_score += quiet_match
            if quiet_match > 7:
                reasons.append("Quiet and peaceful environment")
        
        # Filter based on affordability
        if hood['cost_of_living'] * max_home_price / 10 <= max_home_price:
            # Calculate final score as percentage
            final_score = int((match_score / 60) * 100)  # 60 is max possible score
            if final_score >= 50:  # Only include matches with >50% score
                matches.append({
                    "neighborhood": hood,
                    "match_score": final_score,
                    "reasons": reasons
                })
    
    # Sort matches by score
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return {
        'max_home_price': max_home_price,
        'recommended_neighborhoods': matches[:5],
        'rent_vs_buy_recommendation': 'buy' if max_home_price > family_info['current_monthly_rent'] * 12 * 20 else 'rent'
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
    
    # Family Profile
    story.append(Paragraph("Family Profile", styles['Heading2']))
    family_data = [
        ["Family Members", str(family_info['family_size'])],
        ["Adults", str(family_info['adults'])],
        ["Children", str(family_info['children'])],
        ["Annual Income", f"${family_info['annual_income']:,.2f}"],
        ["Savings", f"${family_info['savings']:,.2f}"]
    ]
    family_table = Table(family_data, colWidths=[200, 300])
    family_table.setStyle(TableStyle([
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
    story.append(family_table)
    story.append(Spacer(1, 20))
    
    # Financial Recommendations
    story.append(Paragraph("Financial Analysis", styles['Heading2']))
    story.append(Paragraph(
        f"Maximum Affordable Home Price: ${report_data['max_home_price']:,.2f}",
        styles['Normal']
    ))
    story.append(Paragraph(
        f"Recommendation: {report_data['rent_vs_buy_recommendation'].upper()}",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))
    
    # Neighborhood Recommendations with Historical Data
    story.append(Paragraph("Recommended Neighborhoods", styles['Heading2']))
    for hood in report_data['recommended_neighborhoods']:
        story.append(Paragraph(
            f"{hood['neighborhood']['name']} ({preferences['city']}, {preferences['state']}) - {hood['match_score']}% Match",
            styles['Heading3']
        ))
        for reason in hood['reasons']:
            story.append(Paragraph(f"• {reason}", styles['Normal']))
        
        # Add historical value trend
        historical_data = hood['neighborhood']['historical_values']
        if isinstance(historical_data, str):
            historical_data = json.loads(historical_data)
        
        if len(historical_data) >= 2:
            start_value = historical_data[0]['value']
            end_value = historical_data[-1]['value']
            appreciation = ((end_value - start_value) / start_value) * 100
            story.append(Paragraph(
                f"• Historical Property Value Appreciation: {appreciation:.1f}%",
                styles['Normal']
            ))
        
        story.append(Spacer(1, 10))
    
    # Generate PDF
    doc.build(story)
    return output_path
