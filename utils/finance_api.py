import yfinance as yf
import requests
import streamlit as st
from utils.logger import get_logger

log = get_logger("finance_api")


# ── Stock functions (yfinance) ─────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)  # 5 minutes
def get_stock_price(ticker: str) -> dict | None:
    """Fetch current stock data via yfinance."""
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.get("lastPrice") or info.get("last_price")
        if price is None:
            log.warning(f"No price data for stock {ticker}")
            return None
        prev = info.get("previousClose") or info.get("previous_close") or price
        result = {
            "ticker": ticker.upper(),
            "price": round(float(price), 2),
            "previous_close": round(float(prev), 2),
            "change_pct": round((float(price) - float(prev)) / float(prev) * 100, 2) if prev else 0,
        }
        log.info(f"Stock price fetched: {ticker} = ${result['price']}")
        return result
    except requests.exceptions.ConnectionError:
        log.error(f"Connection error fetching stock {ticker}")
        return None
    except requests.exceptions.Timeout:
        log.error(f"Timeout fetching stock {ticker}")
        return None
    except Exception as e:
        log.error(f"Error fetching stock {ticker}: {e}")
        return None


@st.cache_data(ttl=3600, show_spinner=False)  # 1 hour
def get_stock_history(ticker: str, period: str = "1mo") -> list[dict]:
    """Fetch historical stock prices."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        if hist.empty:
            return []
        records = []
        for date, row in hist.iterrows():
            records.append({"date": str(date.date()), "close": round(float(row["Close"]), 2)})
        log.info(f"Stock history fetched: {ticker} ({period}), {len(records)} points")
        return records
    except requests.exceptions.ConnectionError:
        log.error(f"Connection error fetching stock history {ticker}")
        return []
    except Exception as e:
        log.error(f"Error fetching stock history {ticker}: {e}")
        return []


# ── Crypto functions (CoinGecko) ───────────────────────────────────────

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Common crypto ticker -> CoinGecko ID mapping
CRYPTO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "DOT": "polkadot",
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "LINK": "chainlink",
    "LTC": "litecoin",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "SHIB": "shiba-inu",
    "BNB": "binancecoin",
}


@st.cache_data(ttl=120, show_spinner=False)  # 2 minutes
def get_crypto_price(ticker: str) -> dict | None:
    """Fetch current crypto price from CoinGecko."""
    coin_id = CRYPTO_IDS.get(ticker.upper())
    if not coin_id:
        return None
    try:
        resp = requests.get(
            f"{COINGECKO_BASE}/simple/price",
            params={"ids": coin_id, "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10,
        )
        if resp.status_code == 429:
            log.warning(f"Rate limited by CoinGecko for {ticker}")
            return None
        resp.raise_for_status()
        data = resp.json().get(coin_id, {})
        price = data.get("usd")
        if price is None:
            return None
        result = {
            "ticker": ticker.upper(),
            "price": round(float(price), 2),
            "change_pct": round(float(data.get("usd_24h_change", 0)), 2),
        }
        log.info(f"Crypto price fetched: {ticker} = ${result['price']}")
        return result
    except requests.exceptions.ConnectionError:
        log.error(f"Connection error fetching crypto {ticker}")
        return None
    except requests.exceptions.Timeout:
        log.error(f"Timeout fetching crypto {ticker}")
        return None
    except requests.exceptions.HTTPError as e:
        log.error(f"HTTP error fetching crypto {ticker}: {e}")
        return None
    except Exception as e:
        log.error(f"Error fetching crypto {ticker}: {e}")
        return None


@st.cache_data(ttl=3600, show_spinner=False)  # 1 hour
def get_crypto_history(ticker: str, days: int = 30) -> list[dict]:
    """Fetch historical crypto prices from CoinGecko."""
    coin_id = CRYPTO_IDS.get(ticker.upper())
    if not coin_id:
        return []
    try:
        resp = requests.get(
            f"{COINGECKO_BASE}/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": days},
            timeout=10,
        )
        if resp.status_code == 429:
            log.warning(f"Rate limited by CoinGecko for {ticker} history")
            return []
        resp.raise_for_status()
        prices = resp.json().get("prices", [])
        from datetime import datetime
        records = []
        for ts, price in prices:
            records.append({
                "date": datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d"),
                "close": round(float(price), 2),
            })
        log.info(f"Crypto history fetched: {ticker} ({days}d), {len(records)} points")
        return records
    except requests.exceptions.ConnectionError:
        log.error(f"Connection error fetching crypto history {ticker}")
        return []
    except Exception as e:
        log.error(f"Error fetching crypto history {ticker}: {e}")
        return []
