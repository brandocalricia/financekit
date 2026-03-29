"""Invoice PDF templates for FinanceKit — Minimal, Professional, Creative."""
import base64
import os
import tempfile
from datetime import datetime
from fpdf import FPDF
from utils.data_persistence import load_json
from utils.formatting import get_currency_symbol


def _sanitize(text: str) -> str:
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "-",
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    return text


def _load_logo_path(settings):
    """If logo base64 is stored in settings, write to temp file and return path."""
    logo_b64 = settings.get("invoice", {}).get("logo_base64", "")
    if not logo_b64:
        return None
    try:
        logo_data = base64.b64decode(logo_b64)
        tmp = os.path.join(tempfile.gettempdir(), "fk_logo.png")
        with open(tmp, "wb") as f:
            f.write(logo_data)
        return tmp
    except Exception:
        return None


def _get_invoice_settings(settings):
    inv = settings.get("invoice", {})
    return {
        "company_name": inv.get("company_name", settings.get("user_name", "")),
        "company_address": inv.get("company_address", ""),
        "company_email": inv.get("company_email", settings.get("user_email", "")),
        "company_phone": inv.get("company_phone", ""),
        "payment_details": inv.get("payment_details", ""),
        "footer_text": inv.get("footer_text", "Thank you for your business!"),
        "tax_rate": inv.get("tax_rate", 0),
        "default_template": inv.get("default_template", "Professional"),
    }


def generate_invoice_number(invoices):
    """Generate auto-incrementing invoice number: INV-YYYY-XXXX."""
    year = datetime.now().strftime("%Y")
    existing = [inv.get("number", "") for inv in invoices if inv.get("number", "").startswith(f"INV-{year}-")]
    if existing:
        nums = []
        for n in existing:
            try:
                nums.append(int(n.split("-")[-1]))
            except ValueError:
                pass
        next_num = max(nums) + 1 if nums else 1
    else:
        next_num = 1
    return f"INV-{year}-{next_num:04d}"


def _calc_totals(line_items, tax_rate=0, discount=0):
    subtotal = sum(item.get("quantity", 0) * item.get("rate", 0) for item in line_items)
    tax_amount = subtotal * (tax_rate / 100) if tax_rate else 0
    total = subtotal + tax_amount - discount
    return subtotal, tax_amount, total


# ═══════════════════════════════════════════════════════════════════════
#  Template: Minimal
# ═══════════════════════════════════════════════════════════════════════

class MinimalInvoice(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def render_minimal(invoice, settings):
    sym = get_currency_symbol()
    inv_settings = _get_invoice_settings(settings)
    logo_path = _load_logo_path(settings)

    pdf = MinimalInvoice()
    pdf.add_page()

    # Logo
    if logo_path and os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=10, w=30)
        pdf.set_y(45)
    else:
        pdf.set_y(15)

    # INVOICE title
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 14, "INVOICE", align="R", new_x="LMARGIN", new_y="NEXT")

    # Invoice number and dates
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"#{invoice.get('number', invoice.get('id', '').upper())}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Date: {invoice.get('date', '')}", align="R", new_x="LMARGIN", new_y="NEXT")
    if invoice.get("due_date"):
        pdf.cell(0, 6, f"Due: {invoice['due_date']}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # From / To
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(140, 140, 140)
    pdf.cell(95, 5, "FROM", new_x="RIGHT")
    pdf.cell(95, 5, "BILL TO", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(95, 7, _sanitize(inv_settings["company_name"] or "Your Name"), new_x="RIGHT")
    client = invoice.get("client_info", {})
    client_name = client.get("name", invoice.get("client", ""))
    pdf.cell(95, 7, _sanitize(client_name), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    if inv_settings["company_address"]:
        pdf.cell(95, 5, _sanitize(inv_settings["company_address"]), new_x="RIGHT")
    else:
        pdf.cell(95, 5, "", new_x="RIGHT")
    if client.get("address"):
        pdf.cell(95, 5, _sanitize(client["address"]), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(95, 5, "", new_x="LMARGIN", new_y="NEXT")

    if inv_settings["company_email"]:
        pdf.cell(95, 5, inv_settings["company_email"], new_x="RIGHT")
    else:
        pdf.cell(95, 5, "", new_x="RIGHT")
    if client.get("email"):
        pdf.cell(95, 5, client["email"], new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(95, 5, "", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(12)

    # Line — thin separator
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(85, 7, "DESCRIPTION", border=0)
    pdf.cell(25, 7, "QTY", border=0, align="C")
    pdf.cell(35, 7, "RATE", border=0, align="R")
    pdf.cell(35, 7, "AMOUNT", border=0, align="R")
    pdf.ln()

    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    # Line items
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    for item in invoice.get("line_items", []):
        desc = str(item.get("description", ""))[:50]
        qty = item.get("quantity", 0)
        rate = item.get("rate", 0)
        amount = qty * rate
        pdf.cell(85, 8, _sanitize(desc), border=0)
        pdf.cell(25, 8, f"{qty:.1f}", border=0, align="C")
        pdf.cell(35, 8, f"{sym}{rate:,.2f}", border=0, align="R")
        pdf.cell(35, 8, f"{sym}{amount:,.2f}", border=0, align="R")
        pdf.ln()

    pdf.ln(4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Totals
    tax_rate = invoice.get("tax_rate", inv_settings.get("tax_rate", 0))
    discount = invoice.get("discount", 0)
    subtotal, tax_amount, total = _calc_totals(invoice.get("line_items", []), tax_rate, discount)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(145, 7, "Subtotal", align="R")
    pdf.cell(35, 7, f"{sym}{subtotal:,.2f}", align="R")
    pdf.ln()

    if tax_rate > 0:
        pdf.cell(145, 7, f"Tax ({tax_rate}%)", align="R")
        pdf.cell(35, 7, f"{sym}{tax_amount:,.2f}", align="R")
        pdf.ln()

    if discount > 0:
        pdf.cell(145, 7, "Discount", align="R")
        pdf.cell(35, 7, f"-{sym}{discount:,.2f}", align="R")
        pdf.ln()

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(145, 10, "Total", align="R")
    pdf.cell(35, 10, f"{sym}{total:,.2f}", align="R")
    pdf.ln(15)

    # Payment terms
    if invoice.get("payment_terms"):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 6, f"Payment Terms: {invoice['payment_terms']}", new_x="LMARGIN", new_y="NEXT")

    # Payment details
    if inv_settings["payment_details"]:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 6, f"Payment: {_sanitize(inv_settings['payment_details'])}", new_x="LMARGIN", new_y="NEXT")

    # Notes
    if invoice.get("notes"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(140, 140, 140)
        pdf.multi_cell(0, 5, _sanitize(f"Notes: {invoice['notes']}"))

    # Footer text
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 8, _sanitize(inv_settings["footer_text"]), align="C")

    return bytes(pdf.output())


# ═══════════════════════════════════════════════════════════════════════
#  Template: Professional
# ═══════════════════════════════════════════════════════════════════════

class ProfessionalInvoice(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        # Indigo header bar
        self.set_fill_color(99, 102, 241)
        self.rect(0, 0, self.w, 12, "F")
        self.set_fill_color(167, 139, 250)
        self.rect(self.w * 0.7, 0, self.w * 0.3, 12, "F")
        self.set_y(4)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, "FinanceKit", align="L")

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"Page {self.page_no()}  |  Generated by FinanceKit", align="C")


def render_professional(invoice, settings):
    sym = get_currency_symbol()
    inv_settings = _get_invoice_settings(settings)
    logo_path = _load_logo_path(settings)

    pdf = ProfessionalInvoice()
    pdf.add_page()
    pdf.set_y(18)

    # Logo + INVOICE header
    if logo_path and os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=16, w=30)
        pdf.set_y(16)

    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 15, "INVOICE", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    inv_num = invoice.get("number", invoice.get("id", "").upper())
    pdf.cell(0, 6, f"Invoice #{inv_num}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Date: {invoice.get('date', '')}", align="R", new_x="LMARGIN", new_y="NEXT")
    if invoice.get("due_date"):
        pdf.cell(0, 6, f"Due: {invoice['due_date']}", align="R", new_x="LMARGIN", new_y="NEXT")
    status_text = "PAID" if invoice.get("paid") else "UNPAID"
    pdf.cell(0, 6, f"Status: {status_text}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # From / To
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(50, 50, 80)
    pdf.cell(95, 7, "From:", new_x="RIGHT")
    pdf.cell(95, 7, "Bill To:", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(95, 6, _sanitize(inv_settings["company_name"] or "Your Name"), new_x="RIGHT")
    client = invoice.get("client_info", {})
    client_name = client.get("name", invoice.get("client", ""))
    pdf.cell(95, 6, _sanitize(client_name), new_x="LMARGIN", new_y="NEXT")

    if inv_settings["company_address"]:
        pdf.cell(95, 5, _sanitize(inv_settings["company_address"]), new_x="RIGHT")
    else:
        pdf.cell(95, 5, "", new_x="RIGHT")
    if client.get("address"):
        pdf.cell(95, 5, _sanitize(client["address"]), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(95, 5, "", new_x="LMARGIN", new_y="NEXT")

    if inv_settings["company_email"]:
        pdf.cell(95, 5, inv_settings["company_email"], new_x="RIGHT")
    else:
        pdf.cell(95, 5, "", new_x="RIGHT")
    if client.get("email"):
        pdf.cell(95, 5, client["email"], new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(95, 5, "", new_x="LMARGIN", new_y="NEXT")

    if inv_settings["company_phone"]:
        pdf.cell(95, 5, inv_settings["company_phone"])
    pdf.ln(12)

    # Line items table header
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(99, 102, 241)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(80, 8, "Description", border=1, fill=True, align="C")
    pdf.cell(30, 8, "Qty / Hours", border=1, fill=True, align="C")
    pdf.cell(35, 8, "Rate", border=1, fill=True, align="C")
    pdf.cell(35, 8, "Amount", border=1, fill=True, align="C")
    pdf.ln()

    # Line items
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    for item in invoice.get("line_items", []):
        desc = str(item.get("description", ""))[:45]
        qty = item.get("quantity", 0)
        rate = item.get("rate", 0)
        amount = qty * rate
        pdf.cell(80, 7, _sanitize(desc), border=1)
        pdf.cell(30, 7, f"{qty:.1f}", border=1, align="C")
        pdf.cell(35, 7, f"{sym}{rate:,.2f}", border=1, align="R")
        pdf.cell(35, 7, f"{sym}{amount:,.2f}", border=1, align="R")
        pdf.ln()

    pdf.ln(4)

    # Totals
    tax_rate = invoice.get("tax_rate", inv_settings.get("tax_rate", 0))
    discount = invoice.get("discount", 0)
    subtotal, tax_amount, total = _calc_totals(invoice.get("line_items", []), tax_rate, discount)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(145, 7, "Subtotal:", align="R")
    pdf.cell(35, 7, f"{sym}{subtotal:,.2f}", align="R")
    pdf.ln()

    if tax_rate > 0:
        pdf.cell(145, 7, f"Tax ({tax_rate}%):", align="R")
        pdf.cell(35, 7, f"{sym}{tax_amount:,.2f}", align="R")
        pdf.ln()

    if discount > 0:
        pdf.cell(145, 7, "Discount:", align="R")
        pdf.cell(35, 7, f"-{sym}{discount:,.2f}", align="R")
        pdf.ln()

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(50, 50, 80)
    pdf.cell(145, 10, "Total:", align="R")
    pdf.cell(35, 10, f"{sym}{total:,.2f}", align="R")
    pdf.ln(12)

    # Payment terms
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(80, 80, 80)
    terms = invoice.get("payment_terms", "Net 30")
    pdf.cell(0, 7, f"Payment Terms: {terms}", new_x="LMARGIN", new_y="NEXT")

    if inv_settings["payment_details"]:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, _sanitize(f"Payment: {inv_settings['payment_details']}"), new_x="LMARGIN", new_y="NEXT")

    # Notes
    if invoice.get("notes"):
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, _sanitize(f"Notes: {invoice['notes']}"), new_x="LMARGIN", new_y="NEXT")

    # Footer
    pdf.ln(12)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, _sanitize(inv_settings["footer_text"]), align="C")

    return bytes(pdf.output())


# ═══════════════════════════════════════════════════════════════════════
#  Template: Creative
# ═══════════════════════════════════════════════════════════════════════

class CreativeInvoice(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(99, 102, 241)
        self.rect(0, self.h - 15, self.w, 15, "F")
        self.cell(0, 8, f"Page {self.page_no()}  |  FinanceKit", align="C")


def render_creative(invoice, settings):
    sym = get_currency_symbol()
    inv_settings = _get_invoice_settings(settings)
    logo_path = _load_logo_path(settings)

    pdf = CreativeInvoice()
    pdf.add_page()

    # Large color block header
    pdf.set_fill_color(99, 102, 241)
    pdf.rect(0, 0, 80, 50, "F")
    pdf.set_fill_color(167, 139, 250)
    pdf.rect(80, 0, pdf.w - 80, 50, "F")

    # Logo in header block
    if logo_path and os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=25)

    # Invoice title in header
    pdf.set_y(10)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 18, "INVOICE", align="R", new_x="LMARGIN", new_y="NEXT")

    # Invoice number large
    inv_num = invoice.get("number", invoice.get("id", "").upper())
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 8, f"#{inv_num}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(55)

    # Date info — right side
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Date: {invoice.get('date', '')}   |   Due: {invoice.get('due_date', 'N/A')}   |   {'PAID' if invoice.get('paid') else 'UNPAID'}",
             align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # From / To blocks with colored accents
    pdf.set_fill_color(245, 243, 255)
    y_start = pdf.get_y()
    pdf.rect(10, y_start, 90, 30, "F")
    pdf.rect(110, y_start, 90, 30, "F")

    # Left accent
    pdf.set_fill_color(99, 102, 241)
    pdf.rect(10, y_start, 3, 30, "F")
    pdf.rect(110, y_start, 3, 30, "F")

    pdf.set_xy(15, y_start + 3)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(80, 5, "FROM")
    pdf.set_x(115)
    pdf.cell(80, 5, "BILL TO")

    pdf.set_xy(15, y_start + 9)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(80, 6, _sanitize(inv_settings["company_name"] or "Your Name"))
    pdf.set_x(115)
    client = invoice.get("client_info", {})
    client_name = client.get("name", invoice.get("client", ""))
    pdf.cell(80, 6, _sanitize(client_name))

    pdf.set_xy(15, y_start + 16)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(80, 5, _sanitize(inv_settings["company_email"]))
    pdf.set_x(115)
    pdf.cell(80, 5, _sanitize(client.get("email", "")))

    pdf.set_xy(15, y_start + 22)
    pdf.cell(80, 5, _sanitize(inv_settings["company_phone"]))
    pdf.set_x(115)
    pdf.cell(80, 5, _sanitize(client.get("address", "")))

    pdf.set_y(y_start + 38)

    # Line items
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(99, 102, 241)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(80, 8, "  DESCRIPTION", border=0, fill=True)
    pdf.cell(25, 8, "QTY", border=0, fill=True, align="C")
    pdf.cell(35, 8, "RATE", border=0, fill=True, align="C")
    pdf.cell(40, 8, "AMOUNT", border=0, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    for i, item in enumerate(invoice.get("line_items", [])):
        if i % 2 == 0:
            pdf.set_fill_color(250, 249, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
        desc = str(item.get("description", ""))[:45]
        qty = item.get("quantity", 0)
        rate = item.get("rate", 0)
        amount = qty * rate
        pdf.cell(80, 8, f"  {_sanitize(desc)}", border=0, fill=True)
        pdf.cell(25, 8, f"{qty:.1f}", border=0, fill=True, align="C")
        pdf.cell(35, 8, f"{sym}{rate:,.2f}", border=0, fill=True, align="R")
        pdf.cell(40, 8, f"{sym}{amount:,.2f}", border=0, fill=True, align="R")
        pdf.ln()

    pdf.ln(6)

    # Totals with accent
    tax_rate = invoice.get("tax_rate", inv_settings.get("tax_rate", 0))
    discount = invoice.get("discount", 0)
    subtotal, tax_amount, total = _calc_totals(invoice.get("line_items", []), tax_rate, discount)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(140, 7, "Subtotal", align="R")
    pdf.cell(40, 7, f"{sym}{subtotal:,.2f}", align="R")
    pdf.ln()

    if tax_rate > 0:
        pdf.cell(140, 7, f"Tax ({tax_rate}%)", align="R")
        pdf.cell(40, 7, f"{sym}{tax_amount:,.2f}", align="R")
        pdf.ln()

    if discount > 0:
        pdf.cell(140, 7, "Discount", align="R")
        pdf.cell(40, 7, f"-{sym}{discount:,.2f}", align="R")
        pdf.ln()

    # Total with background
    pdf.ln(2)
    y_total = pdf.get_y()
    pdf.set_fill_color(99, 102, 241)
    pdf.rect(120, y_total, 80, 12, "F")
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(140, 12, "TOTAL", align="R")
    pdf.cell(40, 12, f"{sym}{total:,.2f}", align="R")
    pdf.ln(18)

    # Payment + Notes
    pdf.set_text_color(80, 80, 80)
    pdf.set_font("Helvetica", "B", 10)
    if invoice.get("payment_terms"):
        pdf.cell(0, 6, f"Payment Terms: {invoice['payment_terms']}", new_x="LMARGIN", new_y="NEXT")
    if inv_settings["payment_details"]:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, _sanitize(f"Payment: {inv_settings['payment_details']}"), new_x="LMARGIN", new_y="NEXT")
    if invoice.get("notes"):
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(0, 5, _sanitize(f"Notes: {invoice['notes']}"))

    # Footer text
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, _sanitize(inv_settings["footer_text"]), align="C")

    return bytes(pdf.output())


# ═══════════════════════════════════════════════════════════════════════
#  Template Router
# ═══════════════════════════════════════════════════════════════════════

TEMPLATES = {
    "Minimal": render_minimal,
    "Professional": render_professional,
    "Creative": render_creative,
}


def render_invoice_pdf(invoice, settings, template_name=None):
    """Generate invoice PDF using specified template (or default from settings)."""
    if template_name is None:
        template_name = _get_invoice_settings(settings).get("default_template", "Professional")
    renderer = TEMPLATES.get(template_name, render_professional)
    return renderer(invoice, settings)
