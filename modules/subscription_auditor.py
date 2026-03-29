import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
from utils.fuzzy_matcher import group_similar_transactions
from utils.data_persistence import load_json, save_json
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout, _theme_colors, _chart_font
from utils.formatting import format_currency, get_currency_symbol
from utils.notifications import create_notification

DATA_FILE = "statement_transactions.json"
DECISIONS_FILE = "sub_decisions.json"
MANUAL_SUBS_FILE = "manual_subscriptions.json"
CANCELLED_FILE = "cancelled_subscriptions.json"
PRICE_HISTORY_FILE = "sub_price_history.json"
USAGE_NOTES_FILE = "sub_usage_notes.json"

SUB_CATEGORIES = [
    "Entertainment", "Productivity", "Cloud/Storage", "News/Media",
    "Health/Fitness", "Education", "Finance", "Shopping",
    "Communication", "Other",
]

# Known subscription services with typical monthly prices and cancellation URLs
KNOWN_SUBSCRIPTIONS = {
    "netflix": {"name": "Netflix", "price": 15.49, "cancel": "https://www.netflix.com/cancelplan", "category": "Entertainment"},
    "spotify": {"name": "Spotify", "price": 10.99, "cancel": "https://support.spotify.com/us/article/how-to-cancel/", "category": "Entertainment"},
    "hulu": {"name": "Hulu", "price": 7.99, "cancel": "https://help.hulu.com/s/article/cancel-account", "category": "Entertainment"},
    "disney": {"name": "Disney+", "price": 7.99, "cancel": "https://help.disneyplus.com/article/disneyplus-cancel-account", "category": "Entertainment"},
    "hbo": {"name": "HBO Max", "price": 15.99, "cancel": "https://help.max.com/us/Manage-Account", "category": "Entertainment"},
    "amazon prime": {"name": "Amazon Prime", "price": 14.99, "cancel": "https://www.amazon.com/gp/help/customer/display.html?nodeId=201118010", "category": "Shopping"},
    "apple music": {"name": "Apple Music", "price": 10.99, "cancel": "https://support.apple.com/en-us/HT202039", "category": "Entertainment"},
    "youtube premium": {"name": "YouTube Premium", "price": 13.99, "cancel": "https://support.google.com/youtube/answer/6308278", "category": "Entertainment"},
    "adobe": {"name": "Adobe Creative Cloud", "price": 54.99, "cancel": "https://helpx.adobe.com/manage-account/using/cancel-subscription.html", "category": "Productivity"},
    "dropbox": {"name": "Dropbox", "price": 11.99, "cancel": "https://help.dropbox.com/account-management/cancel-account", "category": "Cloud/Storage"},
    "icloud": {"name": "iCloud+", "price": 2.99, "cancel": "https://support.apple.com/en-us/HT207594", "category": "Cloud/Storage"},
    "google one": {"name": "Google One", "price": 2.99, "cancel": "https://support.google.com/googleone/answer/9004013", "category": "Cloud/Storage"},
    "linkedin premium": {"name": "LinkedIn Premium", "price": 29.99, "cancel": "https://www.linkedin.com/help/linkedin/answer/a545599", "category": "Productivity"},
    "paramount": {"name": "Paramount+", "price": 5.99, "cancel": "https://help.paramountplus.com/s/article/PD-How-do-I-cancel", "category": "Entertainment"},
    "peacock": {"name": "Peacock", "price": 5.99, "cancel": "https://www.peacocktv.com/help/cancel", "category": "Entertainment"},
    "nordvpn": {"name": "NordVPN", "price": 12.99, "cancel": "https://support.nordvpn.com/General-info/1047407532/How-can-I-cancel-my-subscription.htm", "category": "Communication"},
    "express vpn": {"name": "ExpressVPN", "price": 12.95, "cancel": "https://www.expressvpn.com/support/troubleshooting/cancel-subscription/", "category": "Communication"},
    "chatgpt": {"name": "ChatGPT Plus", "price": 20.00, "cancel": "https://help.openai.com/en/articles/subscription-management", "category": "Productivity"},
    "grammarly": {"name": "Grammarly", "price": 12.00, "cancel": "https://support.grammarly.com/hc/en-us/articles/115000090172", "category": "Productivity"},
    "notion": {"name": "Notion", "price": 8.00, "cancel": "https://www.notion.so/help/manage-your-subscription", "category": "Productivity"},
}


def _load_statements():
    data = load_json(DATA_FILE, default=[])
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()


def _save_statements(df):
    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if isinstance(v, pd.Timestamp):
                r[k] = v.isoformat()
    save_json(DATA_FILE, records)


def _match_known_sub(name):
    """Check if a subscription name matches a known service."""
    name_lower = name.lower()
    for key, info in KNOWN_SUBSCRIPTIONS.items():
        if key in name_lower:
            return info
    return None


def _load_manual_subs():
    return load_json(MANUAL_SUBS_FILE, default=[])


def _save_manual_subs(subs):
    save_json(MANUAL_SUBS_FILE, subs)


def _load_cancelled():
    return load_json(CANCELLED_FILE, default=[])


def _save_cancelled(cancelled):
    save_json(CANCELLED_FILE, cancelled)


def _load_price_history():
    return load_json(PRICE_HISTORY_FILE, default={})


def _save_price_history(history):
    save_json(PRICE_HISTORY_FILE, history)


def _load_usage_notes():
    return load_json(USAGE_NOTES_FILE, default={})


def _save_usage_notes(notes):
    save_json(USAGE_NOTES_FILE, notes)


def _detect_price_changes(sub_df):
    """Compare current detected amounts against stored price history."""
    history = _load_price_history()
    changes = []
    today = datetime.now().strftime("%Y-%m-%d")

    for _, sub in sub_df.iterrows():
        name = sub["Name"]
        current = sub["Monthly Amount"]
        if name in history:
            last_entry = history[name][-1]
            old_amount = last_entry["amount"]
            if abs(current - old_amount) > 0.01:
                pct = ((current - old_amount) / old_amount * 100) if old_amount > 0 else 0
                changes.append({
                    "name": name,
                    "old_amount": old_amount,
                    "new_amount": current,
                    "change_pct": round(pct, 1),
                    "detected_date": today,
                })
                history[name].append({"amount": current, "date": today})
        else:
            history[name] = [{"amount": current, "date": today}]

    _save_price_history(history)
    return changes


def render():
    render_module_header("🔄", "Subscription & Recurring Expense Auditor",
                         "Find recurring charges, plan cancellations, and project lifetime costs. Upload multiple months for best results.")

    # ── Load saved data ─────────────────────────────────────────────────
    if "stmt_transactions" not in st.session_state:
        saved = _load_statements()
        if not saved.empty:
            saved["date"] = pd.to_datetime(saved["date"], errors="coerce")
            saved["amount"] = pd.to_numeric(saved["amount"], errors="coerce")
        st.session_state.stmt_transactions = saved

    if "sub_decisions" not in st.session_state:
        st.session_state.sub_decisions = load_json(DECISIONS_FILE, default={})

    # ── Manual Subscription Entry ──────────────────────────────────────
    with st.expander("➕ Add Subscription Manually"):
        manual_subs = _load_manual_subs()

        with st.form("add_manual_sub", clear_on_submit=True):
            mc1, mc2 = st.columns(2)
            with mc1:
                ms_name = st.text_input("Subscription Name*")
                ms_amount = st.number_input("Amount*", min_value=0.01, step=1.0, format="%.2f")
                ms_freq = st.selectbox("Frequency", ["Monthly", "Quarterly", "Annual"])
            with mc2:
                ms_renewal = st.date_input("Next Renewal Date", value=datetime.now())
                ms_category = st.selectbox("Category", SUB_CATEGORIES)
                ms_cancel_url = st.text_input("Cancel URL (optional)")
            ms_notes = st.text_input("Notes (optional)")

            if st.form_submit_button("Add Subscription", type="primary"):
                if ms_name.strip():
                    new_sub = {
                        "name": ms_name.strip(),
                        "amount": ms_amount,
                        "frequency": ms_freq,
                        "renewal_date": ms_renewal.strftime("%Y-%m-%d"),
                        "category": ms_category,
                        "cancel_url": ms_cancel_url.strip() if ms_cancel_url else "",
                        "notes": ms_notes.strip() if ms_notes else "",
                        "added": datetime.now().strftime("%Y-%m-%d"),
                        "source": "manual",
                    }
                    manual_subs.append(new_sub)
                    _save_manual_subs(manual_subs)
                    st.toast(f"Added {ms_name}!", icon="✅")
                    st.rerun()
                else:
                    st.warning("Please enter a subscription name.")

        # Show existing manual subscriptions with edit/delete
        if manual_subs:
            st.markdown("**Your Manual Subscriptions:**")
            for i, ms in enumerate(manual_subs):
                mc1, mc2, mc3 = st.columns([3, 1, 1])
                monthly = ms["amount"]
                if ms["frequency"] == "Quarterly":
                    monthly = ms["amount"] / 3
                elif ms["frequency"] == "Annual":
                    monthly = ms["amount"] / 12
                mc1.markdown(
                    f"**{ms['name']}** — {format_currency(ms['amount'])}/{ms['frequency'][:2].lower()} "
                    f"· {ms.get('category', 'Other')} · Renews {ms.get('renewal_date', 'N/A')}"
                )
                mc2.caption(f"~{format_currency(monthly)}/mo")
                if mc3.button("🗑️", key=f"del_manual_{i}"):
                    manual_subs.pop(i)
                    _save_manual_subs(manual_subs)
                    st.rerun()

    # ── Upload ──────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Upload a statement (.csv)",
        type=["csv"],
        help="Export a CSV from your bank or credit card provider. Upload multiple months for best results.",
    )

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Could not read the CSV file: {e}")
            df = None

        if df is not None and not df.empty:
            st.success(f"Loaded **{len(df):,}** transactions from upload.")

            # ── Column Mapping ──────────────────────────────────────────
            st.markdown("### Map Your Columns")
            cols = ["— select —"] + list(df.columns)

            col1, col2, col3 = st.columns(3)
            with col1:
                date_col = st.selectbox("Date column", cols, index=_auto_index(df.columns, ["date", "trans date", "transaction date", "posted date"]))
            with col2:
                desc_col = st.selectbox("Description column", cols, index=_auto_index(df.columns, ["description", "desc", "memo", "merchant", "name", "payee", "transaction description"]))
            with col3:
                amount_col = st.selectbox("Amount column", cols, index=_auto_index(df.columns, ["amount", "debit", "charge", "transaction amount"]))

            if "— select —" not in (date_col, desc_col, amount_col):
                if st.button("➕ Add to Statement History", type="primary"):
                    with st.spinner("Processing transactions..."):
                        new_data = pd.DataFrame()
                        new_data["date"] = pd.to_datetime(df[date_col], errors="coerce")
                        new_data["description"] = df[desc_col].astype(str)
                        new_data["amount"] = pd.to_numeric(
                            df[amount_col].astype(str).str.replace(r"[,$()]", "", regex=True), errors="coerce"
                        )
                        new_data = new_data.dropna(subset=["date", "description", "amount"])

                        if not new_data.empty:
                            existing = st.session_state.stmt_transactions
                            if existing.empty:
                                combined = new_data
                            else:
                                combined = pd.concat([existing, new_data], ignore_index=True)
                            combined = combined.drop_duplicates(subset=["date", "description", "amount"], keep="last")
                            combined = combined.sort_values("date").reset_index(drop=True)
                            st.session_state.stmt_transactions = combined
                            _save_statements(combined)
                            st.toast(f"Added {len(new_data)} transactions! Total: {len(combined)}", icon="✅")
                            st.rerun()
            else:
                st.warning("Please map all three columns above to continue.")

    # ── Work with saved data ────────────────────────────────────────────
    work = st.session_state.stmt_transactions.copy()
    manual_subs = _load_manual_subs()

    if work.empty and not manual_subs:
        from utils.ui_helpers import render_empty_state
        render_empty_state("🔄", "No subscription data yet",
                           "Upload a CSV bank statement above or add subscriptions manually to get started.")
        return

    # ── Detect Recurring from Statements ────────────────────────────────
    subscriptions = []

    if not work.empty:
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work["amount"] = pd.to_numeric(work["amount"], errors="coerce")
        work = work.dropna(subset=["date", "description", "amount"])

        # Data management
        st.markdown("---")
        dm1, dm2 = st.columns([3, 1])
        dm1.metric("Total Transactions in History", len(work))
        with dm2:
            if st.button("🗑️ Clear All Statement Data"):
                st.session_state.stmt_transactions = pd.DataFrame()
                _save_statements(pd.DataFrame())
                st.rerun()

        # Only look at expenses (negative amounts) for subscription detection
        expenses = work[work["amount"] < 0].copy()
        if not expenses.empty:
            expenses["abs_amount"] = expenses["amount"].abs()

            threshold = st.slider(
                "Fuzzy match sensitivity",
                50, 100, 75,
                help="Lower = more aggressive grouping. Higher = stricter matching.",
            )

            descriptions = expenses["description"].tolist()
            groups = group_similar_transactions(descriptions, threshold=threshold)

            for rep_desc, indices in groups.items():
                grp = expenses.iloc[indices].copy()
                if len(grp) < 3:
                    continue

                grp_sorted = grp.sort_values("date")
                dates = grp_sorted["date"].tolist()
                gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
                avg_gap = sum(gaps) / len(gaps) if gaps else 0

                if not (10 <= avg_gap <= 95):
                    continue

                amounts = grp["abs_amount"].tolist()
                avg_amount = sum(amounts) / len(amounts)
                if avg_amount > 0:
                    std_amount = (sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)) ** 0.5
                    if std_amount / avg_amount > 0.3:
                        continue

                freq = "Monthly" if avg_gap <= 45 else "Quarterly" if avg_gap <= 95 else "Other"
                multiplier = 12 if freq == "Monthly" else 4 if freq == "Quarterly" else 12

                known = _match_known_sub(rep_desc)

                sub_name = rep_desc.strip()[:60]
                subscriptions.append({
                    "Name": sub_name,
                    "Monthly Amount": round(avg_amount, 2),
                    "Annual Cost": round(avg_amount * multiplier, 2),
                    "5-Year Cost": round(avg_amount * multiplier * 5, 2),
                    "Frequency": freq,
                    "Occurrences": len(grp),
                    "First Seen": grp_sorted["date"].iloc[0].strftime("%Y-%m-%d"),
                    "Last Seen": grp_sorted["date"].iloc[-1].strftime("%Y-%m-%d"),
                    "Known Service": known["name"] if known else None,
                    "Cancel URL": known["cancel"] if known else None,
                    "Category": known["category"] if known else "Other",
                    "Source": "detected",
                })

    # ── Add manual subscriptions to the list ────────────────────────────
    for ms in manual_subs:
        amount = ms["amount"]
        freq = ms["frequency"]
        if freq == "Monthly":
            monthly = amount
            annual = amount * 12
        elif freq == "Quarterly":
            monthly = round(amount / 3, 2)
            annual = amount * 4
        else:  # Annual
            monthly = round(amount / 12, 2)
            annual = amount

        subscriptions.append({
            "Name": ms["name"],
            "Monthly Amount": monthly,
            "Annual Cost": annual,
            "5-Year Cost": round(annual * 5, 2),
            "Frequency": freq,
            "Occurrences": 0,
            "First Seen": ms.get("added", "N/A"),
            "Last Seen": ms.get("renewal_date", "N/A"),
            "Known Service": None,
            "Cancel URL": ms.get("cancel_url", None) or None,
            "Category": ms.get("category", "Other"),
            "Source": "manual",
        })

    if not subscriptions:
        st.info("No recurring charges detected. Try lowering the match sensitivity, uploading more months of data, or adding subscriptions manually.")
        return

    sub_df = pd.DataFrame(subscriptions).sort_values("Annual Cost", ascending=False).reset_index(drop=True)

    # ── Price Change Detection ──────────────────────────────────────────
    detected_df = sub_df[sub_df["Source"] == "detected"]
    if not detected_df.empty:
        price_changes = _detect_price_changes(detected_df)
        if price_changes:
            st.markdown("---")
            st.markdown("### 📈 Price Changes Detected")
            for pc in price_changes:
                direction = "↑" if pc["change_pct"] > 0 else "↓"
                color = "#ef4444" if pc["change_pct"] > 0 else "#22c55e"
                st.markdown(
                    f'<div style="padding:0.6rem 1rem;border-left:3px solid {color};'
                    f'margin-bottom:0.5rem;background:var(--fk-card-bg);border-radius:6px;">'
                    f'<strong>{pc["name"]}</strong>: '
                    f'{format_currency(pc["old_amount"])} → {format_currency(pc["new_amount"])} '
                    f'<span style="color:{color};font-weight:600;">'
                    f'{direction} {abs(pc["change_pct"])}%</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                create_notification(
                    "warning", "subscriptions",
                    f"Price change: {pc['name']}",
                    f"{pc['name']} changed from {format_currency(pc['old_amount'])} to {format_currency(pc['new_amount'])} ({direction}{abs(pc['change_pct'])}%)",
                    action_module="subscription_auditor",
                )

    # ── Summary Stats ───────────────────────────────────────────────────
    st.markdown("---")
    total_monthly = sub_df["Monthly Amount"].sum()
    total_annual = sub_df["Annual Cost"].sum()

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Subscriptions Found", len(sub_df))
    mc2.metric("Total Monthly Cost", format_currency(total_monthly))
    mc3.metric("Total Annual Cost", format_currency(total_annual))

    cancelled_list = _load_cancelled()
    cancelled_savings = sum(c.get("monthly_amount", 0) for c in cancelled_list)
    mc4.metric("Cancelled Savings", f"{format_currency(cancelled_savings)}/mo")

    # Subscription alerts
    _prefs = load_json("settings.json", default={}).get("notifications", {})
    _sub_threshold = _prefs.get("sub_cost_threshold", 200)
    if total_monthly > _sub_threshold:
        create_notification(
            "warning", "subscriptions",
            f"Subscriptions exceed {get_currency_symbol()}{_sub_threshold}/mo",
            f"Your total monthly subscription cost is {format_currency(total_monthly)} ({len(sub_df)} subscriptions)",
            action_module="subscription_auditor",
        )

    create_notification(
        "info", "subscriptions",
        f"Found {len(sub_df)} subscriptions",
        f"Found {len(sub_df)} subscriptions totaling {format_currency(total_monthly)}/mo. Annual cost: {format_currency(total_annual)}",
        action_module="subscription_auditor",
        dedup_hours=168,
    )

    # ── Savings summary (always visible) ─────────────────────────────────
    cancel_names_top = [k for k, v in st.session_state.sub_decisions.items() if v == "Cancel"]
    if cancel_names_top:
        cancel_df_top = sub_df[sub_df["Name"].isin(cancel_names_top)]
        if not cancel_df_top.empty:
            saved_monthly_top = cancel_df_top["Monthly Amount"].sum()
            saved_annual_top = cancel_df_top["Annual Cost"].sum()
            st.markdown(
                f'<div class="fk-savings-banner">'
                f'<div><div class="label">Cancel Savings</div>'
                f'<div class="value">{format_currency(saved_monthly_top)}/mo</div></div>'
                f'<div><div class="label">Annual Savings</div>'
                f'<div class="value">{format_currency(saved_annual_top)}/yr</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Tabs ────────────────────────────────────────────────────────────
    tab_review, tab_categories, tab_cancelled, tab_usage = st.tabs(
        ["📋 Review", "📊 Categories", "❌ Cancelled", "📝 Usage & Notes"]
    )

    # ═══════════════════════════════════════════════════════════════════
    #  TAB: Review Subscriptions
    # ═══════════════════════════════════════════════════════════════════
    with tab_review:
        st.markdown("### Review Your Subscriptions")
        st.caption("Toggle each subscription as Keep or Cancel to plan your savings.")

        # Category filter
        all_cats = sorted(sub_df["Category"].unique().tolist())
        filter_cat = st.selectbox("Filter by Category", ["All"] + all_cats, key="sub_cat_filter")
        display_df = sub_df if filter_cat == "All" else sub_df[sub_df["Category"] == filter_cat]

        for idx, sub in display_df.iterrows():
            sub_key = sub["Name"]
            current_decision = st.session_state.sub_decisions.get(sub_key, "Keep")

            col_main, col_action = st.columns([4, 1])
            with col_main:
                known_badge = f" · **{sub['Known Service']}**" if sub.get("Known Service") else ""
                freq_badge = sub["Frequency"]
                src_badge = " 📝" if sub["Source"] == "manual" else ""
                cat_badge = sub.get("Category", "Other")

                st.markdown(
                    f"**{sub['Name']}**{known_badge}{src_badge} — `{freq_badge}` · `{cat_badge}`"
                )
                occ = sub['Occurrences']
                occ_text = f" · {occ} charges since {sub['First Seen']}" if occ > 0 else ""
                st.markdown(
                    f"<span style='font-size:0.85rem;color:var(--fk-text-muted);'>"
                    f"{format_currency(sub['Monthly Amount'])}/mo · "
                    f"{format_currency(sub['Annual Cost'])}/yr · "
                    f"{format_currency(sub['5-Year Cost'])} over 5 years"
                    f"{occ_text}"
                    f"</span>",
                    unsafe_allow_html=True,
                )

                cancel_url = sub.get("Cancel URL")
                if cancel_url:
                    known_name = sub.get("Known Service", "subscription")
                    st.markdown(
                        f"<a href='{cancel_url}' target='_blank' style='color:#ef4444;font-size:0.82rem;'>"
                        f"Cancel {known_name} →</a>",
                        unsafe_allow_html=True,
                    )

            with col_action:
                decision = st.selectbox(
                    "Decision",
                    ["Keep", "Cancel"],
                    index=0 if current_decision == "Keep" else 1,
                    key=f"dec_{idx}",
                    label_visibility="collapsed",
                )
                if st.session_state.sub_decisions.get(sub_key) != decision:
                    st.session_state.sub_decisions[sub_key] = decision
                    save_json(DECISIONS_FILE, st.session_state.sub_decisions)

                if decision == "Cancel":
                    st.markdown(
                        "<span style='color:#ef4444;font-weight:600;'>❌ Cancel</span>",
                        unsafe_allow_html=True,
                    )
                    # Cancel workflow: confirm cancellation
                    confirmed = st.checkbox("I've cancelled this", key=f"confirmed_{idx}")
                    if confirmed:
                        already = any(c["name"] == sub_key for c in _load_cancelled())
                        if not already:
                            cancelled_entry = {
                                "name": sub_key,
                                "monthly_amount": sub["Monthly Amount"],
                                "annual_amount": sub["Annual Cost"],
                                "cancelled_date": datetime.now().strftime("%Y-%m-%d"),
                                "cancel_url": cancel_url or "",
                            }
                            cl = _load_cancelled()
                            cl.append(cancelled_entry)
                            _save_cancelled(cl)
                            st.toast(f"Recorded cancellation of {sub_key}", icon="✅")
                            st.rerun()
                else:
                    st.markdown(
                        "<span style='color:#22c55e;font-weight:600;'>✅ Keep</span>",
                        unsafe_allow_html=True,
                    )

            st.markdown("---")

        # ── Savings Summary ─────────────────────────────────────────────
        cancel_names = [k for k, v in st.session_state.sub_decisions.items() if v == "Cancel"]
        if cancel_names:
            cancel_df = sub_df[sub_df["Name"].isin(cancel_names)]
            saved_monthly = cancel_df["Monthly Amount"].sum()
            saved_annual = cancel_df["Annual Cost"].sum()
            saved_5yr = cancel_df["5-Year Cost"].sum()

            st.markdown("### 💰 Your Savings Plan")
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Monthly Savings", format_currency(saved_monthly))
            sc2.metric("Annual Savings", format_currency(saved_annual))
            sc3.metric("5-Year Savings", format_currency(saved_5yr))

        # ── Lifetime Cost Projection ────────────────────────────────────
        st.markdown("---")
        st.markdown("### Lifetime Cost Projections")
        st.caption("If you keep each subscription for the next 5 years:")

        projection_data = []
        for _, sub in sub_df.iterrows():
            projection_data.append({
                "Subscription": sub["Name"],
                "Monthly": format_currency(sub['Monthly Amount']),
                "1 Year": format_currency(sub['Annual Cost']),
                "3 Years": format_currency(sub['Annual Cost'] * 3),
                "5 Years": format_currency(sub['5-Year Cost']),
            })
        st.dataframe(pd.DataFrame(projection_data), use_container_width=True, hide_index=True)

        # ── Duplicate Detection ─────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Potential Duplicates")
        from rapidfuzz import fuzz as _fuzz

        dup_pairs = []
        names = sub_df["Name"].tolist()
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                score = _fuzz.token_sort_ratio(names[i].lower(), names[j].lower())
                if score >= 70:
                    dup_pairs.append((names[i], names[j], score))

        if dup_pairs:
            for a, b, score in dup_pairs:
                st.warning(f"**Possible duplicate:** \"{a}\" and \"{b}\" (similarity: {score}%)")
        else:
            st.success("No potential duplicates detected.")

    # ═══════════════════════════════════════════════════════════════════
    #  TAB: Categories
    # ═══════════════════════════════════════════════════════════════════
    with tab_categories:
        st.markdown("### Subscription Categories")

        import plotly.graph_objects as go
        tc = _theme_colors()

        cat_spend = sub_df.groupby("Category")["Monthly Amount"].sum().sort_values(ascending=False)

        cat_colors = {
            "Entertainment": "#ef4444", "Productivity": "#3b82f6",
            "Cloud/Storage": "#8b5cf6", "News/Media": "#f59e0b",
            "Health/Fitness": "#22c55e", "Education": "#06b6d4",
            "Finance": "#10b981", "Shopping": "#f97316",
            "Communication": "#6366f1", "Other": "#94a3b8",
        }
        colors = [cat_colors.get(c, "#94a3b8") for c in cat_spend.index]

        fig = go.Figure(go.Pie(
            labels=cat_spend.index.tolist(),
            values=cat_spend.values.tolist(),
            hole=0.45,
            marker=dict(colors=colors),
            textinfo="label+percent",
            textfont=dict(size=12, color=tc["text"]),
            hovertemplate="%{label}<br>%{value:.2f}/mo<br>%{percent}<extra></extra>",
        ))
        apply_layout(fig, height=380, title="Spending by Category")
        st.plotly_chart(fig, use_container_width=True)

        # Category table
        cat_table = []
        for cat in cat_spend.index:
            cat_subs = sub_df[sub_df["Category"] == cat]
            cat_table.append({
                "Category": cat,
                "Subscriptions": len(cat_subs),
                "Monthly": format_currency(cat_subs["Monthly Amount"].sum()),
                "Annual": format_currency(cat_subs["Annual Cost"].sum()),
            })
        st.dataframe(pd.DataFrame(cat_table), use_container_width=True, hide_index=True)

        # ── Annual Subscription Calendar ────────────────────────────────
        st.markdown("---")
        st.markdown("### Annual Subscription Calendar")
        st.caption("When each subscription renews throughout the year.")

        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        cal_data = {m: [] for m in month_names}
        cal_costs = {m: 0.0 for m in month_names}

        for _, sub in sub_df.iterrows():
            if sub["Frequency"] == "Monthly":
                for m in month_names:
                    cal_data[m].append(sub["Name"][:25])
                    cal_costs[m] += sub["Monthly Amount"]
            elif sub["Frequency"] == "Quarterly":
                try:
                    last_seen = datetime.strptime(sub["Last Seen"], "%Y-%m-%d")
                    renewal_month = last_seen.month
                except Exception:
                    renewal_month = 1
                for offset in range(0, 12, 3):
                    m_idx = (renewal_month - 1 + offset) % 12
                    cal_data[month_names[m_idx]].append(sub["Name"][:25])
                    cal_costs[month_names[m_idx]] += sub["Monthly Amount"]
            elif sub["Frequency"] == "Annual":
                try:
                    last_seen = datetime.strptime(sub["Last Seen"], "%Y-%m-%d")
                    m_idx = last_seen.month - 1
                    cal_data[month_names[m_idx]].append(sub["Name"][:25])
                    cal_costs[month_names[m_idx]] += sub["Annual Cost"]
                except Exception:
                    pass

        month_cost_list = [cal_costs[m] for m in month_names]
        max_cost = max(month_cost_list) if month_cost_list else 1

        fig = go.Figure(go.Bar(
            x=month_names,
            y=month_cost_list,
            marker_color=[
                f"rgba(239,68,68,{0.3 + 0.7 * (c / max_cost)})" if max_cost > 0
                else "#22c55e" for c in month_cost_list
            ],
            text=[format_currency(c) for c in month_cost_list],
            textposition="outside",
            hovertemplate="%{x}<br>Cost: %{text}<br>Subs: " +
                          "<br>".join("" for _ in month_names) + "<extra></extra>",
        ))
        apply_layout(fig, height=300, title="Monthly Subscription Cost",
                     yaxis_title="Cost")
        st.plotly_chart(fig, use_container_width=True)

        # Most expensive month callout
        if month_cost_list:
            peak_idx = month_cost_list.index(max(month_cost_list))
            peak_month = month_names[peak_idx]
            peak_cost = month_cost_list[peak_idx]
            peak_subs = cal_data[peak_month]
            st.info(
                f"**{peak_month}** is your most expensive month at **{format_currency(peak_cost)}** "
                f"with {len(peak_subs)} subscription{'s' if len(peak_subs) != 1 else ''} renewing."
            )

    # ═══════════════════════════════════════════════════════════════════
    #  TAB: Cancelled
    # ═══════════════════════════════════════════════════════════════════
    with tab_cancelled:
        st.markdown("### Cancelled Subscriptions")
        cancelled_list = _load_cancelled()

        if not cancelled_list:
            st.info("No cancelled subscriptions yet. Mark subscriptions as cancelled in the Review tab.")
        else:
            total_saved_monthly = sum(c.get("monthly_amount", 0) for c in cancelled_list)
            total_saved_annual = sum(c.get("annual_amount", 0) for c in cancelled_list)

            cc1, cc2, cc3 = st.columns(3)
            cc1.metric("Total Cancelled", len(cancelled_list))
            cc2.metric("Monthly Savings", format_currency(total_saved_monthly))
            cc3.metric("Annual Savings", format_currency(total_saved_annual))

            st.markdown("---")
            for i, c in enumerate(cancelled_list):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(
                    f"**{c['name']}** — cancelled on {c.get('cancelled_date', 'Unknown')}"
                )
                c2.markdown(f"Saved {format_currency(c.get('monthly_amount', 0))}/mo")
                if c.get("cancel_url"):
                    c3.markdown(
                        f"<a href='{c['cancel_url']}' target='_blank' style='font-size:0.82rem;'>Verify →</a>",
                        unsafe_allow_html=True,
                    )
                # Undo cancellation
                if st.button("↩️ Undo", key=f"undo_cancel_{i}"):
                    name = c["name"]
                    cancelled_list.pop(i)
                    _save_cancelled(cancelled_list)
                    if name in st.session_state.sub_decisions:
                        st.session_state.sub_decisions[name] = "Keep"
                        save_json(DECISIONS_FILE, st.session_state.sub_decisions)
                    st.rerun()
                st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════
    #  TAB: Usage & Notes
    # ═══════════════════════════════════════════════════════════════════
    with tab_usage:
        st.markdown("### Usage Notes & ROI Assessment")
        st.caption("Rate how often you use each subscription to identify savings opportunities.")

        usage_notes = _load_usage_notes()
        usage_options = ["—", "Daily", "Weekly", "Rarely", "Never"]
        changed = False

        for idx, sub in sub_df.iterrows():
            sub_key = sub["Name"]
            entry = usage_notes.get(sub_key, {})
            current_usage = entry.get("usage", "—")
            current_note = entry.get("notes", "")

            uc1, uc2, uc3 = st.columns([2, 1, 2])
            with uc1:
                st.markdown(f"**{sub['Name']}** — {format_currency(sub['Monthly Amount'])}/mo")
            with uc2:
                usage = st.selectbox(
                    "Usage", usage_options,
                    index=usage_options.index(current_usage) if current_usage in usage_options else 0,
                    key=f"usage_{idx}",
                    label_visibility="collapsed",
                )
            with uc3:
                note = st.text_input(
                    "Notes", value=current_note,
                    key=f"note_{idx}",
                    label_visibility="collapsed",
                    placeholder="Add notes...",
                )

            if usage != current_usage or note != current_note:
                usage_notes[sub_key] = {"usage": usage, "notes": note}
                changed = True

        if changed:
            _save_usage_notes(usage_notes)

        # Auto-suggest cancellation for Rarely/Never
        rarely_never = []
        for _, sub in sub_df.iterrows():
            entry = usage_notes.get(sub["Name"], {})
            u = entry.get("usage", "—")
            if u in ("Rarely", "Never"):
                rarely_never.append((sub["Name"], sub["Monthly Amount"], u))

        if rarely_never:
            st.markdown("---")
            st.markdown("### 💡 Consider Cancelling")
            st.caption("These subscriptions are marked as rarely or never used.")
            total_waste = 0
            for name, amount, usage in rarely_never:
                emoji = "🚫" if usage == "Never" else "⚠️"
                st.markdown(
                    f"{emoji} **{name}** — {format_currency(amount)}/mo — Used: **{usage}**"
                )
                total_waste += amount
                create_notification(
                    "info", "subscriptions",
                    f"Rarely used: {name}",
                    f"{name} ({format_currency(amount)}/mo) is marked as '{usage}'. Consider cancelling to save {format_currency(amount * 12)}/yr.",
                    action_module="subscription_auditor",
                    dedup_hours=168,
                )
            st.warning(
                f"You could save **{format_currency(total_waste)}/mo** "
                f"(**{format_currency(total_waste * 12)}/yr**) by cancelling rarely/never used subscriptions."
            )

    # ── Export ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Export Results")

    export_df = sub_df.copy()
    export_df["Decision"] = export_df["Name"].map(
        lambda n: st.session_state.sub_decisions.get(n, "Keep")
    )
    usage_notes = _load_usage_notes()
    export_df["Usage"] = export_df["Name"].map(
        lambda n: usage_notes.get(n, {}).get("usage", "—")
    )
    export_df["Notes"] = export_df["Name"].map(
        lambda n: usage_notes.get(n, {}).get("notes", "")
    )
    export_df = export_df.drop(columns=["Known Service", "Cancel URL"], errors="ignore")

    ec1, ec2 = st.columns(2)

    csv_data = export_df.to_csv(index=False).encode("utf-8")
    ec1.download_button(
        "⬇️ Download CSV",
        data=csv_data,
        file_name="subscriptions_audit.csv",
        mime="text/csv",
    )

    xlsx_buffer = io.BytesIO()
    with pd.ExcelWriter(xlsx_buffer, engine="xlsxwriter") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Subscriptions")
    ec2.download_button(
        "⬇️ Download Excel",
        data=xlsx_buffer.getvalue(),
        file_name="subscriptions_audit.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ── Helpers ─────────────────────────────────────────────────────────────

def _auto_index(columns, candidates: list[str]) -> int:
    col_lower = [c.lower().strip() for c in columns]
    for candidate in candidates:
        for i, c in enumerate(col_lower):
            if candidate in c:
                return i + 1
    return 0
