from collections import defaultdict
from datetime import datetime
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


def detect_recurring_subscriptions(transactions):
    """
    Detect recurring transactions.

    Rules:
    - Only Debit transactions
    - Same merchant appears at least 2 times
    - Gap between transactions is 20-40 days

    Returns:
    {
        "recurring_subscriptions": [],
        "recurring_bills": []
    }
    """

    recurring_subscriptions = []
    recurring_bills = []

    merchant_transactions = defaultdict(list)


    # Group transactions by merchant
    for transaction in transactions:

        if transaction.get("type", "").lower() != "debit":
            continue

        merchant = transaction.get("merchant")

        if merchant:
            merchant_transactions[merchant].append(transaction)



    # Analyze merchants
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
                txns[i-1]["date"],
                "%Y-%m-%d"
            )

            current = datetime.strptime(
                txns[i]["date"],
                "%Y-%m-%d"
            )

            gaps.append(
                (current - previous).days
            )


        recurring_count = sum(
            20 <= gap <= 40
            for gap in gaps
        )


        if recurring_count != len(gaps):
            continue



        average_amount = round(
            sum(
                t["amount"]
                for t in txns
            )
            /
            len(txns),
            2
        )


        category = txns[0].get(
            "category",
            ""
        )



        # Separate bills
        if category in BILL_CATEGORIES:

            recurring_bills.append(
                {
                    "merchant": merchant,
                    "category": category,
                    "monthly_amount": average_amount
                }
            )


        else:

            recurring_subscriptions.append(
                {
                    "merchant": merchant,
                    "frequency": "Monthly",
                    "occurrences": len(txns),
                    "average_amount": average_amount,
                    "transactions": txns
                }
            )



    return {
        "recurring_subscriptions": recurring_subscriptions,
        "recurring_bills": recurring_bills
    }



# TEST

if __name__ == "__main__":

    with open(
        "sample_transactions.json",
        "r"
    ) as file:

        transactions = json.load(file)



    result = detect_recurring_subscriptions(
        transactions
    )


    print(result)