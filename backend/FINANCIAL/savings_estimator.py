from expensive_detector import detect_high_cost_subscriptions
import json


def estimate_yearly_savings(transactions):
    """
    Estimate yearly savings by cancelling high-cost subscriptions.

    Args:
        transactions (list): Standardized transaction list.

    Returns:
        dict: Estimated yearly savings.
    """

    high_cost_subscriptions = detect_high_cost_subscriptions(transactions)

    monthly_savings = sum(
        sub["monthly_cost"]
        for sub in high_cost_subscriptions
    )

    yearly_savings = monthly_savings * 12

    return {
        "monthly_savings": round(monthly_savings, 2),
        "yearly_savings": round(yearly_savings, 2),
        "subscriptions_to_review": high_cost_subscriptions
    }


# ---------------- TEST ----------------
if __name__ == "__main__":

    with open("sample_transactions.json", "r") as file:
        transactions = json.load(file)

    savings = estimate_yearly_savings(transactions)

    print("\n===== Potential Savings =====\n")
    print(savings)