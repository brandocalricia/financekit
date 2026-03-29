# FinanceKit — User Guide

Welcome to FinanceKit! This guide walks you through every module step by step.

---

## Getting Started

1. **Double-click `start.bat`** (Windows) or run `./start.sh` (Mac/Linux)
2. The app opens automatically in your browser at `http://localhost:8501`
3. Use the **sidebar on the left** to switch between modules
4. Click the **FinanceKit** logo at the top-left to return to the Home page anytime

---

## Module 1: Receipt & Invoice Scanner

**What it does:** Extracts data from PDF receipts so you don't have to type it manually.

### Steps:
1. Navigate to **Receipt Scanner** in the sidebar
2. Click **Browse files** (or drag and drop) to upload one or more PDF files
3. Click the **Scan Receipts** button
4. The app extracts: date, vendor name, total amount, and auto-guesses a category
5. **Review the table** — click any cell to edit it if the extraction wasn't perfect
6. Use the **Category** dropdown in each row to recategorize
7. Expand **"View raw extracted text"** to see exactly what text was pulled from each PDF
8. Click **Download CSV** or **Download Excel** to export

### Tips:
- Works best with text-based PDFs (digitally generated receipts)
- Scanned/image PDFs need Tesseract OCR installed (see README)
- You can upload multiple receipts at once and export them all in one spreadsheet

### Test it:
- Upload the files in `sample_data/receipt_walmart.pdf` and `sample_data/receipt_starbucks.pdf`

---

## Module 2: Stock & Crypto Portfolio Tracker

**What it does:** Tracks your investment holdings with live prices, gain/loss, charts, and price alerts.

### Steps:
1. Navigate to **Portfolio Tracker** in the sidebar
2. **Add a holding:**
   - Enter a ticker symbol (e.g., `AAPL` for Apple, `BTC` for Bitcoin)
   - Select type: **Stock** or **Crypto**
   - Enter your **purchase price** and **quantity**
   - Click **Add to Portfolio**
3. The dashboard shows:
   - Current price (fetched live)
   - Market value of each holding
   - Gain/loss in dollars and percentage
   - Total portfolio value at the top
4. Click **Refresh Prices** to fetch updated prices
5. **Charts:** Select a time period (1mo, 3mo, 6mo, 1y) and click **Load Chart** to see performance over time
6. **Price Alerts:**
   - Pick a ticker, choose Above or Below, set a target price
   - Click **Set Alert**
   - Alerts are checked every time you refresh — triggered alerts show in green or red
7. **Email Alerts (optional):** Expand the settings section at the bottom to configure SMTP email notifications

### Supported crypto tickers:
BTC, ETH, SOL, ADA, DOT, DOGE, XRP, AVAX, MATIC, LINK, LTC, UNI, ATOM, SHIB, BNB

### Tips:
- Portfolio data saves automatically to `data/portfolio.json` — it persists between sessions
- Use the **Remove** dropdown to delete a holding
- Stock data comes from Yahoo Finance, crypto from CoinGecko (both free, no API key needed)

### Test it:
- Add `AAPL` (Stock) at $150, qty 10
- Add `BTC` (Crypto) at $30000, qty 0.5
- Click Refresh Prices and Load Chart

---

## Module 3: Financial Report Generator

**What it does:** Turns a spreadsheet of transactions into a polished PDF report with charts.

### Steps:
1. Navigate to **Report Generator** in the sidebar
2. Upload a CSV or Excel file containing your transactions
3. **Map your columns:**
   - The app tries to auto-detect Date, Description, Amount, and Category columns
   - If it guesses wrong, use the dropdowns to select the correct columns
   - Category is optional — if your file doesn't have one, leave it as "none"
4. Optionally enter **your name** (appears on the PDF title page)
5. The app immediately shows:
   - **Summary stats:** total income, total expenses, net, average transaction
   - **Top spending categories** ranked by amount
6. **Charts displayed in-app:**
   - Monthly spending bar chart
   - Category breakdown pie chart
   - Income vs expenses line chart over time
7. Click **Generate PDF Report** to create a downloadable PDF containing all of the above
8. Click **Download PDF** to save it
9. Click **Download Cleaned Excel** to get the processed transaction data as a spreadsheet

### How income vs expenses are detected:
- **Positive amounts** = income (deposits, payments received)
- **Negative amounts** = expenses (purchases, bills)

### Test it:
- Upload `sample_data/transactions.csv`
- All columns should auto-map correctly
- Generate the PDF report

---

## Module 4: Job Application Tracker

**What it does:** Keeps all your job applications organized with status tracking and follow-up reminders.

### Steps:
1. Navigate to **Job Tracker** in the sidebar
2. **Stats bar** at the top shows: total applications, response rate, interviews, and offers
3. **Pipeline chart** shows how many applications are at each status stage
4. **Add a new application:**
   - Fill in: Company, Position, Date Applied, Status, Job Link, Notes
   - Click **Add Application**
5. **Filter and sort:**
   - Filter by status (e.g., show only "Interview" and "Offer")
   - Sort by date, company name, or status
6. **Each application expands** to show full details:
   - Update the status using the dropdown (e.g., move from "Applied" to "Interview")
   - Edit notes
   - Click **Save** to update
   - Click **Delete** to remove
7. **Follow-up reminders:** Applications stuck in "Applied" for 7+ days show a clock icon and a yellow warning
8. Click **Download All Applications (CSV)** to export everything

### Status options:
Applied → Phone Screen → Interview → Offer → Rejected → Withdrawn

### Tips:
- Data saves automatically to `data/job_applications.json`
- The pipeline chart updates in real time as you change statuses
- Use the Notes field to track interviewer names, next steps, or salary info

### Test it:
- Add 3-4 sample applications with different statuses
- Try changing a status and watch the pipeline chart update
- Set one application date to a week ago and see the follow-up reminder appear

---

## Module 5: Subscription & Recurring Expense Auditor

**What it does:** Scans your bank statement to find recurring charges and shows how much you'd save by cancelling some.

### Steps:
1. Navigate to **Subscription Auditor** in the sidebar
2. Upload a CSV bank or credit card statement
3. **Map your columns:**
   - Select which columns are Date, Description, and Amount
   - The app tries to auto-detect these
4. The app analyzes your transactions:
   - Groups similar descriptions using fuzzy matching
   - Identifies charges that repeat monthly or quarterly
   - Filters out one-time purchases
5. **Results show:**
   - Number of recurring subscriptions found
   - Total monthly and annual cost
   - A table with: name, monthly amount, annual cost, frequency, occurrences, first/last seen
6. **Potential duplicates:** The app flags subscriptions with very similar names (e.g., two streaming charges you might have forgotten about)
7. **What-If Savings Calculator:**
   - Check the subscriptions you'd cancel from the dropdown
   - See your projected monthly and annual savings instantly
8. **Export:** Download results as CSV or Excel

### Adjusting sensitivity:
- The **Fuzzy match sensitivity** slider controls how aggressively transactions are grouped
- Lower = more aggressive (groups things that are somewhat similar)
- Higher = stricter (only groups near-exact matches)
- Default of 75 works well for most statements

### Test it:
- Upload `sample_data/bank_statement.csv`
- Columns should auto-map (Date, Description, Amount)
- You should see Netflix, Spotify, Amazon Prime, AT&T, Gym, Adobe, Comcast, and Hulu detected
- Try the What-If calculator — select a few subscriptions to "cancel"

---

## Tips for All Modules

- **Data stays on your computer** — nothing is uploaded to the cloud
- **Refresh the page** (F5) if anything looks stuck
- **To stop the app**, close the terminal window or press `Ctrl+C`
- **To restart**, double-click `start.bat` again
- Your portfolio and job application data persist between sessions automatically
