def generate_ai_recommendations(
    high_cost_subscriptions,
    price_hikes,
    duplicate_subscriptions,
    unused_subscriptions,
    free_trial_conversions,
    upcoming_renewals
):
    """
    Generate smart recommendations based on the outputs
    of all financial analysis modules.
    """

    recommendations = []

    # High-cost subscriptions
    for sub in high_cost_subscriptions:
        recommendations.append({
            "priority": "High",
            "merchant": sub["merchant"],
            "recommendation":
                f"{sub['merchant']} is one of your most expensive subscriptions. "
                "Consider downgrading or cancelling it if you don't use it regularly.",
            "potential_monthly_saving": sub["monthly_cost"],
            "confidence": "High"
        })

    # Price hikes
    for hike in price_hikes:
        recommendations.append({
            "priority": "Medium",
            "merchant": hike["merchant"],
            "recommendation":
                f"{hike['merchant']} increased its price by "
                f"{hike['increase_percent']}%. Review your plan before renewal.",
            "confidence": "Medium"
        })

    # Duplicate subscriptions
    for dup in duplicate_subscriptions:
        recommendations.append({
            "priority": "High",
            "merchant": dup["merchant"],
            "recommendation":
                "Duplicate subscription detected. Cancel the extra subscription to avoid unnecessary spending.",
            "confidence": "High"
        })

    # Unused subscriptions
    for sub in unused_subscriptions:
        recommendations.append({
            "priority": "High",
            "merchant": sub["merchant"],
            "recommendation":
                "This subscription appears to be unused. Consider cancelling it.",
            "confidence": "High"
        })

    # Free trial conversions
    for trial in free_trial_conversions:
        recommendations.append({
            "priority": "Medium",
            "merchant": trial["merchant"],
            "recommendation":
                "Your free trial has converted into a paid subscription. "
                "Review whether you still need this service.",
            "confidence": "Medium"
        })

    # Upcoming renewals
    for renewal in upcoming_renewals:
        recommendations.append({
            "priority": "Low",
            "merchant": renewal["merchant"],
            "recommendation":
                f"Your next payment of {renewal['expected_amount']} is due on "
                f"{renewal['next_payment_date']}.",
            "confidence": "High"
        })

    return recommendations