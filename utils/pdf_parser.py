import re
import io

# Categories guessed from vendor keywords
CATEGORY_KEYWORDS = {
    "Groceries": ["walmart", "costco", "kroger", "safeway", "trader joe", "whole foods", "aldi", "grocery", "market"],
    "Dining": ["restaurant", "mcdonald", "starbucks", "chipotle", "pizza", "burger", "cafe", "diner", "grubhub", "doordash", "uber eats"],
    "Transport": ["uber", "lyft", "gas", "shell", "chevron", "bp", "exxon", "parking", "transit"],
    "Utilities": ["electric", "water", "gas bill", "internet", "comcast", "att", "verizon", "t-mobile"],
    "Shopping": ["amazon", "target", "best buy", "ebay", "etsy", "ikea", "nike", "adidas"],
    "Health": ["pharmacy", "cvs", "walgreens", "doctor", "hospital", "clinic", "dental"],
    "Entertainment": ["netflix", "spotify", "hulu", "disney", "hbo", "cinema", "movie", "theater"],
    "Subscription": ["subscription", "monthly", "annual", "membership"],
}


def guess_category(vendor: str) -> str:
    vendor_lower = vendor.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in vendor_lower:
                return category
    return "Other"


def _extract_date(text: str) -> str:
    patterns = [
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
        r"\b([A-Za-z]+ \d{1,2},? \d{4})\b",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return ""


def _extract_total(text: str) -> str:
    patterns = [
        r"(?:total|amount|grand total|balance due|amount due)[:\s]*\$?([\d,]+\.\d{2})",
        r"\$\s*([\d,]+\.\d{2})",
    ]
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        if matches:
            return matches[-1]
    return ""


def _extract_vendor(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        # First non-empty line is often the vendor/company name
        candidate = lines[0][:80]
        # Remove purely numeric lines
        if not re.match(r"^[\d\s.,$/-]+$", candidate):
            return candidate
        if len(lines) > 1:
            return lines[1][:80]
    return "Unknown"


def parse_pdf(file_bytes: bytes, filename: str) -> dict:
    """Extract receipt info from a PDF file. Returns a dict with date, vendor, total, category."""
    text = ""

    # Try pdfplumber first
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        pass

    # Fallback to PyPDF2
    if not text.strip():
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception:
            pass

    # Fallback to OCR
    if not text.strip():
        try:
            import pytesseract
            from PIL import Image
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(file_bytes)
            for img in images:
                text += pytesseract.image_to_string(img) + "\n"
        except ImportError:
            text = ""
        except Exception:
            text = ""

    if not text.strip():
        return {
            "filename": filename,
            "date": "",
            "vendor": "Could not extract text",
            "total": "",
            "category": "Unknown",
            "raw_text": "",
        }

    vendor = _extract_vendor(text)
    return {
        "filename": filename,
        "date": _extract_date(text),
        "vendor": vendor,
        "total": _extract_total(text),
        "category": guess_category(vendor),
        "raw_text": text[:2000],
    }
