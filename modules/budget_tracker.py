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
    "Savings", "Utilities", "Income", "Other",
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
    "Housing": ["rent", "mortgage", "apartment", "lease", "hoa", "property", "landlord",
                "real estate", "homeowner", "condo", "townhouse", "housing"],
    "Food & Groceries": ["walmart", "costco", "kroger", "safeway", "trader joe", "whole foods",
                         "aldi", "grocery", "market", "supermarket", "food", "publix", "wegmans",
                         "sprouts", "food lion", "giant", "stop & shop", "piggly", "winn-dixie",
                         "h-e-b", "meijer", "winco", "fresh market", "food mart", "grocer"],
    "Dining Out": ["restaurant", "mcdonald", "starbucks", "chipotle", "pizza", "burger", "cafe",
                   "diner", "grubhub", "doordash", "uber eats", "seamless", "taco bell", "subway",
                   "wendy", "chick-fil", "panera", "shake shack", "applebee", "olive garden",
                   "domino", "papa john", "kfc", "popeye", "five guys", "in-n-out", "panda express",
                   "wingstop", "zaxby", "buffalo wild", "ihop", "denny", "waffle house", "cracker barrel",
                   "outback", "red lobster", "texas roadhouse", "cheesecake factory", "postmates"],
    "Transportation": ["uber", "lyft", "gas", "shell", "chevron", "bp", "exxon", "parking",
                       "transit", "metro", "bus", "train", "toll", "auto", "zipcar", "enterprise",
                       "hertz", "avis", "car wash", "oil change", "tire", "mechanic", "dmv",
                       "registration", "insurance auto", "car payment", "fuel", "speedway",
                       "wawa", "sunoco", "marathon", "citgo", "valero", "costco gas"],
    "Entertainment": ["netflix", "hulu", "disney", "hbo", "cinema", "movie", "theater",
                      "youtube", "twitch", "steam", "gaming", "concert", "ticket", "amazon prime video",
                      "paramount+", "peacock", "crunchyroll", "funimation", "amc", "regal",
                      "xbox", "playstation", "nintendo", "epic games", "ticketmaster",
                      "stubhub", "fandango", "bowling", "arcade", "amusement", "zoo", "museum"],
    "Subscriptions": ["spotify", "apple music", "subscription", "membership", "adobe", "dropbox",
                      "icloud", "google one", "amazon prime", "linkedin premium", "patreon",
                      "microsoft 365", "notion", "canva", "grammarly", "nordvpn", "expressvpn",
                      "1password", "lastpass", "evernote", "headspace", "calm", "duolingo",
                      "autopay", "recurring", "monthly fee", "annual fee", "renewal"],
    "Shopping": ["amazon", "target", "best buy", "ebay", "etsy", "ikea", "nike", "adidas",
                 "zara", "h&m", "nordstrom", "macy", "clothing", "apparel",
                 "old navy", "gap", "uniqlo", "shein", "temu", "wish", "wayfair",
                 "home depot", "lowe", "bed bath", "pottery barn", "crate & barrel",
                 "tj maxx", "marshalls", "ross", "burlington", "dollar tree", "five below",
                 "office depot", "staples", "michaels", "hobby lobby"],
    "Health": ["pharmacy", "cvs", "walgreens", "doctor", "hospital", "clinic", "dental",
               "gym", "fitness", "peloton", "health", "medical", "urgent care", "vision",
               "optometrist", "dermatolog", "therapist", "counseling", "prescription",
               "copay", "deductible", "lab", "blood work", "x-ray", "physical therapy",
               "chiropract", "acupuncture", "planet fitness", "la fitness", "anytime fitness",
               "orangetheory", "crossfit", "yoga", "pilates"],
    "Savings": ["savings", "transfer to savings", "invest", "401k", "ira", "brokerage",
                "vanguard", "fidelity", "schwab", "wealthfront", "betterment", "robinhood",
                "acorns", "stash", "sofi invest", "td ameritrade", "etrade", "roth"],
    "Utilities": ["electric", "water", "gas bill", "internet", "comcast", "att", "verizon",
                  "t-mobile", "utility", "phone", "cable", "spectrum", "xfinity", "pge",
                  "duke energy", "con edison", "national grid", "sewage", "trash", "waste",
                  "cox", "frontier", "centurylink", "cricket", "boost mobile", "mint mobile",
                  "google fi", "visible", "electric bill", "power bill", "heating"],
    "Income": ["payroll", "direct deposit", "salary", "wages", "pay check", "paycheck",
               "employer", "ach deposit", "income", "bonus", "commission", "freelance pay",
               "tax refund", "refund", "reimbursement", "cash back", "cashback", "dividend",
               "interest earned", "interest income", "rental income", "side hustle"],
}

BUDGET_TEMPLATES = {
    "Student": {
        "Housing": 600, "Food & Groceries": 200, "Dining Out": 80,
        "Transportation": 50, "Entertainment": 50, "Subscriptions": 20,
        "Shopping": 60, "Health": 30, "Savings": 50, "Utilities": 40, "Income": 0, "Other": 70,
    },
    "Freelancer": {
        "Housing": 1500, "Food & Groceries": 400, "Dining Out": 200,
        "Transportation": 150, "Entertainment": 100, "Subscriptions": 100,
        "Shopping": 150, "Health": 200, "Savings": 500, "Utilities": 150, "Income": 0, "Other": 300,
    },
    "Family": {
        "Housing": 2000, "Food & Groceries": 800, "Dining Out": 300,
        "Transportation": 400, "Entertainment": 200, "Subscriptions": 80,
        "Shopping": 300, "Health": 300, "Savings": 500, "Utilities": 250, "Income": 0, "Other": 370,
    },
    "Single Professional": {
        "Housing": 1800, "Food & Groceries": 300, "Dining Out": 400,
        "Transportation": 200, "Entertainment": 300, "Subscriptions": 80,
        "Shopping": 200, "Health": 150, "Savings": 400, "Utilities": 120, "Income": 0, "Other": 250,
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


def _categorize(description: str, amount: float | None = None) -> str:
    """Auto-categorize a transaction description.

    Priority: learned rules > custom keywords > built-in keywords > "Other".
    Negative amounts (credits) with income-like descriptions → "Income".
    """
    # Check learned rules first (highest priority)
    from utils.category_learner import get_learned_category
    learned = get_learned_category(description)
    if learned:
        return learned

    desc_lower = description.lower()

    # Auto-detect income from negative amounts (credits)
    if amount is not None and amount < 0:
        for kw in CATEGORY_MAP.get("Income", []):
            if kw in desc_lower:
                return "Income"

    # Check custom category keywords
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


@st.dialog("Add Transaction")
def _add_transaction_dialog():
    """Quick manual transaction entry dialog (v4.8)."""
    st.markdown("Add a single expense manually.")
    with st.form("manual_txn_form", clear_on_submit=True):
        tc1, tc2 = st.columns(2)
        with tc1:
            txn_date = st.date_input("Date", value=date.today())
            txn_amount = st.number_input("Amount ($)", min_value=0.01, value=10.0, step=1.0)
        with tc2:
            txn_desc = st.text_input("Description", placeholder="e.g., Starbucks coffee")
            txn_cat = st.selectbox("Category", CATEGORIES)

        if st.form_submit_button("Add Expense", type="primary", width='stretch'):
            if not txn_desc.strip():
                st.error("Please enter a description.")
            else:
                # Load existing transactions and append
                existing = load_json(TRANSACTIONS_FILE, default=[])
                new_txn = {
                    "date": str(txn_date),
                    "description": txn_desc.strip(),
                    "amount": float(txn_amount),
                    "category": txn_cat,
                    "month": txn_date.strftime("%Y-%m"),
                    "source": "manual",
                }
                existing.append(new_txn)
                save_json(TRANSACTIONS_FILE, existing)

                # Also update session state if loaded
                if "budget_transactions" in st.session_state:
                    new_row = pd.DataFrame([new_txn])
                    new_row["date"] = pd.to_datetime(new_row["date"])
                    st.session_state.budget_transactions = pd.concat(
                        [st.session_state.budget_transactions, new_row], ignore_index=True
                    )

                st.toast(f"Added {format_currency(txn_amount)} — {txn_desc}", icon="✅")
                st.rerun()


def render():
    render_module_header("💰", "Budget Tracker", "Set monthly budgets by category and track where your money goes.")

    # Auto-open transaction dialog if triggered from dashboard
    if st.session_state.pop("auto_open_form", False):
        _add_transaction_dialog()

    # Quick add button
    if st.button("➕ Add Transaction", type="primary"):
        _add_transaction_dialog()

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
            if st.button("📋 Load Template", width='stretch') and template != "— custom —":
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
            if st.form_submit_button("💾 Save Budgets", type="primary", width='stretch'):
                data["budgets"] = new_budgets
                budgets = new_budgets
                st.session_state.budget_data = data
                _save(data)
                st.toast("Budgets saved!", icon="✅")
                st.rerun()

    # ── Rollover toggle ──────────────────────────────────────────────────
    settings_roll = load_json("settings.json", default={})
    rollover_enabled = settings_roll.get("budget_rollover", False)
    new_rollover = st.checkbox("🔄 Enable budget rollover (unused budget carries to next month)",
                                value=rollover_enabled, key="rollover_toggle")
    if new_rollover != rollover_enabled:
        settings_roll["budget_rollover"] = new_rollover
        save_json("settings.json", settings_roll)
        st.toast("Rollover " + ("enabled" if new_rollover else "disabled") + "!", icon="✅")
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
                add_cat = st.form_submit_button("➕ Add", width='stretch')
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
                    if st.button("Show", key=f"show_cat_{i}", width='stretch'):
                        custom_cats[i]["hidden"] = False
                        _cat_changed = True
                else:
                    if st.button("Hide", key=f"hide_cat_{i}", width='stretch'):
                        custom_cats[i]["hidden"] = True
                        _cat_changed = True
            with cc3:
                if cat["name"] not in DEFAULT_CATEGORIES:
                    if st.button("🗑️", key=f"del_cat_{i}", width='stretch'):
                        custom_cats.pop(i)
                        _cat_changed = True

        if _cat_changed:
            settings["custom_categories"] = custom_cats
            save_json("settings.json", settings)
            st.toast("Categories updated!", icon="✅")
            st.rerun()

    # ── Tabs ────────────────────────────────────────────────────────────
    from utils.household import is_household_enabled
    _hh_active = is_household_enabled()

    if _hh_active:
        tab_track, tab_analyze, tab_scenarios, tab_bills, tab_splits = st.tabs(
            ["📋 Track", "📊 Analyze", "🔄 Scenarios", "📅 Bills", "✂️ Splits"]
        )
    else:
        tab_track, tab_analyze, tab_scenarios, tab_bills = st.tabs(
            ["📋 Track", "📊 Analyze", "🔄 Scenarios", "📅 Bills"]
        )
        tab_splits = None

    with tab_track:
        _render_track_tab(data, budgets)

    with tab_analyze:
        _render_analyze_tab(budgets)

    with tab_scenarios:
        _render_scenarios_tab(budgets)

    with tab_bills:
        _render_bills_tab()

    if tab_splits is not None:
        with tab_splits:
            _render_splits_tab()


def _render_track_tab(data, budgets):
    """Render the main tracking tab with import and spending analysis."""
    # ── Import Transactions ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Import Bank Transactions")
    st.caption("Upload a CSV from your bank to see spending vs. budget. Same format as the Report Generator.")

    # Account selector for import
    accounts = load_json("accounts.json", default=[])
    selected_account_id = None
    if accounts:
        acc_options = ["All Accounts"] + [f"{a['name']} (····{a.get('last_four','')})" for a in accounts]
        acc_choice = st.selectbox("Account", acc_options, key="budget_import_account")
        if acc_choice != "All Accounts":
            idx = acc_options.index(acc_choice) - 1
            selected_account_id = accounts[idx]["id"]

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
                        if selected_account_id:
                            expenses["account_id"] = selected_account_id
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
        if st.session_state.get("confirm_clear_budget"):
            if st.button("⚠️ Confirm?", width='stretch', type="primary"):
                del st.session_state.budget_transactions
                save_json(TRANSACTIONS_FILE, [])
                st.session_state.pop("confirm_clear_budget", None)
                st.rerun()
        else:
            if st.button("🗑️ Clear Data", width='stretch'):
                st.session_state["confirm_clear_budget"] = True
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
        st.plotly_chart(fig, width='stretch')

    # ── Editable category assignments with pagination (v4.8) ──────────────
    st.markdown("---")
    with st.expander("🏷️ Review & Edit Transaction Categories"):
        from utils.category_learner import is_learned, get_rules_by_category
        learned_count = sum(1 for _, row in month_expenses.iterrows() if is_learned(row.get("description", "")))
        keyword_count = len(month_expenses) - learned_count
        rules_count = sum(get_rules_by_category().values())
        st.caption(
            f"🤖 {learned_count} learned · 🔑 {keyword_count} keyword-matched"
            f" · {rules_count} rule{'s' if rules_count != 1 else ''} total"
            f" · {len(month_expenses)} transactions"
        )
        month_exp_display = month_expenses[["date", "description", "amount", "category"]].copy()
        month_exp_display["date"] = month_exp_display["date"].dt.strftime("%Y-%m-%d")

        # Pagination (v4.8)
        _page_size = 25
        _total_txns = len(month_exp_display)
        _total_pages = max(1, (_total_txns + _page_size - 1) // _page_size)
        if _total_txns > _page_size:
            _pg_col1, _pg_col2, _pg_col3 = st.columns([1, 2, 1])
            with _pg_col2:
                _current_page = st.number_input(
                    f"Page (1–{_total_pages})", min_value=1, max_value=_total_pages,
                    value=1, step=1, key="txn_page",
                )
            _start = (_current_page - 1) * _page_size
            _end = min(_start + _page_size, _total_txns)
            _page_display = month_exp_display.iloc[_start:_end]
            st.caption(f"Showing {_start+1}–{_end} of {_total_txns}")
        else:
            _page_display = month_exp_display

        edited = st.data_editor(
            _page_display,
            column_config={
                "category": st.column_config.SelectboxColumn(options=CATEGORIES),
                "amount": st.column_config.NumberColumn(format="$%.2f"),
            },
            width='stretch',
            hide_index=True,
            num_rows="fixed",
            key="budget_editor",
        )
        if st.button("💾 Apply Category Edits"):
            from utils.category_learner import learn_from_correction
            # Update the session state transactions with edited categories
            for idx, row in edited.iterrows():
                mask = (
                    (expenses["description"] == row["description"]) &
                    (expenses["month"] == selected_month)
                )
                matched = expenses.loc[mask]
                if not matched.empty:
                    old_cat = matched.iloc[0]["category"]
                    new_cat = row["category"]
                    if old_cat != new_cat:
                        learn_from_correction(row["description"], old_cat, new_cat)
                expenses.loc[mask, "category"] = row["category"]
            st.session_state.budget_transactions = expenses
            _save_transactions(expenses)
            st.toast("Categories updated! Future imports will remember your changes.", icon="✅")
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
    today = date.today()
    day_of_month = today.day
    days_in_month = _cal.monthrange(today.year, today.month)[1]
    days_remaining = days_in_month - day_of_month
    pct_used = int(total_spent / total_budget * 100) if total_budget > 0 else 0
    _rem_color = "var(--fk-success)" if remaining >= 0 else "var(--fk-danger)"

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">💰 Budgeted</div>'
            f'<div class="widget-value">{format_currency_int(total_budget)}</div>'
            f'<div class="widget-sub">{len([c for c in budgets if budgets[c] > 0])} categories</div></div>',
            unsafe_allow_html=True,
        )
    with mc2:
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">📊 Spent</div>'
            f'<div class="widget-value">{format_currency_int(total_spent)}</div>'
            f'<div class="widget-sub">{pct_used}% of budget</div></div>',
            unsafe_allow_html=True,
        )
    with mc3:
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">{"✅" if remaining >= 0 else "🚨"} Remaining</div>'
            f'<div class="widget-value" style="color:{_rem_color};">{format_currency_int(remaining)}</div>'
            f'<div class="widget-sub">{"Under" if remaining >= 0 else "Over"} by {format_currency_int(abs(remaining))}</div></div>',
            unsafe_allow_html=True,
        )
    with mc4:
        if day_of_month > 0 and total_spent > 0:
            daily_avg = total_spent / day_of_month
            projected = daily_avg * days_in_month
            st.markdown(
                f'<div class="dash-widget"><div class="widget-title">📅 Daily Avg</div>'
                f'<div class="widget-value">{format_currency_int(daily_avg)}/d</div>'
                f'<div class="widget-sub">{days_remaining}d left · proj: {format_currency_int(projected)}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="dash-widget"><div class="widget-title">📅 Days Left</div>'
                f'<div class="widget-value">{days_remaining}</div>'
                f'<div class="widget-sub">days remaining</div></div>',
                unsafe_allow_html=True,
            )

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
            st.plotly_chart(fig, width='stretch')
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
                st.plotly_chart(fig2, width='stretch')


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
    st.dataframe(table_df, width='stretch', hide_index=True)

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
            st.plotly_chart(fig, width='stretch')

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
        st.plotly_chart(fig, width='stretch')

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
        st.plotly_chart(fig, width='stretch')

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
    st.plotly_chart(fig, width='stretch')

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


# ── Bills Tab ───────────────────────────────────────────────────────────

BILLS_FILE = "bills.json"


def _load_bills() -> list[dict]:
    return load_json(BILLS_FILE, default=[])


def _save_bills(bills: list[dict]):
    save_json(BILLS_FILE, bills)


def _next_due_date(bill: dict) -> date:
    """Calculate the next due date for a bill."""
    import calendar as _cal
    today = date.today()
    due_day = bill.get("due_day", 1)
    freq = bill.get("frequency", "monthly")

    # Clamp to valid day for current month
    _, max_day = _cal.monthrange(today.year, today.month)
    clamped_day = min(due_day, max_day)
    this_month_due = date(today.year, today.month, clamped_day)

    if freq == "weekly":
        # Next occurrence of that weekday (due_day = 0-6 Mon-Sun)
        days_ahead = (due_day - today.weekday()) % 7
        return today + pd.Timedelta(days=days_ahead if days_ahead > 0 else 7)

    if this_month_due >= today:
        return this_month_due

    # Move to next period
    if freq == "monthly":
        next_month = today.month + 1
        next_year = today.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        _, max_day = _cal.monthrange(next_year, next_month)
        return date(next_year, next_month, min(due_day, max_day))
    elif freq == "quarterly":
        next_month = today.month + 3
        next_year = today.year
        while next_month > 12:
            next_month -= 12
            next_year += 1
        _, max_day = _cal.monthrange(next_year, next_month)
        return date(next_year, next_month, min(due_day, max_day))
    elif freq == "annually":
        return date(today.year + 1, today.month, clamped_day)

    return this_month_due


def _is_overdue(bill: dict) -> bool:
    """Check if a bill is overdue (past due_day, not paid this month)."""
    import calendar as _cal
    today = date.today()
    due_day = bill.get("due_day", 1)
    _, max_day = _cal.monthrange(today.year, today.month)
    clamped = min(due_day, max_day)

    if today.day <= clamped:
        return False

    last_paid = bill.get("last_paid", "")
    if last_paid:
        try:
            paid_dt = datetime.fromisoformat(last_paid).date()
            if paid_dt.year == today.year and paid_dt.month == today.month:
                return False
        except Exception:
            pass
    return True


def _days_until_due(bill: dict) -> int:
    """Days until next due date (negative = overdue)."""
    today = date.today()
    next_due = _next_due_date(bill)
    return (next_due - today).days


def get_upcoming_bills(days: int = 30) -> list[dict]:
    """Return bills due within the next N days, sorted by due date."""
    bills = _load_bills()
    today = date.today()
    upcoming = []
    for b in bills:
        if not b.get("active", True):
            continue
        next_due = _next_due_date(b)
        days_away = (next_due - today).days
        if days_away <= days:
            upcoming.append({**b, "_next_due": next_due, "_days_away": days_away})
    # Also check overdue
    for b in bills:
        if not b.get("active", True):
            continue
        if _is_overdue(b):
            next_due = _next_due_date(b)
            entry = {**b, "_next_due": next_due, "_days_away": -1, "_overdue": True}
            # Avoid duplicate
            if not any(u["id"] == b["id"] for u in upcoming):
                upcoming.append(entry)
    upcoming.sort(key=lambda x: x["_next_due"])
    return upcoming


def get_overdue_bills() -> list[dict]:
    """Return bills that are overdue."""
    bills = _load_bills()
    return [b for b in bills if b.get("active", True) and _is_overdue(b)]


def _render_bills_tab():
    """Render the Bills management tab."""
    from utils.ui_helpers import render_empty_state
    import calendar as _cal
    import uuid

    bills = _load_bills()

    # Summary metrics
    active_bills = [b for b in bills if b.get("active", True)]
    monthly_total = sum(
        b["amount"] for b in active_bills
        if b.get("frequency", "monthly") == "monthly"
    )
    quarterly_bills = sum(
        b["amount"] / 3 for b in active_bills
        if b.get("frequency") == "quarterly"
    )
    annual_bills = sum(
        b["amount"] / 12 for b in active_bills
        if b.get("frequency") == "annually"
    )
    est_monthly = monthly_total + quarterly_bills + annual_bills
    auto_count = sum(1 for b in active_bills if b.get("auto_pay"))
    manual_count = len(active_bills) - auto_count

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Monthly Bills", format_currency_int(est_monthly))
    m2.metric("Annual Estimate", format_currency_int(est_monthly * 12))
    m3.metric("Auto-Pay", f"{auto_count} bills")
    m4.metric("Manual", f"{manual_count} bills")

    # Add Bill form
    with st.expander("➕ Add New Bill", expanded=not bills):
        with st.form("add_bill_form", clear_on_submit=True):
            bc1, bc2 = st.columns(2)
            with bc1:
                bill_name = st.text_input("Bill Name", placeholder="e.g. Netflix")
                bill_amount = st.number_input("Amount", min_value=0.01, value=15.00, step=1.0, format="%.2f")
                bill_due_day = st.number_input("Due Day (1-31)", min_value=1, max_value=31, value=1)
            with bc2:
                bill_freq = st.selectbox("Frequency", ["monthly", "quarterly", "annually", "weekly"])
                bill_cat = st.selectbox("Category", CATEGORIES)
                bill_auto = st.checkbox("Auto-pay enabled")
            bill_notes = st.text_input("Notes (optional)", placeholder="Account ending in 1234")

            if st.form_submit_button("➕ Add Bill", type="primary", width='stretch'):
                new_bill = {
                    "id": str(uuid.uuid4())[:8],
                    "name": bill_name.strip(),
                    "amount": bill_amount,
                    "due_day": bill_due_day,
                    "frequency": bill_freq,
                    "category": bill_cat,
                    "auto_pay": bill_auto,
                    "last_paid": "",
                    "notes": bill_notes.strip(),
                    "active": True,
                }
                bills.append(new_bill)
                _save_bills(bills)
                from utils.activity_log import log_activity
                log_activity("added", "budget_tracker", f"Added bill: {bill_name}")
                st.toast(f"Bill '{bill_name}' added!", icon="✅")
                st.rerun()

    if not active_bills:
        render_empty_state("📅", "No bills yet", "Add your first bill above to start tracking due dates.")
        return

    # Upcoming Bills list
    st.markdown("### Upcoming Bills")
    upcoming = get_upcoming_bills(30)

    if upcoming:
        for ub in upcoming:
            overdue = ub.get("_overdue", False) or ub.get("_days_away", 99) < 0
            due_soon = 0 <= ub.get("_days_away", 99) <= 3
            if overdue:
                color = "var(--fk-danger)"
                badge = "OVERDUE"
            elif due_soon:
                color = "var(--fk-warning)"
                badge = f"Due in {ub['_days_away']} day{'s' if ub['_days_away'] != 1 else ''}"
            else:
                color = "var(--fk-success)"
                badge = f"Due in {ub['_days_away']} days"

            auto_tag = " · Auto-pay" if ub.get("auto_pay") else ""
            bc1, bc2 = st.columns([4, 1])
            with bc1:
                st.markdown(
                    f'<div style="padding:8px 12px;border-left:3px solid {color};'
                    f'background:var(--fk-card);border-radius:8px;margin-bottom:4px;">'
                    f'<span style="color:var(--fk-text);font-weight:600;">{ub["name"]}</span>'
                    f' — {format_currency(ub["amount"])}'
                    f'<span style="color:{color};font-size:0.78rem;margin-left:8px;">{badge}{auto_tag}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with bc2:
                if st.button("✅ Paid", key=f"paid_{ub['id']}", width='stretch'):
                    for b in bills:
                        if b["id"] == ub["id"]:
                            b["last_paid"] = date.today().isoformat()
                    _save_bills(bills)
                    st.toast(f"Marked {ub['name']} as paid!", icon="✅")
                    st.rerun()
    else:
        st.info("No bills due in the next 30 days.")

    # Monthly total due
    monthly_due = sum(ub["amount"] for ub in upcoming if ub.get("frequency", "monthly") == "monthly")
    if monthly_due > 0:
        st.caption(f"Total due this month: **{format_currency_int(monthly_due)}**")

    # ── Bill Calendar ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📅 Bill Calendar")

    today = date.today()
    cal_c1, cal_c2, cal_c3 = st.columns([1, 3, 1])
    cal_offset = st.session_state.get("bill_cal_offset", 0)
    with cal_c1:
        if st.button("← Prev", key="cal_prev", width='stretch'):
            st.session_state.bill_cal_offset = cal_offset - 1
            st.rerun()
    with cal_c3:
        if st.button("Next →", key="cal_next", width='stretch'):
            st.session_state.bill_cal_offset = cal_offset + 1
            st.rerun()

    cal_month = today.month + cal_offset
    cal_year = today.year
    while cal_month > 12:
        cal_month -= 12
        cal_year += 1
    while cal_month < 1:
        cal_month += 12
        cal_year -= 1

    with cal_c2:
        st.markdown(f"<div style='text-align:center;font-weight:600;'>"
                     f"{_cal.month_name[cal_month]} {cal_year}</div>", unsafe_allow_html=True)

    _, days_in_month = _cal.monthrange(cal_year, cal_month)
    first_dow = _cal.monthrange(cal_year, cal_month)[0]  # 0=Mon

    # Build bill-by-day mapping
    bills_by_day = {}
    for b in active_bills:
        day = min(b.get("due_day", 1), days_in_month)
        bills_by_day.setdefault(day, []).append(b)

    # Render calendar as HTML table
    header = "".join(f"<th style='padding:6px;color:var(--fk-text-muted);font-size:0.78rem;'>{d}</th>"
                     for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    rows = ""
    day = 1
    for week in range(6):
        if day > days_in_month:
            break
        cells = ""
        for dow in range(7):
            if (week == 0 and dow < first_dow) or day > days_in_month:
                cells += "<td style='padding:4px;'></td>"
            else:
                is_today = (day == today.day and cal_month == today.month and cal_year == today.year)
                bg = "var(--fk-accent)" if is_today else "transparent"
                text_color = "white" if is_today else "var(--fk-text)"
                day_bills = bills_by_day.get(day, [])
                bill_html = ""
                for db in day_bills:
                    bill_html += (
                        f"<div style='font-size:0.65rem;color:var(--fk-accent-light);overflow:hidden;"
                        f"text-overflow:ellipsis;white-space:nowrap;'>"
                        f"{db['name']} {format_currency(db['amount'])}</div>"
                    )
                cells += (
                    f"<td style='padding:4px;vertical-align:top;min-width:80px;height:60px;"
                    f"border:1px solid var(--fk-border);border-radius:4px;'>"
                    f"<div style='background:{bg};color:{text_color};border-radius:50%;width:22px;height:22px;"
                    f"display:flex;align-items:center;justify-content:center;font-size:0.78rem;font-weight:600;'>"
                    f"{day}</div>{bill_html}</td>"
                )
                day += 1
        rows += f"<tr>{cells}</tr>"

    st.markdown(
        f"<table style='width:100%;border-collapse:separate;border-spacing:2px;'>"
        f"<tr>{header}</tr>{rows}</table>",
        unsafe_allow_html=True,
    )

    # ── Manage Bills ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Manage Bills")
    for b in bills:
        bc1, bc2, bc3 = st.columns([4, 1, 1])
        status = "Active" if b.get("active", True) else "Inactive"
        freq = b.get("frequency", "monthly").title()
        with bc1:
            st.markdown(
                f"**{b['name']}** — {format_currency(b['amount'])} · {freq} · Day {b['due_day']} · {status}"
            )
        with bc2:
            if b.get("active", True):
                if st.button("Pause", key=f"pause_{b['id']}", width='stretch'):
                    b["active"] = False
                    _save_bills(bills)
                    st.rerun()
            else:
                if st.button("Resume", key=f"resume_{b['id']}", width='stretch'):
                    b["active"] = True
                    _save_bills(bills)
                    st.rerun()
        with bc3:
            if st.button("🗑️", key=f"del_bill_{b['id']}", width='stretch'):
                bills = [x for x in bills if x["id"] != b["id"]]
                _save_bills(bills)
                st.toast(f"Deleted {b['name']}", icon="🗑️")
                st.rerun()

    # ── Auto-detect bills from transactions ─────────────────────────────
    if "budget_transactions" in st.session_state:
        st.markdown("---")
        with st.expander("🔍 Detect Bills from Transaction History"):
            from utils.insights import detect_bills_from_transactions
            expenses = st.session_state.budget_transactions
            suggestions = detect_bills_from_transactions(expenses.to_dict("records"))
            existing_names = [b["name"].lower() for b in bills]
            suggestions = [s for s in suggestions if s["name"].lower() not in existing_names]
            if suggestions:
                st.caption(f"Found {len(suggestions)} potential recurring bill(s):")
                for s in suggestions[:5]:
                    sc1, sc2 = st.columns([4, 1])
                    with sc1:
                        st.markdown(
                            f"**{s['name']}** — ~{format_currency(s['amount'])} around day {s['due_day']}"
                        )
                    with sc2:
                        if st.button("➕ Add", key=f"add_det_{s['name'][:10]}", width='stretch'):
                            new_bill = {
                                "id": str(uuid.uuid4())[:8],
                                "name": s["name"],
                                "amount": s["amount"],
                                "due_day": s["due_day"],
                                "frequency": "monthly",
                                "category": s.get("category", "Other"),
                                "auto_pay": False,
                                "last_paid": "",
                                "notes": "Auto-detected from transaction history",
                                "active": True,
                            }
                            bills.append(new_bill)
                            _save_bills(bills)
                            st.toast(f"Added {s['name']} as a bill!", icon="✅")
                            st.rerun()
            else:
                st.info("No recurring patterns detected. Import more transaction history to improve detection.")


# ── Scenarios Tab ───────────────────────────────────────────────────────

SCENARIOS_FILE = "budget_scenarios.json"


def _render_scenarios_tab(budgets):
    """Render the what-if budget scenarios tab."""
    from utils.ui_helpers import render_empty_state
    import uuid

    scenarios = load_json(SCENARIOS_FILE, default=[])

    st.markdown("### What-If Budget Scenarios")
    st.caption("Create alternate budget plans and compare them to your current budget.")

    # Create new scenario
    with st.expander("➕ Create New Scenario", expanded=not scenarios):
        with st.form("new_scenario_form"):
            sc_name = st.text_input("Scenario Name", placeholder="e.g. Save More, Cut Dining Out")
            st.markdown("**Adjust budgets for this scenario:**")
            sc_budgets = {}
            cols = st.columns(3)
            for i, cat in enumerate(CATEGORIES):
                with cols[i % 3]:
                    sc_budgets[cat] = st.number_input(
                        cat,
                        min_value=0.0,
                        value=float(budgets.get(cat, 0)),
                        step=50.0,
                        format="%.0f",
                        key=f"sc_{cat}",
                    )
            if st.form_submit_button("💾 Save Scenario", type="primary", width='stretch'):
                if sc_name.strip():
                    scenarios.append({
                        "id": str(uuid.uuid4())[:8],
                        "name": sc_name.strip(),
                        "budgets": sc_budgets,
                        "created_at": datetime.now().isoformat(),
                    })
                    save_json(SCENARIOS_FILE, scenarios)
                    st.toast(f"Scenario '{sc_name}' saved!", icon="✅")
                    st.rerun()

    if not scenarios:
        render_empty_state("🔄", "No scenarios yet", "Create a scenario above to compare budget plans.")
        return

    # Compare scenario vs current budget
    st.markdown("---")
    sc_names = [s["name"] for s in scenarios]
    selected_sc = st.selectbox("Compare scenario", sc_names)
    sc = next((s for s in scenarios if s["name"] == selected_sc), None)

    if sc:
        sc_budgets = sc["budgets"]
        current_total = sum(float(budgets.get(c, 0)) for c in CATEGORIES)
        sc_total = sum(float(sc_budgets.get(c, 0)) for c in CATEGORIES)
        diff = current_total - sc_total
        monthly_savings = diff
        annual_savings = diff * 12

        m1, m2, m3 = st.columns(3)
        m1.metric("Current Budget", format_currency_int(current_total))
        m2.metric("Scenario Budget", format_currency_int(sc_total))
        m3.metric("Monthly Savings", format_currency_int(monthly_savings),
                   delta=f"{format_currency_int(annual_savings)}/year")

        # Side-by-side comparison chart
        comp_data = []
        for cat in CATEGORIES:
            curr_val = float(budgets.get(cat, 0))
            sc_val = float(sc_budgets.get(cat, 0))
            if curr_val > 0 or sc_val > 0:
                comp_data.append({"Category": cat, "Plan": "Current", "Budget": curr_val})
                comp_data.append({"Category": cat, "Plan": selected_sc, "Budget": sc_val})

        if comp_data:
            comp_df = pd.DataFrame(comp_data)
            fig = px.bar(
                comp_df, x="Category", y="Budget", color="Plan",
                barmode="group",
                color_discrete_sequence=["#6366f1", "#22c55e"],
            )
            apply_layout(fig, height=380, xaxis_tickangle=-25)
            st.plotly_chart(fig, width='stretch')

        # Impact summary
        if diff > 0:
            st.success(f"This scenario saves **{format_currency_int(diff)}/month** "
                       f"(**{format_currency_int(annual_savings)}/year**).")
        elif diff < 0:
            st.warning(f"This scenario costs **{format_currency_int(abs(diff))}/month** more "
                       f"(**{format_currency_int(abs(annual_savings))}/year** more).")
        else:
            st.info("This scenario has the same total budget as your current plan.")

        # Delete scenario
        if st.button(f"🗑️ Delete '{selected_sc}'", key="del_scenario"):
            scenarios = [s for s in scenarios if s["name"] != selected_sc]
            save_json(SCENARIOS_FILE, scenarios)
            st.toast(f"Deleted scenario '{selected_sc}'", icon="🗑️")
            st.rerun()

    # Seasonal patterns
    st.markdown("---")
    st.markdown("### 📅 Seasonal Spending Patterns")
    expenses = st.session_state.get("budget_transactions")
    if expenses is not None and not expenses.empty:
        expenses_c = expenses.copy()
        expenses_c["month_num"] = expenses_c["date"].dt.month
        months_covered = expenses_c["date"].dt.to_period("M").nunique()
        if months_covered >= 6:
            import calendar as _cal
            monthly_cat = expenses_c.groupby(["month_num", "category"])["amount"].sum().reset_index()
            # Average across years
            monthly_cat["amount"] = monthly_cat.groupby(["month_num", "category"])["amount"].transform("mean")
            monthly_cat = monthly_cat.drop_duplicates(subset=["month_num", "category"])
            monthly_cat["Month"] = monthly_cat["month_num"].apply(lambda m: _cal.month_abbr[m])

            # Top 5 categories
            top_cats = expenses_c.groupby("category")["amount"].sum().nlargest(5).index.tolist()
            plot_df = monthly_cat[monthly_cat["category"].isin(top_cats)]
            plot_df = plot_df.sort_values("month_num")

            if not plot_df.empty:
                fig = px.line(
                    plot_df, x="Month", y="amount", color="category",
                    markers=True,
                    color_discrete_sequence=CHART_COLORS,
                )
                apply_layout(fig, height=350)
                st.plotly_chart(fig, width='stretch')

                # Seasonal suggestions
                current_month = date.today().month
                for cat in top_cats:
                    cat_data = monthly_cat[monthly_cat["category"] == cat]
                    avg_all = cat_data["amount"].mean()
                    current_avg = cat_data[cat_data["month_num"] == current_month]["amount"].values
                    if len(current_avg) > 0 and avg_all > 0:
                        pct_diff = (current_avg[0] - avg_all) / avg_all * 100
                        if pct_diff > 20:
                            st.info(
                                f"💡 Your **{cat}** spending tends to be **{pct_diff:.0f}% higher** "
                                f"in {_cal.month_name[current_month]}. Consider budgeting "
                                f"{format_currency_int(current_avg[0])} instead of "
                                f"{format_currency_int(avg_all)}."
                            )
        else:
            st.info(f"Need at least 6 months of data for seasonal patterns. "
                    f"You have {months_covered} month(s) so far.")
    else:
        st.info("Import transaction data in the Track tab to see seasonal patterns.")


def _render_splits_tab():
    """Render split expense tracking for household members."""
    from utils.household import (
        get_member_names, create_split, get_balances,
        get_unsettled_splits, settle_split,
    )
    from utils.formatting import format_currency

    members = get_member_names()
    if not members:
        st.info("Add household members in **Settings > Household** to start splitting expenses.")
        return

    st.markdown("### Split an Expense")
    with st.form("split_expense_form", clear_on_submit=True):
        sc1, sc2 = st.columns(2)
        with sc1:
            split_desc = st.text_input("Description", placeholder="Dinner, Groceries, Rent...")
            split_amount = st.number_input("Total Amount", min_value=0.01, step=1.0, value=50.0)
            split_paid_by = st.selectbox("Paid By", members)
        with sc2:
            split_with = st.multiselect("Split With", [m for m in members if m != split_paid_by],
                                         default=[m for m in members if m != split_paid_by])
            split_method = st.selectbox("Split Method", ["Even", "By Percentage", "By Amount", "One Person Paid"])

        if st.form_submit_button("✂️ Create Split", type="primary", width='stretch'):
            if not split_desc:
                st.error("Please enter a description.")
            elif not split_with:
                st.error("Select at least one person to split with.")
            else:
                method_map = {"Even": "even", "By Percentage": "percentage",
                              "By Amount": "amount", "One Person Paid": "one_paid"}
                create_split(split_desc, split_amount, split_paid_by, split_with,
                             method=method_map[split_method])
                st.toast("Split created!", icon="✂️")
                st.rerun()

    # Balances
    st.markdown("---")
    st.markdown("### Who Owes Whom")
    balances = get_balances()
    if balances:
        for (debtor, creditor), amount in balances.items():
            st.markdown(f"- **{debtor}** owes **{creditor}**: {format_currency(amount)}")
    else:
        st.success("All settled up!")

    # Unsettled splits
    unsettled = get_unsettled_splits()
    if unsettled:
        st.markdown("---")
        st.markdown("### Unsettled Splits")
        for s in unsettled:
            with st.expander(f"{s['description']} — {format_currency(s['total'])} (paid by {s['paid_by']})"):
                st.caption(f"Method: {s['method']} | Created: {s['created']}")
                for person, share in s.get("shares", {}).items():
                    st.markdown(f"- {person}: {format_currency(share)}")
                if st.button("✅ Settle Up", key=f"settle_{s['id']}"):
                    settle_split(s["id"])
                    st.toast("Settled!", icon="✅")
                    st.rerun()
