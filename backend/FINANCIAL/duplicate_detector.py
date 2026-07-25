from recurring_detector import detect_recurring_subscriptions
import json


# Categories where multiple subscriptions may be unnecessary
DUPLICATE_CATEGORIES = {
    "Music",
    "Entertainment",
    "Video Streaming",
    "Software",
    "Cloud Storage",
    "Fitness"
}


def detect_duplicate_subscriptions(transactions):
    """
    Detect duplicate subscriptions based on category.

    Args:
        transactions (list)

    Returns:
        list
    """

    recurring = detect_recurring_subscriptions(transactions)

    category_map = {}

    for service in recurring:

        category = service["transactions"][0]["category"]
        merchant = service["merchant"]

        if category not in DUPLICATE_CATEGORIES:
            continue

        if category not in category_map:
            category_map[category] = []

        category_map[category].append(merchant)

    duplicates = []

    for category, merchants in category_map.items():

        if len(merchants) > 1:

            duplicates.append({
                "category": category,
                "services": merchants,
                "recommendation": f"Consider keeping only one {category.lower()} subscription."
            })

    return duplicates


# ---------------- TEST ----------------

if __name__ == "__main__":

    with open("sample_transactions.json", "r") as file:
        transactions = json.load(file)

    duplicates = detect_duplicate_subscriptions(transactions)

    print("\n===== Duplicate Subscriptions =====\n")

    if not duplicates:
        print("No duplicate subscriptions found.")

    else:
        for item in duplicates:
            print(item)