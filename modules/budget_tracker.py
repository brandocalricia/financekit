import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from utils.data_persistence import load_json, save_json, get_mtime
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout, CHART_COLORS
from utils.formatting import format_currency, format_currency_int, get_currency_symbol

DATA_FILE = "budgets.json"
TRANSACTIONS_FILE = "budget_transactions.json"

CATEGORIES = [
    "Housing", "Food & Groceries", "Dining Out", "Transportation",
    "Entertainment", "Subscriptions", "Shopping", "Health",
    "Savings", "Utilities", "Other",
]

# Keyword → budget category mapping for auto-categorization
CATEGORY_MAP = {
    "Housing": ["rent", "mortgage", "apartment", "lease", "hoa", "property"],
    "Food & Groceries": ["walmart", "costco", "kroger", "safeway", "trader joe", "whole foods",
                         "aldi", "grocery", "market", "supermarket", "food", "publix", "wegmans"],
    "Dining Out": ["restaurant", "mcdonald", "starbucks", "chipotle", "pizza", "burger", "cafe",
                   "diner", "grubhub", "doordash", "uber eats", "seamless", "taco bell", "subway",
                   "wendy", "chick-fil", "panera", "shake shack", "applebee", "olive garden"],
    "Transportation": ["uber", "lyft", "gas", "shell", "chevron", "bp", "exxon", "parking",
                       "transit", "metro", "bus", "train", "toll", "auto", "zipcar", "enterprise"],
    "Entertainment": ["netflix", "hulu", "disney", "hbo", "cinema", "movie", "theater",
                      "youtube", "twitch", "steam", "gaming", "concert", "ticket", "amazon prime video"],
    "Subscriptions": ["spotify", "apple music", "subscription", "membership", "adobe", "dropbox",
                      "icloud", "google one", "amazon prime", "linkedin premium", "patreon"],
    "Shopping": ["amazon", "target", "best buy", "ebay", "etsy", "ikea", "nike", "adidas",
                 "zara", "h&m", "nordstrom", "macy", "clothing", "apparel"],
    "Health": ["pharmacy", "cvs", "walgreens", "doctor", "hospital", "clinic", "dental",
               "gym", "fitness", "peloton", "health", "medical", "urgent care", "vision"],
    "Savings": ["savings", "transfer to savings", "invest", "401k", "ira", "brokerage",
                "vanguard", "fidelity", "schwab", "wealthfront"],
    "Utilities": ["electric", "water", "gas bill", "internet", "comcast", "att", "verizon",
                  "t-mobile", "utility", "phone", "cable", "spectrum", "xfinity", "pge"],
}

BUDGET_TEMPLATES = {
    "Student": {
        "Housing": 600, "Food & Groceries": 200, "Dining Out": 80,
        "Transportation": 50, "Entertainment": 50, "Subscriptions": 20,
        "Shopping": 60, "Health": 30, "Savings": 50, "Utilities": 40, "Other": 70,
    },
    "Freelancer": {
        "Housing": 1500, "Food & Groceries": 400, "Dining Out": 200,
        "Transportation": 150, "Entertainment": 100, "Subscriptions": 100,
        "Shopping": 150, "Health": 200, "Savings": 500, "Utilities": 150, "Other": 300,
    },
    "Family": {
        "Housing": 2000, "Food & Groceries": 800, "Dining Out": 300,
        "Transportation": 400, "Entertainment": 200, "Subscriptions": 80,
        "Shopping": 300, "Health": 300, "Savings": 500, "Utilities": 250, "Other": 370,
    },
    "Single Professional": {
        "Housing": 1800, "Food & Groceries": 300, "Dining Out": 400,
        "Transportation": 200, "Entertainment": 300, "Subscriptions": 80,
        "Shopping": 200, "Health": 150, "Savings": 400, "Utilities": 120, "Other": 250,
    },
}


def _load():
    return load_json(DATA_FILE, default={"budgets": {cat: 0 for cat in CATEGORIES}})


def _save(data):
    save_json(DATA_FILE, data)


def _load_transactions():
    """Load persisted budget transactions from disk."""
    data = load_json(TRANSACTIONS_FILE, default=[])
    if data:
        df = pd.DataFrame(data)
        for col in ["date", "description", "amount", "category", "month"]:
            if col not in df.columns:
                df[col] = "" if col != "amount" else 0.0
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        return df
    return None


def _save_transactions(expenses):
    """Persist budget transactions to disk."""
    records = expenses.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if isinstance(v, pd.Timestamp):
                r[k] = v.isoformat()
    save_json(TRANSACTIONS_FILE, records)


def _auto_index(columns, candidates):
    col_lower = [c.lower().strip() for c in columns]
    for cand in candidates:
        for i, c in enumerate(col_lower):
            if cand in c:
                return i + 1
    return 0


def _categorize(description: str) -> str:
    desc_lower = description.lower()
    for cat, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw in desc_lower:
                return cat
    return "Other"


def render():
    render_module_header("💰", "Budget Tracker", "Set monthly budgets by category and track where your money goes.")

    if "budget_data" not in st.session_state:
        st.session_state.budget_data = _load()

    # Load persisted transactions if not in session
    if "budget_transactions" not in st.session_state:
        loaded_txns = _load_transactions()
        if loaded_txns is not None and not loaded_txns.empty:
            st.session_state.budget_transactions = loaded_txns

    data = st.session_state.budget_data
    budgets = data.get("budgets", {cat: 0 for cat in CATEGORIES})
    for cat in CATEGORIES:
        if cat not in budgets:
            budgets[cat] = 0

    # ── Budget Setup ──────────────────────────────────────────────────────
    with st.expander("⚙️ Set Monthly Budgets", expanded=not any(budgets.values())):
        st.markdown("**Quick Load Template**")
        tc1, tc2 = st.columns([3, 1])
        with tc1:
            template = st.selectbox(
                "Load a budget template",
                ["— custom —"] + list(BUDGET_TEMPLATES.keys()),
                help="Student, Freelancer, Family, or Single Professional starting points.",
            )
        with tc2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📋 Load Template", use_container_width=True) and template != "— custom —":
                data["budgets"] = BUDGET_TEMPLATES[template].copy()
                st.session_state.budget_data = data
                _save(data)
                st.toast(f"Loaded **{template}** budget template!", icon="✅")
                st.rerun()

        st.markdown("**Set Category Budgets**")
        with st.form("budget_form"):
            cols = st.columns(3)
            new_budgets = {}
            for i, cat in enumerate(CATEGORIES):
                with cols[i % 3]:
                    new_budgets[cat] = st.number_input(
                        cat,
                        min_value=0.0,
                        value=float(budgets.get(cat, 0)),
                        step=50.0,
                        format="%.0f",
                        key=f"bgt_{cat}",
                    )
            if st.form_submit_button("💾 Save Budgets", type="primary", use_container_width=True):
                data["budgets"] = new_budgets
                budgets = new_budgets
                st.session_state.budget_data = data
                _save(data)
                st.toast("Budgets saved!", icon="✅")
                st.rerun()

    # ── Import Transactions ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Import Bank Transactions")
    st.caption("Upload a CSV from your bank to see spending vs. budget. Same format as the Report Generator.")

    uploaded = st.file_uploader(
        "Upload a CSV bank statement",
        type=["csv"],
        key="budget_upload",
    )

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Could not read file: {e}")
            df = None

        if df is not None and not df.empty:
            st.success(f"Loaded **{len(df):,}** rows.")
            cols_opts = ["— select —"] + list(df.columns)
            c1, c2, c3 = st.columns(3)
            with c1:
                date_col = st.selectbox("Date", cols_opts,
                    index=_auto_index(df.columns, ["date", "trans date", "transaction date"]))
            with c2:
                desc_col = st.selectbox("Description", cols_opts,
                    index=_auto_index(df.columns, ["description", "desc", "memo", "merchant", "name", "payee"]))
            with c3:
                amount_col = st.selectbox("Amount", cols_opts,
                    index=_auto_index(df.columns, ["amount", "debit", "transaction amount"]))

            if "— select —" not in (date_col, desc_col, amount_col):
                if st.button("📊 Analyze Transactions", type="primary"):
                    with st.spinner("Categorizing transactions..."):
                        new_df = pd.DataFrame()
                        new_df["date"] = pd.to_datetime(df[date_col], errors="coerce")
                        new_df["description"] = df[desc_col].astype(str)
                        new_df["amount"] = pd.to_numeric(
                            df[amount_col].astype(str).str.replace(r"[,$()]", "", regex=True),
                            errors="coerce",
                        )
                        new_df = new_df.dropna(subset=["date", "amount"])
                        new_df["category"] = new_df["description"].apply(_categorize)
                        expenses = new_df[new_df["amount"] < 0].copy()
                        expenses["amount"] = expenses["amount"].abs()
                        expenses["month"] = expenses["date"].dt.to_period("M").astype(str)
                        st.session_state.budget_transactions = expenses
                        _save_transactions(expenses)
                    st.toast(f"Categorized {len(expenses)} expense transactions!", icon="✅")
                    st.rerun()
            else:
                st.warning("Please map all three columns to continue.")

    # ── Spending Analysis ─────────────────────────────────────────────────
    if "budget_transactions" not in st.session_state:
        if not any(budgets.values()):
            st.info("Set your monthly budgets above to get started, then import a bank statement.")
        else:
            st.info("Import a bank statement above to see your spending vs. budget.")
            _render_budget_overview(budgets, {})
        return

    expenses = st.session_state.budget_transactions
    months_available = sorted(expenses["month"].unique(), reverse=True)

    st.markdown("---")
    sm1, sm2 = st.columns([3, 1])
    with sm1:
        selected_month = st.selectbox("View month", months_available)
    with sm2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Data", use_container_width=True):
            del st.session_state.budget_transactions
            save_json(TRANSACTIONS_FILE, [])
            st.rerun()

    month_expenses = expenses[expenses["month"] == selected_month]
    spending_by_cat = month_expenses.groupby("category")["amount"].sum().to_dict()

    _render_budget_overview(budgets, spending_by_cat, selected_month)

    # ── Month-over-month ──────────────────────────────────────────────────
    if len(months_available) >= 2:
        st.markdown("---")
        st.markdown("### Month-over-Month Comparison")
        compare = months_available[:2]
        comp_rows = []
        for cat in CATEGORIES:
            for mo in compare:
                mo_exp = expenses[expenses["month"] == mo]
                spent = mo_exp[mo_exp["category"] == cat]["amount"].sum()
                comp_rows.append({"Category": cat, "Month": mo, "Spent ($)": round(spent, 2)})
        comp_df = pd.DataFrame(comp_rows)
        fig = px.bar(
            comp_df, x="Category", y="Spent ($)", color="Month",
            barmode="group",
            title=f"{compare[1]} vs {compare[0]}",
            color_discrete_sequence=["#6366f1", "#a78bfa"],
        )
        apply_layout(fig, height=380, xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)

    # ── Editable category assignments ────────────────────────────────────
    st.markdown("---")
    with st.expander("🏷️ Review & Edit Transaction Categories"):
        month_exp_display = month_expenses[["date", "description", "amount", "category"]].copy()
        month_exp_display["date"] = month_exp_display["date"].dt.strftime("%Y-%m-%d")
        edited = st.data_editor(
            month_exp_display,
            column_config={
                "category": st.column_config.SelectboxColumn(options=CATEGORIES),
                "amount": st.column_config.NumberColumn(format="$%.2f"),
            },
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key="budget_editor",
        )
        if st.button("💾 Apply Category Edits"):
            # Update the session state transactions with edited categories
            for idx, row in edited.iterrows():
                mask = (
                    (expenses["description"] == row["description"]) &
                    (expenses["month"] == selected_month)
                )
                expenses.loc[mask, "category"] = row["category"]
            st.session_state.budget_transactions = expenses
            _save_transactions(expenses)
            st.toast("Categories updated!", icon="✅")
            st.rerun()


def _render_budget_overview(budgets, spending_by_cat, selected_month=None):
    import calendar as _cal
    total_budget = sum(budgets.values())
    total_spent = sum(spending_by_cat.values())
    remaining = total_budget - total_spent

    if selected_month:
        st.markdown(f"### Budget Status — {selected_month}")
    else:
        st.markdown("### Budget Overview")

    sym = get_currency_symbol()
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Total Budgeted", format_currency_int(total_budget))
    mc2.metric("Total Spent", format_currency_int(total_spent))
    mc3.metric("Remaining", format_currency_int(remaining),
               delta=f"{'Under' if remaining >= 0 else 'Over'} by {format_currency_int(abs(remaining))}")

    # Daily spending average & days remaining
    today = date.today()
    day_of_month = today.day
    days_in_month = _cal.monthrange(today.year, today.month)[1]
    days_remaining = days_in_month - day_of_month
    if day_of_month > 0 and total_spent > 0:
        daily_avg = total_spent / day_of_month
        projected = daily_avg * days_in_month
        mc4.metric(f"Daily Avg ({days_remaining}d left)", f"{format_currency_int(daily_avg)}/day",
                   delta=f"Projected: {format_currency_int(projected)}" if total_budget > 0 else None)
    else:
        mc4.metric(f"Days Remaining", f"{days_remaining}")

    # Alert banners
    over_100, over_80 = [], []
    for cat in CATEGORIES:
        budget = budgets.get(cat, 0)
        spent = spending_by_cat.get(cat, 0)
        if budget > 0:
            pct = spent / budget * 100
            if pct >= 100:
                over_100.append(f"**{cat}** {format_currency_int(spent)} / {format_currency_int(budget)}")
            elif pct >= 80:
                over_80.append(f"**{cat}** {format_currency_int(spent)} / {format_currency_int(budget)}")

    if over_100:
        st.error(f"🚨 Over budget: {' · '.join(over_100)}")
    if over_80:
        st.warning(f"⚠️ Approaching limit (80%+): {' · '.join(over_80)}")

    st.markdown("### Category Breakdown")

    for cat in CATEGORIES:
        budget = budgets.get(cat, 0)
        spent = spending_by_cat.get(cat, 0)
        if budget == 0 and spent == 0:
            continue

        pct = (spent / budget * 100) if budget > 0 else (100.0 if spent > 0 else 0.0)
        pct_capped = min(pct, 100.0)

        if pct >= 100:
            bar_color = "#7f1d1d"
            status = "🔴"
        elif pct >= 80:
            bar_color = "#ef4444"
            status = "🟠"
        elif pct >= 50:
            bar_color = "#f59e0b"
            status = "🟡"
        else:
            bar_color = "#22c55e"
            status = "🟢"

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{status} {cat}**")
            st.markdown(
                f'<div style="background:#1e1e2f;border-radius:6px;height:16px;overflow:hidden;">'
                f'<div style="background:{bar_color};width:{pct_capped:.1f}%;height:100%;'
                f'border-radius:6px;"></div></div>',
                unsafe_allow_html=True,
            )
        with col2:
            if budget > 0:
                st.markdown(
                    f'<div style="text-align:right;font-size:0.85rem;color:#94a3b8;padding-top:6px;">'
                    f'{format_currency_int(spent)} / {format_currency_int(budget)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="text-align:right;font-size:0.85rem;color:#94a3b8;padding-top:6px;">'
                    f'{format_currency_int(spent)}</div>',
                    unsafe_allow_html=True,
                )

    # Donut chart
    if total_budget > 0:
        st.markdown("---")
        st.markdown("### Spending Overview")
        dc1, dc2 = st.columns([1, 2])
        with dc1:
            fig = go.Figure(go.Pie(
                labels=["Spent", "Remaining"],
                values=[min(total_spent, total_budget), max(0, total_budget - total_spent)],
                hole=0.65,
                marker_colors=["#6366f1", "#1e1e2f"],
                textinfo="percent",
                hovertemplate=f"%{{label}}: {get_currency_symbol()}%{{value:,.0f}}<extra></extra>",
            ))
            fig.update_layout(
                height=260,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                annotations=[{
                    "text": f"{format_currency_int(total_spent)}<br><span style='font-size:11px'>spent</span>",
                    "x": 0.5, "y": 0.5, "font_size": 18,
                    "showarrow": False, "font_color": "#e2e8f0",
                }],
            )
            st.plotly_chart(fig, use_container_width=True)
        with dc2:
            if spending_by_cat:
                cat_data = [(cat, spending_by_cat.get(cat, 0)) for cat in CATEGORIES
                            if spending_by_cat.get(cat, 0) > 0]
                cat_data.sort(key=lambda x: x[1], reverse=True)
                cat_df = pd.DataFrame(cat_data, columns=["Category", "Amount"])
                fig2 = px.bar(
                    cat_df, x="Amount", y="Category",
                    orientation="h",
                    color_discrete_sequence=["#6366f1"],
                    text="Amount",
                )
                fig2.update_traces(texttemplate=f"{get_currency_symbol()}%{{text:,.0f}}", textposition="outside")
                fig2.update_layout(
                    height=260, margin=dict(t=10, b=10, l=10, r=60),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"),
                    xaxis=dict(gridcolor="#2a2a40"),
                    yaxis=dict(gridcolor="#2a2a40"),
                    showlegend=False,
                )
                st.plotly_chart(fig2, use_container_width=True)
