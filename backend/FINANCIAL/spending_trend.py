from collections import defaultdict


def analyze_spending_trends(transactions):
    """
    Analyze monthly spending pattern.
    """

    monthly_spending = defaultdict(float)


    for transaction in transactions:

        # Only analyze spending
        if transaction.get("type", "").lower() != "debit":
            continue


        month = transaction["date"][:7]

        monthly_spending[month] += transaction.get(
            "amount",
            0
        )


    # Round values
    monthly_spending = {
        month: round(amount, 2)
        for month, amount in sorted(
            monthly_spending.items()
        )
    }


    values = list(
        monthly_spending.values()
    )


    if len(values) < 2:
        trend = "Stable"

    elif values[-1] > values[0]:
        trend = "Increasing"

    elif values[-1] < values[0]:
        trend = "Decreasing"

    else:
        trend = "Stable"


    return {
        "monthly_breakdown": monthly_spending,
        "trend": trend
    }