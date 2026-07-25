from collections import defaultdict
import json


def detect_transaction_anomalies(transactions):
    """
    Detect unusual spending patterns.

    A transaction is considered anomalous when
    the amount is significantly higher than the
    merchant's average spending.
    """

    merchant_amounts = defaultdict(list)

    # Group transaction amounts by merchant
    for transaction in transactions:

        merchant = transaction["merchant"]
        amount = transaction["amount"]

        merchant_amounts[merchant].append(amount)


    anomalies = []


    # Calculate average and detect spikes
    for merchant, amounts in merchant_amounts.items():

        if len(amounts) < 2:
            continue


        average_amount = sum(amounts) / len(amounts)


        for transaction in transactions:

            if transaction["merchant"] == merchant:

                amount = transaction["amount"]


                # Amount is more than 2x average
                if amount > average_amount * 2:

                    anomalies.append({

                        "merchant": merchant,

                        "transaction_id":
                            transaction["transaction_id"],

                        "date":
                            transaction["date"],

                        "amount":
                            amount,

                        "average_amount":
                            round(average_amount, 2),

                        "reason":
                            "Unusual spending spike"

                    })


    return anomalies



# ---------------- TEST ----------------

if __name__ == "__main__":

    with open(
        "sample_transactions.json",
        "r"
    ) as file:

        transactions = json.load(file)


    result = detect_transaction_anomalies(
        transactions
    )


    print("\n===== Transaction Anomalies =====\n")


    if not result:

        print("No anomalies detected.")

    else:

        for item in result:
            print(item)