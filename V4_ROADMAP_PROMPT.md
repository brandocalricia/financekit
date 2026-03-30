# FinanceKit V4.0 Roadmap Prompt

> Paste this entire file into a new Claude Code chat to continue development from v3.0 to v4.0.
> Work one version at a time. Each version is a focused update: implement, test, commit, push, then move on.

---

## IMPORTANT: Working Directory

The FinanceKit project lives at:
```
C:\Users\bzcni\OneDrive\Desktop\vs code projects\Finance Toolkit
```
This is the root of the git repo (`brandocalricia/financekit`). All paths in this document are relative to this directory. The project already exists with a full v3.0 codebase — do NOT build from scratch. Read the existing files first to understand the current state before making any changes. Start with v3.1.

---

## Project Context

**FinanceKit** is a Streamlit-based personal finance toolkit sold on Gumroad ($29.99 one-time). It runs 100% locally — no cloud, no accounts required (optional auth). The target audience is regular people who want to manage their money, NOT developers. This is critical: every UX decision should assume the user is NOT tech-savvy.

### Tech Stack
- **Python 3.14.3** / **Streamlit 1.45.0** / local JSON file storage in `data/`
- **Plotly 6.0.1** for charts (rendered on canvas, NOT HTML — cannot use CSS variables in Plotly configs; must use Python-side theme helpers)
- **fpdf2** for PDF generation (invoices, reports, guide)
- **CSS custom properties** (`--fk-*`) for dark/light theming across all inline HTML
- **chart_config.py** reads `st.session_state.fk_theme` to return theme-appropriate colors — use `_theme_colors()` and `apply_layout()` for all Plotly charts
- **Per-user data isolation**: `set_user_context(user_id)` switches `_path()` to `data/users/{user_id}/`
- **Auth gate** in app.py: if auth is enabled, login page shown before app access
- **`@st.cache_data`** decorators on API calls with TTLs (stocks 5min, crypto 2min, history 1hr)
- **Lazy module loading** via `importlib.import_module()` in app.py with try/except for graceful degradation
- **JSON schema validation** on every `load_json()` call via `validate_and_repair()`
- **Data migration framework** with versioned, idempotent migrations
- **Rotating file logger** (5MB, 3 backups) — `utils/logger.py`
- **pytest test suite**: 60 tests across 9 test files, monkeypatched temp directories

### Current File Structure (v3.0)
```
FinanceKit/
├── app.py                          # Main Streamlit app (1463 lines) — dashboard, routing, auth gate, onboarding
├── start.bat                       # Windows launcher (one-click)
├── start.sh                        # Mac/Linux launcher
├── version.txt                     # Contains "3.0"
├── requirements.txt                # 15 pinned dependencies with comments
├── pytest.ini                      # testpaths=tests, addopts=-v --tb=short
├── generate_guide_pdf.py           # Generates sample_data/FinanceKit_User_Guide.pdf
├── README.md                       # Full product README
├── GUIDE.md                        # Comprehensive user guide (15 sections)
├── GUMROAD_GUIDE.md                # Gumroad listing copy and setup guide
├── CHANGELOG.md                    # Version history v2.1–v3.0
├── V3_ROADMAP_PROMPT.md            # Previous roadmap (v2.1–v3.0)
├── V4_ROADMAP_PROMPT.md            # THIS FILE
│
├── modules/                        # All 7 modules + settings
│   ├── __init__.py
│   ├── budget_tracker.py           # 823 lines — 11 categories, templates, CSV import, analytics
│   ├── goal_tracker.py             # 328 lines — goals, milestones, projections, history charts
│   ├── job_tracker.py              # 1313 lines — freelance: clients, time tracking, invoices, recurring, expenses, P&L
│   ├── portfolio_tracker.py        # 666 lines — stocks, crypto, watchlist, alerts, sector mapping
│   ├── receipt_scanner.py          # 288 lines — PDF/photo OCR, auto-categorize, export
│   ├── report_generator.py         # 491 lines — CSV import, auto-detect banks, PDF reports, email
│   ├── settings.py                 # 1046 lines — 8 tabs: Profile, Modules, Email, Invoice, Auth, Notifications, Data, About
│   └── subscription_auditor.py     # 869 lines — fuzzy matching, manual entry, cancel workflow, usage ratings
│
├── utils/                          # Shared utilities (17 files)
│   ├── __init__.py
│   ├── activity_log.py             # 98 lines — cross-module activity feed
│   ├── auth.py                     # 346 lines — register, login, bcrypt hashing, OAuth config, sessions
│   ├── chart_config.py             # 71 lines — theme-aware Plotly helpers
│   ├── data_persistence.py         # 147 lines — load/save JSON, atomic writes, backups, per-user isolation
│   ├── finance_api.py              # 158 lines — Yahoo Finance + CoinGecko with caching
│   ├── formatting.py               # 118 lines — format_currency, format_date, parse_date, currency symbol
│   ├── fuzzy_matcher.py            # 42 lines — normalize + group similar strings (rapidfuzz)
│   ├── insights.py                 # 162 lines — transaction-based spending insights
│   ├── invoice_templates.py        # 613 lines — 3 branded PDF templates (Minimal, Professional, Creative)
│   ├── logger.py                   # 67 lines — rotating file logger
│   ├── migrations.py               # 155 lines — versioned data migrations
│   ├── notifications.py            # 297 lines — create, read, mark, dedup, email digest
│   ├── pdf_parser.py               # 123 lines — extract text/date/vendor/total from PDFs
│   ├── report_builder.py           # 199 lines — ReportPDF class for styled PDF generation
│   ├── search.py                   # 139 lines — global search across all modules
│   ├── ui_helpers.py               # 40 lines — render_module_header, styled_metric_card, render_empty_state
│   └── validators.py               # 186 lines — JSON schema validation and auto-repair
│
├── tests/                          # 60 tests, 9 test files
│   ├── __init__.py
│   ├── conftest.py                 # fixtures: temp_data_dir, sample_settings, sample_goals, etc.
│   ├── test_auth.py                # 5 tests
│   ├── test_budget_tracker.py      # 4 tests
│   ├── test_data_persistence.py    # 8 tests
│   ├── test_finance_api.py         # 6 tests
│   ├── test_formatting.py          # 11 tests
│   ├── test_fuzzy_matcher.py       # 7 tests
│   ├── test_insights.py            # 2 tests
│   ├── test_notifications.py       # 7 tests
│   └── test_validators.py          # 8 tests
│
├── demo/                           # Streamlit Cloud demo (marketing landing page)
│   ├── .streamlit/config.toml
│   ├── app_demo.py                 # Free demo with 2 unlocked modules
│   └── requirements.txt            # streamlit + pandas only
│
├── assets/                         # Gumroad marketing images (HTML rendered to screenshots)
│   ├── gumroad_thumbnail.html
│   └── gumroad_feature_1..5.html
│
├── sample_data/                    # Test files for demo/development
│   ├── bank_statement.csv
│   ├── receipt_starbucks.pdf
│   ├── receipt_walmart.pdf
│   ├── transactions.csv
│   └── FinanceKit_User_Guide.pdf
│
├── data/                           # Auto-created JSON storage (gitignored)
│   └── backups/
│
└── .streamlit/
    └── config.toml                 # Theme: indigo primary, dark bg
```

### Key Architecture Patterns

1. **Theme system**: CSS variables `--fk-*` defined in app.py, Plotly uses `_theme_colors()` from chart_config.py
2. **Module rendering**: Each module exports `render()`. app.py uses `importlib.import_module(path).render()` with try/except
3. **Data files**: All JSON in `data/`. `load_json()` auto-validates via `validate_and_repair()`. `save_json()` does atomic write + auto-backup
4. **Onboarding**: 5-step `@st.dialog` wizard. Saves `onboarding_complete`, `enabled_modules` to settings.json
5. **Navigation**: Sidebar radio with `NAV_OPTIONS` filtered by `enabled_modules`. `nav_target` session_state for programmatic navigation
6. **Notifications**: `create_notification(type, module, title, message)` → stored in `notifications.json`, shown in sidebar bell
7. **Activity log**: `log_activity(action, module, description)` → stored in `activity_log.json`, shown on dashboard
8. **Auth**: Optional. When enabled, `_show_login_page()` renders before anything else. `set_user_context(user_id)` isolates data

### Version History (completed)
- **v2.1**: Core 7 modules, settings, dark/light theme, launchers
- **v2.2**: Multi-currency, formatting utilities
- **v2.3**: CSS variables overhaul, theme-aware Plotly
- **v2.4**: Dashboard redesign, search, keyboard shortcuts, responsive
- **v2.5**: Notification system, alerts, email digest
- **v2.6**: Authentication, multi-user, net worth, financial health score
- **v2.7**: Subscription auditor rewrite (categories, cancel workflow, usage ratings)
- **v2.8**: Freelance dashboard rewrite (time tracking, 3 invoice templates, recurring invoices, P&L)
- **v2.9**: Logger, validators, migrations, API caching, lazy loading, 60 tests, health check
- **v3.0**: 5-step onboarding, module selection, activity feed, print CSS, full documentation rewrite

### Important Rules
- **One version at a time.** Implement, compile-check, run all tests, commit with descriptive message, push to remote.
- **Plotly charts**: NEVER use CSS variables. Always use `_theme_colors()` and `apply_layout()` from chart_config.py.
- **Currency**: NEVER hardcode `$`. Always use `format_currency()`, `format_currency_int()`, or `get_currency_symbol()`.
- **Colors in HTML**: ALWAYS use `var(--fk-*)` CSS variables. Never hardcode hex colors in inline HTML.
- **Data access**: ALWAYS use `load_json()` / `save_json()` from data_persistence.py. Never direct file I/O for data files.
- **Module headers**: Use `render_module_header(icon, title, description)` from ui_helpers.py.
- **Notifications**: Use `create_notification(type, module, title, message)` for user-facing alerts.
- **Activity logging**: Use `log_activity(action, module, description)` for dashboard feed items.
- **Tests**: Run `pytest tests/ -v` after every version. All tests must pass before committing.
- **Version**: Update `version.txt` for each version. Update fallback strings in app.py and settings.py.
- **Git**: Commit message format: `FinanceKit vX.X — Short Description`. Push after each version.
- **No emojis** in code comments. Emojis are fine in user-facing UI strings only.

---

## V3.1 — One-Click Desktop Experience

**Theme:** The #1 complaint is that launching FinanceKit requires opening a terminal, running commands, and navigating to localhost. A paying customer should double-click an icon and see the app. Solve this completely.

### Tasks

#### 1. Desktop shortcut installer script
- Create `install.py` — a standalone script that:
  - Checks Python is installed (clear error if not: "Please install Python from python.org")
  - Installs dependencies from requirements.txt (shows progress)
  - Creates a desktop shortcut:
    - **Windows**: Creates a `.lnk` shortcut on the Desktop using `winshell` or `pythoncom`, OR creates a `.bat` wrapper with a nice icon. The shortcut should run the app silently (no terminal window visible to user)
    - **Mac**: Creates a `.command` file on Desktop with executable permissions
    - **Linux**: Creates a `.desktop` file in `~/.local/share/applications/`
  - The shortcut name: "FinanceKit"
  - Icon: Use a bundled `.ico` file (create `assets/financekit.ico` — a simple coin/wallet icon generated as a minimal valid ICO)
  - After creating shortcut, prints success message: "FinanceKit installed! Double-click the FinanceKit icon on your desktop to launch."
- The installer should be safe to run multiple times (idempotent)

#### 2. Background server launcher
- Create `launcher.py` — replaces direct `streamlit run` for end users:
  - Starts the Streamlit server as a subprocess (hidden console on Windows using `CREATE_NO_WINDOW`)
  - Waits for the server to be ready (polls `http://localhost:8501` until it responds, timeout 30s)
  - Opens the default browser to `http://localhost:8501`
  - Keeps running in the background (on Windows: system tray icon using `pystray`; on Mac/Linux: just waits for Ctrl+C)
  - **Windows system tray**: Shows a small tray icon with right-click menu:
    - "Open FinanceKit" → opens browser
    - "Restart Server" → kills and restarts streamlit
    - "Quit" → stops server and exits
  - Handles port conflicts: if 8501 is in use, tries 8502, 8503, etc. up to 8510
  - Clean shutdown: kills the Streamlit subprocess on exit
- Add `pystray` and `Pillow` to requirements.txt (Pillow already there, pystray is lightweight)

#### 3. First-run experience improvements
- Update `start.bat` to call `launcher.py` instead of `streamlit run` directly
- Update `start.sh` to call `launcher.py`
- Add a loading message: "Starting FinanceKit... (this may take a few seconds on first launch)"
- If dependencies aren't installed, auto-install them before launching (integrate the install step)

#### 4. Splash/loading screen in app
- In app.py, add a loading state that shows while modules initialize:
  - A centered FinanceKit logo with a subtle CSS animation (pulse/fade)
  - "Loading your financial toolkit..." text
  - Disappears after 1-2 seconds or when content is ready
  - Uses `st.empty()` placeholder that gets replaced

#### 5. User-friendly error pages
- Wrap the entire app.py routing in a top-level try/except
- On unhandled errors, show a friendly error page:
  - "Something went wrong" heading
  - Collapsible technical details
  - "Try refreshing the page" button
  - "If this keeps happening, try running the Health Check in Settings" guidance
  - Log the error to financekit.log

### Files to create
- `install.py` — Desktop shortcut installer
- `launcher.py` — Background server launcher with tray icon
- `assets/financekit.ico` — App icon (minimal valid ICO file, or generate from emoji)

### Files to modify
- `start.bat` — Call launcher.py
- `start.sh` — Call launcher.py
- `requirements.txt` — Add pystray
- `app.py` — Add splash screen, improve error handling
- `version.txt` → 3.1
- `CHANGELOG.md` — Add v3.1 entry

### Acceptance criteria
- [ ] Running `python install.py` creates a working desktop shortcut on Windows
- [ ] Double-clicking the shortcut launches FinanceKit in the browser with no visible terminal
- [ ] System tray icon appears on Windows with Open/Restart/Quit menu
- [ ] Port conflict is handled gracefully (tries next port)
- [ ] Browser opens automatically when server is ready
- [ ] Splash screen shows briefly on app load
- [ ] Unhandled errors show friendly error page instead of crashing
- [ ] All 60 tests still pass

---

## V3.2 — Smart Transaction Categorization & Learning

**Theme:** The auto-categorizer uses hardcoded keyword lists. It should learn from user corrections and get smarter over time. Also add spending anomaly detection.

### Tasks

#### 1. Category learning system
- Create `utils/category_learner.py`:
  - `learn_from_correction(description: str, old_category: str, new_category: str)` — records that this description should map to new_category
  - `get_learned_category(description: str) -> str | None` — checks if we've learned a category for this description pattern
  - Store learned mappings in `data/category_rules.json`: `[{pattern: str, category: str, confidence: float, times_used: int}]`
  - Use fuzzy matching (rapidfuzz) to match new descriptions against learned patterns (threshold 85)
  - Higher `times_used` = higher confidence = takes priority over keyword matching
- Integrate into `budget_tracker.py`:
  - When auto-categorizing transactions, check learned rules FIRST, then fall back to keyword matching
  - When user edits a category in the "Review & Edit" section and clicks Apply, call `learn_from_correction()`
  - Show a small "AI" badge next to categories that were learned vs keyword-matched

#### 2. Spending anomaly detection
- In `utils/insights.py`, add `detect_anomalies() -> list[dict]`:
  - Compare each category's spending this month vs. the rolling 3-month average
  - Flag categories where spending is 50%+ above average as "unusual"
  - Flag individual transactions above $500 or 3x the average transaction in that category
  - Return `[{type: "anomaly", category, current_amount, average_amount, description}]`
- Show anomalies on the dashboard as warning-type alert cards
- Create notifications for anomalies: "Spending Alert: Your Entertainment spending is 65% above your 3-month average"

#### 3. Smart merchant recognition
- Enhance the `CATEGORY_MAP` in budget_tracker.py:
  - Add 50+ more merchant keywords across all categories
  - Add common bill descriptions: "autopay", "recurring", "monthly fee", "annual fee"
  - Add payroll patterns: "payroll", "direct deposit", "salary", "wages" → "Income" (new category)
  - Handle negative amounts as income detection
- Add an "Income" category to `DEFAULT_CATEGORIES` (12 total now)

#### 4. Category management in Settings
- In `settings.py`, add a "Categories" section to the Profile tab:
  - Show all categories with edit/rename capability
  - Allow adding custom categories (stored in settings.json `custom_categories`)
  - Allow hiding categories (soft delete — transactions keep their category but it's hidden from dropdowns)
  - Show learned rules count per category

### Files to create
- `utils/category_learner.py`
- `tests/test_category_learner.py` — Test learning, retrieval, fuzzy matching

### Files to modify
- `utils/insights.py` — Add anomaly detection
- `modules/budget_tracker.py` — Integrate learning, add Income category
- `modules/settings.py` — Add category management
- `app.py` — Show anomaly alerts on dashboard
- `version.txt` → 3.2
- `CHANGELOG.md`

### Acceptance criteria
- [ ] User category corrections are saved and applied to future imports
- [ ] Learned categories take priority over keyword matching
- [ ] Fuzzy matching catches variations of the same merchant (e.g., "STARBUCKS #12345" matches "Starbucks")
- [ ] Spending anomalies detected and shown on dashboard
- [ ] Income category added and auto-detected from positive amounts
- [ ] Custom categories can be created in Settings
- [ ] New tests pass

---

## V3.3 — Bill Calendar & Payment Reminders

**Theme:** Users need to see upcoming bills and due dates at a glance. Add a visual calendar and reminder system.

### Tasks

#### 1. Bills data model
- Add `data/bills.json` schema: `[{id, name, amount, due_day, frequency, category, auto_pay, last_paid, notes, active}]`
  - `due_day`: 1-31 (day of month the bill is due)
  - `frequency`: "monthly", "quarterly", "annually", "weekly"
  - `auto_pay`: boolean — if true, mark as "will be auto-charged"
  - Add schema to `utils/validators.py`

#### 2. Bill Tracker tab in Budget Tracker
- Add a "Bills" tab to `budget_tracker.py` (5th tab alongside existing tabs):
  - **Add Bill form**: Name, amount, due day, frequency, category (from budget categories), auto-pay toggle, notes
  - **Upcoming Bills list**: Bills due in the next 30 days, sorted by date, with:
    - Color coding: red if overdue, yellow if due in 3 days, green otherwise
    - "Mark Paid" button that records `last_paid` date
    - Total amount due this month
  - **Bill Calendar**: A monthly calendar view (HTML table) showing which days have bills due
    - Each day cell shows bill names and amounts
    - Current day highlighted
    - Navigate between months with prev/next buttons
  - **Summary metrics**: Total monthly bills, total annual bills, auto-pay vs manual count

#### 3. Bill reminders via notifications
- In `app.py` startup section, add bill checking:
  - On each app launch, check for bills due in the next 3 days
  - Create notifications: "Bill Due: Netflix ($15.99) is due in 2 days"
  - Check for overdue bills (past due_day, not marked paid this month): "Overdue: Electric bill ($120) was due 5 days ago"
  - Respect notification preferences (use existing per-module toggles — add "bills" module key)

#### 4. Auto-detect bills from transaction history
- Add `detect_bills_from_transactions(transactions: list) -> list[dict]` to `utils/insights.py`:
  - Analyze transaction history to find charges that occur on roughly the same day each month
  - Suggest these as bills: "We detected Netflix charging ~$15.99 around the 15th of each month. Add as a bill?"
  - Show suggestions in the Bills tab with an "Add" button for each
- Also cross-reference with subscription auditor data — any "Keep" subscription could be auto-suggested as a bill

### Files to create
- `tests/test_bills.py` — Test bill creation, due date calculation, overdue detection

### Files to modify
- `modules/budget_tracker.py` — Add Bills tab
- `utils/validators.py` — Add bills.json schema
- `utils/insights.py` — Add bill detection from transactions
- `app.py` — Add bill reminder checks at startup
- `modules/settings.py` — Add "bills" to notification module toggles
- `version.txt` → 3.3
- `CHANGELOG.md`

### Acceptance criteria
- [ ] Bills can be added, edited, marked paid, deleted
- [ ] Calendar view shows bills on correct days with color coding
- [ ] Overdue bills generate warning notifications
- [ ] Upcoming bills (3 days) generate info notifications
- [ ] Auto-detection suggests bills from transaction patterns
- [ ] Dashboard shows "Bills due this week" summary
- [ ] All tests pass

---

## V3.4 — Multi-Account Management

**Theme:** Most people have multiple bank accounts and credit cards. Let them track balances and view spending per-account.

### Tasks

#### 1. Account data model
- Add `data/accounts.json` schema:
  ```
  [{
    id, name, type (checking/savings/credit/cash/investment),
    institution, last_four_digits, balance, color,
    is_default, created_at
  }]
  ```
- Add schema to validators.py

#### 2. Account Manager in Settings
- Add "Accounts" section to Settings Data Management tab:
  - **Add Account form**: Name (e.g., "Chase Checking"), type dropdown, institution, last 4 digits, current balance, color picker
  - **Account list**: Show all accounts with balance, type icon, edit/delete
  - **Set Default**: One account can be marked as default (used when no account specified)

#### 3. Account selection in modules
- **Budget Tracker**: Add account selector dropdown when importing CSV. Transactions tagged with account_id. Filter transactions by account
- **Report Generator**: Add account filter to report — generate report for one account or all accounts
- **Receipt Scanner**: Add optional account selector when scanning receipts

#### 4. Account balances on Dashboard
- Add "Accounts" widget row on dashboard (between existing widgets and net worth):
  - Show each account as a compact card: name, type icon, balance, last 4 digits
  - Color-coded by account color
  - Click to filter dashboard to that account's data
- Include account balances in Net Worth calculation (replaces manual cash balance input)

#### 5. Transfer tracking
- In Budget Tracker, add "Transfer" as a special transaction type:
  - From Account → To Account, amount, date
  - Transfers are excluded from spending totals (they're not income or expense)
  - Show transfers in a separate "Transfers" section

### Files to modify
- `utils/validators.py` — Account schema
- `modules/settings.py` — Account management UI
- `modules/budget_tracker.py` — Account filter, transfer tracking
- `modules/report_generator.py` — Account filter
- `modules/receipt_scanner.py` — Optional account tag
- `app.py` — Account balance widgets on dashboard
- `version.txt` → 3.4
- `CHANGELOG.md`

### Acceptance criteria
- [ ] Accounts can be created with name, type, institution, balance, color
- [ ] Transactions can be tagged to an account
- [ ] Dashboard shows account balance cards
- [ ] Reports can be filtered by account
- [ ] Transfers between accounts tracked separately (not counted as spending)
- [ ] Account balances included in net worth calculation
- [ ] All tests pass

---

## V3.5 — Budget Intelligence & Forecasting

**Theme:** Go beyond simple budget tracking. Add rollover budgets, spending forecasts, and "what-if" scenarios.

### Tasks

#### 1. Budget rollover
- In `budget_tracker.py`, add rollover mode:
  - When enabled in Settings, unused budget from the previous month carries forward
  - Example: $500 grocery budget, spent $400 → $100 rolls into next month → next month budget is $600
  - Track rollover amounts per category in `budgets.json`
  - Show rollover amounts visually: "Base: $500 + Rollover: $100 = Total: $600"
  - Toggle in budget settings: "Enable budget rollover" (default: off)

#### 2. Spending forecast
- Add "Forecast" section to the Analytics tab in budget_tracker.py:
  - Based on current month's spending pace + historical patterns, project end-of-month spending per category
  - Show: "At your current pace, you'll spend $X by month end (budget: $Y)"
  - Visual: projected spending line on the budget bar (dashed line beyond actual spending)
  - If projected to go over: red warning with estimate of how much over

#### 3. What-if budget scenarios
- Add "Scenarios" tab to budget_tracker.py:
  - Let user create named scenarios: "Save More", "Cut Dining Out", "Freelancer Budget"
  - Each scenario is a copy of current budgets with modified amounts
  - Side-by-side comparison chart: current vs scenario
  - Show impact: "This scenario saves $X/month ($Y/year)"
  - Save scenarios in `data/budget_scenarios.json`

#### 4. Seasonal budget adjustments
- Detect seasonal patterns from historical data:
  - If user has 6+ months of data, analyze month-over-month patterns
  - Suggest seasonal adjustments: "Your Entertainment spending tends to be 30% higher in December. Consider budgeting $X instead of $Y."
  - Show seasonal pattern chart: average spending per category per month (12-month view)

### Files to modify
- `modules/budget_tracker.py` — Rollover, forecast, scenarios, seasonal
- `utils/validators.py` — Budget scenarios schema
- `modules/settings.py` — Rollover toggle
- `version.txt` → 3.5
- `CHANGELOG.md`

### Acceptance criteria
- [ ] Budget rollover carries unused amounts to next month when enabled
- [ ] Spending forecast shows projected end-of-month totals
- [ ] Over-budget projections show warning with estimated overage
- [ ] What-if scenarios can be created, compared, and saved
- [ ] Seasonal patterns detected and shown when sufficient data exists
- [ ] All tests pass

---

## V3.6 — Mobile-Friendly Redesign & PWA

**Theme:** Many users want to quickly log expenses from their phone. Make FinanceKit work beautifully on mobile and installable as a PWA.

### Tasks

#### 1. Progressive Web App (PWA) support
- Create `static/manifest.json` with app metadata:
  - `name`: "FinanceKit", `short_name`: "FinanceKit", `start_url`: "/", `display`: "standalone"
  - `theme_color`: "#6366f1", `background_color`: "#0f1117"
  - Icons at 192x192 and 512x512 (generate from logo)
- Create `static/service-worker.js` — basic service worker for:
  - Caching the app shell (CSS, fonts) for faster load
  - Showing "You're offline" message when no connection (NOT full offline mode — just graceful degradation)
- Inject the manifest link and service worker registration into app.py via `st.markdown()` in `<head>`
- Create `static/` directory with PWA assets

#### 2. Mobile quick-entry mode
- Add a "Quick Entry" floating button on mobile (visible only on small screens via CSS `@media`):
  - Opens a compact form overlay:
    - Amount (large number input)
    - Category (select from favorites / recent)
    - Description (optional, short text)
    - Date (defaults to today)
    - "Save" button
  - Saves directly to budget_transactions.json
  - Shows toast confirmation
  - No page navigation required — stays on current page after saving
- Implement as a `@st.dialog` that can be triggered from any page

#### 3. Mobile-optimized layouts
- Audit and improve all module layouts for mobile screens (<768px):
  - **Budget Tracker**: Stack progress bars vertically, larger touch targets
  - **Dashboard**: Single-column widget layout, swipeable module cards
  - **Goal Tracker**: Stack goal cards vertically, larger quick-add buttons ($50, $100, $250, $500)
  - **Receipt Scanner**: Full-width camera button, simplified upload flow
  - **Charts**: Reduce Plotly chart heights on mobile, hide legends on small charts
- Add CSS: `@media (max-width: 768px)` rules for all module-specific components
- Ensure all forms have appropriate `autocomplete` attributes for mobile keyboards

#### 4. Touch-friendly improvements
- Increase all button sizes to minimum 44x44px (Apple HIG minimum)
- Add hover states that also work as active/pressed states on mobile
- Ensure sidebar collapses properly on mobile (already partially done)
- Add swipe gestures hint for sidebar on mobile

### Files to create
- `static/manifest.json`
- `static/service-worker.js`
- `static/icons/` — PWA icons (192x192, 512x512)

### Files to modify
- `app.py` — Inject PWA manifest, add quick-entry dialog, mobile CSS
- `modules/budget_tracker.py` — Mobile layout improvements
- `modules/goal_tracker.py` — Mobile layout
- All other modules — responsive audit
- `version.txt` → 3.6
- `CHANGELOG.md`

### Acceptance criteria
- [ ] App can be "installed" as PWA on mobile Chrome/Safari (Add to Home Screen)
- [ ] Quick-entry button visible on mobile, opens compact expense form
- [ ] Quick entry saves transaction without page navigation
- [ ] All module layouts work well on 375px wide screens
- [ ] Touch targets are minimum 44x44px
- [ ] Charts resize appropriately on mobile
- [ ] All tests pass

---

## V3.7 — Year-in-Review & Tax Summary Reports

**Theme:** At the end of the year, users want to see their full financial picture. Add annual review and tax-relevant summaries.

### Tasks

#### 1. Year-in-Review generator
- Add "Year in Review" tab to Report Generator:
  - Select a year from dropdown (defaults to current year)
  - Generates a comprehensive annual summary:
    - Total income vs total expenses
    - Net savings for the year
    - Top 5 spending categories with year totals
    - Month-by-month spending trend chart
    - Category breakdown donut chart (annual)
    - Highest spending month, lowest spending month
    - Goal achievements during the year
    - Number of invoices generated (freelance)
    - Subscription costs for the year
  - "Generate Year-in-Review PDF" button — beautifully formatted PDF with all charts
  - The PDF should have a polished title page: "2026 Financial Year in Review — [User Name]"

#### 2. Tax summary report
- Add "Tax Summary" section to Year-in-Review tab:
  - **Income summary**: Total freelance income, categorized by client
  - **Deductible expenses**: Filter expenses by tax-deductible categories (user can tag categories as deductible in Settings)
  - **Quarterly breakdown**: Income and expenses by Q1/Q2/Q3/Q4
  - **1099 data**: If freelance income > $600 from any single client, flag it
  - Disclaimer: "This is not tax advice. Consult a tax professional."
  - "Export Tax Summary (CSV)" — exports income and deductible expenses as a CSV suitable for importing into TurboTax or giving to an accountant

#### 3. Tax-deductible category tagging
- In Settings Categories section, add a "Tax Deductible" toggle per category
- Pre-tag: Health, Business Expenses (new subcategory) as deductible
- These tags flow into the Tax Summary report

#### 4. Year-over-year comparison
- Add "Compare Years" section in Report Generator:
  - Select two years to compare
  - Side-by-side bar chart: spending by category, year A vs year B
  - Key metrics compared: total spending, savings rate, top category shifts
  - "You spent 15% less on Dining Out in 2026 vs 2025" type insights

### Files to modify
- `modules/report_generator.py` — Year-in-Review tab, tax summary, YoY comparison
- `utils/report_builder.py` — Year-in-Review PDF template
- `modules/settings.py` — Tax-deductible category toggle
- `version.txt` → 3.7
- `CHANGELOG.md`

### Acceptance criteria
- [ ] Year-in-Review generates comprehensive annual summary with charts
- [ ] Year-in-Review PDF is polished and professional
- [ ] Tax summary shows income by client and deductible expenses
- [ ] Quarterly breakdown available
- [ ] 1099 threshold flagging works
- [ ] Year-over-year comparison shows meaningful differences
- [ ] Categories can be tagged as tax-deductible in Settings
- [ ] All tests pass

---

## V3.8 — Shared Household Finance

**Theme:** Couples and families managing money together need shared budgets, split expenses, and family dashboards.

### Tasks

#### 1. Household mode
- In Settings, add "Household" section:
  - "Enable Household Mode" toggle
  - When enabled, create a `data/household.json`: `{name, members: [user_id1, user_id2, ...], shared_budgets: bool, shared_goals: bool}`
  - Invite members: generate an invite code that another logged-in user can enter to join the household
  - Each household member can see shared data alongside their personal data

#### 2. Split expense tracking
- In Budget Tracker, add "Split Expense" option when adding a transaction:
  - Select "Split with..." → choose household members
  - Split method: "Even", "By percentage", "By amount", "One person paid (owe them back)"
  - Track who owes whom: `data/splits.json`
  - Show "You owe" / "Owed to you" summary on dashboard
  - "Settle up" button that marks a split as resolved

#### 3. Shared goals
- In Goal Tracker, add "Shared Goal" toggle when creating a goal:
  - Shared goals are visible to all household members
  - Each member's contributions are tracked separately
  - Show: "You: $500 · Partner: $300 · Total: $800 / $5,000"
  - Both members can add funds

#### 4. Family dashboard view
- On Dashboard, when household mode is enabled:
  - Add a "Household" tab alongside the personal dashboard
  - Shows: combined net worth, combined spending, shared goals progress
  - Per-member spending comparison (bar chart)
  - Combined bill calendar

### Files to create
- `utils/household.py` — Household management functions
- `tests/test_household.py`

### Files to modify
- `modules/settings.py` — Household settings
- `modules/budget_tracker.py` — Split expenses
- `modules/goal_tracker.py` — Shared goals
- `app.py` — Household dashboard tab
- `utils/validators.py` — Household and splits schemas
- `version.txt` → 3.8
- `CHANGELOG.md`

### Acceptance criteria
- [ ] Household mode can be enabled in Settings
- [ ] Invite codes work for adding household members
- [ ] Expenses can be split evenly, by percentage, or by amount
- [ ] "You owe" / "Owed to you" balances tracked correctly
- [ ] Shared goals show per-member contributions
- [ ] Household dashboard shows combined financial picture
- [ ] All tests pass

---

## V3.9 — Import Ecosystem & Smart Integrations

**Theme:** Make it dead simple to get data into FinanceKit from other tools and formats.

### Tasks

#### 1. YNAB import
- Create `utils/importers.py` with importer classes:
  - `YNABImporter`: Parse YNAB export format (CSV with columns: Account, Flag, Date, Payee, Category Group/Category, Memo, Outflow, Inflow)
  - Map YNAB categories to FinanceKit categories (fuzzy match + user confirmation)
  - Import transactions AND budget amounts
  - Show preview before importing: "Found 450 transactions, 15 categories. Import?"

#### 2. Mint/Monarch import
- `MintImporter`: Parse Mint CSV export (Date, Description, Original Description, Amount, Transaction Type, Category, Account Name, Labels, Notes)
- `MonarchImporter`: Parse Monarch Money CSV export
- Map categories to FinanceKit categories with fuzzy matching

#### 3. OFX/QFX bank file support
- Add `ofxparse` to requirements.txt
- `OFXImporter`: Parse OFX/QFX files (standard bank download format)
  - Extract account info, transactions
  - Auto-detect account type
  - Map to FinanceKit transaction format

#### 4. Import wizard in Report Generator
- Replace the current CSV upload with a smarter import wizard:
  - Step 1: Upload file (CSV, XLS, XLSX, OFX, QFX)
  - Step 2: Auto-detect format (FinanceKit guesses: "This looks like a YNAB export" / "Chase bank statement" / "Unknown CSV")
  - Step 3: Column mapping (auto-mapped, user can override)
  - Step 4: Category mapping (show suggested mappings, user confirms)
  - Step 5: Preview + Import
- Keep backward compatibility with existing CSV import flow

#### 5. Folder watcher for auto-import
- In Settings, add "Auto-Import" section:
  - Set a watch folder path (e.g., `Downloads/`)
  - When a CSV matching bank statement patterns appears in the folder, show a notification: "New bank statement detected: chase_statement_march.csv — Import?"
  - Uses `watchdog` library for file system monitoring (optional — only if user enables it)
  - On app startup, check the watch folder for new files since last check
- Add `watchdog` as optional dependency (graceful import with try/except)

### Files to create
- `utils/importers.py` — YNAB, Mint, Monarch, OFX importers
- `tests/test_importers.py`

### Files to modify
- `modules/report_generator.py` — Import wizard
- `modules/settings.py` — Auto-import folder setting
- `requirements.txt` — Add ofxparse (pin version)
- `app.py` — Check watch folder on startup
- `version.txt` → 3.9
- `CHANGELOG.md`

### Acceptance criteria
- [ ] YNAB CSV export imports correctly with category mapping
- [ ] Mint CSV export imports correctly
- [ ] OFX/QFX files parse and import transactions
- [ ] Import wizard auto-detects file format
- [ ] Category mapping shows suggestions with user confirmation
- [ ] Watch folder detects new files and offers to import
- [ ] All existing CSV import flows still work
- [ ] All tests pass

---

## V4.0 — Final Polish, Performance & Relaunch

**Theme:** The app should feel fast, beautiful, and complete. Comprehensive polish pass, performance optimization, expanded test coverage, and updated marketing.

### Tasks

#### 1. Performance optimization
- **Startup time**: Profile app startup, optimize imports (lazy-load heavy modules)
- **Data loading**: Add in-memory caching for frequently accessed data files (settings, budgets)
- **Chart rendering**: Pre-compute chart data, cache Plotly figures where possible
- **Session state cleanup**: Audit all session_state usage, remove stale keys
- **Asset loading**: Minimize CSS injection, combine CSS blocks where possible

#### 2. UI polish pass
- **Consistent spacing**: Audit all modules for consistent margins, padding, spacing between sections
- **Empty states**: Every module should have a beautiful empty state (icon + message + action button) when no data exists. Audit and improve existing ones
- **Loading states**: Add `st.spinner()` or skeleton loading to all data-fetching operations
- **Transition smoothness**: Ensure theme toggle, navigation, and form submissions feel smooth
- **Form validation**: Add inline validation feedback (red borders, helper text) to all forms

#### 3. Expanded test suite
- Target: 100+ tests (currently 60)
- Add tests for:
  - `test_activity_log.py` — log_activity, get_recent, format_activity
  - `test_category_learner.py` — learning, retrieval, fuzzy matching (if not already added in v3.2)
  - `test_report_builder.py` — PDF generation, stat lines, tables
  - `test_importers.py` — All import formats (if not already added in v3.9)
  - `test_household.py` — Split expenses, shared goals (if not already added in v3.8)
  - `test_bills.py` — Bill tracking, due dates, overdue detection (if not already added in v3.3)
  - `test_launcher.py` — Port finding, server health check
  - `test_migrations.py` — All migration paths
  - Integration tests: test full workflows (create budget → import CSV → check analytics)

#### 4. Complete documentation update
- **README.md**: Update with all v3.1–v4.0 features
- **GUIDE.md**: Add sections for: Desktop App, Bill Calendar, Multi-Account, Budget Forecasting, Year-in-Review, Household Mode, Import Wizard, PWA
- **GUMROAD_GUIDE.md**: Update feature list and comparison table
- **CHANGELOG.md**: Add v3.1–v4.0 entries
- **generate_guide_pdf.py**: Update to include new modules/features

#### 5. Demo app update
- Update `demo/app_demo.py` with v4.0 features:
  - Show desktop app installation preview
  - Show bill calendar preview
  - Show Year-in-Review preview
  - Show household mode preview
  - Update comparison table with all new features
  - Update FAQ with new questions
  - Update version to 4.0

#### 6. Marketing assets
- Update `assets/gumroad_thumbnail.html` — change version badge to v4.0
- Create new feature showcase HTML files for: desktop app, bill calendar, year-in-review, import wizard

#### 7. Code quality final sweep
- Run through EVERY Python file:
  - No unused imports
  - No commented-out code blocks
  - No TODO/FIXME/HACK comments
  - Consistent naming conventions
  - Docstrings on all public functions
  - No hardcoded colors (all CSS variables)
  - No hardcoded currency symbols (all formatting utilities)
- **requirements.txt** — verify all pins, add comments for new dependencies
- **start.bat / start.sh** — verify they work with the new launcher

#### 8. Version finalization
- Update `version.txt` to `4.0`
- Verify version shows correctly in: app sidebar, app footer, Settings About page, demo app, README, tray icon tooltip
- Final commit: `FinanceKit v4.0 — Desktop App, Bill Calendar, Budget Intelligence, Year-in-Review, Household, Import Ecosystem`
- Push to both repos

### Files to modify
Essentially every file — this is the final comprehensive sweep.

### Files to create
- New test files for expanded coverage
- Updated marketing assets

### Acceptance criteria
- [ ] App startup time is under 3 seconds
- [ ] All module empty states are polished
- [ ] Loading spinners on all data-fetching operations
- [ ] 100+ tests passing
- [ ] README, GUIDE, GUMROAD_GUIDE, CHANGELOG all updated
- [ ] Demo app showcases v4.0 features
- [ ] Zero unused imports, zero TODOs, zero hardcoded colors/currencies
- [ ] All tests pass
- [ ] Version 4.0 displayed correctly everywhere
- [ ] The app feels fast, polished, and professional end-to-end

---

## Summary of All Versions

| Version | Theme | Key Features |
|---------|-------|-------------|
| v3.1 | Desktop Experience | Installer, launcher, system tray, splash screen, friendly errors |
| v3.2 | Smart Categorization | Category learning, anomaly detection, merchant recognition, Income category |
| v3.3 | Bill Calendar | Bill tracker, calendar view, payment reminders, auto-detect bills |
| v3.4 | Multi-Account | Account management, per-account filtering, transfers, account dashboard |
| v3.5 | Budget Intelligence | Rollover, forecasts, what-if scenarios, seasonal patterns |
| v3.6 | Mobile & PWA | Progressive web app, quick entry, mobile layouts, touch-friendly |
| v3.7 | Year-in-Review | Annual review PDF, tax summary, deductible tagging, year-over-year |
| v3.8 | Household Finance | Shared mode, split expenses, shared goals, family dashboard |
| v3.9 | Import Ecosystem | YNAB/Mint/Monarch import, OFX support, import wizard, folder watcher |
| v4.0 | Final Polish | Performance, tests (100+), docs, demo, code quality, relaunch |
