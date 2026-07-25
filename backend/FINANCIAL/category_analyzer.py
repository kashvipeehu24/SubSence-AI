from collections import defaultdict


def calculate_category_spending(transactions):

    categories = defaultdict(float)

    for transaction in transactions:

        # Only debit spending
        if transaction.get("type", "").lower() != "debit":
            continue

        category = transaction.get(
            "category",
            "Others"
        )

        amount = transaction.get(
            "amount",
            0
        )

        categories[category] += amount


    return {
        category: round(amount, 2)
        for category, amount in categories.items()
    }