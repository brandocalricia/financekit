import yfinance as yf
import requests


def get_stock_price(ticker: str) -> dict | None:
    """Fetch current stock data via yfinance."""
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.get("lastPrice") or info.get("last_price")
        if price is None:
            return None
        prev = info.get("previousClose") or info.get("previous_close") or price
        return {
            "ticker": ticker.upper(),
            "price": round(float(price), 2),
            "previous_close": round(float(prev), 2),
            "change_pct": round((float(price) - float(prev)) / float(prev) * 100, 2) if prev else 0,
        }
    except Exception:
        return None


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
        return records
    except Exception:
        return []


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
        resp.raise_for_status()
        data = resp.json().get(coin_id, {})
        price = data.get("usd")
        if price is None:
            return None
        return {
            "ticker": ticker.upper(),
            "price": round(float(price), 2),
            "change_pct": round(float(data.get("usd_24h_change", 0)), 2),
        }
    except Exception:
        return None


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
        resp.raise_for_status()
        prices = resp.json().get("prices", [])
        from datetime import datetime
        records = []
        for ts, price in prices:
            records.append({
                "date": datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d"),
                "close": round(float(price), 2),
            })
        return records
    except Exception:
        return []
