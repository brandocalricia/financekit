"""Tests for utils/invoice_templates.py"""
import pytest
from unittest.mock import patch

from utils.invoice_templates import (
    render_minimal,
    render_professional,
    render_creative,
    _calc_totals,
)


SAMPLE_SETTINGS = {
    "user_name": "Test User",
    "user_email": "test@example.com",
    "currency": {"code": "USD", "symbol": "$"},
    "invoice": {
        "company_name": "Acme LLC",
        "company_address": "123 Main St",
        "company_email": "billing@acme.com",
        "company_phone": "555-1234",
        "payment_details": "Bank transfer",
        "footer_text": "Thanks for your business!",
        "tax_rate": 0,
        "default_template": "Professional",
    },
}

SAMPLE_INVOICE = {
    "number": "INV-2026-0001",
    "date": "2026-03-01",
    "due_date": "2026-03-31",
    "client": "Widget Co",
    "client_info": {
        "name": "Widget Co",
        "address": "456 Oak Ave",
        "email": "pay@widget.co",
    },
    "line_items": [
        {"description": "Consulting", "quantity": 10, "rate": 100.0},
        {"description": "Development", "quantity": 5, "rate": 200.0},
    ],
    "tax_rate": 0,
    "discount": 0,
    "paid": False,
    "payment_terms": "Net 30",
    "notes": "Thank you",
}


@patch("utils.invoice_templates.get_currency_symbol", return_value="$")
def test_minimal_template_generates(mock_sym):
    result = render_minimal(SAMPLE_INVOICE, SAMPLE_SETTINGS)
    assert isinstance(result, bytes)
    assert len(result) > 100
    assert result[:5] == b"%PDF-"


@patch("utils.invoice_templates.get_currency_symbol", return_value="$")
def test_professional_template_generates(mock_sym):
    result = render_professional(SAMPLE_INVOICE, SAMPLE_SETTINGS)
    assert isinstance(result, bytes)
    assert len(result) > 100
    assert result[:5] == b"%PDF-"


@patch("utils.invoice_templates.get_currency_symbol", return_value="$")
def test_creative_template_generates(mock_sym):
    result = render_creative(SAMPLE_INVOICE, SAMPLE_SETTINGS)
    assert isinstance(result, bytes)
    assert len(result) > 100
    assert result[:5] == b"%PDF-"


def test_template_with_tax_and_discount():
    line_items = [
        {"description": "Item A", "quantity": 4, "rate": 50.0},
        {"description": "Item B", "quantity": 2, "rate": 75.0},
    ]
    # subtotal = 4*50 + 2*75 = 350
    tax_rate = 10  # 10% -> 35
    discount = 20

    subtotal, tax_amount, total = _calc_totals(line_items, tax_rate, discount)

    assert subtotal == pytest.approx(350.0)
    assert tax_amount == pytest.approx(35.0)
    assert total == pytest.approx(365.0)  # 350 + 35 - 20


@patch("utils.invoice_templates.get_currency_symbol", return_value="$")
def test_template_unicode_safe(mock_sym):
    invoice = {
        **SAMPLE_INVOICE,
        "client": "Rene Descartes",
        "client_info": {
            "name": "Rene Descartes",
            "address": "14 Rue Descartes, Paris",
            "email": "rene@example.com",
        },
        "line_items": [
            {"description": "Analyse strategique", "quantity": 1, "rate": 500.0},
        ],
        "notes": "Merci beaucoup - paiement sous 30 jours",
    }
    # Should not raise on accented / special characters
    result = render_minimal(invoice, SAMPLE_SETTINGS)
    assert isinstance(result, bytes)
    assert result[:5] == b"%PDF-"
