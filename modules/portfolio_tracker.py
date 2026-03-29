import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils.data_persistence import load_json, save_json
from utils.finance_api import (
    get_stock_price, get_stock_history,
    get_crypto_price, get_crypto_history, CRYPTO_IDS,
)
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout, CHART_COLORS
from utils.formatting import format_currency, get_currency_symbol

DATA_FILE = "portfolio.json"


def _load():
    return load_json(DATA_FILE, default={"holdings": [], "alerts": [], "watchlist": []})


def _save(data):
    save_json(DATA_FILE, data)


def render():
    render_module_header("📈", "Stock & Crypto Portfolio Tracker",
                         "Track your holdings, see live prices and performance, and set price alerts.")

    if "portfolio" not in st.session_state:
        st.session_state.portfolio = _load()

    portfolio = st.session_state.portfolio
    holdings = portfolio.get("holdings", [])
    alerts = portfolio.get("alerts", [])
    watchlist = portfolio.get("watchlist", [])

    tab_portfolio, tab_watchlist, tab_alerts = st.tabs(["📊 Portfolio", "👁️ Watchlist", "🔔 Price Alerts"])

    with tab_portfolio:
        # ── Add Holding ───────────────────────────────────────────────────
        with st.expander("➕ Add Holding", expanded=not holdings):
            with st.form("add_holding", clear_on_submit=True):
                hc1, hc2, hc3, hc4 = st.columns(4)
                with hc1:
                    ticker = st.text_input("Ticker Symbol", placeholder="AAPL or BTC").upper().strip()
                with hc2:
                    asset_type = st.selectbox("Type", ["Stock", "Crypto"])
                with hc3:
                    purchase_price = st.number_input("Purchase Price ($)", min_value=0.0, step=0.01, format="%.2f")
                with hc4:
                    quantity = st.number_input("Quantity", min_value=0.0, step=0.01, format="%.4f")

                if st.form_submit_button("➕ Add to Portfolio", type="primary", use_container_width=True):
                    if not ticker:
                        st.error("Please enter a ticker symbol.")
                    elif purchase_price <= 0 or quantity <= 0:
                        st.error("Purchase price and quantity must be > 0.")
                    else:
                        holdings.append({
                            "ticker": ticker,
                            "type": asset_type,
                            "purchase_price": purchase_price,
                            "quantity": quantity,
                            "added": str(datetime.today().date()),
                        })
                        portfolio["holdings"] = holdings
                        _save(portfolio)
                        st.toast(f"Added {quantity} × {ticker}!", icon="✅")
                        st.rerun()

        if not holdings:
            from utils.ui_helpers import render_empty_state
            render_empty_state("📈", "No holdings yet",
                               "Add your first stock or crypto above to see your portfolio dashboard.")
            return

        # ── Live Prices ───────────────────────────────────────────────────
        rc1, rc2 = st.columns([3, 1])
        with rc2:
            if st.button("🔄 Refresh Prices", use_container_width=True):
                st.session_state.pop("price_cache", None)

        if "price_cache" not in st.session_state:
            with st.spinner("Fetching live prices..."):
                cache = {}
                for h in holdings:
                    key = f"{h['ticker']}_{h['type']}"
                    if key not in cache:
                        if h["type"] == "Crypto":
                            cache[key] = get_crypto_price(h["ticker"])
                        else:
                            cache[key] = get_stock_price(h["ticker"])
                st.session_state.price_cache = cache

        price_cache = st.session_state.price_cache

        rows = []
        total_value, total_cost = 0.0, 0.0

        for i, h in enumerate(holdings):
            key = f"{h['ticker']}_{h['type']}"
            price_data = price_cache.get(key)
            current = price_data["price"] if price_data else None
            cost_basis = h["purchase_price"] * h["quantity"]
            total_cost += cost_basis

            if current is not None:
                market_value = current * h["quantity"]
                gain_loss = market_value - cost_basis
                gain_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
                total_value += market_value
                change_pct = price_data.get("change_pct", 0)
            else:
                market_value = gain_loss = gain_pct = change_pct = None
                total_value += cost_basis

            sym = get_currency_symbol()
            rows.append({
                "Ticker": h["ticker"],
                "Type": h["type"],
                "Qty": h["quantity"],
                "Avg Cost": f"{sym}{h['purchase_price']:,.2f}",
                "Current Price": f"{sym}{current:,.2f}" if current else "N/A",
                "Market Value": f"{sym}{market_value:,.2f}" if market_value is not None else "N/A",
                "Gain/Loss ($)": f"{sym}{gain_loss:+,.2f}" if gain_loss is not None else "N/A",
                "Gain/Loss (%)": f"{gain_pct:+.2f}%" if gain_pct is not None else "N/A",
                "24h Change": f"{change_pct:+.2f}%" if change_pct is not None else "N/A",
                "_idx": i,
            })

        total_gain = total_value - total_cost
        total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0

        # Top gainer / loser
        ranked = [(r, float(r["Gain/Loss (%)"].replace("%", "").replace("+", ""))
                   if r["Gain/Loss (%)"] != "N/A" else 0) for r in rows]
        top_gainer = max(ranked, key=lambda x: x[1]) if ranked else None
        top_loser = min(ranked, key=lambda x: x[1]) if ranked else None

        sym = get_currency_symbol()
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Portfolio Value", format_currency(total_value))
        m2.metric("Total Cost Basis", format_currency(total_cost))
        m3.metric("Total Gain/Loss", format_currency(total_gain, show_sign=True), delta=f"{total_gain_pct:+.2f}%")
        if top_gainer:
            m4.metric("Top Gainer", top_gainer[0]["Ticker"], delta=f"{top_gainer[1]:+.2f}%")
        if top_loser:
            m5.metric("Top Loser", top_loser[0]["Ticker"], delta=f"{top_loser[1]:+.2f}%")

        display_df = pd.DataFrame(rows).drop(columns=["_idx"])
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # ── Portfolio Allocation Pie ───────────────────────────────────────
        if any(r["Market Value"] != "N/A" for r in rows):
            st.markdown("---")
            st.markdown("### Portfolio Allocation")
            pc1, pc2 = st.columns(2)

            with pc1:
                # By ticker
                alloc_data = [
                    (r["Ticker"],
                     float(r["Market Value"].replace("$", "").replace(",", "")))
                    for r in rows if r["Market Value"] != "N/A"
                ]
                if alloc_data:
                    alloc_df = pd.DataFrame(alloc_data, columns=["Ticker", "Value"])
                    fig_alloc = px.pie(alloc_df, names="Ticker", values="Value",
                                       title="By Holding",
                                       color_discrete_sequence=CHART_COLORS)
                    fig_alloc.update_traces(hole=0.65)
                    apply_layout(fig_alloc, height=300)
                    st.plotly_chart(fig_alloc, use_container_width=True)

            with pc2:
                # Stocks vs Crypto
                stocks_val = sum(
                    float(r["Market Value"].replace("$", "").replace(",", ""))
                    for r in rows if r["Type"] == "Stock" and r["Market Value"] != "N/A"
                )
                crypto_val = sum(
                    float(r["Market Value"].replace("$", "").replace(",", ""))
                    for r in rows if r["Type"] == "Crypto" and r["Market Value"] != "N/A"
                )
                if stocks_val + crypto_val > 0:
                    fig_type = px.pie(
                        pd.DataFrame({"Type": ["Stocks", "Crypto"], "Value": [stocks_val, crypto_val]}),
                        names="Type", values="Value",
                        title="Stocks vs Crypto",
                        color_discrete_sequence=["#6366f1", "#f59e0b"],
                    )
                    fig_type.update_traces(hole=0.65)
                    apply_layout(fig_type, height=300)
                    st.plotly_chart(fig_type, use_container_width=True)

        # ── Remove Holding ─────────────────────────────────────────────────
        st.markdown("---")
        remove_options = [f"{h['ticker']} ({h['type']}) - Qty: {h['quantity']}" for h in holdings]
        rc1, rc2 = st.columns([4, 1])
        with rc1:
            remove_choice = st.selectbox("Remove a holding", ["— select —"] + remove_options)
        with rc2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Remove", use_container_width=True) and remove_choice != "— select —":
                idx = remove_options.index(remove_choice)
                holdings.pop(idx)
                portfolio["holdings"] = holdings
                _save(portfolio)
                st.session_state.pop("price_cache", None)
                st.rerun()

        # ── Performance Chart (auto-loads) ────────────────────────────────
        st.markdown("---")
        st.markdown("### Portfolio Performance Over Time")
        pc1, pc2 = st.columns([3, 1])
        with pc1:
            period = st.selectbox("Chart period", ["1mo", "3mo", "6mo", "1y"], index=0)
        with pc2:
            st.markdown("<br>", unsafe_allow_html=True)
            reload_perf = st.button("🔄 Reload", use_container_width=True)

        days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
        cache_key = f"perf_cache_{period}"

        if cache_key not in st.session_state or reload_perf:
            with st.spinner("Loading historical data..."):
                perf_data = {}
                total_values = {}
                for h in holdings:
                    if h["type"] == "Crypto":
                        hist = get_crypto_history(h["ticker"], days=days_map.get(period, 30))
                    else:
                        hist = get_stock_history(h["ticker"], period=period)
                    if hist:
                        perf_data[h["ticker"]] = [(r["date"], r["close"] * h["quantity"]) for r in hist]
                        for r in hist:
                            d = r["date"]
                            total_values[d] = total_values.get(d, 0) + r["close"] * h["quantity"]
                st.session_state[cache_key] = (perf_data, total_values)

        perf_data, total_values = st.session_state.get(cache_key, ({}, {}))

        if perf_data:
            fig = go.Figure()
            # Total portfolio value line
            if total_values and len(holdings) > 1:
                sorted_totals = sorted(total_values.items())
                fig.add_trace(go.Scatter(
                    x=[d for d, _ in sorted_totals],
                    y=[v for _, v in sorted_totals],
                    name="Total Portfolio",
                    mode="lines",
                    line=dict(color="#22c55e", width=3, dash="dot"),
                ))
            # Individual holding lines
            for ticker, points in perf_data.items():
                fig.add_trace(go.Scatter(
                    x=[d for d, _ in points],
                    y=[v for _, v in points],
                    name=ticker,
                    mode="lines",
                ))
            apply_layout(fig, height=400, title="Holdings Value Over Time", yaxis_title="Value ($)")
            st.plotly_chart(fig, use_container_width=True)
        elif st.session_state.get(cache_key):
            st.info("No historical data available for the selected period.")

    with tab_watchlist:
        st.markdown("### 👁️ Watchlist")
        st.markdown("Track tickers without adding them to your portfolio.")

        with st.form("add_watchlist", clear_on_submit=True):
            wc1, wc2 = st.columns([2, 1])
            with wc1:
                w_ticker = st.text_input("Ticker Symbol", placeholder="NVDA, ETH...").upper().strip()
            with wc2:
                w_type = st.selectbox("Type", ["Stock", "Crypto"])
            if st.form_submit_button("➕ Add to Watchlist", use_container_width=True):
                if w_ticker and not any(w["ticker"] == w_ticker for w in watchlist):
                    watchlist.append({"ticker": w_ticker, "type": w_type, "added": str(datetime.today().date())})
                    portfolio["watchlist"] = watchlist
                    _save(portfolio)
                    st.toast(f"{w_ticker} added to watchlist!", icon="✅")
                    st.rerun()
                elif not w_ticker:
                    st.error("Enter a ticker.")
                else:
                    st.warning(f"{w_ticker} is already in your watchlist.")

        if not watchlist:
            from utils.ui_helpers import render_empty_state
            render_empty_state("👁️", "Watchlist is empty",
                               "Add tickers above to monitor prices without buying.")
        else:
            if st.button("🔄 Fetch Watchlist Prices"):
                with st.spinner("Fetching prices..."):
                    wl_cache = {}
                    for w in watchlist:
                        key = f"{w['ticker']}_{w['type']}"
                        if key not in wl_cache:
                            if w["type"] == "Crypto":
                                wl_cache[key] = get_crypto_price(w["ticker"])
                            else:
                                wl_cache[key] = get_stock_price(w["ticker"])
                    st.session_state.wl_cache = wl_cache

            wl_cache = st.session_state.get("wl_cache", {})
            wl_rows = []
            for w in watchlist:
                key = f"{w['ticker']}_{w['type']}"
                price_data = wl_cache.get(key)
                price = price_data["price"] if price_data else None
                chg = price_data.get("change_pct") if price_data else None
                wl_rows.append({
                    "Ticker": w["ticker"],
                    "Type": w["type"],
                    "Price": format_currency(price) if price else "—",
                    "24h Change": f"{chg:+.2f}%" if chg is not None else "—",
                    "Added": w.get("added", ""),
                })
            st.dataframe(pd.DataFrame(wl_rows), use_container_width=True, hide_index=True)

            remove_wl = st.selectbox("Remove from watchlist", ["— select —"] + [w["ticker"] for w in watchlist])
            if st.button("🗑️ Remove from Watchlist") and remove_wl != "— select —":
                portfolio["watchlist"] = [w for w in watchlist if w["ticker"] != remove_wl]
                _save(portfolio)
                st.rerun()

    with tab_alerts:
        st.markdown("### 🔔 Price Alerts")
        # Load centralized SMTP settings for email alerts
        _smtp_settings = load_json("settings.json", default={}).get("email_smtp", {})

        with st.form("add_alert", clear_on_submit=True):
            all_tickers = list({h["ticker"] for h in holdings} | {w["ticker"] for w in watchlist})
            if not all_tickers:
                st.info("Add holdings or watchlist items first to set alerts.")
            else:
                ac1, ac2, ac3 = st.columns(3)
                with ac1:
                    alert_ticker = st.selectbox("Ticker", all_tickers)
                with ac2:
                    alert_direction = st.selectbox("Direction", ["Above", "Below"])
                with ac3:
                    alert_price = st.number_input("Target Price ($)", min_value=0.01, step=0.01, format="%.2f")

                if st.form_submit_button("🔔 Set Alert", use_container_width=True):
                    alerts.append({
                        "ticker": alert_ticker,
                        "direction": alert_direction,
                        "target": alert_price,
                    })
                    portfolio["alerts"] = alerts
                    _save(portfolio)
                    st.toast(f"Alert set: {alert_ticker} {alert_direction.lower()} ${alert_price:,.2f}", icon="✅")
                    st.rerun()

        if alerts:
            # Auto-check alerts using available price data
            price_cache_all = dict(st.session_state.get("price_cache", {}))
            price_cache_all.update(st.session_state.get("wl_cache", {}))
            triggered, remaining = [], []
            for a in alerts:
                key_s = f"{a['ticker']}_Stock"
                key_c = f"{a['ticker']}_Crypto"
                price_data = price_cache_all.get(key_s) or price_cache_all.get(key_c)
                current = price_data["price"] if price_data else None
                if current is not None:
                    hit = (a["direction"] == "Above" and current >= a["target"]) or \
                          (a["direction"] == "Below" and current <= a["target"])
                    if hit:
                        triggered.append(a)
                        icon = "🟢" if a["direction"] == "Above" else "🔴"
                        st.success(f"{icon} **TRIGGERED:** {a['ticker']} at {format_currency(current)} — target: {a['direction'].lower()} {format_currency(a['target'])}")
                    else:
                        remaining.append(a)
                        st.write(f"⏳ {a['ticker']} {a['direction'].lower()} {format_currency(a['target'])} — currently {format_currency(current)}")
                else:
                    remaining.append(a)
                    st.write(f"⏳ {a['ticker']} {a['direction'].lower()} {format_currency(a['target'])} — refresh prices first")

            if triggered and st.button("Clear triggered alerts"):
                portfolio["alerts"] = remaining
                _save(portfolio)
                st.rerun()

        with st.expander("⚙️ Email Alert Settings (optional)"):
            st.caption(
                "Set up SMTP to receive email notifications when alerts trigger. "
                "You can also configure these in **Settings → Email (SMTP)**."
            )
            smtp_host = st.text_input("SMTP Server", value=_smtp_settings.get("server", ""), placeholder="smtp.gmail.com")
            smtp_port = st.number_input("Port", value=int(_smtp_settings.get("port", 587)), step=1)
            smtp_user = st.text_input("Email Address", value=_smtp_settings.get("email", ""))
            smtp_pass = st.text_input("Password / App Password", type="password", value=_smtp_settings.get("password", ""))

            if st.button("Send Test Email"):
                if not all([smtp_host, smtp_user, smtp_pass]):
                    st.error("Fill in all SMTP fields.")
                else:
                    try:
                        import smtplib
                        from email.mime.text import MIMEText
                        msg = MIMEText("FinanceKit test email — alerts are working!")
                        msg["Subject"] = "FinanceKit Test Alert"
                        msg["From"] = smtp_user
                        msg["To"] = smtp_user
                        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                            server.starttls()
                            server.login(smtp_user, smtp_pass)
                            server.send_message(msg)
                        st.toast("Test email sent!", icon="✅")
                    except Exception as e:
                        st.error(f"Failed: {e}")
