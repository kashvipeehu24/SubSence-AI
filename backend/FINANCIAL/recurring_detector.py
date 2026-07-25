from collections import defaultdict
from datetime import datetime
import json


def detect_recurring_subscriptions(transactions):
    """
    Detect recurring transaction-like payments.

    A transaction is considered recurring if:
    - It is a Debit transaction.
    - The same merchant appears at least 2 times.
    - Consecutive transactions are approximately 20–40 days apart.
    """

    recurring_services = []

    merchant_transactions = defaultdict(list)

    # Group transactions by merchant
    for transaction in transactions:

        if transaction.get("type", "").lower() != "debit":
            continue

        merchant = transaction["merchant"]
        merchant_transactions[merchant].append(transaction)

    # Analyze each merchant
    for merchant, txns in merchant_transactions.items():

        if len(txns) < 2:
            continue

        txns.sort(
            key=lambda x: datetime.strptime(
                x["date"],
                "%Y-%m-%d"
            )
        )

        gaps = []

        for i in range(1, len(txns)):

            previous = datetime.strptime(
                txns[i - 1]["date"],
                "%Y-%m-%d"
            )

            current = datetime.strptime(
                txns[i]["date"],
                "%Y-%m-%d"
            )

            gaps.append((current - previous).days)

        recurring_gap_count = sum(
            20 <= gap <= 40
            for gap in gaps
        )

        if recurring_gap_count == len(gaps):

            average_amount = round(
                sum(t["amount"] for t in txns) / len(txns),
                2
            )

            recurring_services.append({
                "merchant": merchant,
                "frequency": "Monthly",
                "occurrences": len(txns),
                "average_amount": average_amount,
                "transactions": txns
            })

    return recurring_services


# ---------------- TEST ----------------

if __name__ == "__main__":

    with open("sample_transactions.json", "r") as file:
        transactions = json.load(file)

    recurring = detect_recurring_subscriptions(transactions)

    print("\n===== Recurring Services =====\n")

    for service in recurring:
        print(service)