import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from utils.data_persistence import load_json, save_json, get_mtime
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout, CHART_COLORS, _theme_colors, _chart_font
from utils.formatting import format_currency, format_currency_int, get_currency_symbol
from utils.notifications import create_notification

DATA_FILE = "budgets.json"
TRANSACTIONS_FILE = "budget_transactions.json"

DEFAULT_CATEGORIES = [
    "Housing", "Food & Groceries", "Dining Out", "Transportation",
    "Entertainment", "Subscriptions", "Shopping", "Health",
    "Savings", "Utilities", "Other",
]


def _get_categories() -> list[str]:
    """Return categories including any custom ones, excluding hidden."""
    settings = load_json("settings.json", default={})
    custom = settings.get("custom_categories", [])
    if not custom:
        return DEFAULT_CATEGORIES
    visible = [c["name"] for c in custom if not c.get("hidden", False)]
    return visible if visible else DEFAULT_CATEGORIES


CATEGORIES = _get_categories()

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
    # Check custom category keywords first
    settings = load_json("settings.json", default={})
    custom_keywords = settings.get("custom_category_keywords", {})
    for cat, keywords in custom_keywords.items():
        for kw in keywords:
            if kw.lower() in desc_lower:
                return cat
    # Fall back to defaults
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

    # ── Custom Categories ────────────────────────────────────────────────
    with st.expander("📂 Manage Categories"):
        settings = load_json("settings.json", default={})
        custom_cats = settings.get("custom_categories", [])

        # Initialize from defaults if empty
        if not custom_cats:
            custom_cats = [{"name": c, "hidden": False, "order": i} for i, c in enumerate(DEFAULT_CATEGORIES)]

        st.caption("Add, hide, or reorder budget categories.")

        # Add new category
        with st.form("add_cat_form", clear_on_submit=True):
            ac1, ac2 = st.columns([3, 1])
            with ac1:
                new_cat_name = st.text_input("New category name", placeholder="e.g., Pet Care")
            with ac2:
                st.markdown("<br>", unsafe_allow_html=True)
                add_cat = st.form_submit_button("➕ Add", use_container_width=True)
            if add_cat and new_cat_name.strip():
                existing_names = [c["name"].lower() for c in custom_cats]
                if new_cat_name.strip().lower() in existing_names:
                    st.error("Category already exists.")
                else:
                    custom_cats.append({
                        "name": new_cat_name.strip(),
                        "hidden": False,
                        "order": len(custom_cats),
                    })
                    settings["custom_categories"] = custom_cats
                    save_json("settings.json", settings)
                    st.toast(f"Added category '{new_cat_name.strip()}'!", icon="✅")
                    st.rerun()

        # Show / hide / rename
        _cat_changed = False
        for i, cat in enumerate(custom_cats):
            cc1, cc2, cc3 = st.columns([3, 1, 1])
            with cc1:
                hidden_label = " (hidden)" if cat.get("hidden") else ""
                st.markdown(f"**{cat['name']}**{hidden_label}")
            with cc2:
                if cat.get("hidden"):
                    if st.button("Show", key=f"show_cat_{i}", use_container_width=True):
                        custom_cats[i]["hidden"] = False
                        _cat_changed = True
                else:
                    if st.button("Hide", key=f"hide_cat_{i}", use_container_width=True):
                        custom_cats[i]["hidden"] = True
                        _cat_changed = True
            with cc3:
                if cat["name"] not in DEFAULT_CATEGORIES:
                    if st.button("🗑️", key=f"del_cat_{i}", use_container_width=True):
                        custom_cats.pop(i)
                        _cat_changed = True

        if _cat_changed:
            settings["custom_categories"] = custom_cats
            save_json("settings.json", settings)
            st.toast("Categories updated!", icon="✅")
            st.rerun()

    # ── Tabs ────────────────────────────────────────────────────────────
    tab_track, tab_analyze = st.tabs(["📋 Track", "📊 Analyze"])

    with tab_track:
        _render_track_tab(data, budgets)

    with tab_analyze:
        _render_analyze_tab(budgets)


def _render_track_tab(data, budgets):
    """Render the main tracking tab with import and spending analysis."""
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
            from utils.ui_helpers import render_empty_state
            render_empty_state("💰", "No budgets set yet",
                               "Set your monthly budgets above, then import a bank statement to track spending.")
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

    # Fire notification alerts
    _check_budget_alerts(budgets, spending_by_cat, total_budget, total_spent, days_remaining)

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
                f'<div style="background:var(--fk-progress-bg);border-radius:6px;height:16px;overflow:hidden;">'
                f'<div style="background:{bar_color};width:{pct_capped:.1f}%;height:100%;'
                f'border-radius:6px;"></div></div>',
                unsafe_allow_html=True,
            )
        with col2:
            if budget > 0:
                st.markdown(
                    f'<div style="text-align:right;font-size:0.85rem;color:var(--fk-text-muted);padding-top:6px;">'
                    f'{format_currency_int(spent)} / {format_currency_int(budget)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="text-align:right;font-size:0.85rem;color:var(--fk-text-muted);padding-top:6px;">'
                    f'{format_currency_int(spent)}</div>',
                    unsafe_allow_html=True,
                )

    # Donut chart
    if total_budget > 0:
        st.markdown("---")
        st.markdown("### Spending Overview")
        dc1, dc2 = st.columns([1, 2])
        with dc1:
            _tc = _theme_colors()
            fig = go.Figure(go.Pie(
                labels=["Spent", "Remaining"],
                values=[min(total_spent, total_budget), max(0, total_budget - total_spent)],
                hole=0.65,
                marker_colors=["#6366f1", _tc["grid"]],
                textinfo="percent",
                hovertemplate=f"%{{label}}: {get_currency_symbol()}%{{value:,.0f}}<extra></extra>",
            ))
            fig.update_layout(
                height=260,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                font=_chart_font(),
                annotations=[{
                    "text": f"{format_currency_int(total_spent)}<br><span style='font-size:11px'>spent</span>",
                    "x": 0.5, "y": 0.5, "font_size": 18,
                    "showarrow": False, "font_color": _tc["font_color"],
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
                apply_layout(fig2, height=260, margin=dict(t=10, b=10, l=10, r=60), showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)


def _check_budget_alerts(budgets, spending_by_cat, total_budget, total_spent, days_remaining):
    """Fire notification alerts for budget conditions."""
    sym = get_currency_symbol()
    prefs = load_json("settings.json", default={}).get("notifications", {})
    warn_pct = prefs.get("budget_warn_pct", 80)

    for cat, budget in budgets.items():
        if budget <= 0:
            continue
        spent = spending_by_cat.get(cat, 0)
        pct = spent / budget * 100
        remaining = budget - spent

        if pct >= 100:
            over = spent - budget
            create_notification(
                "alert", "budget",
                f"{cat} over budget",
                f"You've exceeded your {cat} budget by {sym}{over:,.0f}",
                action_module="budget_tracker",
            )
        elif pct >= warn_pct:
            create_notification(
                "warning", "budget",
                f"{cat} at {pct:.0f}% of budget",
                f"{cat} is at {pct:.0f}% of your {sym}{budget:,.0f} budget — {sym}{remaining:,.0f} remaining",
                action_module="budget_tracker",
            )

    if total_budget > 0:
        total_pct = total_spent / total_budget * 100
        if total_pct >= 90:
            create_notification(
                "warning", "budget",
                f"Total spending at {total_pct:.0f}%",
                f"You've used {total_pct:.0f}% of your total monthly budget with {days_remaining} days remaining",
                action_module="budget_tracker",
            )


def _render_analyze_tab(budgets):
    """Render the analytics tab with deep spending analysis."""
    from utils.insights import generate_insights

    expenses = st.session_state.get("budget_transactions")
    if expenses is None or expenses.empty:
        from utils.ui_helpers import render_empty_state
        render_empty_state("📊", "No transaction data yet",
                           "Import a bank statement in the Track tab to unlock spending analytics.")
        return

    sym = get_currency_symbol()
    expenses = expenses.copy()
    expenses["month_key"] = expenses["date"].dt.to_period("M").astype(str)
    months_available = sorted(expenses["month_key"].unique(), reverse=True)
    today = date.today()

    # ── Spending Insights ────────────────────────────────────────────────
    insights = generate_insights(limit=5)
    if insights:
        st.markdown("### 💡 Spending Insights")
        for ins in insights:
            css_cls = ins.get("type", "tip")
            st.markdown(
                f'<div class="insight-card {css_cls}">'
                f'<div class="insight-text">{ins["text"]}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("")

    # ── Budget vs Actual Table ───────────────────────────────────────────
    st.markdown("### 📋 Budget vs Actual")
    this_month = months_available[0]
    this_df = expenses[expenses["month_key"] == this_month]
    this_by_cat = this_df.groupby("category")["amount"].sum()

    table_rows = []
    for cat in CATEGORIES:
        budget = float(budgets.get(cat, 0))
        actual = this_by_cat.get(cat, 0)
        remaining = budget - actual
        var_pct = (actual / budget * 100) if budget > 0 else (100.0 if actual > 0 else 0.0)
        if var_pct >= 100:
            status = "🔴 Over"
        elif var_pct >= 80:
            status = "🟡 Near"
        else:
            status = "🟢 Under"
        table_rows.append({
            "Category": cat,
            f"Budget ({sym})": round(budget, 0),
            f"Actual ({sym})": round(actual, 2),
            f"Remaining ({sym})": round(remaining, 2),
            "Variance (%)": round(var_pct, 1),
            "Status": status,
        })

    # Total row
    total_budget = sum(float(budgets.get(cat, 0)) for cat in CATEGORIES)
    total_actual = this_by_cat.sum()
    total_remaining = total_budget - total_actual
    total_var_pct = (total_actual / total_budget * 100) if total_budget > 0 else 0
    table_rows.append({
        "Category": "**TOTAL**",
        f"Budget ({sym})": round(total_budget, 0),
        f"Actual ({sym})": round(total_actual, 2),
        f"Remaining ({sym})": round(total_remaining, 2),
        "Variance (%)": round(total_var_pct, 1),
        "Status": "🔴 Over" if total_var_pct >= 100 else ("🟡 Near" if total_var_pct >= 80 else "🟢 Under"),
    })

    table_df = pd.DataFrame(table_rows)
    st.dataframe(table_df, use_container_width=True, hide_index=True)

    # ── Spending Forecast ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔮 Spending Forecast")
    import calendar as _cal
    day_of_month = today.day
    days_in_month = _cal.monthrange(today.year, today.month)[1]

    if day_of_month > 0:
        forecast_rows = []
        for cat in CATEGORIES:
            budget = float(budgets.get(cat, 0))
            actual = this_by_cat.get(cat, 0)
            if actual > 0 and day_of_month > 0:
                daily_rate = actual / day_of_month
                projected = daily_rate * days_in_month
            else:
                projected = 0
            forecast_rows.append({
                "Category": cat,
                "Actual So Far": actual,
                "Projected Total": projected,
                "Budget": budget,
            })

        forecast_df = pd.DataFrame(forecast_rows)
        forecast_df = forecast_df[forecast_df["Projected Total"] > 0].sort_values("Projected Total", ascending=True)

        if not forecast_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=forecast_df["Category"],
                x=forecast_df["Actual So Far"],
                name="Spent",
                orientation="h",
                marker_color="#6366f1",
            ))
            fig.add_trace(go.Bar(
                y=forecast_df["Category"],
                x=forecast_df["Projected Total"] - forecast_df["Actual So Far"],
                name="Projected Remaining",
                orientation="h",
                marker_color="rgba(99,102,241,0.3)",
            ))
            # Budget markers
            for _, row in forecast_df.iterrows():
                if row["Budget"] > 0:
                    fig.add_shape(
                        type="line",
                        y0=row["Category"], y1=row["Category"],
                        x0=row["Budget"], x1=row["Budget"],
                        line=dict(color="#ef4444", width=2, dash="dash"),
                    )

            apply_layout(fig, height=max(300, len(forecast_df) * 35),
                         margin=dict(t=10, b=10, l=10, r=60),
                         barmode="stack", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

            total_projected = sum(r["Projected Total"] for _, r in forecast_df.iterrows())
            if total_budget > 0:
                if total_projected > total_budget:
                    st.warning(
                        f"⚠️ At your current pace, you'll spend **{format_currency_int(total_projected)}** "
                        f"by end of month (budget: {format_currency_int(total_budget)})"
                    )
                else:
                    st.success(
                        f"✅ On track! Projected: **{format_currency_int(total_projected)}** "
                        f"(budget: {format_currency_int(total_budget)})"
                    )

    # ── Spending Trends (6 months) ───────────────────────────────────────
    if len(months_available) >= 2:
        st.markdown("---")
        st.markdown("### 📈 Spending Trends")
        trend_months = months_available[:6]
        trend_data = []
        for m in trend_months:
            m_df = expenses[expenses["month_key"] == m]
            m_by_cat = m_df.groupby("category")["amount"].sum()
            for cat in CATEGORIES:
                trend_data.append({"Month": m, "Category": cat, "Amount": m_by_cat.get(cat, 0)})

        trend_df = pd.DataFrame(trend_data)
        # Top 5 categories by total spend
        cat_totals = trend_df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        top_cats = cat_totals.head(5).index.tolist()
        top_df = trend_df[trend_df["Category"].isin(top_cats)].sort_values("Month")

        # Add total line
        total_by_month = trend_df.groupby("Month")["Amount"].sum().reset_index()
        total_by_month["Category"] = "Total"
        total_by_month.columns = ["Month", "Amount", "Category"]
        plot_df = pd.concat([top_df, total_by_month], ignore_index=True)

        fig = px.line(
            plot_df, x="Month", y="Amount", color="Category",
            markers=True,
            color_discrete_sequence=CHART_COLORS + ["#ffffff"],
        )
        apply_layout(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)

    # ── Top 10 Merchants ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🏪 Top 10 Merchants")
    this_df_merchants = this_df.copy()
    # Normalize merchant names
    this_df_merchants["merchant"] = this_df_merchants["description"].str.strip().str.title()
    merchant_totals = this_df_merchants.groupby("merchant").agg(
        total=("amount", "sum"),
        count=("amount", "count"),
    ).sort_values("total", ascending=False).head(10)

    if not merchant_totals.empty:
        merchant_totals = merchant_totals.reset_index()
        merchant_totals["label"] = merchant_totals.apply(
            lambda r: f"{r['merchant']} ({int(r['count'])} txns)", axis=1
        )
        fig = px.bar(
            merchant_totals, x="total", y="label",
            orientation="h",
            color_discrete_sequence=["#8b5cf6"],
            text="total",
        )
        fig.update_traces(texttemplate=f"{sym}%{{text:,.0f}}", textposition="outside")
        apply_layout(fig, height=max(300, len(merchant_totals) * 35),
                     margin=dict(t=10, b=10, l=10, r=80), showlegend=False)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    # ── Day-of-Week Spending ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📅 Day-of-Week Spending Pattern")
    this_df_dow = this_df.copy()
    this_df_dow["dow"] = this_df_dow["date"].dt.dayofweek
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    dow_avg = this_df_dow.groupby("dow")["amount"].mean().reindex(range(7), fill_value=0)

    fig = go.Figure(go.Bar(
        x=dow_names,
        y=dow_avg.values,
        marker_color=["#6366f1" if v < dow_avg.max() else "#ef4444" for v in dow_avg.values],
        text=[f"{sym}{v:,.0f}" for v in dow_avg.values],
        textposition="outside",
    ))
    apply_layout(fig, height=300, margin=dict(t=10, b=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Weekend vs weekday insight
    weekday_avg = dow_avg.iloc[:5].mean()
    weekend_avg = dow_avg.iloc[5:].mean()
    if weekday_avg > 0 and weekend_avg > 0:
        if weekend_avg > weekday_avg:
            pct = (weekend_avg - weekday_avg) / weekday_avg * 100
            st.info(f"💡 You spend **{pct:.0f}% more** on weekends than weekdays.")
        else:
            pct = (weekday_avg - weekend_avg) / weekday_avg * 100
            st.info(f"💡 You spend **{pct:.0f}% less** on weekends than weekdays.")
