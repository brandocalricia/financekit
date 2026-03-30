# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [3.7] — Year-in-Review & Tax Summary Reports

### Added
- Year-in-Review section in Report Generator — select a year to see annual income, expenses, net savings, savings rate, top categories, month-by-month trend chart, and category donut chart
- "Generate Year-in-Review PDF" button with downloadable annual summary report
- Tax Summary section — income by source with 1099 flagging ($600+ threshold), deductible expenses by category, quarterly income/expense breakdown table
- Tax data CSV export for any selected year
- Tax-deductible category toggle in Settings (Profile > Budget Categories) — mark categories as deductible for tax reports
- Compare Years section — side-by-side bar chart comparing monthly spending across two years with summary metrics

### Changed
- Report Generator now includes Year-in-Review, Tax Summary, and Compare Years sections below the main charts
- Category management in Settings expanded with "Tax Ded." checkbox column

## [3.6] — Mobile-Friendly Redesign & PWA

### Added
- Progressive Web App (PWA) support — installable on mobile via "Add to Home Screen"
- `manifest.json` with app metadata, theme colors, and icons
- Service worker with network-first caching and offline fallback message
- PWA icons at 192x192 and 512x512
- Mobile quick-entry dialog — compact expense form accessible from Quick Actions
- Quick entry saves directly to budget transactions without page navigation
- Mobile FAB (floating action button) CSS — visible only on screens <768px
- Touch-friendly CSS — minimum 44px button heights on mobile
- Apple mobile web app meta tags for iOS home screen

### Changed
- Sidebar Quick Actions now includes "Quick Entry" button
- All buttons have minimum 44px touch targets on mobile
- Tab controls have increased touch targets on mobile

### Files Added
- `static/manifest.json` — PWA manifest
- `static/service-worker.js` — Basic service worker
- `static/icons/icon-192.png`, `static/icons/icon-512.png` — PWA icons

## [3.5] — Budget Intelligence & Forecasting

### Added
- Budget rollover toggle — unused budget carries forward to next month when enabled
- What-if budget scenarios tab — create, save, and compare alternate budget plans
- Side-by-side comparison chart (current vs scenario) with monthly/annual savings impact
- Seasonal spending pattern detection (requires 6+ months of data)
- Seasonal budget adjustment suggestions based on historical month-over-month patterns
- `budget_scenarios.json` for storing named scenarios

### Changed
- Budget Tracker now has 4 tabs: Track, Analyze, Scenarios, Bills
- Budget setup area shows rollover toggle

## [3.4] — Multi-Account Management

### Added
- Account management in Settings (add, edit balance, set default, delete)
- Account types: checking, savings, credit, cash, investment with type icons
- Account color coding and last-4-digits display
- Account balance widget cards on dashboard
- Account selector when importing CSV in Budget Tracker (tags transactions with account_id)
- Account filter in Report Generator
- `accounts.json` schema in validators.py
- Account balances contribute to net worth calculation

### Changed
- Dashboard shows account balance cards between main widgets and alerts

## [3.3] — Bill Calendar & Payment Reminders

### Added
- Bills tab in Budget Tracker with add, edit, mark paid, delete, and pause/resume
- Monthly bill calendar view (HTML table) with bill names on due days, month navigation
- Upcoming bills list with color-coded urgency (red=overdue, yellow=due soon, green=OK)
- Bill reminder notifications on app startup (3-day warning + overdue alerts)
- Auto-detect bills from transaction history (finds recurring charges on similar days)
- "Bills Due This Week" section on dashboard
- Bill summary metrics (monthly total, annual estimate, auto-pay vs manual count)
- `bills.json` schema in validators.py
- "Bill Reminders" toggle in notification settings
- 8 new tests for bill tracking

### Changed
- Dashboard shows upcoming bill alerts alongside spending alerts

### Files Added
- `tests/test_bills.py` — 8 tests for bill tracking

## [3.2] — Smart Transaction Categorization & Learning

### Added
- Category learning system (`utils/category_learner.py`) — records user corrections and applies them to future imports via fuzzy matching
- Learned categories take priority over keyword matching (learned > custom > built-in)
- Spending anomaly detection — flags categories 50%+ above 3-month average and individual transactions >$500
- Anomaly alerts shown on dashboard with warning cards
- "Income" category added (12 categories total) with auto-detection from payroll/deposit keywords
- Negative amounts with income-like descriptions auto-categorize as Income
- 50+ new merchant keywords across all categories (restaurants, stores, services)
- Category management in Settings (add custom categories, hide categories, view learned rules count)
- "AI" badge in Review & Edit showing learned vs keyword-matched transaction counts
- 10 new tests for category learner (fuzzy matching, learning, retrieval, deletion)

### Changed
- `_categorize()` now checks learned rules first, then custom keywords, then built-in keywords
- Budget templates updated to include Income category
- Applying category edits in Budget Tracker now records corrections for future learning

### Files Added
- `utils/category_learner.py` — Category learning with fuzzy matching
- `tests/test_category_learner.py` — 10 tests

## [3.1] — One-Click Desktop Experience

### Added
- Desktop shortcut installer (`install.py`) — creates a clickable shortcut on Windows, Mac, and Linux
- Background server launcher (`launcher.py`) — starts Streamlit silently, opens browser automatically
- Windows system tray icon with Open, Restart, and Quit menu (via `pystray`)
- Port conflict handling — automatically tries ports 8501-8510 if the default is in use
- App icon (`assets/financekit.ico`) for desktop shortcut and tray
- Splash/loading screen with animated logo on first render
- Friendly error pages for unhandled module errors with retry button and troubleshooting guidance
- Auto-dependency installation on first launch via `launcher.py`
- Hidden console window on Windows (no terminal visible to end user)

### Changed
- `start.bat` and `start.sh` now delegate to `launcher.py` for a cleaner launch experience
- Module errors now log to `financekit.log` with full tracebacks
- `requirements.txt` — added `pystray==0.19.5` for system tray support

### Files Added
- `launcher.py` — Background server launcher with tray icon
- `install.py` — Desktop shortcut installer
- `assets/financekit.ico` — Application icon
- `_launch_silent.bat` / `_launch_hidden.vbs` — Generated by installer for silent Windows launch

## [3.0] — Final Polish, Onboarding Redesign & Relaunch

### Added
- Module selection — enable/disable modules during onboarding and in Settings
- Sidebar and dashboard filter by enabled modules
- Quick Actions row on dashboard (Transaction, Receipt, Report, Goal)
- Recent Activity feed on dashboard (cross-module action log)
- Activity logging utility (utils/activity_log.py)
- @media print CSS for clean browser printing
- Modules tab in Settings for toggling modules on/off
- Re-run onboarding wizard option in Settings
- CHANGELOG.md covering all versions v2.1–v3.0

### Changed
- Redesigned onboarding from 3-step to polished 5-step wizard (Welcome, Profile, Modules, Import, Tour)
- Complete rewrite of README.md, GUIDE.md, GUMROAD_GUIDE.md
- Demo app updated for v3.0 features
- Code quality sweep — unused imports, docstrings, requirements.txt audit

### Fixed
- Version references updated to 3.0 across all files

## [2.9] — Performance, Reliability & Testing

### Added
- Rotating file logger (5MB, 3 backups) in utils/logger.py
- JSON schema validation on every data load (utils/validators.py)
- Data migration framework with versioned migrations (utils/migrations.py)
- API response caching (stocks 5min, crypto 2min, history 1hr)
- Lazy module loading via importlib
- Graceful module degradation (try/except around module render)
- Specific exception handling for API calls (ConnectionError, Timeout, 429)
- pytest test suite with 60 tests across 9 test files
- Logs viewer in Settings (filter by level, download, clear)
- Health check in Settings (Python, packages, data dir, JSON, connectivity, SMTP, migrations)

## [2.8] — Freelance Dashboard Pro & Invoice System

### Added
- 6 tabs: Overview, Clients, Time, Invoices, Recurring, Expenses
- Time tracking with start/stop timer and manual entry
- 3 branded invoice PDF templates (Minimal, Professional, Creative)
- Recurring invoices with auto-generation
- Expense tracking with P&L view
- Client payment reliability scoring
- Invoice settings tab in Settings (company info, tax rate, logo upload)

### Changed
- Complete rewrite of Freelance Dashboard (job_tracker.py)

## [2.7] — Enhanced Portfolio & Subscriptions

### Added
- Manual subscription entry with categories (10 categories)
- Price change detection with history tracking
- Cancel workflow with confirmation and undo
- Usage & Notes tab (Daily/Weekly/Rarely/Never ratings)
- Category donut chart and calendar view
- Cancelled subscriptions tab with total savings

### Changed
- Complete rewrite of Subscription Auditor module

## [2.6] — Authentication & Multi-User

### Added
- Local account authentication (register, login, password hashing with bcrypt)
- Per-user data isolation (data/users/{user_id}/)
- Session management with expiry and "Remember me"
- Password reset with token-based flow
- Google OAuth and GitHub OAuth configuration
- Account management (change password, delete account)
- Auth gate in app.py — login page shown before app access
- Net Worth calculator (assets - liabilities) on dashboard
- Financial Health Score gauge (budget adherence, savings rate, emergency fund, debt ratio, subscription efficiency)
- Net worth trend chart with monthly snapshots

## [2.5] — Notifications & Alerts

### Added
- In-app notification system (create, read, mark read, dedup)
- Notification bell with unread badge in sidebar
- Per-module notification toggles in Settings
- Alert thresholds (budget %, portfolio change %, subscription cost, invoice overdue)
- Email digest (daily/weekly) via SMTP
- Dashboard alert cards from unread notifications
- Grouped notification panel (Today, This Week, Older)

## [2.4] — Dashboard & UX Polish

### Added
- Time-of-day greeting on dashboard
- Quick Import banner (CSV drop zone)
- Module cards with activity indicators
- Insight engine with context-aware tips
- Global search across all modules
- Keyboard shortcuts (0-7, 9, ?)
- Responsive design (tablet and mobile breakpoints)

### Changed
- Dashboard layout with 4-column widget row

## [2.3] — Theme System Overhaul

### Added
- CSS custom properties (--fk-*) for all colors
- Light mode with complete variable set

### Changed
- All inline HTML uses CSS variables instead of hardcoded colors
- Plotly charts use theme-aware colors via chart_config.py

### Fixed
- Theme persistence across page refreshes

## [2.2] — Currency & Formatting

### Added
- Multi-currency support (USD, EUR, GBP, CAD, AUD, JPY)
- Centralized formatting utilities (format_currency, format_date, parse_date)
- Date format preferences (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD)

### Changed
- All modules use centralized currency formatting instead of hardcoded $

## [2.1] — Kickoff & Core Structure

### Added
- Budget Tracker with 11 categories, templates (Student, Freelancer, Family, Professional)
- Goal Tracker with milestone celebrations, progress history
- Receipt Scanner with OCR (Tesseract), camera input, auto-categorization
- Portfolio Tracker with stocks (Yahoo Finance) and crypto (CoinGecko)
- Report Generator with CSV import, auto-detect bank formats
- Freelance Dashboard with client tracking, invoice generation
- Subscription Auditor with fuzzy matching, known subscriptions database
- Settings module with profile, SMTP email, data management
- Dark/light theme with CSS custom properties
- start.bat and start.sh launchers
