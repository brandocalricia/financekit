"""Import ecosystem — parsers for YNAB, Mint, Monarch, and OFX/QFX formats."""
import pandas as pd
import io
from datetime import datetime
from rapidfuzz import fuzz


# ── Category mapping ────────────────────────────────────────────────────

FINANCEKIT_CATEGORIES = [
    "Housing", "Food & Groceries", "Dining Out", "Transportation",
    "Entertainment", "Subscriptions", "Shopping", "Health",
    "Savings", "Utilities", "Income", "Other",
]


def fuzzy_map_category(source_category, threshold=65):
    """Map an external category name to the closest FinanceKit category."""
    if not source_category or not source_category.strip():
        return "Other", 0
    source = source_category.strip().lower()

    # Direct mapping overrides
    DIRECT_MAP = {
        "groceries": "Food & Groceries",
        "grocery": "Food & Groceries",
        "food": "Food & Groceries",
        "restaurants": "Dining Out",
        "restaurant": "Dining Out",
        "food & drink": "Dining Out",
        "dining": "Dining Out",
        "rent": "Housing",
        "mortgage": "Housing",
        "home": "Housing",
        "auto": "Transportation",
        "gas": "Transportation",
        "car": "Transportation",
        "transit": "Transportation",
        "travel": "Transportation",
        "fun": "Entertainment",
        "movies": "Entertainment",
        "music": "Entertainment",
        "streaming": "Subscriptions",
        "subscription": "Subscriptions",
        "clothes": "Shopping",
        "clothing": "Shopping",
        "doctor": "Health",
        "medical": "Health",
        "pharmacy": "Health",
        "healthcare": "Health",
        "electric": "Utilities",
        "internet": "Utilities",
        "phone": "Utilities",
        "water": "Utilities",
        "income": "Income",
        "paycheck": "Income",
        "salary": "Income",
        "wages": "Income",
        "transfer": "Savings",
        "savings": "Savings",
        "investment": "Savings",
    }

    if source in DIRECT_MAP:
        return DIRECT_MAP[source], 100

    best_match = "Other"
    best_score = 0
    for fk_cat in FINANCEKIT_CATEGORIES:
        score = fuzz.token_sort_ratio(source, fk_cat.lower())
        if score > best_score:
            best_score = score
            best_match = fk_cat

    if best_score >= threshold:
        return best_match, best_score
    return "Other", best_score


def map_categories_bulk(source_categories):
    """Map a list of source categories, return dict of source -> (fk_category, score)."""
    unique = set(source_categories)
    return {cat: fuzzy_map_category(cat) for cat in unique}


# ── Format detection ────────────────────────────────────────────────────

def detect_format(df):
    """Detect the import format from a DataFrame's columns."""
    cols_lower = set(c.lower().strip() for c in df.columns)

    # YNAB
    ynab_cols = {"date", "payee", "memo", "outflow", "inflow"}
    if len(ynab_cols & cols_lower) >= 4:
        return "YNAB"

    # Mint
    mint_cols = {"date", "description", "original description", "amount", "transaction type", "category"}
    if len(mint_cols & cols_lower) >= 4:
        return "Mint"

    # Monarch
    monarch_cols = {"date", "merchant", "category", "amount", "account"}
    if len(monarch_cols & cols_lower) >= 4:
        return "Monarch"

    # Known banks (Chase, BofA, etc.) — handled by report_generator's existing detection
    return "CSV"


def detect_file_type(filename):
    """Detect file type from extension."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext in ("ofx", "qfx"):
        return "OFX"
    if ext in ("xlsx", "xls"):
        return "Excel"
    if ext == "csv":
        return "CSV"
    return "Unknown"


# ── YNAB Importer ───────────────────────────────────────────────────────

class YNABImporter:
    """Parse YNAB CSV export format."""

    @staticmethod
    def can_parse(df):
        cols = set(c.lower().strip() for c in df.columns)
        return len({"date", "payee", "outflow", "inflow"} & cols) >= 3

    @staticmethod
    def parse(df):
        col_map = {c.lower().strip(): c for c in df.columns}
        result = pd.DataFrame()

        date_col = col_map.get("date", "")
        result["date"] = pd.to_datetime(df[date_col], errors="coerce") if date_col else pd.NaT

        payee_col = col_map.get("payee", "")
        memo_col = col_map.get("memo", "")
        if payee_col:
            result["description"] = df[payee_col].astype(str)
            if memo_col:
                memo = df[memo_col].fillna("").astype(str)
                result["description"] = result["description"] + " " + memo
        else:
            result["description"] = ""

        # YNAB uses separate Outflow/Inflow columns
        outflow_col = col_map.get("outflow", "")
        inflow_col = col_map.get("inflow", "")
        outflow = pd.to_numeric(
            df[outflow_col].astype(str).str.replace(r"[,$]", "", regex=True),
            errors="coerce"
        ).fillna(0) if outflow_col else 0
        inflow = pd.to_numeric(
            df[inflow_col].astype(str).str.replace(r"[,$]", "", regex=True),
            errors="coerce"
        ).fillna(0) if inflow_col else 0
        result["amount"] = inflow - outflow

        # Category mapping
        cat_col = col_map.get("category group/category", col_map.get("category", ""))
        if cat_col and cat_col in df.columns:
            mappings = map_categories_bulk(df[cat_col].fillna("Other").astype(str))
            result["category"] = df[cat_col].astype(str).map(lambda x: mappings.get(x, ("Other", 0))[0])
        else:
            result["category"] = "Other"

        result = result.dropna(subset=["date"])
        result["description"] = result["description"].str.strip()
        return result

    @staticmethod
    def get_budgets(df):
        """Extract budget amounts from YNAB data if present."""
        col_map = {c.lower().strip(): c for c in df.columns}
        budget_col = col_map.get("budgeted", "")
        cat_col = col_map.get("category group/category", col_map.get("category", ""))
        if not budget_col or not cat_col:
            return {}
        budgets = {}
        for _, row in df.iterrows():
            cat = str(row.get(cat_col, "Other"))
            mapped, _ = fuzzy_map_category(cat)
            amt = pd.to_numeric(
                str(row.get(budget_col, 0)).replace(",", "").replace("$", ""),
                errors="coerce"
            )
            if pd.notna(amt) and amt > 0:
                budgets[mapped] = budgets.get(mapped, 0) + amt
        return budgets


# ── Mint Importer ───────────────────────────────────────────────────────

class MintImporter:
    """Parse Mint CSV export format."""

    @staticmethod
    def can_parse(df):
        cols = set(c.lower().strip() for c in df.columns)
        return len({"date", "description", "amount", "transaction type", "category"} & cols) >= 4

    @staticmethod
    def parse(df):
        col_map = {c.lower().strip(): c for c in df.columns}
        result = pd.DataFrame()

        date_col = col_map.get("date", "")
        result["date"] = pd.to_datetime(df[date_col], errors="coerce") if date_col else pd.NaT

        desc_col = col_map.get("description", col_map.get("original description", ""))
        result["description"] = df[desc_col].astype(str) if desc_col else ""

        amount_col = col_map.get("amount", "")
        type_col = col_map.get("transaction type", "")
        if amount_col:
            amount = pd.to_numeric(
                df[amount_col].astype(str).str.replace(r"[,$]", "", regex=True),
                errors="coerce"
            ).fillna(0)
            # Mint: debits are positive, credits are negative — flip for our convention
            if type_col and type_col in df.columns:
                is_debit = df[type_col].astype(str).str.lower() == "debit"
                amount = amount.where(~is_debit, -amount)
            result["amount"] = amount
        else:
            result["amount"] = 0

        cat_col = col_map.get("category", "")
        if cat_col and cat_col in df.columns:
            mappings = map_categories_bulk(df[cat_col].fillna("Other").astype(str))
            result["category"] = df[cat_col].astype(str).map(lambda x: mappings.get(x, ("Other", 0))[0])
        else:
            result["category"] = "Other"

        result = result.dropna(subset=["date"])
        return result


# ── Monarch Importer ────────────────────────────────────────────────────

class MonarchImporter:
    """Parse Monarch Money CSV export format."""

    @staticmethod
    def can_parse(df):
        cols = set(c.lower().strip() for c in df.columns)
        return len({"date", "merchant", "category", "amount"} & cols) >= 3

    @staticmethod
    def parse(df):
        col_map = {c.lower().strip(): c for c in df.columns}
        result = pd.DataFrame()

        date_col = col_map.get("date", "")
        result["date"] = pd.to_datetime(df[date_col], errors="coerce") if date_col else pd.NaT

        desc_col = col_map.get("merchant", col_map.get("description", ""))
        result["description"] = df[desc_col].astype(str) if desc_col else ""

        amount_col = col_map.get("amount", "")
        if amount_col:
            result["amount"] = pd.to_numeric(
                df[amount_col].astype(str).str.replace(r"[,$]", "", regex=True),
                errors="coerce"
            ).fillna(0)
        else:
            result["amount"] = 0

        cat_col = col_map.get("category", "")
        if cat_col and cat_col in df.columns:
            mappings = map_categories_bulk(df[cat_col].fillna("Other").astype(str))
            result["category"] = df[cat_col].astype(str).map(lambda x: mappings.get(x, ("Other", 0))[0])
        else:
            result["category"] = "Other"

        result = result.dropna(subset=["date"])
        return result


# ── OFX/QFX Importer ───────────────────────────────────────────────────

class OFXImporter:
    """Parse OFX/QFX bank file format."""

    @staticmethod
    def can_parse(filename):
        return filename.lower().endswith((".ofx", ".qfx"))

    @staticmethod
    def parse(file_content):
        try:
            from ofxparse import OfxParser
        except ImportError:
            raise ImportError("ofxparse is required for OFX/QFX import. Install with: pip install ofxparse")

        if isinstance(file_content, str):
            file_content = file_content.encode("utf-8")
        ofx = OfxParser.parse(io.BytesIO(file_content))

        rows = []
        if ofx.account and ofx.account.statement:
            for txn in ofx.account.statement.transactions:
                rows.append({
                    "date": txn.date,
                    "description": txn.payee or txn.memo or "",
                    "amount": float(txn.amount),
                    "category": "Other",
                })

        if not rows:
            return pd.DataFrame(columns=["date", "description", "amount", "category"])

        result = pd.DataFrame(rows)
        result["date"] = pd.to_datetime(result["date"], errors="coerce")
        return result


# ── Unified import interface ────────────────────────────────────────────

IMPORTERS = {
    "YNAB": YNABImporter,
    "Mint": MintImporter,
    "Monarch": MonarchImporter,
}


def auto_import(df=None, file_content=None, filename=""):
    """Auto-detect format and parse. Returns (format_name, parsed_df)."""
    # OFX/QFX
    if filename and OFXImporter.can_parse(filename):
        return "OFX", OFXImporter.parse(file_content)

    # CSV/Excel
    if df is not None:
        fmt = detect_format(df)
        if fmt in IMPORTERS:
            return fmt, IMPORTERS[fmt].parse(df)
        return fmt, None

    return "Unknown", None
