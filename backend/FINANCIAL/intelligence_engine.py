import json

from recurring_detector import detect_recurring_subscriptions
from bill_detector import detect_recurring_bills
from duplicate_detector import detect_duplicate_subscriptions
from price_hike_detector import detect_price_hikes
from expensive_detector import detect_high_cost_subscriptions
from spending_calculator import calculate_subscription_spending
from savings_estimator import estimate_yearly_savings
from future_projection import predict_future_spending
from health_score import calculate_financial_health_score
from trial_detector import detect_free_trial_conversion


def run_financial_intelligence(transactions):
    """
    Run the complete Financial Intelligence Engine.
    """

    recurring = detect_recurring_subscriptions(transactions)

    spending = calculate_subscription_spending(recurring)

    bills = detect_recurring_bills(transactions)

    duplicates = detect_duplicate_subscriptions(transactions)

    price_hikes = detect_price_hikes(transactions)

    expensive = detect_high_cost_subscriptions(transactions)

    savings = estimate_yearly_savings(transactions)

    future = predict_future_spending(transactions)

    health = calculate_financial_health_score(transactions)

    trials = detect_free_trial_conversion(transactions)

    return {

        "financial_health_score": health["financial_health_score"],

        "risk_level": health["risk_level"],

        "recurring_services": recurring,

        "recurring_bills": bills,

        "duplicate_services": duplicates,

        "price_hikes": price_hikes,

        "free_trial_conversions": trials,

        "high_cost_subscriptions": expensive,

        "monthly_spending": spending["monthly_spending"],

        "yearly_spending": spending["yearly_spending"],

        "potential_savings": savings,

        "future_projection": future
    }


# ---------------- TEST ----------------

if __name__ == "__main__":

    with open("sample_transactions.json", "r") as file:
        transactions = json.load(file)

    result = run_financial_intelligence(transactions)

    print("\n===== Financial Intelligence Report =====\n")

    print(json.dumps(result, indent=4))