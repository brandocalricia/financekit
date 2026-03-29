# FinanceKit

**Your all-in-one personal finance toolkit** — 7 powerful modules, zero subscriptions, runs 100% locally.

**$29.99 one-time purchase** → [Get FinanceKit on Gumroad](https://5207453582610.gumroad.com/l/zbnsjc)

**Try the free demo** → [Live Demo on Streamlit Cloud](https://financekit-demo-financekit.streamlit.app/)

---

## Why FinanceKit?

- **One-time purchase** — $29.99 and it's yours forever. No monthly fees, no subscriptions.
- **Runs locally** — Your financial data never leaves your computer. Zero cloud, zero tracking.
- **Privacy-first** — No accounts, no data collection, no telemetry. You own your data.
- **7 modules in one** — Replaces YNAB ($14.99/mo), QuickBooks ($15/mo), Mint alternatives ($9.99/mo), and more.
- **Built with Python** — Transparent, hackable, and extensible if you want to customize it.

---

## Modules

### 💰 Budget Tracker
Set monthly budgets across 11 categories (Housing, Food, Dining, Transportation, etc.). Import bank CSVs to auto-categorize transactions and see spending vs. budget with color-coded progress bars, donut charts, and month-over-month comparisons. Includes pre-made templates for Students, Freelancers, Families, and Single Professionals.

### 🎯 Savings Goal Tracker
Set savings goals with deadlines and monthly contributions. Track progress with visual bars, projection dates ("At your current rate, you'll reach this by..."), and milestone celebrations. Each goal keeps a history chart of your savings over time.

### 🧾 Receipt & Invoice Scanner
Upload PDFs, JPGs, or PNGs — or snap a photo with your phone's camera. OCR extracts vendor, date, total, and auto-categorizes by vendor name. Edit any field, then export to Excel or CSV.

### 📈 Stock & Crypto Portfolio Tracker
Track stocks (via Yahoo Finance) and crypto (via CoinGecko) with live prices. See portfolio allocation pie charts, top gainer/loser, and performance over time. Includes a watchlist for tickers you don't own yet, and price alerts with optional email notifications.

### 📊 Financial Report Generator
Upload transactions from any bank (auto-detects Chase, Bank of America, Wells Fargo, Capital One, Amex). Get summary stats, monthly spending charts, category breakdowns, and an income vs. expenses line chart. Generate a professional PDF report and email it directly.

### 💼 Freelance Dashboard
Track clients, log projects, and set rates. Generate clean invoice PDFs with line items, quantities, and rates. Mark invoices as Paid/Unpaid and monitor outstanding balance. See monthly income charts and client profitability breakdowns.

### 🔄 Subscription & Recurring Expense Auditor
Upload bank statements to auto-detect recurring charges using fuzzy matching. See each subscription's monthly, annual, and 5-year projected cost. Toggle Keep/Cancel per subscription to plan your savings. Includes a known subscription database with direct cancellation links for 20+ services, an annual renewal calendar, and duplicate charge detection.

---

## Quick Start (Windows)

```
1. Make sure Python 3.10+ is installed (check "Add Python to PATH" during install)
2. Double-click start.bat
3. The app opens in your browser at http://localhost:8501
```

## Quick Start (Mac / Linux)

```bash
chmod +x start.sh
./start.sh
```

## Manual Setup

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

### Optional: OCR Support

For scanning image-based (scanned) PDF receipts and photos, install Tesseract OCR:

- **Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki
- **macOS:** `brew install tesseract`
- **Linux:** `sudo apt install tesseract-ocr`

The app works fine without Tesseract — it will just skip OCR for image-only files.

---

## File Structure

```
FinanceKit/
├── app.py                  # Main Streamlit app (dashboard + routing)
├── start.bat               # One-click launcher (Windows)
├── start.sh                # One-click launcher (Mac/Linux)
├── modules/                # All 7 module files
│   ├── budget_tracker.py
│   ├── goal_tracker.py
│   ├── receipt_scanner.py
│   ├── portfolio_tracker.py
│   ├── report_generator.py
│   ├── job_tracker.py      # Freelance Dashboard
│   └── subscription_auditor.py
├── utils/                  # Shared utilities
│   ├── data_persistence.py
│   ├── finance_api.py
│   ├── fuzzy_matcher.py
│   ├── pdf_parser.py
│   └── report_builder.py
├── data/                   # Local JSON storage (auto-created)
├── demo/                   # Free demo version (for Streamlit Cloud)
├── .streamlit/config.toml  # Theme configuration
├── requirements.txt
└── README.md
```

---

## License

FinanceKit is proprietary software. The demo version source code is available for review. Full version available at [Gumroad](https://5207453582610.gumroad.com/l/zbnsjc).
