from recurring_detector import detect_recurring_subscriptions
import json


def detect_high_cost_subscriptions(transactions, threshold=20.0):
    """
    Detect subscriptions whose average monthly cost exceeds a threshold.

    Args:
        transactions (list): Standardized transaction list.
        threshold (float): Monthly cost threshold.

    Returns:
        list: High-cost subscriptions.
    """

    recurring_services = detect_recurring_subscriptions(transactions)

    high_cost_subscriptions = []

    for service in recurring_services:

        category = service["transactions"][0]["category"]

        # Skip recurring bills
        if category in [
            "Utilities",
            "Electricity",
            "Water",
            "Gas",
            "Internet",
            "Mobile",
            "Insurance"
        ]:
            continue

        if service["average_amount"] > threshold:

            high_cost_subscriptions.append({
                "merchant": service["merchant"],
                "monthly_cost": service["average_amount"],
                "threshold": threshold,
                "category": category
            })

    return high_cost_subscriptions


# ---------------- TEST ----------------

if __name__ == "__main__":

    with open("sample_transactions.json", "r") as file:
        transactions = json.load(file)

    expensive = detect_high_cost_subscriptions(transactions)

    print("\n===== High Cost Subscriptions =====\n")

    if not expensive:
        print("No high-cost subscriptions found.")

    else:
        for sub in expensive:
            print(sub)