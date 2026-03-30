import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils.i18n import t
from utils.data_persistence import load_json, save_json
from utils.finance_api import (
    get_stock_price, get_stock_history,
    get_crypto_price, get_crypto_history, CRYPTO_IDS,
)
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout, CHART_COLORS
from utils.formatting import format_currency, get_currency_symbol
from utils.notifications import create_notification

DATA_FILE = "portfolio.json"

# Sector mapping for common tickers
SECTOR_MAP = {
    "AAPL": "Tech", "MSFT": "Tech", "GOOGL": "Tech", "GOOG": "Tech", "AMZN": "Tech",
    "META": "Tech", "NVDA": "Tech", "TSLA": "Tech", "AMD": "Tech", "INTC": "Tech",
    "CRM": "Tech", "ORCL": "Tech", "ADBE": "Tech", "NFLX": "Tech", "PYPL": "Tech",
    "SQ": "Tech", "SHOP": "Tech", "UBER": "Tech", "SNAP": "Tech", "PINS": "Tech",
    "CSCO": "Tech", "IBM": "Tech", "QCOM": "Tech", "TXN": "Tech", "AVGO": "Tech",
    "NOW": "Tech", "SNOW": "Tech", "PLTR": "Tech", "NET": "Tech", "DDOG": "Tech",
    "JPM": "Finance", "BAC": "Finance", "WFC": "Finance", "GS": "Finance", "MS": "Finance",
    "V": "Finance", "MA": "Finance", "AXP": "Finance", "C": "Finance", "BLK": "Finance",
    "SCHW": "Finance", "COF": "Finance", "USB": "Finance",
    "JNJ": "Healthcare", "UNH": "Healthcare", "PFE": "Healthcare", "ABBV": "Healthcare",
    "MRK": "Healthcare", "LLY": "Healthcare", "TMO": "Healthcare", "ABT": "Healthcare",
    "MDT": "Healthcare", "DHR": "Healthcare", "BMY": "Healthcare", "AMGN": "Healthcare",
    "XOM": "Energy", "CVX": "Energy", "COP": "Energy", "SLB": "Energy", "EOG": "Energy",
    "OXY": "Energy", "MPC": "Energy", "VLO": "Energy", "PSX": "Energy",
    "PG": "Consumer", "KO": "Consumer", "PEP": "Consumer", "WMT": "Consumer",
    "COST": "Consumer", "HD": "Consumer", "NKE": "Consumer", "MCD": "Consumer",
    "SBUX": "Consumer", "TGT": "Consumer", "LOW": "Consumer", "DIS": "Consumer",
    "BA": "Industrial", "CAT": "Industrial", "HON": "Industrial", "UPS": "Industrial",
    "GE": "Industrial", "MMM": "Industrial", "LMT": "Industrial", "RTX": "Industrial",
    "DE": "Industrial", "UNP": "Industrial", "FDX": "Industrial",
    "AMT": "Real Estate", "PLD": "Real Estate", "CCI": "Real Estate", "SPG": "Real Estate",
    "O": "Real Estate", "EQIX": "Real Estate",
    "NEE": "Utilities", "DUK": "Utilities", "SO": "Utilities", "D": "Utilities",
    "AEP": "Utilities", "SRE": "Utilities",
    "LIN": "Materials", "APD": "Materials", "ECL": "Materials", "NEM": "Materials",
    "FCX": "Materials", "DOW": "Materials",
    "BTC": "Crypto", "ETH": "Crypto", "SOL": "Crypto", "ADA": "Crypto",
    "XRP": "Crypto", "DOT": "Crypto", "DOGE": "Crypto", "AVAX": "Crypto",
    "MATIC": "Crypto", "LINK": "Crypto", "UNI": "Crypto", "ATOM": "Crypto",
    "BNB": "Crypto", "LTC": "Crypto",
}


def _load():
    return load_json(DATA_FILE, default={
        "holdings": [], "alerts": [], "watchlist": [], "trade_history": [],
    })


def _save(data):
    save_json(DATA_FILE, data)


def _get_sector(ticker: str, holding: dict) -> str:
    """Get sector for a ticker, checking user override first."""
    return holding.get("sector", SECTOR_MAP.get(ticker, "Other"))


@st.dialog(t("add_holding"))
def _add_holding_dialog():
    """Dialog for adding a new stock or crypto holding (v4.9)."""
    with st.form("add_holding_dlg", clear_on_submit=True):
        hc1, hc2 = st.columns(2)
        with hc1:
            ticker = st.text_input(t("ticker_symbol"), placeholder="AAPL or BTC").upper().strip()
            purchase_price = st.number_input(t("purchase_price"), min_value=0.0, step=0.01, format="%.2f")
            div_yield = st.number_input(t("dividend_yield_pct"), min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
        with hc2:
            asset_type = st.selectbox(t("type"), ["Stock", "Crypto"])
            quantity = st.number_input(t("quantity"), min_value=0.0, step=0.01, format="%.4f")
            _sector_options = ["Auto-detect", "Tech", "Healthcare", "Finance", "Energy",
                               "Consumer", "Industrial", "Real Estate", "Utilities", "Materials", "Crypto", "Other"]
            sector_choice = st.selectbox(t("sector"), _sector_options)

        if st.form_submit_button(t("add_to_portfolio"), type="primary", width='stretch'):
            if not ticker:
                st.error(t("error_enter_ticker"))
            elif purchase_price <= 0 or quantity <= 0:
                st.error(t("error_price_qty_positive"))
            else:
                portfolio = st.session_state.portfolio
                new_holding = {
                    "ticker": ticker,
                    "type": asset_type,
                    "purchase_price": purchase_price,
                    "quantity": quantity,
                    "added": str(datetime.today().date()),
                    "dividend_yield": div_yield,
                }
                if sector_choice != "Auto-detect":
                    new_holding["sector"] = sector_choice
                portfolio.setdefault("holdings", []).append(new_holding)
                _save(portfolio)
                st.toast(t("toast_added_holding").format(quantity=quantity, ticker=ticker))
                st.rerun()


def render():
    render_module_header("", t("portfolio_tracker_title"),
                         t("portfolio_tracker_subtitle"))

    if "portfolio" not in st.session_state:
        st.session_state.portfolio = _load()

    portfolio = st.session_state.portfolio
    holdings = portfolio.get("holdings", [])
    alerts = portfolio.get("alerts", [])
    watchlist = portfolio.get("watchlist", [])

    trade_history = portfolio.get("trade_history", [])

    # Add holding button (opens dialog)
    if st.button(t("add_holding"), type="primary"):
        _add_holding_dialog()

    tab_portfolio, tab_watchlist, tab_trades, tab_alerts = st.tabs([
        t("portfolio_tab"), t("watchlist_tab"), t("trade_history_tab"), t("price_alerts_tab")
    ])

    with tab_portfolio:

        if not holdings:
            from utils.ui_helpers import render_empty_state
            render_empty_state("", t("no_holdings_yet"),
                               t("no_holdings_yet_desc"))
            return

        # ── Live Prices ───────────────────────────────────────────────────
        rc1, rc2 = st.columns([3, 1])
        with rc2:
            if st.button(t("refresh_prices"), width='stretch'):
                st.session_state.pop("price_cache", None)

        if "price_cache" not in st.session_state:
            with st.spinner(t("fetching_live_prices")):
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

            # Daily change alerts
            if change_pct is not None:
                _prefs = load_json("settings.json", default={}).get("notifications", {})
                _change_threshold = _prefs.get("portfolio_change_pct", 5)
                if change_pct <= -_change_threshold:
                    create_notification(
                        "warning", "portfolio",
                        f"{h['ticker']} down {abs(change_pct):.1f}% today",
                        f"{h['ticker']} is down {abs(change_pct):.1f}% today",
                        action_module="portfolio_tracker",
                    )
                elif change_pct >= _change_threshold * 2:
                    create_notification(
                        "success", "portfolio",
                        f"{h['ticker']} up {change_pct:.1f}% today",
                        f"{h['ticker']} is up {change_pct:.1f}% today!",
                        action_module="portfolio_tracker",
                    )

            sym = get_currency_symbol()
            rows.append({
                t("col_ticker"): h["ticker"],
                t("col_type"): h["type"],
                t("col_qty"): h["quantity"],
                t("col_avg_cost"): f"{sym}{h['purchase_price']:,.2f}",
                t("col_current_price"): f"{sym}{current:,.2f}" if current else "N/A",
                t("col_market_value"): f"{sym}{market_value:,.2f}" if market_value is not None else "N/A",
                t("col_gain_loss_dollar"): f"{sym}{gain_loss:+,.2f}" if gain_loss is not None else "N/A",
                t("col_gain_loss_pct"): f"{gain_pct:+.2f}%" if gain_pct is not None else "N/A",
                t("col_24h_change"): f"{change_pct:+.2f}%" if change_pct is not None else "N/A",
                "_idx": i,
            })

        total_gain = total_value - total_cost
        total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0

        # Top gainer / loser
        ranked = [(r, float(r[t("col_gain_loss_pct")].replace("%", "").replace("+", ""))
                   if r[t("col_gain_loss_pct")] != "N/A" else 0) for r in rows]
        top_gainer = max(ranked, key=lambda x: x[1]) if ranked else None
        top_loser = min(ranked, key=lambda x: x[1]) if ranked else None

        # Dividend income
        annual_div_income = 0
        for h in holdings:
            dy = h.get("dividend_yield", 0)
            if dy > 0:
                key = f"{h['ticker']}_{h['type']}"
                pd_data = price_cache.get(key)
                price = pd_data["price"] if pd_data else h["purchase_price"]
                annual_div_income += price * h["quantity"] * (dy / 100)

        # CAGR calculation
        earliest_date = min((h.get("added", str(datetime.today().date())) for h in holdings), default=str(datetime.today().date()))
        days_invested = (datetime.today().date() - datetime.strptime(earliest_date, "%Y-%m-%d").date()).days
        years_invested = max(days_invested / 365.25, 0.01)  # avoid division by zero
        total_return = total_gain / total_cost if total_cost > 0 else 0
        cagr = ((1 + total_return) ** (1 / years_invested) - 1) * 100

        sym = get_currency_symbol()
        # Row 1: Portfolio Value, Total Gain/Loss, CAGR, Est. Annual Dividends
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t("portfolio_value"), format_currency(total_value))
        m2.metric(t("total_gain_loss"), format_currency(total_gain, show_sign=True), delta=f"{total_gain_pct:+.2f}%")
        with m3:
            _cagr_color = "var(--fk-success)" if cagr >= 0 else "var(--fk-danger)"
            st.markdown(
                f'<div class="dash-widget"><div class="widget-title">{t("cagr")}</div>'
                f'<div class="widget-value" style="color:{_cagr_color};">{cagr:+.2f}%</div>'
                f'<div class="widget-sub">{t("annualized_return_over").format(years=f"{years_invested:.1f}")}</div></div>',
                unsafe_allow_html=True)
        m4.metric(t("est_annual_dividends"), format_currency(annual_div_income) if annual_div_income > 0 else "—")
        # Row 2: Cost Basis, Top Gainer, Top Loser, Holdings Count
        m5, m6, m7, m8 = st.columns(4)
        m5.metric(t("cost_basis"), format_currency(total_cost))
        if top_gainer:
            m6.metric(t("top_gainer"), top_gainer[0][t("col_ticker")], delta=f"{top_gainer[1]:+.2f}%")
        if top_loser:
            m7.metric(t("top_loser"), top_loser[0][t("col_ticker")], delta=f"{top_loser[1]:+.2f}%")
        m8.metric(t("holdings_count"), len(holdings))

        display_df = pd.DataFrame(rows).drop(columns=["_idx"])

        def _color_gain(val):
            """Color gains green, losses red."""
            if isinstance(val, str):
                val = val.replace("$", "").replace(",", "").replace("+", "").replace("%", "")
                try:
                    num = float(val)
                except (ValueError, TypeError):
                    return ""
                if num > 0:
                    return "color: #22c55e"
                elif num < 0:
                    return "color: #ef4444"
            return ""

        styled_df = display_df.style.map(_color_gain, subset=[t("col_gain_loss_dollar"), t("col_gain_loss_pct"), t("col_24h_change")])
        st.dataframe(styled_df, width='stretch', hide_index=True)

        # ── Portfolio Allocation Pie ───────────────────────────────────────
        if any(r[t("col_market_value")] != "N/A" for r in rows):
            st.markdown("---")
            st.markdown(f"### {t('portfolio_allocation')}")
            pc1, pc2 = st.columns(2)

            with pc1:
                # By ticker
                alloc_data = [
                    (r[t("col_ticker")],
                     float(r[t("col_market_value")].replace("$", "").replace(",", "")))
                    for r in rows if r[t("col_market_value")] != "N/A"
                ]
                if alloc_data:
                    alloc_df = pd.DataFrame(alloc_data, columns=["Ticker", "Value"])
                    fig_alloc = px.pie(alloc_df, names="Ticker", values="Value",
                                       title=t("by_holding"),
                                       color_discrete_sequence=CHART_COLORS)
                    fig_alloc.update_traces(hole=0.65)
                    apply_layout(fig_alloc, height=300)
                    st.plotly_chart(fig_alloc, width='stretch')

            with pc2:
                # Sector allocation
                sector_data = {}
                for i, h in enumerate(holdings):
                    r = rows[i] if i < len(rows) else None
                    if r and r[t("col_market_value")] != "N/A":
                        sector = _get_sector(h["ticker"], h)
                        val = float(r[t("col_market_value")].replace("$", "").replace(",", ""))
                        sector_data[sector] = sector_data.get(sector, 0) + val

                if sector_data:
                    sector_df = pd.DataFrame(
                        {"Sector": list(sector_data.keys()), "Value": list(sector_data.values())}
                    ).sort_values("Value", ascending=False)
                    fig_sector = px.pie(sector_df, names="Sector", values="Value",
                                        title=t("sector_allocation"),
                                        color_discrete_sequence=CHART_COLORS)
                    fig_sector.update_traces(hole=0.65)
                    apply_layout(fig_sector, height=300)
                    st.plotly_chart(fig_sector, width='stretch')

                    # Diversification warning
                    total_val = sum(sector_data.values())
                    for sector, val in sector_data.items():
                        if total_val > 0 and (val / total_val) > 0.4:
                            st.warning(t("diversification_warning").format(sector=sector, pct=f"{val/total_val*100:.0f}"))
                            create_notification(
                                "warning", "portfolio",
                                f"{sector} over 40% of portfolio",
                                f"{sector} is {val/total_val*100:.0f}% of your portfolio — consider diversifying",
                                action_module="portfolio_tracker",
                            )

        # ── Sell / Remove Holding ─────────────────────────────────────────
        st.markdown("---")
        sell_options = [f"{h['ticker']} ({h['type']}) - Qty: {h['quantity']}" for h in holdings]
        with st.expander(t("sell_or_remove_holding")):
            sc1, sc2 = st.columns([3, 1])
            with sc1:
                sell_choice = st.selectbox(t("select_holding"), ["— select —"] + sell_options, key="sell_select")
            if sell_choice != "— select —":
                sell_idx = sell_options.index(sell_choice)
                sell_h = holdings[sell_idx]
                with st.form("sell_form"):
                    sf1, sf2 = st.columns(2)
                    with sf1:
                        sell_qty = st.number_input(t("quantity_to_sell"), min_value=0.01,
                                                    max_value=float(sell_h["quantity"]),
                                                    value=float(sell_h["quantity"]), step=0.01, format="%.4f")
                    with sf2:
                        _key = f"{sell_h['ticker']}_{sell_h['type']}"
                        _current = price_cache.get(_key, {}).get("price", sell_h["purchase_price"]) if price_cache else sell_h["purchase_price"]
                        sell_price = st.number_input(t("sale_price"), min_value=0.01,
                                                      value=float(_current), step=0.01, format="%.2f")

                    sf_btn1, sf_btn2 = st.columns(2)
                    with sf_btn1:
                        if st.form_submit_button(t("sell_and_record"), type="primary", width='stretch'):
                            realized_gl = (sell_price - sell_h["purchase_price"]) * sell_qty
                            # Determine short/long term
                            added_date = sell_h.get("added", "")
                            holding_days = 0
                            try:
                                added_dt = datetime.strptime(added_date, "%Y-%m-%d")
                                holding_days = (datetime.now() - added_dt).days
                            except (ValueError, TypeError):
                                pass
                            term = "Long-term" if holding_days > 365 else "Short-term"

                            trade = {
                                "date": str(datetime.today().date()),
                                "ticker": sell_h["ticker"],
                                "type": sell_h["type"],
                                "quantity": sell_qty,
                                "buy_price": sell_h["purchase_price"],
                                "sell_price": sell_price,
                                "gain_loss": round(realized_gl, 2),
                                "term": term,
                                "holding_days": holding_days,
                            }
                            if "trade_history" not in portfolio:
                                portfolio["trade_history"] = []
                            portfolio["trade_history"].append(trade)

                            # Update or remove holding
                            remaining_qty = sell_h["quantity"] - sell_qty
                            if remaining_qty <= 0.0001:
                                holdings.pop(sell_idx)
                            else:
                                holdings[sell_idx]["quantity"] = remaining_qty
                            portfolio["holdings"] = holdings
                            _save(portfolio)
                            st.session_state.pop("price_cache", None)
                            gl_str = format_currency(abs(realized_gl))
                            _gl_label = t("gain") if realized_gl >= 0 else t("loss")
                            st.toast(t("toast_sold_holding").format(qty=sell_qty, ticker=sell_h['ticker'], gl_label=_gl_label, gl_str=gl_str, term=term))
                            st.rerun()

                    with sf_btn2:
                        if st.form_submit_button(t("remove_no_record"), width='stretch'):
                            holdings.pop(sell_idx)
                            portfolio["holdings"] = holdings
                            _save(portfolio)
                            st.session_state.pop("price_cache", None)
                            st.rerun()

        # ── Export Portfolio ───────────────────────────────────────────────
        if st.button(t("export_portfolio_csv"), width='content'):
            export_rows = []
            for i, h in enumerate(holdings):
                r = rows[i] if i < len(rows) else {}
                export_rows.append({
                    t("col_ticker"): h["ticker"],
                    t("col_type"): h["type"],
                    t("col_shares"): h["quantity"],
                    t("col_avg_cost"): h["purchase_price"],
                    t("col_current_price"): r.get(t("col_current_price"), "N/A").replace("$", "").replace(",", ""),
                    t("col_market_value"): r.get(t("col_market_value"), "N/A").replace("$", "").replace(",", ""),
                    t("col_gain_loss_dollar"): r.get(t("col_gain_loss_dollar"), "N/A").replace("$", "").replace(",", "").replace("+", ""),
                    t("col_gain_loss_pct"): r.get(t("col_gain_loss_pct"), "N/A").replace("%", "").replace("+", ""),
                    t("col_sector"): _get_sector(h["ticker"], h),
                    t("col_dividend_yield_pct"): h.get("dividend_yield", 0),
                })
            export_df = pd.DataFrame(export_rows)
            csv_data = export_df.to_csv(index=False)
            st.download_button(
                t("download_csv"),
                data=csv_data,
                file_name=f"portfolio_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

        # ── Performance Chart (auto-loads) ────────────────────────────────
        st.markdown("---")
        st.markdown(f"### {t('portfolio_performance_over_time')}")
        pc1, pc2 = st.columns([3, 1])
        with pc1:
            period = st.selectbox(t("chart_period"), ["1mo", "3mo", "6mo", "1y"], index=0)
        with pc2:
            st.markdown("<br>", unsafe_allow_html=True)
            reload_perf = st.button(t("reload"), width='stretch')

        days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
        cache_key = f"perf_cache_{period}"

        if cache_key not in st.session_state or reload_perf:
            with st.spinner(t("loading_historical_data")):
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
                    name=t("total_portfolio"),
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

            # S&P 500 benchmark overlay (normalized to portfolio start value)
            try:
                sp500_hist = get_stock_history("^GSPC", period=period)
                if sp500_hist and total_values:
                    sorted_totals = sorted(total_values.items())
                    start_val = sorted_totals[0][1] if sorted_totals else total_cost
                    sp_start = sp500_hist[0]["close"] if sp500_hist else 1
                    sp_normalized = [(r["date"], r["close"] / sp_start * start_val) for r in sp500_hist]
                    fig.add_trace(go.Scatter(
                        x=[d for d, _ in sp_normalized],
                        y=[v for _, v in sp_normalized],
                        name=t("sp500_scaled"),
                        mode="lines",
                        line=dict(color="#94a3b8", width=2, dash="dash"),
                    ))
                    # Alpha calculation
                    sp_end = sp500_hist[-1]["close"] if sp500_hist else sp_start
                    sp_return = (sp_end - sp_start) / sp_start * 100
                    port_return = total_gain_pct
                    alpha = port_return - sp_return
                    st.caption(t("portfolio_return_summary").format(port_return=f"{port_return:+.2f}", sp_return=f"{sp_return:+.2f}", alpha=f"{alpha:+.2f}"))
            except Exception:
                pass

            apply_layout(fig, height=400, title=t("holdings_value_over_time"), yaxis_title=t("value_dollar"))
            st.plotly_chart(fig, width='stretch')
        elif st.session_state.get(cache_key):
            st.info(t("no_historical_data"))

    with tab_watchlist:
        st.markdown(f"### {t('watchlist_title')}")
        st.markdown(t("watchlist_subtitle"))

        with st.form("add_watchlist", clear_on_submit=True):
            wc1, wc2 = st.columns([2, 1])
            with wc1:
                w_ticker = st.text_input(t("ticker_symbol"), placeholder="NVDA, ETH...").upper().strip()
            with wc2:
                w_type = st.selectbox(t("type"), ["Stock", "Crypto"])
            if st.form_submit_button(t("add_to_watchlist"), width='stretch'):
                if w_ticker and not any(w["ticker"] == w_ticker for w in watchlist):
                    watchlist.append({"ticker": w_ticker, "type": w_type, "added": str(datetime.today().date())})
                    portfolio["watchlist"] = watchlist
                    _save(portfolio)
                    st.toast(t("toast_added_to_watchlist").format(ticker=w_ticker))
                    st.rerun()
                elif not w_ticker:
                    st.error(t("error_enter_ticker"))
                else:
                    st.warning(t("warning_already_in_watchlist").format(ticker=w_ticker))

        if not watchlist:
            from utils.ui_helpers import render_empty_state
            render_empty_state("", t("watchlist_empty"),
                               t("watchlist_empty_desc"))
        else:
            if st.button(t("fetch_watchlist_prices")):
                with st.spinner(t("fetching_prices")):
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
                    t("col_ticker"): w["ticker"],
                    t("col_type"): w["type"],
                    t("col_price"): format_currency(price) if price else "—",
                    t("col_24h_change"): f"{chg:+.2f}%" if chg is not None else "—",
                    t("col_added"): w.get("added", ""),
                })
            st.dataframe(pd.DataFrame(wl_rows), width='stretch', hide_index=True)

            remove_wl = st.selectbox(t("remove_from_watchlist"), ["— select —"] + [w["ticker"] for w in watchlist])
            if st.button(t("remove_from_watchlist_btn")) and remove_wl != "— select —":
                portfolio["watchlist"] = [w for w in watchlist if w["ticker"] != remove_wl]
                _save(portfolio)
                st.rerun()

    with tab_trades:
        st.markdown(f"### {t('trade_history_title')}")
        trade_history = portfolio.get("trade_history", [])
        if not trade_history:
            from utils.ui_helpers import render_empty_state
            render_empty_state("", t("no_trades_yet"),
                               t("no_trades_yet_desc"))
        else:
            # Summary
            total_realized = sum(t.get("gain_loss", 0) for t in trade_history)
            st_gains = sum(t.get("gain_loss", 0) for t in trade_history if t.get("term") == "Short-term" and t.get("gain_loss", 0) > 0)
            lt_gains = sum(t.get("gain_loss", 0) for t in trade_history if t.get("term") == "Long-term" and t.get("gain_loss", 0) > 0)
            st_losses = sum(t.get("gain_loss", 0) for t in trade_history if t.get("term") == "Short-term" and t.get("gain_loss", 0) < 0)
            lt_losses = sum(t.get("gain_loss", 0) for t in trade_history if t.get("term") == "Long-term" and t.get("gain_loss", 0) < 0)

            tm1, tm2, tm3 = st.columns(3)
            tm1.metric(t("total_realized_pnl"), format_currency(total_realized, show_sign=True))
            tm2.metric(t("short_term_pnl"), format_currency(st_gains + st_losses, show_sign=True))
            tm3.metric(t("long_term_pnl"), format_currency(lt_gains + lt_losses, show_sign=True))

            trade_df = pd.DataFrame(trade_history)
            display_cols = ["date", "ticker", "type", "quantity", "buy_price", "sell_price", "gain_loss", "term"]
            available_cols = [c for c in display_cols if c in trade_df.columns]
            st.dataframe(
                trade_df[available_cols].sort_values("date", ascending=False),
                width='stretch', hide_index=True,
                column_config={
                    "gain_loss": st.column_config.NumberColumn(t("col_gain_loss_dollar"), format="$%.2f"),
                    "buy_price": st.column_config.NumberColumn(t("col_buy_price"), format="$%.2f"),
                    "sell_price": st.column_config.NumberColumn(t("col_sell_price"), format="$%.2f"),
                },
            )

            if st.session_state.get("confirm_clear_trades"):
                if st.button(t("confirm_clear"), type="primary"):
                    portfolio["trade_history"] = []
                    _save(portfolio)
                    st.session_state.pop("confirm_clear_trades", None)
                    st.rerun()
            else:
                if st.button(t("clear_trade_history")):
                    st.session_state["confirm_clear_trades"] = True
                    st.rerun()

    with tab_alerts:
        st.markdown(f"### {t('price_alerts_title')}")
        # Load centralized SMTP settings for email alerts
        _smtp_settings = load_json("settings.json", default={}).get("email_smtp", {})

        with st.form("add_alert", clear_on_submit=True):
            all_tickers = list({h["ticker"] for h in holdings} | {w["ticker"] for w in watchlist})
            if not all_tickers:
                st.info(t("add_holdings_first_for_alerts"))
            else:
                ac1, ac2, ac3 = st.columns(3)
                with ac1:
                    alert_ticker = st.selectbox(t("col_ticker"), all_tickers)
                with ac2:
                    alert_direction = st.selectbox(t("direction"), [t("above"), t("below")])
                with ac3:
                    alert_price = st.number_input(t("target_price"), min_value=0.01, step=0.01, format="%.2f")

                if st.form_submit_button(t("set_alert"), width='stretch'):
                    alerts.append({
                        "ticker": alert_ticker,
                        "direction": alert_direction,
                        "target": alert_price,
                    })
                    portfolio["alerts"] = alerts
                    _save(portfolio)
                    st.toast(t("toast_alert_set").format(ticker=alert_ticker, direction=alert_direction.lower(), price=f"${alert_price:,.2f}"))
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
                        st.success(t("alert_triggered").format(ticker=a['ticker'], current=format_currency(current), direction=a['direction'].lower(), target=format_currency(a['target'])))
                        create_notification(
                            "alert", "portfolio",
                            f"{a['ticker']} crossed {a['direction'].lower()} {format_currency(a['target'])}",
                            f"{a['ticker']} crossed {a['direction'].lower()} {format_currency(a['target'])} (current: {format_currency(current)})",
                            action_module="portfolio_tracker",
                        )
                    else:
                        remaining.append(a)
                        st.write(t("alert_status_current").format(ticker=a['ticker'], direction=a['direction'].lower(), target=format_currency(a['target']), current=format_currency(current)))
                else:
                    remaining.append(a)
                    st.write(t("alert_status_no_price").format(ticker=a['ticker'], direction=a['direction'].lower(), target=format_currency(a['target'])))

            if triggered and st.button(t("clear_triggered_alerts")):
                portfolio["alerts"] = remaining
                _save(portfolio)
                st.rerun()

        with st.expander(t("email_alert_settings")):
            st.caption(t("email_alert_settings_desc"))
            smtp_host = st.text_input(t("smtp_server"), value=_smtp_settings.get("server", ""), placeholder="smtp.gmail.com")
            smtp_port = st.number_input(t("smtp_port"), value=int(_smtp_settings.get("port", 587)), step=1)
            smtp_user = st.text_input(t("email_address"), value=_smtp_settings.get("email", ""))
            smtp_pass = st.text_input(t("password_app_password"), type="password", value=_smtp_settings.get("password", ""))

            if st.button(t("send_test_email")):
                if not all([smtp_host, smtp_user, smtp_pass]):
                    st.error(t("error_fill_smtp_fields"))
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
                        st.toast(t("toast_test_email_sent"))
                    except Exception as e:
                        st.error(t("error_failed").format(error=e))
