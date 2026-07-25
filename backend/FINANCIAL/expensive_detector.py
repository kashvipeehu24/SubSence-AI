from recurring_detector import detect_recurring_subscriptions
import json


# Monthly cost threshold

HIGH_COST_THRESHOLD = 20.0



def detect_high_cost_subscriptions(transactions):
    """
    Detect subscriptions with high monthly cost.

    Returns:
        List of expensive subscriptions.
    """



    recurring_data = detect_recurring_subscriptions(
        transactions
    )


    subscriptions = recurring_data.get(
        "recurring_subscriptions",
        []
    )



    expensive_subscriptions = []



    for service in subscriptions:


        amount = service.get(
            "average_amount",
            0
        )


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



        if amount > HIGH_COST_THRESHOLD:


            expensive_subscriptions.append(
                {
                    "merchant": service.get(
                        "merchant",
                        ""
                    ),

                    "monthly_cost": round(
                        amount,
                        2
                    ),

                    "threshold": HIGH_COST_THRESHOLD,

                    "category": category
                }
            )



    return expensive_subscriptions




# TEST

if __name__ == "__main__":


    with open(
        "sample_transactions.json",
        "r"
    ) as file:

        transactions = json.load(file)



    result = detect_high_cost_subscriptions(
        transactions
    )



    print(
        "\n===== High Cost Subscriptions =====\n"
    )


    for item in result:

        print(item)