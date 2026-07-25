import json

from recurring_detector import detect_recurring_subscriptions
from spending_calculator import calculate_subscription_spending
from duplicate_detector import detect_duplicate_subscriptions
from price_hike_detector import detect_price_hikes
from expensive_detector import detect_high_cost_subscriptions
from savings_estimator import estimate_yearly_savings
from future_projection import predict_future_spending
from health_score import calculate_financial_health_score
from category_analyzer import calculate_category_spending
from spending_trend import analyze_spending_trends
from free_trial_detector import detect_free_trial_conversions
from recommendation_engine import generate_subscription_recommendations
from renewal_predictor import predict_subscription_renewals
from trial_detector import detect_free_trial_conversion
from anomaly_detector import detect_transaction_anomalies
from unused_subscription_detector import detect_unused_subscriptions


def run_financial_intelligence(transactions):
    """
    Main Financial Intelligence Engine.

    Input:
        transactions.json

    Output:
        financial_analysis.json
    """

    # -----------------------------
    # Recurring Detection
    # -----------------------------

    recurring = detect_recurring_subscriptions(transactions)

    subscriptions = recurring.get(
        "recurring_subscriptions",
        []
    )

    bills = recurring.get(
        "recurring_bills",
        []
    )


    # -----------------------------
    # Spending Analysis
    # -----------------------------

    spending = calculate_subscription_spending(
        subscriptions
    )


    # -----------------------------
    # Intelligence Modules
    # -----------------------------

    duplicates = detect_duplicate_subscriptions(
        transactions
    )


    price_hikes = detect_price_hikes(
        transactions
    )


    expensive = detect_high_cost_subscriptions(
        transactions
    )


    savings = estimate_yearly_savings(
        transactions
    )


    future = predict_future_spending(
        transactions
    )

    categories = calculate_category_spending(
        transactions
    )

    anomalies = detect_transaction_anomalies(
        transactions
    )

    trends = analyze_spending_trends(
        transactions
    )

    free_trials = detect_free_trial_conversions(
        transactions
    )

    health = calculate_financial_health_score(
        transactions
    )

    recommendations = generate_subscription_recommendations(
        transactions
    )

    renewals = predict_subscription_renewals(
        transactions
    )

    free_trial_conversions = detect_free_trial_conversion(
        transactions
    )

    unused = detect_unused_subscriptions(transactions)

    # -----------------------------
    # Financial Risks
    # -----------------------------

    risks = []


    if price_hikes:
        risks.append(
            {
                "risk": "subscription_price_increase",
                "severity": "Medium"
            }
        )


    if expensive:
        risks.append(
            {
                "risk": "high_cost_subscription",
                "severity": "High"
            }
        )


    # -----------------------------
    # Final JSON Contract
    # -----------------------------

    result = {

        "financial_health_score":
            health["financial_health_score"],


        "risk_level":
            health["risk_level"],


        "financial_risks":
            risks,


        "spending_categories": categories,


        "spending_trends": trends,


        "recommendations": recommendations,


        "upcoming_renewals": renewals,


        "transaction_anomalies": anomalies,


        "unused_subscriptions": unused,


        "subscription_cost_analysis":
            {
                "monthly_cost":
                    spending["monthly_spending"],

                "annual_cost":
                    spending["yearly_spending"]
            },


        "recurring_subscriptions":
            subscriptions,


        "recurring_bills":
            bills,


        "duplicate_subscriptions":
            duplicates,


        "price_hikes":
            price_hikes,


        "free_trial_conversions": free_trial_conversions,


        "high_cost_subscriptions":
            expensive,


        "monthly_spending":
            spending["monthly_spending"],


        "yearly_spending":
            spending["yearly_spending"],


        "potential_savings":
            savings,


        "future_projection":
            future
    }


    return result



# -----------------------------
# RUN ENGINE
# -----------------------------

if __name__ == "__main__":

    with open(
        "sample_transactions.json",
        "r"
    ) as file:

        transactions = json.load(file)


    result = run_financial_intelligence(
        transactions
    )


    with open(
        "financial_analysis.json",
        "w"
    ) as file:

        json.dump(
            result,
            file,
            indent=4
        )


    print(
        "\nFinancial analysis generated successfully!"
    )