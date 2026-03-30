# FinanceKit

**Your all-in-one personal finance toolkit -- 7 powerful modules, zero subscriptions, runs 100% locally.**

![Version](https://img.shields.io/badge/version-3.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)

**$29.99 one-time purchase** -- [Get FinanceKit on Gumroad](https://5207453582610.gumroad.com/l/zbnsjc)

**Try the free demo** -- [Live Demo on Streamlit Cloud](https://financekit-demo-financekit.streamlit.app/)

**Source** -- [GitHub](https://github.com/brandocalricia/financekit)

---

## What's New in v3.0

- **5-Step Onboarding Flow** -- New users are guided through a streamlined setup wizard covering profile creation, module selection, theme preferences, and initial configuration so they can get productive immediately.
- **Module Selection** -- Choose which modules appear in your sidebar. Disable modules you do not use for a cleaner, focused interface.
- **Activity Feed** -- A real-time activity log on the dashboard shows recent actions across all modules, making it easy to pick up where you left off.
- **Print Support** -- Generate printer-friendly views of budgets, goals, portfolios, and reports directly from the app.
- **Accessibility Improvements** -- Improved keyboard navigation, ARIA labels, high-contrast support, and screen reader compatibility throughout the interface.
- **Code Quality Sweep** -- Comprehensive refactoring across the entire codebase: standardized formatting, centralized chart configuration, improved data validation, expanded test coverage, and cleaner utility separation.

---

## Feature Overview

### Budget Tracker

Set monthly budgets across 11 categories (Housing, Food, Dining, Transportation, Healthcare, Entertainment, Shopping, Education, Personal, Savings, and Other). Import bank CSV files to auto-categorize transactions and visualize spending versus budget with color-coded progress bars, donut charts, and month-over-month comparisons. Includes pre-built templates for Students, Freelancers, Families, and Single Professionals. Detailed spending analytics surface trends and highlight categories where you are over or under budget.

### Goal Tracker

Define savings goals with target amounts, deadlines, and monthly contribution schedules. Track progress with visual bars and milestone markers. The projection engine estimates your completion date based on current contribution rate. Each goal maintains a full history chart so you can review your savings trajectory over time.

### Receipt Scanner

Upload PDFs, JPGs, or PNGs -- or capture a photo directly with your device camera. OCR (powered by Tesseract) extracts vendor name, date, and total amount automatically. Transactions are auto-categorized by vendor name using fuzzy matching. Edit any extracted field manually, then export the full receipt log to Excel or CSV.

### Portfolio Tracker

Track stocks via Yahoo Finance and cryptocurrencies via CoinGecko with live price data. View portfolio allocation pie charts, top gainers and losers, and performance over time. Maintain a watchlist for tickers you do not yet own. Set price alerts with optional email notifications so you never miss a significant move.

### Report Generator

Upload transaction exports from any major bank -- the parser auto-detects formats from Chase, Bank of America, Wells Fargo, Capital One, and American Express. Generate summary statistics, monthly spending charts, category breakdowns, and income-versus-expenses line charts. Export a professional PDF report or email it directly from the app.

### Freelance Dashboard

Manage clients, log projects, and define hourly or flat rates. Generate polished invoice PDFs using one of three built-in templates, complete with line items, quantities, rates, and payment terms. Support for recurring invoices on a configurable schedule. Mark invoices as Paid or Unpaid and monitor outstanding balances. View monthly income charts, client profitability breakdowns, and a full profit-and-loss summary.

### Subscription Auditor

Upload bank statements to auto-detect recurring charges using fuzzy matching against a known subscription database of 20+ services. View each subscription's monthly, annual, and 5-year projected cost. Toggle Keep or Cancel per subscription to plan your savings. Includes direct cancellation links, usage ratings, category-level analysis, an annual renewal calendar, and duplicate charge detection.

---

## Additional Features

- **Authentication** -- Local account system with hashed passwords (bcrypt). Optional OAuth integration for streamlined login.
- **Notifications** -- Configurable alerts for budget thresholds, goal milestones, price movements, invoice due dates, and subscription renewals.
- **Financial Health Score** -- An at-a-glance composite score based on your budget adherence, savings rate, debt ratio, and investment diversification.
- **Net Worth Tracker** -- Aggregate your assets and liabilities into a single dashboard view with historical trend charts.
- **Dark and Light Theme** -- Toggle between dark and light modes from the sidebar. Preference is saved across sessions.
- **Keyboard Shortcuts** -- Navigate modules, trigger actions, and switch views without reaching for the mouse.
- **Data Backups** -- Export and import your full dataset as JSON. Schedule automatic backups to ensure you never lose data.

---

## Screenshots

| Dashboard | Budget Tracker | Portfolio Tracker |
|-----------|---------------|-------------------|
| ![Dashboard](assets/screenshots/dashboard.png) | ![Budget](assets/screenshots/budget.png) | ![Portfolio](assets/screenshots/portfolio.png) |

| Report Generator | Freelance Dashboard | Subscription Auditor |
|-------------------|---------------------|----------------------|
| ![Reports](assets/screenshots/reports.png) | ![Freelance](assets/screenshots/freelance.png) | ![Subscriptions](assets/screenshots/subscriptions.png) |

---

## Quick Start

### Windows

```
1. Make sure Python 3.10+ is installed (check "Add Python to PATH" during install).
2. Double-click start.bat
3. The app opens in your browser at http://localhost:8501
```

### Mac

```bash
chmod +x start.sh
./start.sh
```

### Linux

```bash
chmod +x start.sh
./start.sh
```

### Manual Setup

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

### Optional: OCR Support

For scanning image-based (scanned) PDF receipts and photos, install Tesseract OCR:

- **Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki
- **macOS:** `brew install tesseract`
- **Linux:** `sudo apt install tesseract-ocr`

The app works without Tesseract installed. It will skip OCR for image-only files and still handle text-based PDFs normally.

---

## Authentication Setup

FinanceKit includes a local authentication system. On first launch, you will be prompted to create an admin account. Passwords are hashed with bcrypt and stored locally.

To enable OAuth (optional):

1. Create a `.streamlit/secrets.toml` file in the project root.
2. Add your OAuth provider credentials:
   ```toml
   [auth]
   provider = "google"
   client_id = "YOUR_CLIENT_ID"
   client_secret = "YOUR_CLIENT_SECRET"
   redirect_uri = "http://localhost:8501"
   ```
3. Restart the app. The login screen will display the OAuth option alongside local login.

---

## Requirements

Python 3.10 or higher is required. All dependencies are installed automatically by the launcher scripts or via `pip install -r requirements.txt`.

| Package | Version |
|---------|---------|
| streamlit | 1.45.0 |
| pandas | 2.2.3 |
| plotly | 6.0.1 |
| pdfplumber | 0.11.6 |
| PyPDF2 | 3.0.1 |
| pytesseract | 0.3.13 |
| Pillow | 11.1.0 |
| openpyxl | 3.1.5 |
| yfinance | 0.2.54 |
| requests | 2.32.3 |
| rapidfuzz | 3.12.2 |
| fpdf2 | 2.8.3 |
| xlsxwriter | 3.2.2 |
| kaleido | 0.2.1 |
| bcrypt | 4.2.1 |

---

## File Structure

```
FinanceKit/
├── app.py                          # Main Streamlit app (dashboard + routing)
├── start.bat                       # One-click launcher (Windows)
├── start.sh                        # One-click launcher (Mac/Linux)
├── version.txt                     # Current version number
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Test configuration
├── README.md                       # This file
├── GUIDE.md                        # User guide
├── GUMROAD_GUIDE.md                # Gumroad listing guide
├── CHANGELOG.md                    # Version history
├── generate_guide_pdf.py           # Script to build PDF user guide
│
├── modules/                        # All 7 module files
│   ├── __init__.py
│   ├── budget_tracker.py
│   ├── goal_tracker.py
│   ├── receipt_scanner.py
│   ├── portfolio_tracker.py
│   ├── report_generator.py
│   ├── job_tracker.py              # Freelance Dashboard
│   ├── subscription_auditor.py
│   └── settings.py                 # User preferences and configuration
│
├── utils/                          # Shared utilities
│   ├── __init__.py
│   ├── activity_log.py             # Activity feed logging
│   ├── auth.py                     # Authentication (local + OAuth)
│   ├── chart_config.py             # Centralized Plotly chart settings
│   ├── data_persistence.py         # JSON read/write helpers
│   ├── finance_api.py              # Yahoo Finance and CoinGecko wrappers
│   ├── formatting.py               # Number and currency formatting
│   ├── fuzzy_matcher.py            # Subscription and vendor matching
│   ├── insights.py                 # Financial health score and analytics
│   ├── invoice_templates.py        # Invoice PDF templates
│   ├── logger.py                   # Application logging
│   ├── migrations.py               # Data schema migrations
│   ├── notifications.py            # Alert and notification system
│   ├── pdf_parser.py               # Bank statement PDF parsing
│   ├── report_builder.py           # PDF report generation
│   ├── search.py                   # Global search across modules
│   ├── ui_helpers.py               # Reusable Streamlit UI components
│   └── validators.py               # Input validation functions
│
├── tests/                          # Test suite
│   ├── conftest.py                 # Shared fixtures
│   └── test_*.py                   # Unit and integration tests
│
├── demo/                           # Free demo version
│   └── app_demo.py                 # Demo app for Streamlit Cloud
│
├── data/                           # Local JSON storage (auto-created at runtime)
│
├── assets/                         # Gumroad HTML assets
│
└── .streamlit/
    └── config.toml                 # Streamlit theme configuration
```

---

## FAQ

**Q: Do I need an internet connection to use FinanceKit?**
A: No. FinanceKit runs entirely on your local machine. The only features that require internet access are the Portfolio Tracker (for live stock and crypto prices) and email-based report delivery.

**Q: Where is my data stored?**
A: All data is stored as JSON files in the `data/` directory inside the project folder. Nothing is sent to external servers.

**Q: Can I use FinanceKit on multiple computers?**
A: Yes. Copy the entire FinanceKit folder (including the `data/` directory) to another machine. As long as Python 3.10+ is installed, it will work identically.

**Q: What banks are supported by the Report Generator?**
A: The parser auto-detects CSV exports from Chase, Bank of America, Wells Fargo, Capital One, and American Express. Other bank formats can be used if they follow a standard CSV structure with date, description, and amount columns.

**Q: Is Tesseract required?**
A: No. Tesseract is only needed for OCR on image-based receipts and scanned PDFs. Text-based PDFs and all other features work without it.

**Q: How do I update to a new version?**
A: Download the latest release from Gumroad, then copy your `data/` folder from the old installation into the new one. The migration system will handle any schema changes automatically on first launch.

**Q: Can I customize the modules shown in the sidebar?**
A: Yes. Use the module selection feature (introduced in v3.0) from the settings page to enable or disable individual modules.

---

## License

FinanceKit is proprietary software. The demo version source code is available for review. Full version available at [Gumroad](https://5207453582610.gumroad.com/l/zbnsjc).
