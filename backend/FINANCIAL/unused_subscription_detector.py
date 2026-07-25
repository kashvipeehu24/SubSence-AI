from collections import defaultdict
from datetime import datetime

def detect_unused_subscriptions(transactions, inactive_days=60):
    """
    Detect subscriptions that have not been charged recently.
    """

    merchant_transactions = defaultdict(list)

    # Group debit transactions by merchant
    for transaction in transactions:
        if transaction.get("type", "").lower() == "debit":
            merchant_transactions[transaction["merchant"]].append(transaction)

    if not merchant_transactions:
        return []

    # Find the latest transaction date in dataset
    latest_date = max(
        datetime.strptime(t["date"], "%Y-%m-%d")
        for t in transactions
    )

    unused = []

    for merchant, txns in merchant_transactions.items():

        last_txn = max(
            datetime.strptime(t["date"], "%Y-%m-%d")
            for t in txns
        )

        days_since = (latest_date - last_txn).days

        if days_since >= inactive_days:
            unused.append({
                "merchant": merchant,
                "last_payment": last_txn.strftime("%Y-%m-%d"),
                "days_since_last_payment": days_since,
                "recommendation": "Review whether this subscription is still needed."
            })

    return unused