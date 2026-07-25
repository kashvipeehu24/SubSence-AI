from recurring_detector import detect_recurring_subscriptions
import json

# Categories that are bills (not subscriptions)
BILL_CATEGORIES = {
    "Utilities",
    "Electricity",
    "Water",
    "Gas",
    "Internet",
    "Mobile",
    "Insurance"
}


def calculate_subscription_spending(recurring_services):
    """
    Calculate total monthly and yearly subscription spending.

    Args:
        recurring_services (list): List of detected recurring services.

    Returns:
        dict: Monthly and yearly subscription spending.
    """

    monthly_spending = 0

    for service in recurring_services:

        category = service["transactions"][0]["category"]

        # Skip recurring bills
        if category in BILL_CATEGORIES:
            continue

        monthly_spending += service["average_amount"]

    yearly_spending = monthly_spending * 12

    return {
        "monthly_spending": round(monthly_spending, 2),
        "yearly_spending": round(yearly_spending, 2)
    }


# ---------------- TEST ----------------

if __name__ == "__main__":

    with open("sample_transactions.json", "r") as file:
        transactions = json.load(file)

    recurring_services = detect_recurring_subscriptions(transactions)

    spending = calculate_subscription_spending(recurring_services)

    print("\n===== Subscription Spending =====\n")

    print(spending)