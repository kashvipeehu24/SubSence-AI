from recurring_detector import detect_recurring_subscriptions
import json



def detect_price_hikes(transactions):
    """
    Detect subscription price increases.

    Returns:
        List of price hike records.
    """



    recurring_data = detect_recurring_subscriptions(
        transactions
    )


    subscriptions = recurring_data.get(
        "recurring_subscriptions",
        []
    )


    price_hikes = []



    for service in subscriptions:


        txns = service.get(
            "transactions",
            []
        )


        if len(txns) < 2:
            continue



        # Sort transactions by date

        txns.sort(
            key=lambda x: x["date"]
        )



        old_price = txns[0].get(
            "amount",
            0
        )


        new_price = txns[-1].get(
            "amount",
            0
        )



        # Detect increase

        if new_price > old_price:


            increase_percent = (
                (new_price - old_price)
                /
                old_price
            ) * 100



            price_hikes.append(
                {
                    "merchant": service.get(
                        "merchant",
                        ""
                    ),

                    "old_price": round(
                        old_price,
                        2
                    ),

                    "new_price": round(
                        new_price,
                        2
                    ),

                    "increase_percent": round(
                        increase_percent,
                        2
                    )
                }
            )



    return price_hikes




# TEST

if __name__ == "__main__":


    with open(
        "sample_transactions.json",
        "r"
    ) as file:

        transactions = json.load(file)



    hikes = detect_price_hikes(
        transactions
    )



    print(
        "\n===== Price Hikes =====\n"
    )


    for item in hikes:

        print(item)