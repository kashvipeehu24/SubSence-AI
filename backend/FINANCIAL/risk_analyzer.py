def analyze_financial_risks(
        duplicate_services,
        price_hikes,
        high_cost_subscriptions
):
    """
    Detect financial risks based on spending behavior.
    """

    risks = []

    if duplicate_services:
        risks.append({
            "risk": "duplicate_subscriptions",
            "severity": "Medium"
        })


    if price_hikes:
        risks.append({
            "risk": "subscription_price_increase",
            "severity": "Medium"
        })


    if high_cost_subscriptions:
        risks.append({
            "risk": "high_cost_subscription",
            "severity": "High"
        })


    return risks