# FinanceKit v3.0 — User Guide

Welcome to FinanceKit! This guide walks you through every module step by step.

---

## Getting Started

1. **Double-click `start.bat`** (Windows) or run `./start.sh` (Mac/Linux)
2. The app opens automatically in your browser at `http://localhost:8501`
3. On first launch, the **5-step onboarding wizard** guides you through setup:
   - **Step 1 — Welcome:** Introduction and "Get Started" button
   - **Step 2 — Profile:** Set your name, email, currency, and date format
   - **Step 3 — Choose Modules:** Enable/disable any of the 7 modules (all on by default)
   - **Step 4 — Import Data:** Import a bank CSV, restore from a backup ZIP, or start fresh
   - **Step 5 — Quick Tour:** Visual walkthrough of key features
4. Use the **sidebar on the left** to switch between modules (only enabled modules appear)
5. Click the **FinanceKit** logo at the top-left to return to the Dashboard anytime
6. To re-run onboarding or change which modules are enabled, go to **Settings > Modules**

---

## Module 1: Receipt & Invoice Scanner

**What it does:** Extracts data from PDF receipts and photos so you don't have to type it manually.

### Steps:
1. Navigate to **Receipt Scanner** in the sidebar
2. Choose the **Upload Files** tab or the **Camera** tab
3. Click **Browse files** (or drag and drop) to upload one or more PDF, JPG, or PNG files
4. Click the **Scan & Add Receipts** button
5. The app extracts: date, vendor name, total amount, and auto-guesses a category
6. **Review the table** — click any cell to edit it if the extraction wasn't perfect
7. Use the **Category** dropdown in each row to recategorize
8. Expand **"View raw extracted text"** to see exactly what text was pulled from each file
9. Click **Download CSV** or **Download Excel** to export
10. If you have 3+ receipts with dates and totals, a **Monthly Receipt Spending** chart appears at the top

### Tips:
- Works best with text-based PDFs (digitally generated receipts)
- Scanned/image PDFs and photos need Tesseract OCR installed (see README)
- You can upload multiple receipts at once and export them all in one spreadsheet
- Use the **Camera** tab on mobile to snap receipt photos directly
- Click **Clear All** (two-click confirmation) to remove all receipts and start fresh

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
   - 24-hour change percentage
   - Total portfolio value, cost basis, and gain/loss at the top
   - Top gainer and top loser
4. Click **Refresh Prices** to fetch updated prices
5. **Allocation charts:** Two donut charts show allocation by holding and by type (Stocks vs Crypto)
6. **Performance chart:** Select a time period (1mo, 3mo, 6mo, 1y) — the chart loads automatically showing individual holding values and total portfolio value over time
7. **Watchlist tab:** Add tickers to monitor without owning them. Click **Fetch Watchlist Prices** to see current prices
8. **Price Alerts tab:**
   - Pick a ticker, choose Above or Below, set a target price
   - Click **Set Alert**
   - Alerts are checked every time you refresh — triggered alerts show in green or red
   - Click **Clear triggered alerts** to remove ones that have fired
9. **Email Alerts (optional):** Expand the settings section at the bottom of the Alerts tab to configure SMTP email notifications

### Supported crypto tickers:
BTC, ETH, SOL, ADA, DOT, DOGE, XRP, AVAX, MATIC, LINK, LTC, UNI, ATOM, SHIB, BNB

### Tips:
- Portfolio data saves automatically to `data/portfolio.json` — it persists between sessions
- Use the **Remove** dropdown at the bottom of the Portfolio tab to delete a holding
- Stock data comes from Yahoo Finance, crypto from CoinGecko (both free, no API key needed)

### Test it:
- Add `AAPL` (Stock) at $150, qty 10
- Add `BTC` (Crypto) at $30000, qty 0.5
- Click Refresh Prices and check the performance chart

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
4. Click **Add to Transaction History** to import the data
5. Optionally enter **your name** (appears on the PDF title page)
6. The app immediately shows:
   - **Summary stats:** total income, total expenses, net, average transaction
   - **Top spending categories** ranked by amount
7. **Charts displayed in-app:**
   - Monthly spending bar chart
   - Category breakdown donut chart
   - Income vs expenses line chart over time
8. Optionally expand the **Net Worth Calculator** to include assets and liabilities in the report
9. Click **Generate PDF Report** to create a downloadable PDF containing all of the above
10. Click **Download PDF** to save it
11. Click **Download Cleaned Excel** to get the processed transaction data as a spreadsheet
12. Expand **Email This Report** to send the PDF via email using SMTP

### How income vs expenses are detected:
- **Positive amounts** = income (deposits, payments received)
- **Negative amounts** = expenses (purchases, bills)

### Supported bank formats (auto-detected):
Chase, Bank of America, Wells Fargo, Capital One, American Express, and any generic CSV

### Quick Import:
- You can also drop a CSV on the **Dashboard** quick import banner, then navigate to Report Generator — the file will be ready to map

### Test it:
- Upload `sample_data/transactions.csv`
- All columns should auto-map correctly
- Generate the PDF report

---

## Module 4: Freelance Dashboard

**What it does:** Track clients, log projects, generate invoices, and monitor your freelance income.

### Steps:
1. Navigate to **Freelance Dashboard** in the sidebar
2. You'll see four tabs: **Overview**, **Clients & Jobs**, **Invoices**, and **Income**

### Overview Tab:
- Shows key metrics: Total Invoiced, Total Paid, Outstanding balance, and Active Clients
- A warning banner appears if you have unpaid invoices
- **Monthly Freelance Income** bar chart shows your earning trends (only paid invoices)
- **Client Profitability** horizontal bar chart shows which clients have paid the most

### Clients & Jobs Tab:
1. Click **Add New Client / Job** to expand the form
2. Fill in: Client/Company Name, Project/Job Description, Date Started, Status, Rate Type (Hourly/Flat Rate), Rate, and Notes
3. Click **Add Client/Job**
4. Use the **status filter** to show clients at specific stages
5. A **pipeline bar chart** shows how many clients are at each status
6. Expand any client to:
   - Update their status
   - Edit notes
   - Click **Save** to persist changes
   - Click **Delete** to remove

### Invoices Tab:
1. Select a **Client** from the dropdown
2. Set the **Invoice Date** and **Payment Terms** (Net 30, Net 15, Net 60, Due on Receipt)
3. Enter your name (for the invoice header)
4. Add up to **5 line items** with Description, Qty/Hours, and Rate
5. Click **Create Invoice** — the total is auto-calculated from line items
6. View all invoices sorted by date, with Paid/Unpaid icons
7. Expand any invoice to:
   - See the line items table
   - **Mark Paid / Mark Unpaid**
   - **Download PDF** — a clean, branded invoice PDF
   - **Delete** the invoice

### Income Tab:
- View lifetime income (paid), total invoiced, and collection rate
- Monthly income bar chart and client income pie chart
- **Export All Invoices (CSV)** button at the bottom

### Status options:
In Progress, Completed, Invoiced, Paid, On Hold, Cancelled

### Tips:
- Data saves automatically to `data/freelance_data.json`
- Invoice PDFs include line items, totals, payment terms, and a "Thank you for your business!" footer
- The pipeline chart updates in real time as you change statuses

---

## Module 5: Subscription & Recurring Expense Auditor

**What it does:** Scans your bank statement to find recurring charges and shows how much you'd save by cancelling some.

### Steps:
1. Navigate to **Subscription Auditor** in the sidebar
2. Upload a CSV bank or credit card statement
3. **Map your columns:**
   - Select which columns are Date, Description, and Amount
   - The app tries to auto-detect these
4. Click **Add to Statement History**
5. The app analyzes your transactions:
   - Groups similar descriptions using fuzzy matching
   - Identifies charges that repeat monthly or quarterly
   - Filters out one-time purchases
6. **Results show:**
   - Number of recurring subscriptions found
   - Total monthly and annual cost
   - Known subscription matches with direct **cancel links** (Netflix, Spotify, etc.)
7. **Keep/Cancel toggles:**
   - Set each subscription to Keep or Cancel
   - Your decisions persist between sessions
   - A **savings summary banner** appears showing how much you'd save
8. **Lifetime Cost Projections:** A table showing the 1-year, 3-year, and 5-year cost if you keep each subscription
9. **Potential Duplicates:** The app flags subscriptions with very similar names
10. **Annual Calendar:** A bar chart showing how many subscriptions renew each month
11. **Export:** Download results as CSV or Excel (includes your Keep/Cancel decisions)

### Adjusting sensitivity:
- The **Fuzzy match sensitivity** slider controls how aggressively transactions are grouped
- Lower = more aggressive (groups things that are somewhat similar)
- Higher = stricter (only groups near-exact matches)
- Default of 75 works well for most statements
- Upload multiple months of data for best detection results

### Test it:
- Upload `sample_data/bank_statement.csv`
- Columns should auto-map (Date, Description, Amount)
- You should see Netflix, Spotify, Amazon Prime, AT&T, Gym, Adobe, Comcast, and Hulu detected
- Try toggling some subscriptions to "Cancel" and see the savings summary

---

## Module 6: Budget Tracker

**What it does:** Set monthly budgets by category, import bank transactions, and track spending against your budget with color-coded progress bars and charts.

### Steps:
1. Navigate to **Budget Tracker** in the sidebar
2. **Set up your budgets:**
   - Expand **Set Monthly Budgets**
   - Choose a **Quick Load Template** (Student, Freelancer, Family, or Single Professional) to start with recommended amounts
   - Or manually set amounts for each of the 11 categories
   - Click **Save Budgets**

### Import Transactions:
1. Upload a CSV bank statement in the **Import Bank Transactions** section
2. Map the Date, Description, and Amount columns
3. Click **Analyze Transactions**
4. The app auto-categorizes each transaction using keyword matching (e.g., "Starbucks" → Dining Out, "Walmart" → Food & Groceries)

### Budget Status:
- **Top metrics:** Total Budgeted, Total Spent, Remaining, and Daily Average with days remaining
- **Alert banners:** Red alerts for over-budget categories, yellow warnings for categories at 80%+
- **Category Breakdown:** Color-coded progress bars for each category:
  - Green (under 50%) → Yellow (50-80%) → Orange (80-100%) → Red (over budget)
  - Shows dollar amounts spent vs. budgeted

### Spending Overview:
- **Donut chart:** Spent vs. Remaining of total budget
- **Horizontal bar chart:** Spending by category, sorted by amount

### Month-over-Month Comparison:
- If you have 2+ months of data, a grouped bar chart compares spending by category between the two most recent months

### Edit Categories:
- Expand **Review & Edit Transaction Categories** to see all transactions for the selected month
- Change any transaction's category using the dropdown
- Click **Apply Category Edits** to save changes

### 11 Budget Categories:
Housing, Food & Groceries, Dining Out, Transportation, Entertainment, Subscriptions, Shopping, Health, Savings, Utilities, Other

### Tips:
- Transactions persist in `data/budget_transactions.json` between sessions
- Use the month selector to view different months
- Click **Clear Data** to reset transactions and start fresh
- The auto-categorizer uses keyword matching — you can always manually correct categories

---

## Module 7: Savings Goal Tracker

**What it does:** Set savings goals with targets, deadlines, and monthly contributions. Track progress with visual progress bars, milestone celebrations, and projection dates.

### Steps:
1. Navigate to **Goal Tracker** in the sidebar
2. **Add a goal:**
   - Enter a **Goal Name** (e.g., Emergency Fund, Vacation, New Car)
   - Set a **Target Amount** and how much you've **Already Saved**
   - Choose a **Target Date** (deadline)
   - Set a **Monthly Contribution** amount
   - Optionally add **Notes** about why this goal matters
   - Click **Add Goal**

### Goal Dashboard:
- **Summary bar:** Active Goals count, Total Saved, Total Remaining, Goals Completed
- Each goal shows an expandable card with:
  - **Progress bar** with color coding (gray → purple → indigo → green)
  - **Status icon:** 🎯 (starting), 📈 (25%+), 💪 (50%+), 🔥 (75%+), 🏆 (complete)
  - **Metrics:** Saved, Target, Remaining, Monthly contribution
  - **Projection:** Estimated completion date based on your monthly contribution
  - **On-track indicator:** Green if projected date is before deadline, yellow warning if behind

### Milestone Celebrations:
- At **25%, 50%, 75%** → 🎉 Balloons animation + toast notification
- At **100%** → 🏆 Snow animation + completion celebration
- A **milestone log** shows which milestones you've reached

### Managing Goals:
- **Quick-add funds:** Click +$50, +$100, +$250, or +$500 to instantly add money
- **Custom update:** Enter a specific amount and click **Update**
- **History chart:** If you have 2+ data points, a line chart shows your savings progress over time with a dashed goal line
- **Delete:** Click the delete button to remove a goal

### Tips:
- All goals save to `data/goals.json` and persist between sessions
- The projection calculator tells you when you'll reach your goal at your current contribution rate
- Adding funds records a history entry — the more entries, the better your history chart looks
- Notes are great for motivation — write down WHY the goal matters

---

## Module 8: Settings

**What it does:** Configure your profile, modules, email settings, invoices, authentication, notifications, manage data, and check for updates.

### Profile:
- Set your **display name** (used in report headers, invoice "from" field, and dashboard greeting)
- Set your **email address** (prefilled in email-related features)
- Choose your **currency** (USD, EUR, GBP, CAD, AUD, JPY) — all modules will display the chosen currency symbol
- Choose your **date format** (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD) — all date displays across the app will respect this

### Modules:
- Toggle each of the 7 modules on or off
- Disabled modules are hidden from the sidebar and dashboard
- Click **Re-run Onboarding Wizard** to go through the 5-step setup again

### Email (SMTP):
- Configure SMTP settings once and they'll be used across Report Generator and Portfolio Tracker
- Fields: Server, Port, Email, App Password
- Click **Send Test Email** to verify your configuration
- Expand the help section for step-by-step Gmail App Password instructions

### Invoice:
- Set company/business info (name, address, email, phone, payment details)
- Configure default tax rate and invoice template (Minimal, Professional, Creative)
- Upload a company logo for invoices (PNG/JPG, max 500KB)

### Notifications:
- Master toggle for all in-app notifications
- Per-module toggles (Budget, Goals, Portfolio, Subscriptions, Freelance, Receipts)
- Alert thresholds: budget warning %, portfolio change %, subscription cost warning, invoice overdue days
- Email digest: daily or weekly summary of unread notifications via SMTP

### Data Management:
- **Liabilities:** Add debts and loans for net worth calculation
- **Export All Data:** Creates a ZIP file containing all your data files for backup
- **Import Data:** Upload a previously exported ZIP to restore your data
- **Reset All Data:** Two-click confirmation to delete all data files (keeps backups)
- A table shows all data files with their sizes and record counts

### About:
- Shows current version, Python version, and Streamlit version
- Links to GitHub repo and Gumroad product page
- **Check for Updates** compares your version against the latest available
- **Logs Viewer:** Filter logs by level (INFO, WARNING, ERROR), download or clear
- **Health Check:** Verify Python, packages, data directory, JSON validity, connectivity, SMTP, and migrations

---

## Setting Up Authentication

FinanceKit supports optional authentication to protect your data and enable multi-user access. **By default, authentication is disabled** — the app works exactly as before with no login required.

### Enabling Authentication:
1. Go to **Settings → Authentication**
2. Toggle **Require authentication** to ON
3. If no user accounts exist yet, you'll be prompted to create the first (admin) account
4. Enter a display name, email, and password, then click **Create Admin Account & Enable Auth**
5. After enabling, the login page will appear on every app launch

### Creating Additional Accounts:
- On the login page, click **Create an account**
- Fill in display name, email, and password
- The password strength indicator shows weak (red), medium (yellow), or strong (green)
- Passwords must be at least 6 characters

### Signing In:
- Enter your email and password on the login page
- Check **Remember me** to stay signed in for 30 days (default session is 24 hours)
- Your user avatar and name appear in the sidebar when signed in
- Click **Sign Out** in the sidebar to log out

### Per-User Data Isolation:
- Each user gets their own data directory (`data/users/{user_id}/`)
- All budgets, goals, receipts, portfolio data, etc. are completely isolated between users
- Existing data in `data/` from before auth was enabled remains accessible when auth is disabled

### Password Reset:
1. On the login page, click **Forgot password?**
2. Enter your email address and click **Send Reset Token**
3. A one-time reset token is displayed on screen (valid for 1 hour)
4. Copy the token, enter it along with your new password, and click **Reset Password**

### Account Management:
- **Change Password:** Go to Settings → Authentication → Change Password (local accounts only)
- **Delete Account:** Go to Settings → Authentication → Delete Account (requires two-click confirmation)
- OAuth users (Google/GitHub) manage their passwords through their provider

### Setting Up Google OAuth (Optional):
1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Go to **APIs & Services → OAuth consent screen** and choose External
4. Fill in app name (e.g., "FinanceKit") and your email
5. Go to **Credentials → Create Credentials → OAuth 2.0 Client ID**
6. Select **Web application**
7. Add `http://localhost:8501` to **Authorized redirect URIs**
8. Copy the **Client ID** and **Client Secret**
9. Paste them in FinanceKit: **Settings → Authentication → Google OAuth 2.0**

### Setting Up GitHub OAuth (Optional):
1. Go to [github.com/settings/developers](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Set **Application name** to "FinanceKit"
4. Set **Homepage URL** to `http://localhost:8501`
5. Set **Authorization callback URL** to `http://localhost:8501`
6. Click **Register application**
7. Copy the **Client ID** and generate a **Client Secret**
8. Paste them in FinanceKit: **Settings → Authentication → GitHub OAuth**

### Security Notes:
- `auth_config.json` contains OAuth secrets — do not share or commit this file
- Passwords are hashed with bcrypt (or SHA-256 fallback if bcrypt is unavailable)
- Session expiry can be configured in Settings → Authentication (default: 24 hours)
- User data directories are automatically created with empty default files on first login

### Troubleshooting:
- **"No account found"**: Make sure you're using the exact email you registered with
- **OAuth not working**: Verify your Client ID and Secret are correct, and that the redirect URI matches your FinanceKit URL
- **Session expired**: Sign in again. Check "Remember me" for longer sessions
- **Forgot your only admin password**: Delete `data/users.json` and re-enable auth to create a new admin account

---

## Dashboard Features (v3.0)

- **Financial Health Score:** Gauge showing weighted score from budget adherence, savings rate, emergency fund, debt ratio, and subscription efficiency
- **Net Worth Tracker:** Assets (portfolio + goals + cash) minus liabilities, with monthly snapshots and trend chart
- **Quick Actions:** Four large buttons — Add Transaction, Scan Receipt, Generate Report, New Goal
- **Recent Activity Feed:** Last 10 actions across all modules (transactions, receipts, goals, invoices, etc.)
- **Module Cards:** Summary widgets for each enabled module with activity indicators

---

## Keyboard Shortcuts

- **0:** Dashboard
- **1:** Receipt Scanner
- **2:** Portfolio Tracker
- **3:** Report Generator
- **4:** Freelance Dashboard
- **5:** Subscription Auditor
- **6:** Budget Tracker
- **7:** Goal Tracker
- **9:** Settings
- **?:** Show shortcuts help

---

## Tips for All Modules

- **Data stays on your computer** — nothing is uploaded to the cloud
- **Refresh the page** (F5) if anything looks stuck
- **To stop the app**, close the terminal window or press `Ctrl+C`
- **To restart**, double-click `start.bat` again
- Your data persists between sessions automatically in the `data/` folder
- Automatic backups are created every time data is saved (up to 5 versions per file)
- You can run FinanceKit offline for most features (Portfolio Tracker needs internet for live prices)
- Use **Settings > Modules** to enable/disable modules and customize your sidebar
- Use **Ctrl+P** to print the current page — print styles hide the sidebar and interactive elements
