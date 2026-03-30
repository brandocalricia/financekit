import streamlit as st
import pandas as pd
import io
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import plotly.express as px
import plotly.graph_objects as go
from utils.data_persistence import load_json, save_json
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout, CHART_COLORS
from utils.formatting import format_currency, format_currency_int, get_currency_symbol

DATA_FILE = "transactions.json"

# Known bank CSV header patterns for auto-detection
BANK_FORMATS = {
    "Chase": {
        "date": ["transaction date", "post date"],
        "desc": ["description"],
        "amount": ["amount"],
        "detect_cols": ["transaction date", "description", "amount", "type"],
    },
    "Bank of America": {
        "date": ["date"],
        "desc": ["description", "payee"],
        "amount": ["amount"],
        "detect_cols": ["date", "description", "amount", "running bal."],
    },
    "Wells Fargo": {
        "date": ["date"],
        "desc": ["description", "payee"],
        "amount": ["amount"],
        "detect_cols": ["date", "amount", "description", "deposits/credits", "withdrawals/debits"],
    },
    "Capital One": {
        "date": ["transaction date", "posted date"],
        "desc": ["description", "merchant name"],
        "amount": ["debit", "credit", "amount"],
        "detect_cols": ["transaction date", "posted date", "card no.", "description", "debit"],
    },
    "American Express": {
        "date": ["date"],
        "desc": ["description"],
        "amount": ["amount"],
        "detect_cols": ["date", "description", "amount", "extended details", "appears on your statement as"],
    },
}


def _load_transactions():
    data = load_json(DATA_FILE, default=[])
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()


def _save_transactions(df):
    if df.empty:
        save_json(DATA_FILE, [])
        return
    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if isinstance(v, pd.Timestamp):
                r[k] = v.isoformat()
    save_json(DATA_FILE, records)


def _detect_bank(df):
    """Try to detect which bank exported this CSV."""
    col_lower = set(c.lower().strip() for c in df.columns)
    for bank, fmt in BANK_FORMATS.items():
        detect = set(fmt["detect_cols"])
        # If 2+ of the detect columns are present, match
        if len(detect & col_lower) >= 2:
            return bank, fmt
    return None, None


def _auto_idx(columns, candidates):
    col_lower = [c.lower().strip() for c in columns]
    for cand in candidates:
        for i, c in enumerate(col_lower):
            if cand in c:
                return i + 1
    return 0


def _auto_idx_optional(columns, candidates):
    col_lower = [c.lower().strip() for c in columns]
    for cand in candidates:
        for i, c in enumerate(col_lower):
            if cand in c:
                return i + 1
    return 0


def render():
    render_module_header("📊", "Financial Report Generator",
                         "Upload transactions and get a polished PDF report with charts and summary statistics.")

    if "report_transactions" not in st.session_state:
        saved = _load_transactions()
        if not saved.empty:
            saved["date"] = pd.to_datetime(saved["date"], errors="coerce")
            saved["amount"] = pd.to_numeric(saved["amount"], errors="coerce")
        st.session_state.report_transactions = saved

    # Check for Quick Import from dashboard
    if "quick_import_df" in st.session_state and st.session_state.quick_import_df is not None:
        st.info(
            f"📥 Quick Import ready: **{st.session_state.get('quick_import_name', 'uploaded file')}** "
            f"({len(st.session_state.quick_import_df):,} rows). Map the columns below to import it."
        )

    # ── Report Templates (v5.6) ─────────────────────────────────────────
    with st.expander("📋 Quick Reports — Generate from templates"):
        from utils.report_builder import REPORT_TEMPLATES
        _settings = load_json("settings.json", default={})
        _user_name = _settings.get("user_name", "") or st.session_state.get("user_name", "")

        # Collect data for templates
        _tmpl_data = {
            "transactions": load_json("budget_transactions.json", default=[]),
            "budgets": load_json("budgets.json", default={"budgets": {}}).get("budgets", {}),
            "goals": load_json("goals.json", default={"goals": []}).get("goals", []),
            "holdings": load_json("portfolio.json", default={"holdings": []}).get("holdings", []),
            "liabilities": load_json("liabilities.json", default=[]),
        }

        tc1, tc2 = st.columns([2, 1])
        with tc1:
            template_choice = st.selectbox(
                "Report template",
                list(REPORT_TEMPLATES.keys()),
                key="report_template",
            )
        with tc2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📄 Generate PDF", key="gen_template_pdf", type="primary", width='stretch'):
                gen_func = REPORT_TEMPLATES[template_choice]
                pdf_bytes = gen_func(_user_name, _settings, _tmpl_data)
                _fname = template_choice.lower().replace(" ", "_").replace("-", "_")
                st.download_button(
                    f"💾 Download {template_choice}",
                    data=pdf_bytes,
                    file_name=f"financekit_{_fname}.pdf",
                    mime="application/pdf",
                    key="dl_template_pdf",
                )

        st.caption("Templates: Monthly Summary, Year-in-Review, Tax Summary, Net Worth Statement, Cash Flow Analysis")

    # ── Upload ────────────────────────────────────────────────────────────
    _rg_accounts = load_json("accounts.json", default=[])
    if _rg_accounts:
        _rg_acc_opts = ["All Accounts"] + [f"{a['name']} (····{a.get('last_four','')})" for a in _rg_accounts]
        _rg_acc_choice = st.selectbox("Account Filter", _rg_acc_opts, key="rg_account_filter")
    uploaded = st.file_uploader(
        "Upload transactions file",
        type=["csv", "xlsx", "xls", "ofx", "qfx"],
        help="Supports YNAB, Mint, Monarch, OFX/QFX, Chase, BofA, Wells Fargo, Capital One, Amex, and standard CSV.",
    )

    # Use quick import if no manual upload
    working_upload = uploaded
    if working_upload is None and "quick_import_df" in st.session_state:
        df_candidate = st.session_state.quick_import_df
    else:
        df_candidate = None

    _smart_parsed = None  # Result from smart importer

    if working_upload is not None:
        from utils.importers import detect_file_type, OFXImporter, auto_import, detect_format
        file_type = detect_file_type(working_upload.name)

        if file_type == "OFX":
            try:
                _smart_parsed = OFXImporter.parse(working_upload.read())
                st.success(f"✅ Detected **OFX/QFX** bank file — {len(_smart_parsed)} transactions found.")
            except Exception as e:
                st.error(f"Could not parse OFX file: {e}")
        else:
            try:
                if working_upload.name.endswith((".xlsx", ".xls")):
                    df_candidate = pd.read_excel(working_upload)
                else:
                    df_candidate = pd.read_csv(working_upload)
            except Exception as e:
                st.error(f"Could not read the file: {e}")
                df_candidate = None

            # Smart format detection
            if df_candidate is not None and not df_candidate.empty:
                smart_fmt = detect_format(df_candidate)
                if smart_fmt in ("YNAB", "Mint", "Monarch"):
                    st.success(f"✅ Detected **{smart_fmt}** export format!")
                    fmt_name, parsed = auto_import(df=df_candidate, filename=working_upload.name)
                    if parsed is not None and not parsed.empty:
                        _smart_parsed = parsed
                        # Show category mapping preview
                        with st.expander("📋 Category Mapping Preview"):
                            from utils.importers import map_categories_bulk
                            cats = _smart_parsed["category"].unique()
                            st.caption(f"Mapped {len(cats)} categories to FinanceKit categories.")
                            for cat in sorted(cats):
                                st.markdown(f"- {cat}")

    # Smart import path (YNAB, Mint, Monarch, OFX)
    if _smart_parsed is not None and not _smart_parsed.empty:
        st.markdown(f"### Preview ({len(_smart_parsed)} transactions)")
        st.dataframe(_smart_parsed.head(10), width='stretch', hide_index=True)

        if st.button("➕ Import All Transactions", type="primary", key="smart_import_btn"):
            new_data = _smart_parsed.copy()
            new_data = new_data.dropna(subset=["date", "amount"])
            if not new_data.empty:
                existing = st.session_state.report_transactions
                combined = new_data if existing.empty else pd.concat([existing, new_data], ignore_index=True)
                combined = combined.drop_duplicates(subset=["date", "description", "amount"], keep="last")
                combined = combined.sort_values("date").reset_index(drop=True)
                st.session_state.report_transactions = combined
                _save_transactions(combined)
                st.session_state.pop("quick_import_df", None)
                st.session_state.pop("quick_import_name", None)
                st.toast(f"Imported {len(new_data)} transactions! Total: {len(combined)}", icon="✅")
                st.rerun()

    elif df_candidate is not None and not df_candidate.empty:
        # Fallback: manual column mapping (existing flow)
        detected_bank, bank_fmt = _detect_bank(df_candidate)
        if detected_bank:
            st.success(f"✅ Detected bank format: **{detected_bank}**")
        else:
            st.info("Could not auto-detect bank format — please map columns manually below.")

        col_file_info = f"Loaded **{len(df_candidate):,}** rows and **{len(df_candidate.columns)}** columns."
        st.success(col_file_info)

        # Column mapping — pre-fill if bank detected
        st.markdown("### Map Your Columns")
        cols = ["— select —"] + list(df_candidate.columns)
        date_default = (_auto_idx(df_candidate.columns, bank_fmt["date"]) if bank_fmt
                        else _auto_idx(df_candidate.columns, ["date", "trans date", "transaction date"]))
        desc_default = (_auto_idx(df_candidate.columns, bank_fmt["desc"]) if bank_fmt
                        else _auto_idx(df_candidate.columns, ["description", "desc", "memo", "merchant", "name", "payee"]))
        amount_default = (_auto_idx(df_candidate.columns, bank_fmt["amount"]) if bank_fmt
                          else _auto_idx(df_candidate.columns, ["amount", "debit", "transaction amount"]))

        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            date_col = st.selectbox("Date", cols, index=date_default)
        with mc2:
            desc_col = st.selectbox("Description", cols, index=desc_default)
        with mc3:
            amount_col = st.selectbox("Amount", cols, index=amount_default)
        with mc4:
            cat_col = st.selectbox("Category (optional)", ["— none —"] + list(df_candidate.columns),
                                   index=_auto_idx_optional(df_candidate.columns, ["category", "type", "class"]))

        if "— select —" not in (date_col, desc_col, amount_col):
            if st.button("➕ Add to Transaction History", type="primary"):
                new_data = pd.DataFrame()
                new_data["date"] = pd.to_datetime(df_candidate[date_col], errors="coerce")
                new_data["description"] = df_candidate[desc_col].astype(str)
                new_data["amount"] = pd.to_numeric(
                    df_candidate[amount_col].astype(str).str.replace(r"[,$()]", "", regex=True),
                    errors="coerce",
                )
                if cat_col != "— none —":
                    new_data["category"] = df_candidate[cat_col].astype(str)
                else:
                    new_data["category"] = "Uncategorized"
                new_data = new_data.dropna(subset=["date", "amount"])

                if not new_data.empty:
                    existing = st.session_state.report_transactions
                    combined = new_data if existing.empty else pd.concat([existing, new_data], ignore_index=True)
                    combined = combined.drop_duplicates(subset=["date", "description", "amount"], keep="last")
                    combined = combined.sort_values("date").reset_index(drop=True)
                    st.session_state.report_transactions = combined
                    _save_transactions(combined)
                    # Clear quick import
                    st.session_state.pop("quick_import_df", None)
                    st.session_state.pop("quick_import_name", None)
                    st.toast(f"Added {len(new_data)} transactions! Total: {len(combined)}", icon="✅")
                    st.rerun()
        else:
            st.warning("Please map at least Date, Description, and Amount to continue.")

    # ── Work with saved data ──────────────────────────────────────────────
    work = st.session_state.report_transactions.copy()

    if work.empty:
        from utils.ui_helpers import render_empty_state
        render_empty_state("📊", "No transactions yet",
                           "Upload a CSV or Excel file above to generate your financial report.")
        return

    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work["amount"] = pd.to_numeric(work["amount"], errors="coerce")
    work = work.dropna(subset=["date", "amount"])
    work["month"] = work["date"].dt.to_period("M").astype(str)

    st.markdown("---")
    dm1, dm2 = st.columns([3, 1])
    dm1.metric("Total Transactions in History", len(work))
    with dm2:
        if st.button("🗑️ Clear All Transactions", width='stretch'):
            st.session_state.report_transactions = pd.DataFrame()
            _save_transactions(pd.DataFrame())
            st.rerun()

    income = work[work["amount"] > 0]
    expenses = work[work["amount"] < 0].copy()
    expenses["amount"] = expenses["amount"].abs()

    total_income = income["amount"].sum()
    total_expenses = expenses["amount"].sum()
    net = total_income - total_expenses
    avg_txn = work["amount"].mean()
    date_range_str = f"{work['date'].min().strftime('%b %d, %Y')} – {work['date'].max().strftime('%b %d, %Y')}"

    user_name = st.text_input("Your name (optional — used in the report header)", "")

    # ── Net Worth Section ─────────────────────────────────────────────────
    with st.expander("💎 Net Worth Calculator (optional)"):
        st.markdown("Add your assets and liabilities to include a net worth summary in the report.")
        nc1, nc2 = st.columns(2)
        with nc1:
            checking = st.number_input("Checking/Savings ($)", min_value=0.0, step=100.0, format="%.0f")
            investments = st.number_input("Investments/Retirement ($)", min_value=0.0, step=100.0, format="%.0f")
            real_estate = st.number_input("Real Estate Value ($)", min_value=0.0, step=1000.0, format="%.0f")
            other_assets = st.number_input("Other Assets ($)", min_value=0.0, step=100.0, format="%.0f")
        with nc2:
            mortgage = st.number_input("Mortgage Balance ($)", min_value=0.0, step=100.0, format="%.0f")
            car_loan = st.number_input("Car Loan ($)", min_value=0.0, step=100.0, format="%.0f")
            student_loan = st.number_input("Student Loans ($)", min_value=0.0, step=100.0, format="%.0f")
            cc_debt = st.number_input("Credit Card Debt ($)", min_value=0.0, step=100.0, format="%.0f")
            other_debt = st.number_input("Other Liabilities ($)", min_value=0.0, step=100.0, format="%.0f")

        total_assets = checking + investments + real_estate + other_assets
        total_liabilities = mortgage + car_loan + student_loan + cc_debt + other_debt
        net_worth = total_assets - total_liabilities

        nwc1, nwc2, nwc3 = st.columns(3)
        nwc1.metric("Total Assets", format_currency_int(total_assets))
        nwc2.metric("Total Liabilities", format_currency_int(total_liabilities))
        nwc3.metric("Net Worth", format_currency_int(net_worth))

    net_worth_data = {
        "total_assets": checking + investments + real_estate + other_assets,
        "total_liabilities": mortgage + car_loan + student_loan + cc_debt + other_debt,
    } if any([checking, investments, real_estate, other_assets, mortgage, car_loan,
               student_loan, cc_debt, other_debt]) else None

    # ── Summary Stats ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Summary Statistics")
    st.caption(f"Period: {date_range_str}")

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Total Income", format_currency(total_income))
    sc2.metric("Total Expenses", format_currency(total_expenses))
    sc3.metric("Net", format_currency(net), delta=format_currency(abs(net)))
    sc4.metric("Avg Transaction", format_currency(avg_txn))

    top_cats = pd.Series(dtype=float)
    if not expenses.empty:
        top_cats = expenses.groupby("category")["amount"].sum().sort_values(ascending=False).head(5)
        st.markdown("**Top Spending Categories:**")
        for cat, amt in top_cats.items():
            pct = amt / total_expenses * 100 if total_expenses > 0 else 0
            st.markdown(f"- {cat}: **{format_currency(amt)}** ({pct:.1f}%)")

    # ── Charts ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Charts")

    if not expenses.empty:
        monthly_expenses = expenses.groupby("month")["amount"].sum().reset_index()
        monthly_expenses.columns = ["Month", "Amount"]
        fig_monthly = px.bar(
            monthly_expenses, x="Month", y="Amount",
            title="Monthly Spending",
            color_discrete_sequence=["#6366f1"],
            text="Amount",
        )
        fig_monthly.update_traces(texttemplate=f"{get_currency_symbol()}%{{text:,.0f}}", textposition="outside")
        apply_layout(fig_monthly, height=350)
        st.plotly_chart(fig_monthly, width='stretch')

        cat_totals = expenses.groupby("category")["amount"].sum().reset_index()
        cat_totals.columns = ["Category", "Amount"]
        fig_pie = px.pie(
            cat_totals, names="Category", values="Amount",
            title="Spending by Category",
            color_discrete_sequence=CHART_COLORS,
        )
        fig_pie.update_traces(hole=0.65)
        apply_layout(fig_pie, height=380)
        st.plotly_chart(fig_pie, width='stretch')
    else:
        st.info("No expense data to chart yet. Import transactions to see spending visualizations.")

    # Income vs Expenses trend
    _has_income = not income.empty
    _has_expenses = not expenses.empty
    if _has_income or _has_expenses:
        monthly_income = income.groupby("month")["amount"].sum().reset_index() if _has_income else pd.DataFrame(columns=["month", "amount"])
        monthly_income.columns = ["Month", "Income"]
        monthly_exp2 = expenses.groupby("month")["amount"].sum().reset_index() if _has_expenses else pd.DataFrame(columns=["month", "amount"])
        monthly_exp2.columns = ["Month", "Expenses"]
        merged = pd.merge(monthly_income, monthly_exp2, on="Month", how="outer").fillna(0).sort_values("Month")

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=merged["Month"], y=merged["Income"], name="Income",
                                      line=dict(color="#22c55e", width=3)))
        fig_line.add_trace(go.Scatter(x=merged["Month"], y=merged["Expenses"], name="Expenses",
                                      line=dict(color="#ef4444", width=3)))
        apply_layout(fig_line, height=350, title="Income vs Expenses Over Time")
        st.plotly_chart(fig_line, width='stretch')

    # ── Year-in-Review ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Year-in-Review")

    available_years = sorted(work["date"].dt.year.dropna().unique().astype(int), reverse=True)
    if available_years:
        yir_year = st.selectbox("Select Year", available_years, key="yir_year_select")
        year_data = work[work["date"].dt.year == yir_year].copy()

        if not year_data.empty:
            y_income = year_data[year_data["amount"] > 0]
            y_expenses = year_data[year_data["amount"] < 0].copy()
            y_expenses["amount"] = y_expenses["amount"].abs()

            y_total_income = y_income["amount"].sum()
            y_total_expenses = y_expenses["amount"].sum()
            y_net_savings = y_total_income - y_total_expenses
            y_savings_rate = (y_net_savings / y_total_income * 100) if y_total_income > 0 else 0

            yc1, yc2, yc3, yc4 = st.columns(4)
            yc1.metric(f"{yir_year} Income", format_currency(y_total_income))
            yc2.metric(f"{yir_year} Expenses", format_currency(y_total_expenses))
            yc3.metric("Net Savings", format_currency(y_net_savings))
            yc4.metric("Savings Rate", f"{y_savings_rate:.1f}%")

            # Top categories for the year
            if not y_expenses.empty:
                y_top = y_expenses.groupby("category")["amount"].sum().sort_values(ascending=False).head(5)
                st.markdown(f"**Top {yir_year} Spending Categories:**")
                for cat, amt in y_top.items():
                    pct = amt / y_total_expenses * 100 if y_total_expenses > 0 else 0
                    st.markdown(f"- {cat}: **{format_currency(amt)}** ({pct:.1f}%)")

            # Month-by-month trend
            y_monthly_inc = y_income.groupby(y_income["date"].dt.month)["amount"].sum()
            y_monthly_exp = y_expenses.groupby(y_expenses["date"].dt.month)["amount"].sum()
            import calendar
            months = list(range(1, 13))
            month_labels = [calendar.month_abbr[m] for m in months]
            inc_vals = [y_monthly_inc.get(m, 0) for m in months]
            exp_vals = [y_monthly_exp.get(m, 0) for m in months]

            fig_yir = go.Figure()
            fig_yir.add_trace(go.Bar(x=month_labels, y=inc_vals, name="Income",
                                     marker_color=CHART_COLORS[3]))
            fig_yir.add_trace(go.Bar(x=month_labels, y=exp_vals, name="Expenses",
                                     marker_color=CHART_COLORS[5]))
            apply_layout(fig_yir, height=350, title=f"{yir_year} Monthly Income vs Expenses",
                         barmode="group")
            st.plotly_chart(fig_yir, width='stretch')

            # Category donut for the year
            if not y_expenses.empty:
                y_cat_totals = y_expenses.groupby("category")["amount"].sum().reset_index()
                y_cat_totals.columns = ["Category", "Amount"]
                fig_yir_pie = px.pie(y_cat_totals, names="Category", values="Amount",
                                     title=f"{yir_year} Spending Breakdown",
                                     color_discrete_sequence=CHART_COLORS)
                fig_yir_pie.update_traces(hole=0.65)
                apply_layout(fig_yir_pie, height=380)
                st.plotly_chart(fig_yir_pie, width='stretch')

            # Generate Year-in-Review PDF
            if st.button(f"📄 Generate {yir_year} Year-in-Review PDF", key="yir_pdf_btn"):
                with st.spinner("Generating Year-in-Review PDF..."):
                    try:
                        pdf_bytes = _build_year_in_review_pdf(
                            yir_year, user_name, y_total_income, y_total_expenses,
                            y_net_savings, y_savings_rate,
                            y_top if not y_expenses.empty else pd.Series(dtype=float),
                            fig_yir, fig_yir_pie if not y_expenses.empty else None,
                        )
                        st.session_state["yir_pdf"] = pdf_bytes
                        st.toast("Year-in-Review PDF generated!", icon="✅")
                    except Exception as e:
                        st.error(f"Error generating PDF: {e}")

            if "yir_pdf" in st.session_state:
                st.download_button(
                    f"⬇️ Download {yir_year} Year-in-Review PDF",
                    data=st.session_state["yir_pdf"],
                    file_name=f"year_in_review_{yir_year}.pdf",
                    mime="application/pdf",
                    key="yir_pdf_dl",
                )
        else:
            st.info(f"No transactions found for {yir_year}.")
    else:
        st.info("Upload transactions to generate a Year-in-Review report.")

    # ── Tax Summary ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Tax Summary")

    if available_years:
        tax_year = st.selectbox("Tax Year", available_years, key="tax_year_select")
        tax_data = work[work["date"].dt.year == tax_year].copy()

        if not tax_data.empty:
            # Load tax-deductible categories from settings
            _tax_settings = load_json("settings.json", default={})
            _tax_cats = _tax_settings.get("custom_categories", [])
            deductible_names = {c["name"] for c in _tax_cats if c.get("tax_deductible", False)}

            # Income by source/description
            tax_income = tax_data[tax_data["amount"] > 0].copy()
            tax_expenses = tax_data[tax_data["amount"] < 0].copy()
            tax_expenses["amount"] = tax_expenses["amount"].abs()

            st.markdown(f"#### {tax_year} Income Summary")
            if not tax_income.empty:
                # Group by description (approximate source/client)
                inc_by_source = tax_income.groupby("description")["amount"].sum().sort_values(ascending=False)
                total_tax_income = tax_income["amount"].sum()

                # Flag sources over $600 (1099 threshold)
                st.markdown(f"**Total Income:** {format_currency(total_tax_income)}")
                for src, amt in inc_by_source.head(15).items():
                    flag = " — **1099 likely**" if amt >= 600 else ""
                    st.markdown(f"- {src}: {format_currency(amt)}{flag}")

                if (inc_by_source >= 600).any():
                    st.warning("Sources marked '1099 likely' exceed the $600 threshold for 1099-MISC/NEC reporting.")
            else:
                st.info("No income transactions found.")

            # Deductible expenses
            st.markdown(f"#### {tax_year} Deductible Expenses")
            if deductible_names:
                ded_expenses = tax_expenses[tax_expenses["category"].isin(deductible_names)]
                if not ded_expenses.empty:
                    ded_by_cat = ded_expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
                    total_deductible = ded_expenses["amount"].sum()
                    st.markdown(f"**Total Deductible:** {format_currency(total_deductible)}")
                    for cat, amt in ded_by_cat.items():
                        st.markdown(f"- {cat}: {format_currency(amt)}")
                else:
                    st.info("No expenses in tax-deductible categories for this year.")
            else:
                st.info("No categories marked as tax-deductible. Go to **Settings > Profile > Budget Categories** to mark categories.")

            # Quarterly breakdown
            st.markdown(f"#### {tax_year} Quarterly Breakdown")
            tax_data["quarter"] = tax_data["date"].dt.quarter
            q_income = tax_data[tax_data["amount"] > 0].groupby("quarter")["amount"].sum()
            q_expenses_raw = tax_data[tax_data["amount"] < 0].copy()
            q_expenses_raw["amount"] = q_expenses_raw["amount"].abs()
            q_expenses_sum = q_expenses_raw.groupby("quarter")["amount"].sum()

            q_rows = []
            for q in range(1, 5):
                q_inc = q_income.get(q, 0)
                q_exp = q_expenses_sum.get(q, 0)
                q_rows.append({"Quarter": f"Q{q}", "Income": q_inc, "Expenses": q_exp, "Net": q_inc - q_exp})
            q_df = pd.DataFrame(q_rows)
            st.dataframe(q_df.style.format({"Income": lambda x: format_currency(x),
                                             "Expenses": lambda x: format_currency(x),
                                             "Net": lambda x: format_currency(x)}),
                         width='stretch', hide_index=True)

            # CSV export
            tax_csv_buf = io.StringIO()
            tax_export = tax_data.drop(columns=["month", "quarter"], errors="ignore").copy()
            tax_export["date"] = tax_export["date"].dt.strftime("%Y-%m-%d")
            tax_export.to_csv(tax_csv_buf, index=False)
            st.download_button(
                f"⬇️ Download {tax_year} Tax Data (CSV)",
                data=tax_csv_buf.getvalue(),
                file_name=f"tax_data_{tax_year}.csv",
                mime="text/csv",
                key="tax_csv_dl",
            )
        else:
            st.info(f"No transactions found for tax year {tax_year}.")

    # ── Compare Years ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Compare Years")

    if len(available_years) >= 2:
        cmp_c1, cmp_c2 = st.columns(2)
        with cmp_c1:
            cmp_year1 = st.selectbox("Year A", available_years, index=0, key="cmp_year_a")
        with cmp_c2:
            year_b_options = [y for y in available_years if y != cmp_year1]
            cmp_year2 = st.selectbox("Year B", year_b_options, index=0, key="cmp_year_b") if year_b_options else None

        if cmp_year2:
            import calendar as cal_mod
            y1_data = work[work["date"].dt.year == cmp_year1]
            y2_data = work[work["date"].dt.year == cmp_year2]

            y1_exp = y1_data[y1_data["amount"] < 0].copy()
            y1_exp["amount"] = y1_exp["amount"].abs()
            y2_exp = y2_data[y2_data["amount"] < 0].copy()
            y2_exp["amount"] = y2_exp["amount"].abs()

            months = list(range(1, 13))
            m_labels = [cal_mod.month_abbr[m] for m in months]

            y1_monthly = y1_exp.groupby(y1_exp["date"].dt.month)["amount"].sum()
            y2_monthly = y2_exp.groupby(y2_exp["date"].dt.month)["amount"].sum()

            fig_cmp = go.Figure()
            fig_cmp.add_trace(go.Bar(
                x=m_labels, y=[y1_monthly.get(m, 0) for m in months],
                name=str(cmp_year1), marker_color=CHART_COLORS[0],
            ))
            fig_cmp.add_trace(go.Bar(
                x=m_labels, y=[y2_monthly.get(m, 0) for m in months],
                name=str(cmp_year2), marker_color=CHART_COLORS[3],
            ))
            apply_layout(fig_cmp, height=350,
                         title=f"Monthly Spending: {cmp_year1} vs {cmp_year2}",
                         barmode="group")
            st.plotly_chart(fig_cmp, width='stretch')

            # Summary comparison
            y1_total = y1_exp["amount"].sum()
            y2_total = y2_exp["amount"].sum()
            y1_inc = y1_data[y1_data["amount"] > 0]["amount"].sum()
            y2_inc = y2_data[y2_data["amount"] > 0]["amount"].sum()

            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown(f"**{cmp_year1}**")
                st.metric("Total Expenses", format_currency(y1_total))
                st.metric("Total Income", format_currency(y1_inc))
                st.metric("Net", format_currency(y1_inc - y1_total))
            with cc2:
                st.markdown(f"**{cmp_year2}**")
                st.metric("Total Expenses", format_currency(y2_total))
                st.metric("Total Income", format_currency(y2_inc))
                st.metric("Net", format_currency(y2_inc - y2_total))
    elif len(available_years) == 1:
        st.info("Need at least 2 years of data to compare.")
    else:
        st.info("Upload transactions to compare years.")

    # ── Generate & Export ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Generate Report")

    gc1, gc2 = st.columns(2)

    with gc1:
        if st.button("📄 Generate PDF Report", type="primary"):
            with st.spinner("Generating PDF..."):
                try:
                    pdf_bytes = _build_pdf(
                        user_name, date_range_str,
                        total_income, total_expenses, net, avg_txn,
                        top_cats, fig_monthly, fig_pie, fig_line,
                        work, net_worth_data,
                    )
                    st.session_state["report_pdf"] = pdf_bytes
                    st.toast("PDF generated!", icon="✅")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")

        if "report_pdf" in st.session_state:
            st.download_button(
                "⬇️ Download PDF",
                data=st.session_state["report_pdf"],
                file_name="financial_report.pdf",
                mime="application/pdf",
            )

    with gc2:
        xlsx_buf = io.BytesIO()
        with pd.ExcelWriter(xlsx_buf, engine="xlsxwriter") as writer:
            work.drop(columns=["month"], errors="ignore").to_excel(writer, index=False, sheet_name="Transactions")
        st.download_button(
            "⬇️ Download Excel",
            data=xlsx_buf.getvalue(),
            file_name="transactions_cleaned.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # ── Email Report ───────────────────────────────────────────────────────
    with st.expander("📧 Email This Report"):
        st.caption(
            "Send the PDF report via email. Uses SMTP settings from **Settings → Email** "
            "or environment variables, with manual override below."
        )
        # Load centralized SMTP settings
        _smtp_cfg = load_json("settings.json", default={}).get("email_smtp", {})
        smtp_host = _smtp_cfg.get("server", "") or os.environ.get("SMTP_HOST", "")
        smtp_user = _smtp_cfg.get("email", "") or os.environ.get("SMTP_USER", "")
        smtp_pass_env = _smtp_cfg.get("password", "") or os.environ.get("SMTP_PASS", "")

        ec1, ec2 = st.columns(2)
        with ec1:
            recipient_email = st.text_input("Send to (email address)")
            email_smtp_host = st.text_input("SMTP Host", value=smtp_host or "", placeholder="smtp.gmail.com")
            email_smtp_port = st.number_input("Port", value=int(_smtp_cfg.get("port", 587)), step=1)
        with ec2:
            email_user = st.text_input("From email", value=smtp_user or "")
            email_pass = st.text_input("Password / App Password", type="password",
                                        value=smtp_pass_env or "")

        if st.button("📤 Send Report"):
            if "report_pdf" not in st.session_state:
                st.error("Generate the PDF first above.")
            elif not recipient_email:
                st.error("Enter a recipient email address.")
            elif not all([email_smtp_host, email_user, email_pass]):
                st.error("Fill in all SMTP fields.")
            else:
                try:
                    msg = MIMEMultipart()
                    msg["From"] = email_user
                    msg["To"] = recipient_email
                    msg["Subject"] = f"FinanceKit Financial Report — {date_range_str}"
                    _sym = get_currency_symbol()
                    msg.attach(MIMEText(
                        f"Hi,\n\nPlease find your FinanceKit financial report attached.\n\n"
                        f"Period: {date_range_str}\n"
                        f"Income: {_sym}{total_income:,.2f}\n"
                        f"Expenses: {_sym}{total_expenses:,.2f}\n"
                        f"Net: {_sym}{net:,.2f}\n\n"
                        f"Generated by FinanceKit",
                        "plain",
                    ))
                    attachment = MIMEBase("application", "octet-stream")
                    attachment.set_payload(st.session_state["report_pdf"])
                    encoders.encode_base64(attachment)
                    attachment.add_header("Content-Disposition", 'attachment; filename="financial_report.pdf"')
                    msg.attach(attachment)

                    with smtplib.SMTP(email_smtp_host, int(email_smtp_port)) as server:
                        server.starttls()
                        server.login(email_user, email_pass)
                        server.send_message(msg)
                    st.toast(f"Report sent to {recipient_email}!", icon="✅")
                except Exception as e:
                    st.error(f"Failed to send: {e}")


# ── PDF Builder ───────────────────────────────────────────────────────────

def _build_pdf(user_name, date_range, total_income, total_expenses, net, avg_txn,
               top_cats, fig_monthly, fig_pie, fig_line, work_df, net_worth_data=None):
    from utils.report_builder import ReportPDF
    sym = get_currency_symbol()

    pdf = ReportPDF(title="FinanceKit Financial Report", user_name=user_name)
    pdf.add_title_page(date_range=date_range)

    pdf.add_page()
    pdf.add_section_header("Summary Statistics")
    pdf.add_summary_box({
        "Total Income": f"{sym}{total_income:,.2f}",
        "Total Expenses": f"{sym}{total_expenses:,.2f}",
        "Net": f"{sym}{net:,.2f}",
        "Average Transaction": f"{sym}{avg_txn:,.2f}",
        "Period": date_range,
    })
    pdf.ln(4)

    if net_worth_data:
        pdf.add_section_header("Net Worth")
        nw = net_worth_data["total_assets"] - net_worth_data["total_liabilities"]
        pdf.add_stat_line("Total Assets:", f"{sym}{net_worth_data['total_assets']:,.2f}")
        pdf.add_stat_line("Total Liabilities:", f"{sym}{net_worth_data['total_liabilities']:,.2f}")
        pdf.add_stat_line("Net Worth:", f"{sym}{nw:,.2f}")
        pdf.ln(4)

    if not top_cats.empty:
        pdf.add_section_header("Top Spending Categories")
        for cat, amt in top_cats.items():
            pdf.add_stat_line(f"  {cat}:", f"{sym}{amt:,.2f}")

    pdf.add_page()
    pdf.add_section_header("Monthly Spending")
    pdf.add_chart_image(fig_monthly)

    if fig_pie is not None:
        pdf.add_page()
        pdf.add_section_header("Spending by Category")
        pdf.add_chart_image(fig_pie)

    pdf.add_page()
    pdf.add_section_header("Income vs Expenses")
    pdf.add_chart_image(fig_line)

    pdf.add_page()
    pdf.add_section_header("Transaction Details")
    table_df = work_df.drop(columns=["month"], errors="ignore").copy()
    table_df["date"] = table_df["date"].dt.strftime("%Y-%m-%d")
    table_df["amount"] = table_df["amount"].apply(lambda x: f"{sym}{x:,.2f}")
    headers = list(table_df.columns)
    rows = [[str(c) for c in row] for row in table_df.head(200).values.tolist()]
    pdf.add_table(headers, rows)

    return pdf.get_bytes()


def _build_year_in_review_pdf(year, user_name, total_income, total_expenses,
                               net_savings, savings_rate, top_cats, fig_monthly, fig_pie):
    from utils.report_builder import ReportPDF
    sym = get_currency_symbol()

    pdf = ReportPDF(title=f"FinanceKit {year} Year-in-Review", user_name=user_name)
    pdf.add_title_page(date_range=f"January – December {year}")

    pdf.add_page()
    pdf.add_section_header(f"{year} Annual Summary")
    pdf.add_summary_box({
        "Total Income": f"{sym}{total_income:,.2f}",
        "Total Expenses": f"{sym}{total_expenses:,.2f}",
        "Net Savings": f"{sym}{net_savings:,.2f}",
        "Savings Rate": f"{savings_rate:.1f}%",
    })
    pdf.ln(4)

    if not top_cats.empty:
        pdf.add_section_header("Top Spending Categories")
        for cat, amt in top_cats.items():
            pdf.add_stat_line(f"  {cat}:", f"{sym}{amt:,.2f}")

    pdf.add_page()
    pdf.add_section_header("Monthly Income vs Expenses")
    pdf.add_chart_image(fig_monthly)

    if fig_pie is not None:
        pdf.add_page()
        pdf.add_section_header("Spending Breakdown")
        pdf.add_chart_image(fig_pie)

    return pdf.get_bytes()
