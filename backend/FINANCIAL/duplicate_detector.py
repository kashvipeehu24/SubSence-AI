from recurring_detector import detect_recurring_subscriptions
import json


# Categories where duplicate subscriptions are possible

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

    Example:
    Netflix + Disney+ -> Entertainment duplicates

    Returns:
        List of duplicate subscription warnings
    """


    recurring_data = detect_recurring_subscriptions(
        transactions
    )


    subscriptions = recurring_data.get(
        "recurring_subscriptions",
        []
    )


    category_map = {}



    for service in subscriptions:


        transaction_list = service.get(
            "transactions",
            []
        )


        if not transaction_list:
            continue



        category = transaction_list[0].get(
            "category",
            ""
        )


        merchant = service.get(
            "merchant",
            ""
        )



        if category not in DUPLICATE_CATEGORIES:
            continue



        if category not in category_map:

            category_map[category] = []



        category_map[category].append(
            merchant
        )



    duplicates = []



    for category, merchants in category_map.items():


        if len(merchants) > 1:


            duplicates.append(
                {
                    "category": category,
                    "services": merchants,
                    "recommendation":
                        f"Consider keeping only one {category.lower()} subscription."
                }
            )



    return duplicates




# TEST

if __name__ == "__main__":


    with open(
        "sample_transactions.json",
        "r"
    ) as file:

        transactions = json.load(file)



    result = detect_duplicate_subscriptions(
        transactions
    )



    print(
        "\n===== Duplicate Subscriptions =====\n"
    )


    if not result:

        print(
            "No duplicate subscriptions found."
        )

    else:

        for item in result:

            print(item)