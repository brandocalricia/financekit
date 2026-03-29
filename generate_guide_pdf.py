from fpdf import FPDF

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=20)


def section_header(text):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(50, 50, 80)
    pdf.cell(0, 14, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_text_color(0, 0, 0)


def sub_header(text):
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(70, 70, 110)
    pdf.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def body(text):
    pdf.set_font("Helvetica", "", 10.5)
    pdf.multi_cell(0, 6, text)
    pdf.ln(2)


def bullet(text):
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, f"  -  {text}")


def numbered(num, text):
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, f"  {num}. {text}")


# Title page
pdf.add_page()
pdf.set_font("Helvetica", "B", 36)
pdf.ln(50)
pdf.cell(0, 18, "FinanceKit", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 18)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 12, "User Guide", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(10)
pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 8, "Version 1.0", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Your all-in-one personal finance toolkit", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_text_color(0, 0, 0)

# Getting Started
section_header("Getting Started")
numbered(1, "Double-click start.bat (Windows) or run ./start.sh (Mac/Linux)")
numbered(2, "The app opens automatically in your browser at http://localhost:8501")
numbered(3, "Use the sidebar on the left to switch between modules")
numbered(4, "Click the FinanceKit logo at the top-left to return Home anytime")

# Module 1
section_header("Module 1: Receipt & Invoice Scanner")
body("Extracts data from PDF receipts so you don't have to type it manually.")
sub_header("How to Use")
numbered(1, "Navigate to Receipt Scanner in the sidebar")
numbered(2, "Click Browse files or drag and drop to upload one or more PDF files")
numbered(3, "Click the Scan Receipts button")
numbered(4, "The app extracts: date, vendor name, total amount, and auto-guesses a category")
numbered(5, "Review the table and click any cell to edit if the extraction wasn't perfect")
numbered(6, "Use the Category dropdown in each row to recategorize")
numbered(7, 'Expand "View raw extracted text" to see the raw text from each PDF')
numbered(8, "Click Download CSV or Download Excel to export")
sub_header("Tips")
bullet("Works best with text-based PDFs (digitally generated receipts)")
bullet("Scanned/image PDFs need Tesseract OCR installed (see README)")
bullet("You can upload multiple receipts at once and export them all in one spreadsheet")
sub_header("Test It")
bullet("Upload sample_data/receipt_walmart.pdf and sample_data/receipt_starbucks.pdf")

# Module 2
section_header("Module 2: Stock & Crypto Portfolio Tracker")
body("Tracks your investment holdings with live prices, gain/loss, charts, and price alerts.")
sub_header("How to Use")
numbered(1, "Navigate to Portfolio Tracker in the sidebar")
numbered(2, "Add a holding: enter a ticker symbol (e.g. AAPL for Apple, BTC for Bitcoin)")
numbered(3, "Select Stock or Crypto, enter your purchase price and quantity")
numbered(4, "Click Add to Portfolio")
numbered(5, "The dashboard shows: current price, market value, gain/loss per holding, total portfolio value")
numbered(6, "Click Refresh Prices to fetch updated prices anytime")
numbered(7, "Select a time period (1mo, 3mo, 6mo, 1y) and click Load Chart for performance history")
numbered(8, "Set Price Alerts: pick a ticker, choose Above or Below, set a target price")
numbered(9, "Optional: configure email alerts in the settings section at the bottom")
sub_header("Supported Crypto Tickers")
body("BTC, ETH, SOL, ADA, DOT, DOGE, XRP, AVAX, MATIC, LINK, LTC, UNI, ATOM, SHIB, BNB")
sub_header("Tips")
bullet("Portfolio saves automatically and persists between sessions")
bullet("Stock data from Yahoo Finance, crypto from CoinGecko (both free, no API key needed)")
bullet("Use the Remove dropdown to delete a holding")
sub_header("Test It")
bullet("Add AAPL (Stock) at $150, qty 10")
bullet("Add BTC (Crypto) at $30,000, qty 0.5")
bullet("Click Refresh Prices and Load Chart")

# Module 3
section_header("Module 3: Financial Report Generator")
body("Turns a spreadsheet of transactions into a polished PDF report with charts and summary statistics.")
sub_header("How to Use")
numbered(1, "Navigate to Report Generator in the sidebar")
numbered(2, "Upload a CSV or Excel file containing your transactions")
numbered(3, "Map your columns using the dropdowns: Date, Description, Amount, and optionally Category")
numbered(4, "Optionally enter your name (appears on the PDF title page)")
numbered(5, "Review the summary stats: total income, total expenses, net, average transaction")
numbered(6, "View the charts: monthly spending, category breakdown, income vs expenses over time")
numbered(7, "Click Generate PDF Report to create the report, then Download PDF to save it")
numbered(8, "Click Download Cleaned Excel for the processed transaction data as a spreadsheet")
sub_header("How Income vs Expenses Are Detected")
bullet("Positive amounts = income (deposits, payments received)")
bullet("Negative amounts = expenses (purchases, bills)")
sub_header("Test It")
bullet("Upload sample_data/transactions.csv - all columns should auto-map correctly")

# Module 4
section_header("Module 4: Job Application Tracker")
body("Keeps all your job applications organized with status tracking and follow-up reminders.")
sub_header("How to Use")
numbered(1, "Navigate to Job Tracker in the sidebar")
numbered(2, "View the stats bar: total applications, response rate, interviews, offers")
numbered(3, "View the pipeline chart showing how many applications are at each stage")
numbered(4, "Add a new application: fill in Company, Position, Date Applied, Status, Link, Notes")
numbered(5, "Click Add Application")
numbered(6, "Use the filters to show only certain statuses, and sort by date, company, or status")
numbered(7, "Expand any application to update its status, edit notes, save changes, or delete it")
numbered(8, 'Applications stuck in "Applied" for 7+ days get a follow-up reminder automatically')
numbered(9, "Click Download All Applications (CSV) to export everything")
sub_header("Status Pipeline")
body("Applied > Phone Screen > Interview > Offer > Rejected > Withdrawn")
sub_header("Tips")
bullet("Data saves automatically between sessions")
bullet("Use the Notes field to track interviewer names, salary info, or next steps")
bullet("The pipeline chart updates in real time as you change statuses")

# Module 5
section_header("Module 5: Subscription & Recurring Expense Auditor")
body("Scans your bank statement to find recurring charges and shows how much you could save by cancelling some.")
sub_header("How to Use")
numbered(1, "Navigate to Subscription Auditor in the sidebar")
numbered(2, "Upload a CSV bank or credit card statement")
numbered(3, "Map your columns: Date, Description, and Amount (the app tries to auto-detect)")
numbered(4, "Review detected recurring subscriptions: name, monthly amount, annual cost, frequency")
numbered(5, "Check the Potential Duplicates section for flagged similar charges")
numbered(6, "Use the What-If Savings Calculator: select subscriptions to cancel, see projected savings")
numbered(7, "Export results as CSV or Excel")
sub_header("Adjusting Sensitivity")
bullet("The Fuzzy match sensitivity slider controls how aggressively transactions are grouped")
bullet("Lower = more aggressive grouping (groups somewhat similar items)")
bullet("Higher = stricter matching (only near-exact matches)")
bullet("Default of 75 works well for most bank statements")
sub_header("Test It")
bullet("Upload sample_data/bank_statement.csv")
bullet("Should detect Netflix, Spotify, Amazon Prime, AT&T, Gym, Adobe, Comcast, Hulu")
bullet("Try the What-If calculator and select a few to cancel")

# General Tips
section_header("General Tips")
pdf.ln(4)
bullet("All your data stays on your computer. Nothing is uploaded to the cloud.")
bullet("Refresh the page (F5) if anything looks stuck.")
bullet("To stop the app, close the terminal window or press Ctrl+C.")
bullet("To restart, double-click start.bat again.")
bullet("Portfolio and job application data persist between sessions automatically.")
bullet("You can run FinanceKit offline for most features (Portfolio Tracker needs internet for live prices).")

pdf.output("sample_data/FinanceKit_User_Guide.pdf")
print("User Guide PDF created successfully")
