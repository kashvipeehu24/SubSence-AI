from collections import defaultdict
from datetime import datetime
import json


def detect_free_trial_conversion(transactions):
    """
    Detect subscriptions that started as free trials
    and later became paid.
    """

    merchant_transactions = defaultdict(list)

    # Group by merchant
    for transaction in transactions:

        if transaction.get("type", "").lower() == "debit":

            merchant = transaction["merchant"]

            merchant_transactions[merchant].append(transaction)

    converted_trials = []

    for merchant, txns in merchant_transactions.items():

        if len(txns) < 2:
            continue

        # Sort by date
        txns.sort(
            key=lambda x: datetime.strptime(
                x["date"],
                "%Y-%m-%d"
            )
        )

        amounts = [t["amount"] for t in txns]

        # Detect free → paid
        if amounts[0] == 0 and amounts[-1] > 0:

            converted_trials.append({

                "merchant": merchant,

                "trial_price": amounts[0],

                "current_price": amounts[-1],

                "recommendation":
                    "Review whether you still use this subscription."

            })

    return converted_trials


# ---------------- TEST ----------------

if __name__ == "__main__":

    with open("sample_transactions.json", "r") as file:
        transactions = json.load(file)

    trials = detect_free_trial_conversion(transactions)

    print("\n===== Free Trial Conversions =====\n")

    if not trials:
        print("No free trial conversions detected.")

    else:
        for item in trials:
            print(item)