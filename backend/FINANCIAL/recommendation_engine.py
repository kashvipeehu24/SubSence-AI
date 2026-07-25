from expensive_detector import detect_high_cost_subscriptions
from duplicate_detector import detect_duplicate_subscriptions
from price_hike_detector import detect_price_hikes


def generate_subscription_recommendations(transactions):
    """
    Generate subscription cancellation recommendations.
    """

    recommendations = []


    # -----------------------------
    # High Cost Recommendations
    # -----------------------------

    expensive = detect_high_cost_subscriptions(
        transactions
    )


    for subscription in expensive:

        monthly_cost = subscription.get(
            "monthly_cost",
            0
        )

        recommendations.append({

            "merchant":
                subscription.get("merchant"),

            "action":
                "Consider cancelling or switching plan",

            "reason":
                "High cost subscription",

            "monthly_saving":
                round(monthly_cost, 2),

            "yearly_saving":
                round(monthly_cost * 12, 2)

        })



    # -----------------------------
    # Price Increase Recommendations
    # -----------------------------

    hikes = detect_price_hikes(
        transactions
    )


    for item in hikes:

        recommendations.append({

            "merchant":
                item.get("merchant"),

            "action":
                "Review subscription pricing",

            "reason":
                "Subscription price increased",

            "increase_percent":
                item.get(
                    "increase_percent"
                )

        })



    # -----------------------------
    # Duplicate Recommendations
    # -----------------------------

    duplicates = detect_duplicate_subscriptions(
        transactions
    )


    for item in duplicates:

        recommendations.append({

            "category":
                item.get("category"),

            "action":
                "Keep only one subscription",

            "reason":
                "Multiple subscriptions detected"

        })


    return recommendations