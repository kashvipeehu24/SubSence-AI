from recurring_detector import detect_recurring_subscriptions
import json


BILL_CATEGORIES = {
    "Utilities",
    "Electricity",
    "Water",
    "Gas",
    "Internet",
    "Mobile",
    "Insurance"
}


def detect_price_hikes(transactions):
    """
    Detect silent price increases in recurring subscriptions.

    Args:
        transactions (list): Standardized transaction list.

    Returns:
        list: Detected price hikes.
    """

    recurring_services = detect_recurring_subscriptions(transactions)

    price_hikes = []

    for service in recurring_services:

        category = service["transactions"][0]["category"]

        # Ignore recurring bills
        if category in BILL_CATEGORIES:
            continue

        merchant = service["merchant"]

        # Get this merchant's transactions from original data
        merchant_txns = [
            t for t in transactions
            if t["merchant"] == merchant
        ]

        # Sort by date
        merchant_txns.sort(
            key=lambda x: x["date"]
        )

        amounts = [
            t["amount"]
            for t in merchant_txns
        ]

        # Compare first and latest amount
        old_price = amounts[0]
        new_price = amounts[-1]

        if new_price > old_price:

            increase_percent = (
                (new_price - old_price) / old_price
            ) * 100

            price_hikes.append({
                "merchant": merchant,
                "old_price": round(old_price, 2),
                "new_price": round(new_price, 2),
                "increase_percent": round(increase_percent, 2)
            })

    return price_hikes


# ---------------- TEST ----------------

if __name__ == "__main__":

    with open("sample_transactions.json", "r") as file:
        transactions = json.load(file)

    hikes = detect_price_hikes(transactions)

    print("\n===== Price Hikes =====\n")

    if not hikes:
        print("No price hikes detected.")

    else:
        for hike in hikes:
            print(hike)