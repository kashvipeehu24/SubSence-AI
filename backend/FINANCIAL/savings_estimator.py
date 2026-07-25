from expensive_detector import detect_high_cost_subscriptions
import json



def estimate_yearly_savings(transactions):
    """
    Estimate yearly savings by cancelling
    high-cost subscriptions.

    Returns:
        {
            "monthly_savings": amount,
            "yearly_savings": amount,
            "subscriptions_to_review": []
        }
    """



    high_cost_subscriptions = detect_high_cost_subscriptions(
        transactions
    )



    monthly_savings = sum(
        subscription.get(
            "monthly_cost",
            0
        )
        for subscription in high_cost_subscriptions
    )



    yearly_savings = monthly_savings * 12



    return {

        "monthly_savings": round(
            monthly_savings,
            2
        ),

        "yearly_savings": round(
            yearly_savings,
            2
        ),

        "subscriptions_to_review":
            high_cost_subscriptions

    }




# TEST

if __name__ == "__main__":


    with open(
        "sample_transactions.json",
        "r"
    ) as file:

        transactions = json.load(file)



    savings = estimate_yearly_savings(
        transactions
    )



    print(
        "\n===== Potential Savings =====\n"
    )


    print(savings)