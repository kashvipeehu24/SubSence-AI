from recurring_detector import detect_recurring_subscriptions
import json


def detect_recurring_bills(transactions):
    """
    Detect recurring bills from transactions.

    Returns:
        List of recurring bills.
    """


    recurring_data = detect_recurring_subscriptions(
        transactions
    )


    recurring_bills = recurring_data.get(
        "recurring_bills",
        []
    )


    return recurring_bills



# TEST

if __name__ == "__main__":


    with open(
        "sample_transactions.json",
        "r"
    ) as file:

        transactions = json.load(file)



    bills = detect_recurring_bills(
        transactions
    )


    print("\n===== Recurring Bills =====\n")


    for bill in bills:

        print(bill)