import os
import uuid
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime


def calculate_affordability(annual_income, savings, monthly_expenses):
    """Calculate maximum affordable home price based on financial situation."""
    monthly_income = annual_income / 12
    net_monthly_income = max(0, monthly_income - monthly_expenses)
    max_monthly_payment = net_monthly_income * 0.28

    monthly_pti = max_monthly_payment * 0.8
    max_price_from_income = (monthly_pti * 12 * 20) / (1 + 0.015)
    max_price_from_savings = savings * 5

    return max(0, min(max_price_from_income, max_price_from_savings))


def generate_integrated_report(preferences, family_info, neighborhoods):
    """Generate comprehensive report with recommendations."""
    max_home_price = calculate_affordability(
        family_info['annual_income'],
        family_info['savings'],
        family_info.get('monthly_expenses', 0)
    )

    monthly_income = family_info['annual_income'] / 12
    max_monthly_payment = monthly_income * 0.28
    interest_rate = family_info.get('interest_rate', 6.5)
    down_payment_pct = family_info.get('down_payment_percent', 20) / 100
    loan_amount = family_info['target_home_price'] * (1 - down_payment_pct)
    monthly_rate = interest_rate / 12 / 100
    n_payments = 30 * 12

    if monthly_rate > 0:
        monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    else:
        monthly_mortgage = loan_amount / n_payments if n_payments > 0 else 0

    monthly_property_tax = family_info['target_home_price'] * 0.012 / 12
    monthly_insurance = family_info['target_home_price'] * 0.001 / 12
    monthly_maintenance = family_info['target_home_price'] * 0.01 / 12
    total_monthly_cost = monthly_mortgage + monthly_property_tax + monthly_insurance + monthly_maintenance

    current_rent = family_info.get('current_monthly_rent', 0)
    if current_rent > 0:
        rent_vs_buy = 'buy' if (total_monthly_cost < max_monthly_payment and
                                total_monthly_cost < current_rent * 1.2) else 'rent'
    else:
        rent_vs_buy = 'buy' if total_monthly_cost < max_monthly_payment else 'rent'

    housing_type_scores = {
        "Very Urban": 10, "Somewhat Urban": 7.5, "Mixed": 5,
        "Somewhat Suburban": 2.5, "Very Suburban": 0
    }
    pref_urban = housing_type_scores.get(preferences.get('housing_type', 'Mixed'), 5)

    transport_score_map = {
        "Walking": lambda h: h['walkability_score'],
        "Public Transit": lambda h: h['transport_score'],
        "Mix": lambda h: (h['walkability_score'] + h['transport_score']) / 2,
        "Personal Vehicle": lambda h: 10 - h['transport_score'] / 2
    }
    get_transport_score = transport_score_map.get(preferences.get('transport', 'Mix'),
                                                   lambda h: 5)

    nightlife_pref = preferences.get('nightlife', 5)
    shopping_pref = preferences.get('shopping', 5)
    outdoor_pref = preferences.get('outdoor', 5)
    quiet_pref = preferences.get('quiet', 5)

    all_scored = []
    for hood in neighborhoods:
        scores = {}
        reasons = []

        listings = hood.get('property_listings', [])
        if isinstance(listings, str):
            try:
                listings = json.loads(listings)
            except Exception:
                listings = []
        if listings:
            min_price = min(l['price'] for l in listings)
            if min_price > max_home_price * 1.5:
                reasons.append(f"Note: listings start at ${min_price:,.0f} — may be above your budget")

        school_score = hood['school_rating']
        if family_info.get('children', 0) > 0:
            school_score = min(10, school_score * 1.3)
        scores['school'] = school_score
        if hood['school_rating'] >= 8:
            reasons.append(f"Excellent schools (Rating: {hood['school_rating']}/10)")

        safety = hood.get('safety_score', round(hood['school_rating'] * 0.9, 1))
        scores['safety'] = safety
        if safety >= 8:
            reasons.append("Safe neighborhood for families")

        transport_match = get_transport_score(hood)
        scores['transport'] = transport_match

        hood_urban = (hood['walkability_score'] + hood['transport_score']) / 2
        housing_match = max(0, 10 - abs(hood_urban - pref_urban))
        scores['housing_type'] = housing_match

        def _lifestyle_match(score, pref):
            weight = max(0.5, pref / 5)
            return min(10.0, score * weight)

        nightlife_match = _lifestyle_match(hood.get('nightlife_score', 5), nightlife_pref)
        shopping_match  = _lifestyle_match(hood.get('shopping_score', 5),  shopping_pref)
        outdoor_match   = _lifestyle_match(hood.get('outdoor_score', 5),   outdoor_pref)
        quiet_match     = _lifestyle_match(hood.get('quiet_score', 5),     quiet_pref)
        lifestyle_score = (nightlife_match + shopping_match + outdoor_match + quiet_match) / 4
        scores['lifestyle'] = lifestyle_score

        if nightlife_pref >= 7 and hood.get('nightlife_score', 5) >= 8:
            reasons.append("Active nightlife and entertainment scene")
        if outdoor_pref >= 7 and hood.get('outdoor_score', 5) >= 8:
            reasons.append("Excellent outdoor activities and green spaces")
        if quiet_pref >= 7 and hood.get('quiet_score', 5) >= 7:
            reasons.append("Peaceful and quiet neighborhood")
        if shopping_pref >= 7 and hood.get('shopping_score', 5) >= 7:
            reasons.append("Great shopping and retail access")

        try:
            historical_data = (hood['historical_values'] if isinstance(hood['historical_values'], list)
                               else json.loads(hood['historical_values']))
        except Exception:
            historical_data = []
        if len(historical_data) >= 2:
            start_value = historical_data[0]['value']
            end_value = historical_data[-1]['value']
            if start_value > 0:
                appreciation = ((end_value - start_value) / start_value) * 100
                appreciation_score = min(10, appreciation / 3)
                if appreciation > 15:
                    reasons.append(f"Strong property value growth: {appreciation:.1f}% over 5 years")
            else:
                appreciation_score = 5
        else:
            appreciation_score = 5
        scores['appreciation'] = appreciation_score

        max_possible = len(scores) * 10
        final_score = int((sum(scores.values()) / max_possible) * 100)
        final_score = min(100, max(0, final_score))

        all_scored.append({
            "neighborhood": hood,
            "match_score": final_score,
            "reasons": reasons
        })

    all_scored.sort(key=lambda x: x['match_score'], reverse=True)
    matches = all_scored[:3]

    return {
        'max_home_price': max_home_price,
        'recommended_neighborhoods': matches,
        'rent_vs_buy_recommendation': rent_vs_buy
    }


def create_pdf_report(report_data, family_info, preferences):
    """Generate a downloadable PDF report with all analysis results."""
    output_path = f"/tmp/home_report_{uuid.uuid4().hex}.pdf"
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=16, spaceAfter=12)

    story.append(Paragraph("Your Personalized Home Decision Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))

    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(
        f"Based on your financial profile and preferences, we recommend you "
        f"{report_data['rent_vs_buy_recommendation'].upper()}. "
        f"Your maximum affordable home price is ${report_data['max_home_price']:,.2f}.",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))

    story.append(Paragraph("Financial Analysis", heading_style))
    financial_data = [
        ["Metric", "Value"],
        ["Annual Income", f"${family_info['annual_income']:,.2f}"],
        ["Monthly Income", f"${family_info['annual_income'] / 12:,.2f}"],
        ["Total Savings", f"${family_info['savings']:,.2f}"],
        ["Current Monthly Rent", f"${family_info.get('current_monthly_rent', 0):,.2f}"],
        ["Target Home Price", f"${family_info.get('target_home_price', 0):,.2f}"],
        ["Down Payment", f"${family_info.get('down_payment', 0):,.2f}"],
        ["Monthly Expenses", f"${family_info.get('monthly_expenses', 0):,.2f}"]
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

    story.append(Paragraph("Recommended Neighborhoods", heading_style))
    for match in report_data['recommended_neighborhoods']:
        hood = match['neighborhood']
        story.append(Paragraph(f"{hood['name']} — {match['match_score']}% Match", styles['Heading3']))

        metrics_data = [
            ["Metric", "Score"],
            ["Cost of Living", f"{hood['cost_of_living']}/10"],
            ["School Rating", f"{hood['school_rating']}/10"],
            ["Safety", f"{hood.get('safety_score', 'N/A')}/10"],
            ["Transport Score", f"{hood['transport_score']}/10"],
            ["Walkability", f"{hood['walkability_score']}/10"],
            ["Nightlife", f"{hood.get('nightlife_score', 'N/A')}/10"],
            ["Dining", f"{hood.get('dining_score', 'N/A')}/10"],
            ["Outdoor Activities", f"{hood.get('outdoor_score', 'N/A')}/10"]
        ]
        t = Table(metrics_data)
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ]))
        story.append(t)
        story.append(Spacer(1, 10))

        if match.get('reasons'):
            story.append(Paragraph("Why this neighborhood?", styles['Heading4']))
            for reason in match['reasons']:
                story.append(Paragraph(f"• {reason}", styles['Normal']))
        story.append(Spacer(1, 15))

        listings = hood.get('property_listings', [])
        if isinstance(listings, str):
            listings = json.loads(listings)
        if listings:
            story.append(Paragraph("Available Properties:", styles['Heading4']))
            for listing in listings:
                story.append(Paragraph(
                    f"${listing['price']:,} — {listing['bedrooms']}bd/{listing['bathrooms']}ba, "
                    f"{listing['sqft']:,} sqft, Built {listing['year_built']}",
                    styles['Normal']
                ))
        story.append(Spacer(1, 20))

    doc.build(story)
    return output_path
