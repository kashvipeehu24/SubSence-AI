def calculate_subscription_spending(subscriptions):
    """
    Calculate total monthly and yearly subscription spending.

    Args:
        subscriptions:
            List of recurring subscription dictionaries.

    Returns:
        {
            "monthly_spending": amount,
            "yearly_spending": amount
        }
    """

    monthly_spending = 0


    for service in subscriptions:

        monthly_spending += service.get(
            "average_amount",
            0
        )


    yearly_spending = monthly_spending * 12


    return {
        "monthly_spending": round(
            monthly_spending,
            2
        ),
        "yearly_spending": round(
            yearly_spending,
            2
        )
    }