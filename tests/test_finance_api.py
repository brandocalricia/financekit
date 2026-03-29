"""Tests for finance API with mocked responses."""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear Streamlit cache before each test."""
    try:
        from utils.finance_api import get_stock_price, get_crypto_price, get_stock_history, get_crypto_history
        get_stock_price.clear()
        get_crypto_price.clear()
        get_stock_history.clear()
        get_crypto_history.clear()
    except Exception:
        pass
    yield


def test_stock_price_success():
    mock_info = MagicMock()
    mock_info.get = lambda key, default=None: {
        "lastPrice": 175.50, "previousClose": 173.00
    }.get(key, default)

    with patch("utils.finance_api.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.fast_info = mock_info
        from utils.finance_api import get_stock_price
        result = get_stock_price("AAPL")

    assert result is not None
    assert result["ticker"] == "AAPL"
    assert result["price"] == 175.50
    assert result["previous_close"] == 173.00
    assert "change_pct" in result


def test_stock_price_failure():
    with patch("utils.finance_api.yf.Ticker") as mock_ticker:
        mock_ticker.side_effect = Exception("Network error")
        from utils.finance_api import get_stock_price
        result = get_stock_price("INVALID")

    assert result is None


def test_crypto_price_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "bitcoin": {"usd": 65000.50, "usd_24h_change": 2.5}
    }
    mock_response.raise_for_status = MagicMock()

    with patch("utils.finance_api.requests.get", return_value=mock_response):
        from utils.finance_api import get_crypto_price
        result = get_crypto_price("BTC")

    assert result is not None
    assert result["ticker"] == "BTC"
    assert result["price"] == 65000.50
    assert result["change_pct"] == 2.5


def test_crypto_unknown_ticker():
    from utils.finance_api import get_crypto_price
    result = get_crypto_price("UNKNOWN_COIN")
    assert result is None


def test_rate_limit_handling():
    mock_response = MagicMock()
    mock_response.status_code = 429

    with patch("utils.finance_api.requests.get", return_value=mock_response):
        from utils.finance_api import get_crypto_price
        result = get_crypto_price("ETH")

    assert result is None


def test_history_data_format():
    mock_ticker = MagicMock()
    import pandas as pd
    hist_data = pd.DataFrame({
        "Close": [150.0, 152.5, 148.0],
    }, index=pd.to_datetime(["2026-03-01", "2026-03-02", "2026-03-03"]))
    mock_ticker.return_value.history.return_value = hist_data

    with patch("utils.finance_api.yf.Ticker", mock_ticker):
        from utils.finance_api import get_stock_history
        result = get_stock_history("AAPL", period="5d")

    assert len(result) == 3
    assert "date" in result[0]
    assert "close" in result[0]
    assert result[0]["close"] == 150.0
