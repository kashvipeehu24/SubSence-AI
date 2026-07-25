from recurring_detector import detect_recurring_subscriptions
from spending_calculator import calculate_subscription_spending
from price_hike_detector import detect_price_hikes
import json



def predict_future_spending(transactions):
    """
    Predict future yearly subscription spending.

    Assumption:
    - If any price hike is detected,
      assume 5% increase next year.
    - Otherwise, spending remains same.

    Returns:
        {
            "current_yearly_spending": amount,
            "projected_yearly_spending": amount,
            "assumed_growth_rate": "%"
        }
    """



    recurring_data = detect_recurring_subscriptions(
        transactions
    )



    subscriptions = recurring_data.get(
        "recurring_subscriptions",
        []
    )



    spending = calculate_subscription_spending(
        subscriptions
    )



    current_yearly = spending.get(
        "yearly_spending",
        0
    )



    price_hikes = detect_price_hikes(
        transactions
    )



    growth_rate = (
        0.05
        if len(price_hikes) > 0
        else 0.0
    )



    projected_yearly = (
        current_yearly
        *
        (1 + growth_rate)
    )



    return {

        "current_yearly_spending": round(
            current_yearly,
            2
        ),

        "projected_yearly_spending": round(
            projected_yearly,
            2
        ),

        "assumed_growth_rate":
            f"{growth_rate * 100:.0f}%"

    }




# TEST

if __name__ == "__main__":


    with open(
        "sample_transactions.json",
        "r"
    ) as file:

        transactions = json.load(file)



    projection = predict_future_spending(
        transactions
    )



    print(
        "\n===== Future Projection =====\n"
    )


    print(
        json.dumps(
            projection,
            indent=4
        )
    )