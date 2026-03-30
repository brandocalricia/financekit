"""Tests for import ecosystem — YNAB, Mint, Monarch parsers and category mapping."""
import pandas as pd
import pytest
from utils.importers import (
    fuzzy_map_category, map_categories_bulk, detect_format,
    detect_file_type, YNABImporter, MintImporter, MonarchImporter,
    auto_import,
)


# ── Category mapping tests ──────────────────────────────────────────────

def test_fuzzy_map_direct():
    cat, score = fuzzy_map_category("groceries")
    assert cat == "Food & Groceries"
    assert score == 100


def test_fuzzy_map_fuzzy():
    cat, score = fuzzy_map_category("Food & Drink")
    # Should map to either Dining Out or Food & Groceries
    assert cat in ("Dining Out", "Food & Groceries")


def test_fuzzy_map_unknown():
    cat, score = fuzzy_map_category("xyzzy quantum stuff")
    assert cat == "Other"


def test_fuzzy_map_empty():
    cat, score = fuzzy_map_category("")
    assert cat == "Other"


def test_map_bulk():
    result = map_categories_bulk(["groceries", "rent", "unknown thing"])
    assert result["groceries"][0] == "Food & Groceries"
    assert result["rent"][0] == "Housing"


# ── Format detection tests ──────────────────────────────────────────────

def test_detect_ynab_format():
    df = pd.DataFrame(columns=["Date", "Payee", "Category", "Memo", "Outflow", "Inflow"])
    assert detect_format(df) == "YNAB"


def test_detect_mint_format():
    df = pd.DataFrame(columns=["Date", "Description", "Original Description", "Amount",
                                "Transaction Type", "Category", "Account Name"])
    assert detect_format(df) == "Mint"


def test_detect_monarch_format():
    df = pd.DataFrame(columns=["Date", "Merchant", "Category", "Amount", "Account"])
    assert detect_format(df) == "Monarch"


def test_detect_csv_fallback():
    df = pd.DataFrame(columns=["col_a", "col_b", "col_c"])
    assert detect_format(df) == "CSV"


def test_detect_file_type():
    assert detect_file_type("statement.ofx") == "OFX"
    assert detect_file_type("export.qfx") == "OFX"
    assert detect_file_type("data.csv") == "CSV"
    assert detect_file_type("report.xlsx") == "Excel"


# ── YNAB importer tests ────────────────────────────────────────────────

def test_ynab_parse():
    df = pd.DataFrame({
        "Date": ["2024-01-15", "2024-01-16"],
        "Payee": ["Starbucks", "Payroll"],
        "Memo": ["Coffee", "Salary"],
        "Outflow": ["5.50", "0"],
        "Inflow": ["0", "3000.00"],
        "Category": ["Dining", "Income"],
    })
    assert YNABImporter.can_parse(df)
    result = YNABImporter.parse(df)
    assert len(result) == 2
    assert result.iloc[0]["amount"] == -5.50
    assert result.iloc[1]["amount"] == 3000.00


def test_ynab_cannot_parse():
    df = pd.DataFrame(columns=["col_a", "col_b"])
    assert not YNABImporter.can_parse(df)


# ── Mint importer tests ────────────────────────────────────────────────

def test_mint_parse():
    df = pd.DataFrame({
        "Date": ["01/15/2024", "01/16/2024"],
        "Description": ["WALMART", "PAYCHECK"],
        "Original Description": ["WALMART SUPERCENTER", "ADP PAYROLL"],
        "Amount": ["45.99", "2500.00"],
        "Transaction Type": ["debit", "credit"],
        "Category": ["Shopping", "Income"],
        "Account Name": ["Chase Checking", "Chase Checking"],
    })
    assert MintImporter.can_parse(df)
    result = MintImporter.parse(df)
    assert len(result) == 2


# ── Monarch importer tests ─────────────────────────────────────────────

def test_monarch_parse():
    df = pd.DataFrame({
        "Date": ["2024-01-15"],
        "Merchant": ["Amazon"],
        "Category": ["Shopping"],
        "Amount": ["-29.99"],
        "Account": ["Checking"],
    })
    assert MonarchImporter.can_parse(df)
    result = MonarchImporter.parse(df)
    assert len(result) == 1
    assert result.iloc[0]["description"] == "Amazon"


# ── Auto-import tests ──────────────────────────────────────────────────

def test_auto_import_ynab():
    df = pd.DataFrame({
        "Date": ["2024-01-15"],
        "Payee": ["Test Store"],
        "Memo": [""],
        "Outflow": ["10.00"],
        "Inflow": ["0"],
    })
    fmt, result = auto_import(df=df, filename="ynab_export.csv")
    assert fmt == "YNAB"
    assert result is not None
    assert len(result) == 1


def test_auto_import_unknown():
    df = pd.DataFrame({"a": [1], "b": [2]})
    fmt, result = auto_import(df=df, filename="random.csv")
    assert fmt == "CSV"
    assert result is None
