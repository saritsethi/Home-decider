import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from utils.financial_calculations import calculate_rent_vs_buy

def calculate_affordability(annual_income, savings, monthly_expenses):
    """Calculate maximum affordable home price based on financial situation."""
    # Common rules of thumb:
    # - Monthly housing payment should not exceed 28% of gross monthly income
    # - Down payment should be at least 20% of home price
    monthly_income = annual_income / 12
    max_monthly_payment = monthly_income * 0.28
    
    # Subtract existing monthly expenses to get available payment amount
    available_monthly_payment = max_monthly_payment - monthly_expenses
    
    # Calculate max home price based on 30-year mortgage at 4.5% interest
    max_price_from_income = (available_monthly_payment * 12 * 20)  # Rough estimate
    
    # Calculate max home price based on down payment (assuming 20% down)
    max_price_from_savings = savings * 5  # Since savings represents 20%
    
    # Return the lower of the two limits
    return min(max_price_from_income, max_price_from_savings)

def generate_integrated_report(preferences, family_info, matched_neighborhoods):
    """Generate comprehensive report with recommendations."""
    # Calculate affordability
    max_home_price = calculate_affordability(
        family_info['annual_income'],
        family_info['savings'],
        family_info['monthly_expenses']
    )
    
    # Filter neighborhoods based on affordability
    affordable_neighborhoods = [
        n for n in matched_neighborhoods
        if n['neighborhood']['cost_of_living'] * max_home_price / 10 <= max_home_price
    ]
    
    # Adjust neighborhood scores based on family needs
    for hood in affordable_neighborhoods:
        # Increase importance of school ratings for families with children
        if family_info['children'] > 0:
            school_bonus = hood['neighborhood']['school_rating'] / 10 * 25
            hood['match_score'] = (hood['match_score'] * 3 + school_bonus) / 4
    
    # Sort by adjusted scores
    recommended_neighborhoods = sorted(
        affordable_neighborhoods,
        key=lambda x: x['match_score'],
        reverse=True
    )[:5]
    
    # Calculate rent vs buy recommendation
    financial_analysis = calculate_rent_vs_buy(
        home_price=max_home_price,
        down_payment=family_info['savings'],
        interest_rate=4.5,  # Assumed fixed rate
        loan_term=30,
        monthly_rent=family_info['monthly_expenses'],  # Using current expenses as rent estimate
        property_tax_rate=1.2,
        maintenance_cost_percent=1.0,
        home_appreciation_rate=3.0,
        rent_increase_rate=2.0,
        investment_return_rate=7.0
    )
    
    return {
        'max_home_price': max_home_price,
        'recommended_neighborhoods': recommended_neighborhoods,
        'financial_analysis': financial_analysis,
        'rent_vs_buy_recommendation': 'buy' if financial_analysis['Cumulative_Buying_Costs'].iloc[-1] < financial_analysis['Cumulative_Rental_Costs'].iloc[-1] else 'rent'
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
    
    # Neighborhood Recommendations
    story.append(Paragraph("Recommended Neighborhoods", styles['Heading2']))
    for hood in report_data['recommended_neighborhoods']:
        story.append(Paragraph(
            f"{hood['neighborhood']['name']} - {hood['match_score']}% Match",
            styles['Heading3']
        ))
        for reason in hood['reasons']:
            story.append(Paragraph(f"• {reason}", styles['Normal']))
        story.append(Spacer(1, 10))
    
    # Generate PDF
    doc.build(story)
    
    return output_path
