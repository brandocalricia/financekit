# FinanceKit v4.0 -- User Guide

This is the complete user guide for FinanceKit v4.0. It covers installation, every module, configuration, and troubleshooting. Whether you are a first-time user or upgrading from a previous version, this document will walk you through the entire application.

---

## 1. Getting Started

### Installation

FinanceKit requires Python 3.10 or newer. You can verify your Python version by opening a terminal and running:

```
python --version
```

Once Python is confirmed, install the required dependencies:

```
pip install -r requirements.txt
```

This installs Streamlit, reporting libraries, API clients, and all other packages FinanceKit depends on. No external database is needed. All data is stored locally on your machine as JSON files.

### First Run

On Windows, double-click `start.bat` or run `python install.py` to create a desktop shortcut with system tray icon. On macOS or Linux, run `./start.sh` from a terminal. The application will launch in your default web browser at `http://localhost:8501`. If the browser does not open automatically, navigate to that address manually.

To stop the application, close the terminal window, press `Ctrl+C` in the terminal, or right-click the system tray icon and select Quit.

You can also install FinanceKit as a Progressive Web App on mobile devices by visiting the app in your mobile browser and tapping "Add to Home Screen".

### Onboarding Wizard

The first time you launch FinanceKit, a 5-step onboarding wizard guides you through initial setup:

1. **Welcome** -- A brief introduction to FinanceKit and what it can do. Click "Get Started" to proceed.
2. **Profile** -- Enter your display name, email address, preferred currency, and date format. These settings are used across all modules.
3. **Choose Modules** -- Select which modules you want enabled. All modules are available by default, but you can disable any you do not need. Disabled modules are hidden from the sidebar. You can re-enable them later in Settings.
4. **Import Data** -- Optionally upload a bank CSV or a previous FinanceKit backup ZIP to populate the application with your existing financial data right away.
5. **Quick Tour** -- A guided walkthrough highlighting the Dashboard, sidebar navigation, and key features. You can skip this step if you prefer to explore on your own.

After completing the wizard, you land on the Dashboard. Use the sidebar on the left to navigate between modules at any time. Click the FinanceKit logo at the top-left to return to the Dashboard from anywhere.

---

## 2. Authentication Setup

FinanceKit supports optional authentication to protect your data and enable multi-user access. By default, authentication is disabled and the application works without any login required.

### Local Accounts

To enable authentication:

1. Go to Settings and open the Authentication section.
2. Toggle "Require authentication" to ON.
3. If no user accounts exist, you will be prompted to create the first admin account. Enter a display name, email, and password, then click "Create Admin Account & Enable Auth."
4. After enabling, the login page appears on every launch.

To register additional accounts, click "Create an account" on the login page. Enter a display name, email, and password. The password strength indicator shows weak (red), medium (yellow), or strong (green). Passwords must be at least 6 characters.

To sign in, enter your email and password. Check "Remember me" to stay signed in for 30 days; the default session length is 24 hours. Your user avatar and name appear in the sidebar when signed in. Click "Sign Out" in the sidebar to log out.

### Google OAuth Setup

Google OAuth lets users sign in with their Google account. To configure it:

1. Go to [console.cloud.google.com](https://console.cloud.google.com/) and create a new project or select an existing one.
2. Navigate to APIs & Services, then OAuth consent screen. Choose External.
3. Fill in the app name (for example, "FinanceKit") and your email address.
4. Go to Credentials, then Create Credentials, then OAuth 2.0 Client ID.
5. Select Web application as the application type.
6. Add `http://localhost:8501` to the Authorized redirect URIs list.
7. Copy the Client ID and Client Secret that are generated.
8. In FinanceKit, go to Settings, then Authentication, then Google OAuth 2.0. Paste the Client ID and Client Secret there.

Users will now see a "Sign in with Google" button on the login page.

### GitHub OAuth Setup

GitHub OAuth lets users sign in with their GitHub account. To configure it:

1. Go to [github.com/settings/developers](https://github.com/settings/developers) and click New OAuth App.
2. Set the Application name to "FinanceKit."
3. Set the Homepage URL to `http://localhost:8501`.
4. Set the Authorization callback URL to `http://localhost:8501`.
5. Click Register application.
6. Copy the Client ID and generate a Client Secret.
7. In FinanceKit, go to Settings, then Authentication, then GitHub OAuth. Paste the Client ID and Client Secret there.

Users will now see a "Sign in with GitHub" button on the login page.

### Session Management and Password Reset

Session expiry can be configured in Settings under Authentication. The default is 24 hours; checking "Remember me" extends it to 30 days.

To reset a forgotten password:

1. On the login page, click "Forgot password?"
2. Enter the email address associated with your account and click "Send Reset Token."
3. A one-time reset token is displayed on screen. It is valid for 1 hour.
4. Copy the token, enter it along with your new password, and click "Reset Password."

You can also change your password while signed in by going to Settings, then Authentication, then Change Password. This option is available for local accounts only; OAuth users manage passwords through their provider.

To delete an account, go to Settings, then Authentication, then Delete Account. This requires a two-click confirmation. The `auth_config.json` file contains OAuth secrets and should not be shared or committed to version control. Passwords are hashed with bcrypt (or SHA-256 fallback if bcrypt is unavailable).

---

## 3. Dashboard

The Dashboard is the home screen of FinanceKit. It provides a high-level overview of your financial health and quick access to every module.

### Financial Health Score

The Financial Health Score is a composite metric displayed prominently at the top of the Dashboard. It is calculated from five components, each weighted equally:

- **Budget Adherence** -- How closely your actual spending matches your budget targets. Staying within budget across all categories yields a higher score.
- **Savings Rate** -- The percentage of your income that you are saving each month. A higher savings rate improves this component.
- **Emergency Fund** -- Progress toward having three to six months of expenses saved. This is derived from your savings goals that are tagged as emergency funds.
- **Debt Ratio** -- Your total liabilities divided by total assets. A lower ratio results in a higher score.
- **Subscription Efficiency** -- The proportion of your subscriptions marked as "Keep" with daily or weekly usage ratings, relative to your total subscription spending. Cutting unused subscriptions improves this score.

The score is displayed as a number from 0 to 100 with a color-coded gauge. Scores above 80 are green, 50 to 80 are yellow, and below 50 are red.

### Net Worth Tracker

The Net Worth section shows your total assets minus total liabilities. Assets include savings, investments (pulled from Portfolio Tracker), and any manually entered assets. Liabilities include debts and obligations you have entered.

Monthly snapshots are taken automatically so you can see your net worth trend over time in a line chart. Each snapshot records the date, total assets, total liabilities, and net worth.

### Quick Actions Row

A row of action buttons provides one-click access to common tasks: add a receipt, log a transaction, add funds to a goal, check portfolio prices, and import a bank statement. Each button navigates you directly to the relevant module with the appropriate form open.

### Recent Activity Feed

The Recent Activity section shows a chronological feed of your latest actions across all modules. This includes transactions added, goals updated, receipts scanned, invoices created, and subscription decisions made. Each entry shows a timestamp, a brief description, and the module it belongs to.

### Module Widgets and Cards

Below the summary sections, the Dashboard displays cards for each enabled module. Each card shows a key metric or status summary: budget remaining this month, next goal milestone, portfolio value change, pending invoices, and subscription costs. Clicking a card navigates to that module.

---

## 4. Budget Tracker

The Budget Tracker lets you set monthly spending budgets by category, import transactions from your bank, and monitor your spending with progress bars and charts.

### Categories

The Budget Tracker uses 11 spending categories:

1. Housing
2. Food & Groceries
3. Dining Out
4. Transportation
5. Utilities
6. Entertainment
7. Shopping
8. Health & Medical
9. Insurance
10. Personal
11. Other

Every transaction you import is assigned to one of these categories. You can change the category of any transaction manually after import.

### Templates

Four budget templates are available to give you a starting point:

- **Student** -- Lower amounts across the board with emphasis on food, transportation, and entertainment.
- **Freelancer** -- Accounts for variable income with higher allocations for utilities, insurance, and a generous "Other" category for business expenses.
- **Family** -- Higher housing, groceries, health, and insurance budgets reflecting household expenses.
- **Professional** -- Balanced allocations typical of a salaried individual with moderate spending across all categories.

To use a template, expand "Set Monthly Budgets," select a template from the Quick Load dropdown, adjust any amounts as needed, and click "Save Budgets." You can modify individual category amounts at any time.

### CSV Import for Spending Tracking

To import transactions, upload a CSV bank or credit card statement. Map the Date, Description, and Amount columns using the dropdowns (the application attempts auto-detection). Click "Analyze Transactions" to import. The application auto-categorizes each transaction using keyword matching. For example, grocery store names map to "Food & Groceries" and restaurant names map to "Dining Out."

After import, expand "Review & Edit Transaction Categories" to see all transactions for the selected month. You can change any transaction's category using the dropdown in each row, then click "Apply Category Edits" to save.

### Analytics Tab

The Analytics tab provides three views of your spending data:

- **Spending vs. Budget** -- Color-coded progress bars for each category. Green indicates under 50% spent, yellow indicates 50 to 80%, orange indicates 80 to 100%, and red indicates over budget. Dollar amounts and percentages are shown for each category.
- **Month-over-Month Comparison** -- If you have two or more months of data, a grouped bar chart compares spending by category between months. This helps you spot trends and seasonal changes in your spending.
- **Daily Averages** -- Your total spending divided by the number of days elapsed in the current month, alongside a projection of where you will end up if spending continues at the current rate.

Summary metrics at the top show Total Budgeted, Total Spent, Remaining, and Daily Average with days remaining in the month. Alert banners appear for categories that are over budget (red) or approaching the limit at 80% or higher (yellow).

---

## 5. Goal Tracker

The Goal Tracker helps you set savings goals, track progress, and stay motivated with milestones and projections.

### Creating Goals

To create a goal, navigate to the Goal Tracker and fill in:

- **Goal Name** -- A descriptive label such as "Emergency Fund," "Vacation," or "New Car."
- **Target Amount** -- The total dollar amount you want to save.
- **Already Saved** -- How much you have saved toward this goal so far.
- **Target Date** -- Your deadline for reaching the goal.
- **Monthly Contribution** -- How much you plan to add each month.
- **Notes** (optional) -- A reminder of why this goal matters to you.

Click "Add Goal" to create it. The goal appears on your dashboard with a progress bar and key metrics.

### Quick-Add Buttons

Each goal card has quick-add buttons for common contribution amounts: +$50, +$100, +$250, and +$500. Clicking one of these buttons instantly adds that amount to the goal and records a history entry. For a custom amount, enter the value in the input field and click "Update."

### Milestone Celebrations

FinanceKit celebrates your progress at four milestones:

- **25%** -- A balloons animation plays and a toast notification congratulates you on reaching a quarter of your goal.
- **50%** -- Another celebration marks the halfway point.
- **75%** -- A third celebration signals you are in the home stretch.
- **100%** -- A snow animation and completion message appear when you reach your target.

A milestone log on each goal card shows which milestones you have reached and when.

### Progress History Chart

Each goal tracks a history of contributions. Once you have two or more data points, a line chart appears showing your savings progress over time. A dashed horizontal line marks your target amount, and a projected completion date is calculated based on your monthly contribution rate. If the projection falls before your deadline, an on-track indicator appears in green. If you are behind pace, a yellow warning is shown.

---

## 6. Receipt Scanner

The Receipt Scanner extracts data from PDF receipts and photos so you do not have to enter it manually.

### Upload and Camera Input

Navigate to the Receipt Scanner and choose either the Upload Files tab or the Camera tab. In the Upload tab, click "Browse files" or drag and drop one or more PDF, JPG, or PNG files. In the Camera tab (useful on mobile devices), snap a photo of a receipt directly. You can upload multiple receipts at once.

Click "Scan & Add Receipts" to process the files. The application extracts the date, vendor name, total amount, and auto-assigns a category for each receipt.

### OCR Extraction

For text-based PDFs (digitally generated receipts), extraction works out of the box with no additional setup. For scanned PDFs and photos, Tesseract OCR must be installed on your system for accurate text recognition. Without Tesseract, the application will still attempt extraction but accuracy will be reduced. See the Troubleshooting section for installation guidance.

You can expand "View raw extracted text" on any receipt to see exactly what text was pulled from the file. This is useful for verifying extraction accuracy or debugging issues with specific receipt formats.

### Auto-Categorization by Vendor Name

The application matches recognized vendor names against a built-in dictionary to assign categories automatically. For example, a receipt from a grocery store is categorized as "Food & Groceries" and one from a restaurant is categorized as "Dining Out." You can change any category using the dropdown in the results table.

### Export to Excel and CSV

Click "Download CSV" or "Download Excel" to export all scanned receipts as a spreadsheet. The export includes date, vendor, amount, category, and the source filename. If you have three or more receipts with valid dates and totals, a Monthly Receipt Spending chart appears at the top of the page showing your receipt spending over time.

Click "Clear All" (two-click confirmation) to remove all receipts and start fresh.

---

## 7. Portfolio Tracker

The Portfolio Tracker monitors your investment holdings with live prices, gain/loss calculations, charts, and price alerts.

### Adding Holdings

To add a holding, enter a ticker symbol (for example, AAPL for Apple or BTC for Bitcoin), select the type (Stock or Crypto), enter your purchase price and quantity, and click "Add to Portfolio." The application fetches the current price and calculates your market value, gain or loss in dollars, gain or loss as a percentage, and the 24-hour price change.

Stock prices come from Yahoo Finance and crypto prices come from CoinGecko. Both are free and require no API key. Supported crypto tickers include BTC, ETH, SOL, ADA, DOT, DOGE, XRP, AVAX, MATIC, LINK, LTC, UNI, ATOM, SHIB, and BNB.

### Live Prices

Click "Refresh Prices" to fetch updated prices for all holdings. The portfolio dashboard shows each holding's current price, market value, and gain or loss. Summary metrics at the top display total portfolio value, total cost basis, total gain or loss, and your top gainer and top loser.

### Allocation Charts and Performance

Two donut charts show your portfolio allocation: one by individual holding and one by asset type (stocks versus crypto). A performance chart lets you select a time period (1 month, 3 months, 6 months, or 1 year) and displays the value of individual holdings and the total portfolio over time.

To remove a holding, use the "Remove" dropdown at the bottom of the Portfolio tab.

### Watchlist and Price Alerts

The Watchlist tab lets you monitor tickers without owning them. Add a ticker and click "Fetch Watchlist Prices" to see current prices.

The Price Alerts tab lets you set target prices for any ticker. Choose a ticker, select Above or Below, set the target price, and click "Set Alert." Alerts are checked every time you refresh prices. Triggered alerts appear highlighted in green or red. Click "Clear triggered alerts" to dismiss fired alerts.

For email notifications, expand the email settings section at the bottom of the Alerts tab. Configure your SMTP credentials (or use the ones from Settings) and the application will email you when an alert triggers.

---

## 8. Report Generator

The Report Generator turns a spreadsheet of bank transactions into a polished PDF report with summary statistics and charts.

### Auto-Detect Bank CSV Formats

The application automatically detects CSV formats from five major banks: Chase, Bank of America, Wells Fargo, Capital One, and American Express. It also handles any generic CSV file. When you upload a file, the application identifies the bank format and maps the Date, Description, Amount, and Category columns accordingly. If auto-detection is not perfect, use the dropdowns to correct the column mapping. Category is optional.

Click "Add to Transaction History" to import the data. Optionally enter your name, which appears on the PDF title page.

### Summary Statistics and Charts

After import, the application displays:

- **Summary stats** -- Total income, total expenses, net amount, and average transaction size. Positive amounts are treated as income and negative amounts as expenses.
- **Top spending categories** ranked by total amount.
- **Monthly spending bar chart** showing expenses by month.
- **Category breakdown donut chart** showing the proportion of spending in each category.
- **Income vs. expenses line chart** tracking both over time.

You can also expand the Net Worth Calculator to include assets and liabilities in the report.

### PDF Report Generation and Email

Click "Generate PDF Report" to compile all statistics and charts into a downloadable PDF document. Click "Download PDF" to save it to your computer. Click "Download Cleaned Excel" to export the processed transaction data as a spreadsheet.

To email the report, expand "Email This Report" and either enter SMTP credentials or use the ones configured in Settings. The PDF is attached to the email automatically.

You can also drop a CSV on the Dashboard quick import banner and then navigate to the Report Generator. The file will be ready to map.

---

## 9. Freelance Dashboard

The Freelance Dashboard is a complete freelance business management tool covering clients, time tracking, invoicing, and profit and loss.

### Client Management

Navigate to the Freelance Dashboard and open the Clients & Jobs tab. Click "Add New Client / Job" to expand the form. Fill in the client or company name, project description, date started, status, rate type (hourly or flat rate), rate, and notes. Click "Add Client/Job."

Clients can be assigned one of four statuses: Active, Inactive, Lead, or Archived. Use the status filter to show clients at specific stages. A pipeline bar chart shows how many clients are at each status. Expand any client to update their status, edit notes, save changes, or delete the record.

### Time Tracking

The time tracking feature supports two modes. The timer mode lets you start a clock, work on a task, and stop it when finished. The manual entry mode lets you enter hours directly for a specific date and client. Logged time is associated with the client and used in invoicing and income calculations.

### Invoice Generation

Open the Invoices tab, select a client from the dropdown, set the invoice date and payment terms (Net 30, Net 15, Net 60, or Due on Receipt), and enter your name for the invoice header. Add up to five line items, each with a description, quantity or hours, and rate. Click "Create Invoice" to generate it. The total is calculated automatically from the line items.

Three invoice templates are available:

- **Minimal** -- Clean and simple with basic formatting. Suitable for small projects and individual clients.
- **Professional** -- Structured layout with your company information, logo, and detailed line item table. Suitable for corporate clients.
- **Creative** -- Styled with modern design elements. Suitable for design, marketing, and creative industry work.

Select your preferred template in Settings under Invoice Settings, where you can also configure your company name, address, and upload a logo.

### Recurring Invoices

For ongoing engagements, you can set an invoice to recur automatically. Choose a frequency (weekly, biweekly, or monthly) and the application will generate new invoices on schedule based on the line items and rate from the original invoice.

### Expense Tracking and Profit and Loss

The Income tab shows lifetime income (paid invoices only), total invoiced, and your collection rate. Monthly income and client income charts provide visual breakdowns. The expense tracking feature lets you log business expenses and associate them with clients. The profit and loss view subtracts expenses from income to show your true earnings. Click "Export All Invoices (CSV)" to download your complete invoice history.

---

## 10. Subscription Auditor

The Subscription Auditor analyzes your bank statements to find recurring charges and helps you decide which subscriptions to keep or cancel.

### Auto-Detect Recurring Charges

Upload a CSV bank or credit card statement and map the Date, Description, and Amount columns. The application groups similar transactions using fuzzy matching, identifies charges that repeat monthly or quarterly, and filters out one-time purchases. The fuzzy match sensitivity slider (default 75) controls grouping aggressiveness. Lower values group more liberally; higher values require near-exact matches. Upload multiple months of data for the best detection results.

Results show the number of recurring subscriptions found, total monthly cost, and total annual cost. Known subscriptions (such as Netflix, Spotify, and Amazon Prime) are identified with direct cancel links.

### Categories and Manual Entry

Detected subscriptions are organized into 10 categories. You can also add subscriptions manually if they were not detected from your statement. Manual entry is useful for subscriptions charged to payment methods not included in the uploaded CSV.

### Keep or Cancel Decisions

Each subscription has a Keep/Cancel toggle. Set each one according to your preference. Your decisions persist between sessions. A savings summary banner shows how much you would save monthly and annually by cancelling the subscriptions you have marked. Lifetime cost projections show the 1-year, 3-year, and 5-year cost if you keep each subscription.

### Usage Ratings

Rate how often you use each subscription: Daily, Weekly, Rarely, or Never. These ratings feed into the Subscription Efficiency component of your Dashboard Financial Health Score. Subscriptions rated as "Never" are flagged for review.

### Price Change Detection

If you upload statements from multiple months, the application detects price changes in your subscriptions. A notification appears when a subscription's charge has increased or decreased compared to previous months, helping you catch silent price hikes.

The application also flags potential duplicate subscriptions with very similar names and shows an annual calendar bar chart indicating how many subscriptions renew each month. Export results as CSV or Excel, including your Keep/Cancel decisions and usage ratings.

---

## 11. Settings

The Settings page is the central configuration hub for FinanceKit.

### Profile, Currency, and Date Format

Set your display name (used in report headers, invoice "from" fields, and dashboard greeting), email address (prefilled in email features), preferred currency (USD, EUR, GBP, CAD, AUD, JPY), and date format (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD). All modules respect your currency and date format choices.

### Module Toggle

Enable or disable individual modules. Disabled modules are hidden from the sidebar and do not appear on the Dashboard. This is useful if you only use a subset of FinanceKit's features and want a cleaner interface.

### SMTP Email Configuration

Configure SMTP settings once and they are used across the Report Generator, Portfolio Tracker price alerts, and invoice emailing. Enter your SMTP server, port, email address, and app password. Click "Send Test Email" to verify the configuration. A help section provides step-by-step instructions for setting up a Gmail App Password.

### Invoice Settings

Configure your company name, address, phone number, and upload a logo. These details appear on generated invoices. Select your default invoice template (Minimal, Professional, or Creative). You can override the template on a per-invoice basis when creating invoices in the Freelance Dashboard.

### Authentication Settings

Toggle authentication on or off, manage OAuth provider credentials (Google and GitHub), configure session expiry duration, and manage user accounts. See the Authentication Setup section of this guide for full details.

### Notification Preferences and Thresholds

Configure which types of notifications you want to receive and set thresholds for automatic alerts. For example, you can set a budget warning threshold (default 80%) so that notifications appear when spending in any category exceeds that percentage. You can also configure goal milestone notifications, portfolio price alert notifications, and subscription renewal reminders. Per-module notification toggles let you silence alerts from modules you want to monitor passively.

### Data Management

- **Export All Data** -- Creates a ZIP file containing all your data files for backup. The ZIP includes budgets, goals, receipts, portfolio, freelance data, subscriptions, settings, and notification history.
- **Import Data** -- Upload a previously exported ZIP to restore your data. This overwrites current data with the contents of the backup.
- **Reset All Data** -- Two-click confirmation to delete all data files. Backups are preserved.

A table shows all data files with their sizes and record counts.

### Logs Viewer and Health Check

The Logs Viewer displays application logs including errors, warnings, and informational messages. Use it to diagnose issues or verify that background processes (such as recurring invoice generation) are running correctly.

The Health Check runs a series of diagnostics: verifying Python version, checking that all dependencies are installed, confirming data directory permissions, testing network connectivity for API-dependent features, and validating SMTP configuration if set. Results are displayed with pass/fail indicators for each check.

---

## 12. Notifications

FinanceKit includes an in-app notification system that keeps you informed of important events across all modules.

### Notification Types

Notifications are categorized into four types:

- **Info** -- General information such as successful imports, completed exports, and module status updates.
- **Warning** -- Alerts that require attention, such as approaching budget limits, subscriptions with price changes, and goals that are behind schedule.
- **Success** -- Positive confirmations such as goal milestones reached, invoices paid, and reports generated.
- **Alert** -- Urgent notifications such as budget categories exceeding their limit, triggered price alerts, and overdue invoices.

Notifications appear as a badge count in the sidebar. Click the notification icon to view the full list. Each notification shows the type, message, timestamp, and source module.

### Per-Module Toggles

In Settings under Notification Preferences, you can enable or disable notifications for each module independently. For example, you might want to receive budget warnings but not portfolio price change notifications.

### Email Digest

If SMTP is configured, you can opt into an email digest that summarizes your notifications. The digest includes budget status, upcoming goal deadlines, triggered price alerts, and subscription renewal reminders.

---

## 13. Keyboard Shortcuts

FinanceKit supports keyboard shortcuts for fast navigation. Press any of the following keys while the application is focused:

| Key | Action |
|-----|--------|
| 0 | Go to Dashboard |
| 1 | Open Budget Tracker |
| 2 | Open Goal Tracker |
| 3 | Open Receipt Scanner |
| 4 | Open Portfolio Tracker |
| 5 | Open Report Generator |
| 6 | Open Freelance Dashboard |
| 7 | Open Subscription Auditor |
| 9 | Open Settings |
| ? | Show help overlay with all shortcuts |

These shortcuts work from any page. The help overlay (triggered by ?) also displays a summary of each module.

---

## 14. Data Management

### Local Storage

All data is stored locally on your computer in the `data/` directory as JSON files. Nothing is uploaded to the cloud. Each module has its own data file (for example, `budget_transactions.json`, `goals.json`, `portfolio.json`, `freelance_data.json`, and `subscriptions.json`). Settings are stored in `settings.json`.

### Automatic Backups

Every time a data file is saved, FinanceKit creates a backup copy automatically. Up to five backup versions are retained per file, with the oldest backup being replaced when the limit is reached. Backups are stored alongside the original files with a timestamp suffix.

### Export and Import

Use Settings to export all data as a single ZIP file. This is the recommended way to back up your data before upgrades or system changes. To restore, upload the ZIP file through the Import Data feature in Settings. Importing overwrites current data with the backup contents, so export your current data first if you want to preserve it.

### Per-User Data Isolation

When authentication is enabled, each user gets their own data directory at `data/users/{user_id}/`. All budgets, goals, receipts, portfolio data, freelance records, and subscriptions are completely isolated between users. Data in the root `data/` directory from before authentication was enabled remains accessible when authentication is disabled.

---

## 15. Troubleshooting

### Python Not Found

If running `start.bat` or `start.sh` produces a "Python not found" error, ensure Python 3.10 or newer is installed and added to your system PATH. On Windows, reinstall Python from python.org and check the "Add Python to PATH" option during installation. On macOS, use `brew install python`. On Linux, use your distribution's package manager (for example, `sudo apt install python3`).

### Port Already in Use

If the application reports that port 8501 is already in use, another instance of FinanceKit or another Streamlit application is running. Close the other instance or specify a different port by running:

```
streamlit run app.py --server.port 8502
```

### OCR Not Working

Receipt scanning for scanned PDFs and photos requires Tesseract OCR. If text extraction produces poor results or empty output for image-based files:

- On Windows, download and install Tesseract from [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki). Add the installation directory to your system PATH.
- On macOS, run `brew install tesseract`.
- On Linux, run `sudo apt install tesseract-ocr`.

Text-based PDFs (digitally generated) do not require Tesseract and should extract correctly without it.

### API Rate Limits

The Portfolio Tracker fetches stock prices from Yahoo Finance and crypto prices from CoinGecko. Both services are free but impose rate limits. If prices fail to load or you see rate limit errors, wait a few minutes before clicking "Refresh Prices" again. Avoid refreshing more than a few times per minute.

### How to Run the Health Check

Go to Settings and scroll to the bottom of the page. Click "Run Health Check" to execute a diagnostic scan. The health check verifies your Python version, installed dependencies, data directory permissions, network connectivity, and SMTP configuration. Each check displays a pass or fail result with details about any issues found. Address any failed checks and run the health check again to confirm resolution.

---

This concludes the FinanceKit v3.0 User Guide. For additional help, visit the GitHub repository linked in Settings or run the in-app health check to diagnose issues.
