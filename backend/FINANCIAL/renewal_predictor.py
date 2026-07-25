from datetime import datetime, timedelta

from recurring_detector import detect_recurring_subscriptions



def predict_subscription_renewals(transactions):
    """
    Predict next subscription renewal dates.
    """

    recurring_data = detect_recurring_subscriptions(
        transactions
    )


    subscriptions = recurring_data.get(
        "recurring_subscriptions",
        []
    )


    renewals = []


    for service in subscriptions:

        txns = service.get(
            "transactions",
            []
        )


        if not txns:
            continue


        # Sort latest transaction
        txns.sort(
            key=lambda x: x["date"]
        )


        last_transaction = txns[-1]


        last_date = datetime.strptime(
            last_transaction["date"],
            "%Y-%m-%d"
        )


        next_date = last_date + timedelta(
            days=30
        )


        renewals.append({

            "merchant":
                service.get("merchant"),


            "last_payment_date":
                last_transaction["date"],


            "next_payment_date":
                next_date.strftime(
                    "%Y-%m-%d"
                ),


            "expected_amount":
                round(
                    last_transaction["amount"],
                    2
                )
        })


    return renewals