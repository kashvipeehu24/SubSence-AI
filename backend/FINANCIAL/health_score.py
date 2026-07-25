from recurring_detector import detect_recurring_subscriptions
from price_hike_detector import detect_price_hikes
from spending_calculator import calculate_subscription_spending
from savings_estimator import estimate_yearly_savings
from expensive_detector import detect_high_cost_subscriptions
import json

# Categories treated as recurring bills (not subscriptions)
BILL_CATEGORIES = {
    "Utilities",
    "Electricity",
    "Water",
    "Gas",
    "Internet",
    "Mobile",
    "Insurance"
}


def calculate_financial_health_score(transactions):
    """
    Calculate Financial Health Score (0-100).

    Factors considered:
    - Subscription Count
    - Price Hikes
    - High-Cost Subscriptions
    - Monthly Spending
    - Potential Savings

    Returns:
        dict
    """

    score = 100

    # Get data from previous modules
    recurring = detect_recurring_subscriptions(transactions)
    price_hikes = detect_price_hikes(transactions)
    spending = calculate_subscription_spending(recurring)
    savings = estimate_yearly_savings(transactions)
    expensive = detect_high_cost_subscriptions(transactions)

    # -----------------------------
    # 1. Subscription Count
    # -----------------------------
    subscription_count = 0

    for service in recurring:
        category = service["transactions"][0]["category"]

        if category in BILL_CATEGORIES:
            continue

        subscription_count += 1

    if subscription_count >= 6:
        score -= 20
    elif subscription_count >= 4:
        score -= 10

    # -----------------------------
    # 2. Price Hikes
    # -----------------------------
    score -= len(price_hikes) * 5

    # -----------------------------
    # 3. High Cost Subscriptions
    # -----------------------------
    score -= len(expensive) * 8

    # -----------------------------
    # 4. Monthly Spending
    # -----------------------------
    monthly = spending["monthly_spending"]

    if monthly > 100:
        score -= 20
    elif monthly > 50:
        score -= 10

    # -----------------------------
    # 5. Potential Savings
    # -----------------------------
    yearly_savings = savings["yearly_savings"]

    if yearly_savings > 300:
        score -= 10

    # Keep score between 0 and 100
    score = max(0, min(100, score))

    # -----------------------------
    # Risk Level
    # -----------------------------
    if score >= 80:
        risk = "Low"
    elif score >= 60:
        risk = "Medium"
    else:
        risk = "High"

    return {
        "financial_health_score": score,
        "risk_level": risk,
        "subscription_count": subscription_count,
        "price_hikes": len(price_hikes),
        "high_cost_subscriptions": len(expensive),
        "monthly_spending": spending["monthly_spending"],
        "potential_yearly_savings": yearly_savings
    }


# ---------------- TEST ----------------

if __name__ == "__main__":

    with open("sample_transactions.json", "r") as file:
        transactions = json.load(file)

    result = calculate_financial_health_score(transactions)

    print("\n===== Financial Health Score =====\n")

    for key, value in result.items():
        print(f"{key}: {value}")