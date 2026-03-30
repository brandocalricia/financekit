"""Rule-based spending insights engine for FinanceKit."""
import pandas as pd
from datetime import datetime, date
from utils.data_persistence import load_json
from utils.formatting import format_currency_int, get_currency_symbol


def _load_transactions() -> pd.DataFrame | None:
    data = load_json("budget_transactions.json", default=[])
    if not data:
        return None
    df = pd.DataFrame(data)
    for col in ["date", "description", "amount", "category", "month"]:
        if col not in df.columns:
            df[col] = "" if col != "amount" else 0.0
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])
    return df if not df.empty else None


def _month_key(dt) -> str:
    return dt.strftime("%Y-%m")


def generate_insights(limit: int = 5) -> list[dict]:
    """Generate spending insights from budget transaction history.

    Returns list of {"type": "tip|warning|success", "text": "..."} dicts.
    """
    df = _load_transactions()
    if df is None:
        return []

    sym = get_currency_symbol()
    insights = []
    today = date.today()
    current_month = _month_key(today)

    # Group by month + category
    df["month_key"] = df["date"].dt.to_period("M").astype(str)
    months_available = sorted(df["month_key"].unique(), reverse=True)

    if len(months_available) < 2:
        # Not enough history for comparisons
        total = df["amount"].sum()
        top_cat = df.groupby("category")["amount"].sum().idxmax()
        top_amt = df.groupby("category")["amount"].sum().max()
        insights.append({
            "type": "tip",
            "text": f"Your top spending category is **{top_cat}** at {format_currency_int(top_amt)}. "
                    f"Import more months to see trends.",
        })
        return insights[:limit]

    this_month = months_available[0]
    last_month = months_available[1]
    this_df = df[df["month_key"] == this_month]
    last_df = df[df["month_key"] == last_month]

    this_total = this_df["amount"].sum()
    last_total = last_df["amount"].sum()

    # --- Insight 1: Month-over-month total change ---
    if last_total > 0:
        change_pct = (this_total - last_total) / last_total * 100
        if change_pct > 15:
            insights.append({
                "type": "warning",
                "text": f"Your spending is up **{change_pct:.0f}%** this month "
                        f"({format_currency_int(this_total)} vs {format_currency_int(last_total)} last month).",
            })
        elif change_pct < -10:
            insights.append({
                "type": "success",
                "text": f"Great job! Spending is down **{abs(change_pct):.0f}%** this month "
                        f"({format_currency_int(this_total)} vs {format_currency_int(last_total)} last month).",
            })

    # --- Insight 2: Category spikes (>50% above 3-month avg) ---
    if len(months_available) >= 3:
        last_3 = months_available[1:4]
        avg_df = df[df["month_key"].isin(last_3)]
        avg_by_cat = avg_df.groupby("category")["amount"].sum() / len(last_3)
        this_by_cat = this_df.groupby("category")["amount"].sum()

        for cat in this_by_cat.index:
            avg_val = avg_by_cat.get(cat, 0)
            this_val = this_by_cat.get(cat, 0)
            if avg_val > 0 and this_val > avg_val * 1.5:
                spike_pct = (this_val - avg_val) / avg_val * 100
                insights.append({
                    "type": "warning",
                    "text": f"**{cat}** spending spiked **{spike_pct:.0f}%** above your 3-month average "
                            f"({format_currency_int(this_val)} vs avg {format_currency_int(avg_val)}).",
                })

    # --- Insight 3: Increasing trends (3+ months in a row) ---
    if len(months_available) >= 3:
        for cat in df["category"].unique():
            cat_monthly = []
            for m in months_available[:4]:
                m_df = df[(df["month_key"] == m) & (df["category"] == cat)]
                cat_monthly.append(m_df["amount"].sum())
            # Check if spending increased 3 months in a row (most recent first)
            if len(cat_monthly) >= 3 and cat_monthly[0] > cat_monthly[1] > cat_monthly[2] > 0:
                insights.append({
                    "type": "warning",
                    "text": f"**{cat}** spending has increased for 3 months straight. "
                            f"Consider reviewing this category.",
                })

    # --- Insight 4: Consistent underspending (opportunity to reallocate) ---
    budgets_data = load_json("budgets.json", default={"budgets": {}})
    budgets = budgets_data.get("budgets", {})
    this_by_cat = this_df.groupby("category")["amount"].sum()
    for cat, budget in budgets.items():
        budget = float(budget)
        if budget <= 0:
            continue
        spent = this_by_cat.get(cat, 0)
        if spent < budget * 0.3 and budget >= 50:
            insights.append({
                "type": "tip",
                "text": f"You've only used **{spent / budget * 100:.0f}%** of your {cat} budget. "
                        f"Consider reallocating {format_currency_int(budget - spent)} to savings.",
            })

    # --- Insight 5: Weekend vs weekday spending ---
    this_df_copy = this_df.copy()
    this_df_copy["dow"] = this_df_copy["date"].dt.dayofweek  # 0=Mon, 6=Sun
    weekday_avg = this_df_copy[this_df_copy["dow"] < 5]["amount"].mean()
    weekend_avg = this_df_copy[this_df_copy["dow"] >= 5]["amount"].mean()
    if weekday_avg > 0 and weekend_avg > 0:
        if weekend_avg > weekday_avg * 1.3:
            pct_more = (weekend_avg - weekday_avg) / weekday_avg * 100
            insights.append({
                "type": "tip",
                "text": f"You spend **{pct_more:.0f}% more** on weekends than weekdays. "
                        f"Weekend avg: {format_currency_int(weekend_avg)}/day vs "
                        f"weekday avg: {format_currency_int(weekday_avg)}/day.",
            })

    # --- Insight 6: Top merchant concentration ---
    top_merchants = this_df.groupby("description")["amount"].sum().sort_values(ascending=False)
    if len(top_merchants) >= 3:
        top1_name = top_merchants.index[0]
        top1_pct = top_merchants.iloc[0] / this_total * 100 if this_total > 0 else 0
        if top1_pct > 25:
            insights.append({
                "type": "tip",
                "text": f"**{top1_name}** accounts for **{top1_pct:.0f}%** of your spending this month "
                        f"({format_currency_int(top_merchants.iloc[0])}).",
            })

    return insights[:limit]


def get_top_insight() -> dict | None:
    """Return the single most important insight for dashboard display."""
    insights = generate_insights(limit=1)
    return insights[0] if insights else None


def detect_anomalies() -> list[dict]:
    """Detect spending anomalies by comparing current month to rolling 3-month average.

    Returns list of dicts:
      {"type": "anomaly", "category": str, "current_amount": float,
       "average_amount": float, "description": str}
    """
    df = _load_transactions()
    if df is None:
        return []

    today = date.today()
    current_month = _month_key(today)
    df["month_key"] = df["date"].dt.to_period("M").astype(str)
    months_available = sorted(df["month_key"].unique(), reverse=True)

    if len(months_available) < 2:
        return []

    this_month = months_available[0]
    this_df = df[df["month_key"] == this_month]
    anomalies = []

    # Category-level anomalies: spending 50%+ above 3-month average
    prev_months = months_available[1:4]
    if prev_months:
        prev_df = df[df["month_key"].isin(prev_months)]
        avg_by_cat = prev_df.groupby("category")["amount"].sum() / len(prev_months)
        this_by_cat = this_df.groupby("category")["amount"].sum()

        for cat in this_by_cat.index:
            if cat == "Income":
                continue
            avg_val = avg_by_cat.get(cat, 0)
            this_val = this_by_cat.get(cat, 0)
            if avg_val > 0 and this_val > avg_val * 1.5:
                pct_above = int((this_val - avg_val) / avg_val * 100)
                anomalies.append({
                    "type": "anomaly",
                    "category": cat,
                    "current_amount": float(this_val),
                    "average_amount": float(avg_val),
                    "description": (
                        f"Your {cat} spending is {pct_above}% above your "
                        f"{len(prev_months)}-month average "
                        f"({format_currency_int(this_val)} vs avg {format_currency_int(avg_val)})"
                    ),
                })

    # Individual transaction anomalies: >$500 or >3x category average
    for cat in this_df["category"].unique():
        if cat == "Income":
            continue
        cat_txns = this_df[this_df["category"] == cat]
        cat_avg = cat_txns["amount"].mean()
        for _, row in cat_txns.iterrows():
            if row["amount"] > 500 or (cat_avg > 0 and row["amount"] > cat_avg * 3):
                desc = row.get("description", "Unknown")
                anomalies.append({
                    "type": "anomaly",
                    "category": cat,
                    "current_amount": float(row["amount"]),
                    "average_amount": float(cat_avg),
                    "description": (
                        f"Large transaction: {desc} ({format_currency_int(row['amount'])}) "
                        f"in {cat}"
                    ),
                })

    return anomalies
