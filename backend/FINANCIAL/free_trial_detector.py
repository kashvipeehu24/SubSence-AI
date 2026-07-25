from datetime import datetime


# Amount considered as free trial
TRIAL_AMOUNT_THRESHOLD = 1.0


def detect_free_trial_conversions(transactions):
    """
    Detect free trial to paid subscription conversions.

    Rules:
    - Same merchant
    - First transaction amount <= $1
    - Later transaction from same merchant is a paid amount

    Returns:
        list of trial conversions
    """

    merchant_transactions = {}

    # Group transactions by merchant
    for transaction in transactions:

        merchant = transaction.get(
            "merchant",
            ""
        )

        if merchant not in merchant_transactions:
            merchant_transactions[merchant] = []

        merchant_transactions[merchant].append(transaction)


    conversions = []


    for merchant, txns in merchant_transactions.items():

        if len(txns) < 2:
            continue


        # Sort by date
        txns.sort(
            key=lambda x: x["date"]
        )


        first_transaction = txns[0]


        first_amount = first_transaction.get(
            "amount",
            0
        )


        # Check trial payment
        if first_amount <= TRIAL_AMOUNT_THRESHOLD:


            for payment in txns[1:]:

                paid_amount = payment.get(
                    "amount",
                    0
                )


                if paid_amount > TRIAL_AMOUNT_THRESHOLD:

                    conversions.append({

                        "merchant": merchant,

                        "trial_date":
                            first_transaction["date"],

                        "conversion_date":
                            payment["date"],

                        "subscription_amount":
                            paid_amount,

                        "message":
                            "Free trial converted into paid subscription"
                    })


                    break


    return conversions



# TEST

if __name__ == "__main__":

    import json


    with open(
        "sample_transactions.json",
        "r"
    ) as file:

        transactions = json.load(file)


    result = detect_free_trial_conversions(
        transactions
    )


    print(result)