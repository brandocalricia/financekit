import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
from utils.fuzzy_matcher import group_similar_transactions
from utils.data_persistence import load_json, save_json
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout, _theme_colors, _chart_font
from utils.formatting import format_currency, get_currency_symbol

DATA_FILE = "statement_transactions.json"
DECISIONS_FILE = "sub_decisions.json"

# Known subscription services with typical monthly prices and cancellation URLs
KNOWN_SUBSCRIPTIONS = {
    "netflix": {"name": "Netflix", "price": 15.49, "cancel": "https://www.netflix.com/cancelplan"},
    "spotify": {"name": "Spotify", "price": 10.99, "cancel": "https://support.spotify.com/us/article/how-to-cancel/"},
    "hulu": {"name": "Hulu", "price": 7.99, "cancel": "https://help.hulu.com/s/article/cancel-account"},
    "disney": {"name": "Disney+", "price": 7.99, "cancel": "https://help.disneyplus.com/article/disneyplus-cancel-account"},
    "hbo": {"name": "HBO Max", "price": 15.99, "cancel": "https://help.max.com/us/Manage-Account"},
    "amazon prime": {"name": "Amazon Prime", "price": 14.99, "cancel": "https://www.amazon.com/gp/help/customer/display.html?nodeId=201118010"},
    "apple music": {"name": "Apple Music", "price": 10.99, "cancel": "https://support.apple.com/en-us/HT202039"},
    "youtube premium": {"name": "YouTube Premium", "price": 13.99, "cancel": "https://support.google.com/youtube/answer/6308278"},
    "adobe": {"name": "Adobe Creative Cloud", "price": 54.99, "cancel": "https://helpx.adobe.com/manage-account/using/cancel-subscription.html"},
    "dropbox": {"name": "Dropbox", "price": 11.99, "cancel": "https://help.dropbox.com/account-management/cancel-account"},
    "icloud": {"name": "iCloud+", "price": 2.99, "cancel": "https://support.apple.com/en-us/HT207594"},
    "google one": {"name": "Google One", "price": 2.99, "cancel": "https://support.google.com/googleone/answer/9004013"},
    "linkedin premium": {"name": "LinkedIn Premium", "price": 29.99, "cancel": "https://www.linkedin.com/help/linkedin/answer/a545599"},
    "paramount": {"name": "Paramount+", "price": 5.99, "cancel": "https://help.paramountplus.com/s/article/PD-How-do-I-cancel"},
    "peacock": {"name": "Peacock", "price": 5.99, "cancel": "https://www.peacocktv.com/help/cancel"},
    "nordvpn": {"name": "NordVPN", "price": 12.99, "cancel": "https://support.nordvpn.com/General-info/1047407532/How-can-I-cancel-my-subscription.htm"},
    "express vpn": {"name": "ExpressVPN", "price": 12.95, "cancel": "https://www.expressvpn.com/support/troubleshooting/cancel-subscription/"},
    "chatgpt": {"name": "ChatGPT Plus", "price": 20.00, "cancel": "https://help.openai.com/en/articles/subscription-management"},
    "grammarly": {"name": "Grammarly", "price": 12.00, "cancel": "https://support.grammarly.com/hc/en-us/articles/115000090172"},
    "notion": {"name": "Notion", "price": 8.00, "cancel": "https://www.notion.so/help/manage-your-subscription"},
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

    if work.empty:
        from utils.ui_helpers import render_empty_state
        render_empty_state("🔄", "No statement data yet",
                           "Upload a CSV bank statement above to find recurring charges and subscriptions.")
        return

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
    if expenses.empty:
        st.warning("No expense transactions found. Make sure negative amounts represent charges.")
        return
    expenses["abs_amount"] = expenses["amount"].abs()

    # ── Detect Recurring Charges ────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Detected Subscriptions & Recurring Charges")

    threshold = st.slider(
        "Fuzzy match sensitivity",
        50, 100, 75,
        help="Lower = more aggressive grouping. Higher = stricter matching.",
    )

    descriptions = expenses["description"].tolist()
    groups = group_similar_transactions(descriptions, threshold=threshold)

    # Initialize keep/cancel decisions — load from disk if available
    if "sub_decisions" not in st.session_state:
        st.session_state.sub_decisions = load_json(DECISIONS_FILE, default={})

    subscriptions = []
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

        # Check against known subscription database
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
        })

    if not subscriptions:
        st.info("No recurring charges detected. Try lowering the match sensitivity or uploading more months of data.")
        return

    sub_df = pd.DataFrame(subscriptions).sort_values("Annual Cost", ascending=False).reset_index(drop=True)

    # ── Summary Stats ───────────────────────────────────────────────────
    total_monthly = sub_df["Monthly Amount"].sum()
    total_annual = sub_df["Annual Cost"].sum()

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Recurring Subscriptions Found", len(sub_df))
    mc2.metric("Total Monthly Cost", format_currency(total_monthly))
    mc3.metric("Total Annual Cost", format_currency(total_annual))

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

    # ── Subscription Cards with Keep/Cancel Toggle ──────────────────────
    st.markdown("---")
    st.markdown("### Review Your Subscriptions")
    st.caption("Toggle each subscription as Keep or Cancel to plan your savings.")

    for idx, sub in sub_df.iterrows():
        sub_key = sub["Name"]
        current_decision = st.session_state.sub_decisions.get(sub_key, "Keep")

        col_main, col_action = st.columns([4, 1])
        with col_main:
            known_badge = f" · **{sub['Known Service']}**" if sub.get("Known Service") else ""
            freq_badge = sub["Frequency"]

            st.markdown(
                f"**{sub['Name']}**{known_badge} — `{freq_badge}`"
            )
            st.markdown(
                f"<span style='font-size:0.85rem;color:var(--fk-text-muted);'>"
                f"{format_currency(sub['Monthly Amount'])}/mo · "
                f"{format_currency(sub['Annual Cost'])}/yr · "
                f"{format_currency(sub['5-Year Cost'])} over 5 years · "
                f"{sub['Occurrences']} charges since {sub['First Seen']}"
                f"</span>",
                unsafe_allow_html=True,
            )

            if sub.get("Cancel URL"):
                st.markdown(
                    f"<a href='{sub['Cancel URL']}' target='_blank' style='color:#ef4444;font-size:0.82rem;'>"
                    f"Cancel {sub.get('Known Service', 'subscription')} →</a>",
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
            else:
                st.markdown(
                    "<span style='color:#22c55e;font-weight:600;'>✅ Keep</span>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")

    # ── Savings Summary ─────────────────────────────────────────────────
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

    # ── Lifetime Cost Projection ────────────────────────────────────────
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

    # ── Duplicate Detection ─────────────────────────────────────────────
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

    # ── Annual Subscription Calendar ────────────────────────────────────
    st.markdown("---")
    st.markdown("### Annual Subscription Calendar")
    st.caption("When each subscription renews throughout the year.")

    import plotly.graph_objects as go
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    cal_data = {m: [] for m in month_names}
    for _, sub in sub_df.iterrows():
        try:
            last_seen = datetime.strptime(sub["Last Seen"], "%Y-%m-%d")
            if sub["Frequency"] == "Monthly":
                for m in month_names:
                    cal_data[m].append(sub["Name"][:25])
            elif sub["Frequency"] == "Quarterly":
                renewal_month = last_seen.month
                for offset in range(0, 12, 3):
                    m_idx = (renewal_month - 1 + offset) % 12
                    cal_data[month_names[m_idx]].append(sub["Name"][:25])
        except Exception:
            pass

    # Display as a compact view
    month_costs = []
    for m in month_names:
        count = len(cal_data[m])
        month_costs.append(count)

    fig = go.Figure(go.Bar(
        x=month_names,
        y=month_costs,
        marker_color=["#ef4444" if c > 5 else "#f59e0b" if c > 3 else "#22c55e" for c in month_costs],
        text=month_costs,
        textposition="outside",
    ))
    apply_layout(fig, height=280, title="Subscriptions Renewing Per Month",
                 yaxis_title="Active Subscriptions")
    st.plotly_chart(fig, use_container_width=True)

    # ── Export ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Export Results")

    # Add decision column to export
    export_df = sub_df.copy()
    export_df["Decision"] = export_df["Name"].map(
        lambda n: st.session_state.sub_decisions.get(n, "Keep")
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
