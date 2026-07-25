from recurring_detector import detect_recurring_subscriptions
import json

# Categories considered as recurring bills
BILL_CATEGORIES = {
    "Utilities",
    "Electricity",
    "Water",
    "Gas",
    "Internet",
    "Mobile",
    "Insurance"
}


def detect_recurring_bills(transactions):
    """
    Detect recurring bills from recurring transactions.
    """

    recurring = detect_recurring_subscriptions(transactions)

    bills = []

    for service in recurring:

        category = service["transactions"][0]["category"]

        if category in BILL_CATEGORIES:

            bills.append({

                "merchant": service["merchant"],

                "category": category,

                "monthly_amount": service["average_amount"]

            })

    return bills


# ---------------- TEST ----------------

if __name__ == "__main__":

    with open("sample_transactions.json", "r") as file:
        transactions = json.load(file)

    bills = detect_recurring_bills(transactions)

    print("\n===== Recurring Bills =====\n")

    if not bills:
        print("No recurring bills detected.")

    else:
        for bill in bills:
            print(bill)