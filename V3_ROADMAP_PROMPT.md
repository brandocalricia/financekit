# FinanceKit V2.2 → V3.0 Roadmap Prompt

**Paste everything below this line into a new Claude Code chat.**

---

You are working on **FinanceKit**, a Streamlit-based personal finance toolkit sold on Gumroad for $29.99. The project is at `C:\Users\bzcni\OneDrive\Desktop\vs code projects\Finance Toolkit` and the repo is `brandocalricia/financekit`. There is also a separate demo/email-marketing repo at `C:\Users\bzcni\OneDrive\Desktop\vs code projects\Finance Toolkit Email Campaign` (`brandocalricia/financekit-email-campaign`).

The app is currently at **v2.1**. We are incrementally upgrading it to **v3.0** in steps of 0.1. Each version should be a single focused update that gets committed and pushed before moving to the next. **Do one version at a time. Ask me before starting each new version.** Do NOT try to do multiple versions at once.

Below is the full roadmap. Each version lists exactly what to build, what files to touch, and what the acceptance criteria are.

---

## Current State (v2.1)

### Architecture
- **Framework:** Streamlit 1.45.0, Python 3.11
- **Storage:** Local JSON files in `data/` with atomic writes + auto-backup (5 versions)
- **Navigation:** Sidebar radio buttons, 8 pages (Dashboard + 7 modules)
- **Styling:** Custom dark theme (#0f1117 bg, #6366f1 indigo primary, #a78bfa purple accent), Inter font, responsive CSS at 992px/768px breakpoints
- **Charts:** Plotly with shared config via `utils/chart_config.py`
- **Total codebase:** ~5,820 lines across 19 Python files

### 7 Modules
1. **Budget Tracker** (450 lines) — 11 categories, 4 templates (Student/Freelancer/Family/Professional), CSV import, auto-categorize via keyword mapping, persistent transactions to `budget_transactions.json`, donut charts, color-coded progress bars
2. **Goal Tracker** (286 lines) — savings goals with target/deadline/monthly contribution, projection date calculation, milestone celebrations, history chart, quick-add fund buttons (+$50/+$100/+$250/+$500), stored in `goals.json`
3. **Receipt Scanner** (254 lines) — PDF/image upload, pdfplumber→PyPDF2→Tesseract OCR chain, vendor/date/total extraction, auto-categorization, batch upload, CSV/Excel export, two-click clear confirmation, stored in `receipts.json`
4. **Portfolio Tracker** (403 lines) — stocks (Yahoo Finance) + crypto (CoinGecko, 15 tickers), 3 tabs (Portfolio/Watchlist/Alerts), live price refresh, gain/loss calculation, allocation donut, performance charts (1mo/3mo/6mo/1y), price alerts with optional SMTP email, stored in `portfolio.json`
5. **Report Generator** (481 lines) — bank CSV/Excel upload, auto-detect 5 bank formats (Chase/BofA/Wells Fargo/Capital One/Amex), column mapping UI, summary stats, monthly spending bar + category pie + income vs expenses line charts, branded PDF via ReportPDF class, email PDF, download cleaned Excel
6. **Freelance Dashboard** (523 lines) — clients with name/email/rate, projects with hours/rate/auto-calculated value, invoice PDF generation with payment terms, mark invoices paid/unpaid, monthly income chart, client profitability breakdown, outstanding balance tracking, CSV export. Data file is still named `job_applications.json` (needs renaming)
7. **Subscription Auditor** (444 lines) — bank CSV upload with auto-column mapping, RapidFuzz fuzzy transaction grouping (threshold slider 0-100), 20 known subscriptions with cancel URLs, keep/cancel toggles persisted to `sub_decisions.json`, what-if savings calculator, duplicate flagging, annual renewal calendar, 5-year projected cost, CSV/Excel export

### Utilities
- `data_persistence.py` (106 lines) — `load_json()` / `save_json()` with atomic writes (temp file + os.replace), auto-backup before every save to `data/backups/`, keeps 5 backups per file, `_restore_from_backup()` on JSONDecodeError, `get_mtime()` for session sync
- `finance_api.py` (108 lines) — `get_stock_price()` / `get_stock_history()` via yfinance, `get_crypto_price()` / `get_crypto_history()` via CoinGecko, `CRYPTO_IDS` mapping for 15 coins
- `pdf_parser.py` (123 lines) — `parse_pdf()` via pdfplumber with PyPDF2 fallback, `_extract_date()` / `_extract_total()` / `_extract_vendor()` regex extraction, `guess_category()` keyword matching, Tesseract OCR fallback for image PDFs
- `fuzzy_matcher.py` (42 lines) — `normalize_description()` removes dates/IDs, `group_similar_transactions()` via RapidFuzz token_sort_ratio
- `chart_config.py` (37 lines) — `CHART_COLORS` (6-color palette), `CHART_FONT`, `CHART_LAYOUT` dict, `apply_layout()`, `donut_layout()`
- `ui_helpers.py` (28 lines) — `render_module_header()` (icon + title + description + gradient underline), `styled_metric_card()` (dashboard widget HTML)
- `report_builder.py` (199 lines) — `ReportPDF(FPDF)` class: branded indigo header bar, decorative title page, `add_section_header()`, `add_stat_line()`, `add_summary_box()`, `add_chart_image()` (Plotly→PNG via kaleido subprocess), `add_table()` with alternating rows, `get_bytes()`

### Data Files (all in `data/`)
- `budgets.json` — category budget allocations
- `goals.json` — savings goals with id/name/target/current/deadline/monthly/history
- `receipts.json` — scanned receipt entries
- `portfolio.json` — holdings/alerts/watchlist
- `transactions.json` — imported bank transactions
- `job_applications.json` — freelance clients/invoices (misnamed, needs → `freelance_data.json`)
- `budget_transactions.json` — individual budget transaction log
- `sub_decisions.json` — subscription keep/cancel choices
- `statement_transactions.json` — raw imported bank statement data

### Other Files
- `demo/app_demo.py` (623 lines) — Streamlit Cloud marketing page with hero, feature showcase, FAQ, pricing comparison, free Budget Tracker sample, floating CTA
- `start.bat` (44 lines) — Windows launcher: checks Python, installs deps, runs Streamlit
- `start.sh` (36 lines) — Mac/Linux launcher: same flow with python3
- `README.md` (112 lines) — product pitch, module descriptions, quick start, file structure
- `GUIDE.md` (194 lines) — user walkthroughs for 5/7 modules (missing Budget Tracker + Goal Tracker sections, "Job Tracker" section needs renaming)
- `sample_data/` — `bank_statement.csv` (56 rows), `transactions.csv` (40 rows), 2 sample receipt PDFs, pre-generated User Guide PDF
- `assets/` — 6 Gumroad HTML product images (thumbnail + 5 feature showcases)

### Known Issues to Fix Along the Way
- `GUIDE.md` is missing Budget Tracker and Goal Tracker walkthroughs
- Module is called "Freelance Dashboard" in UI but data file is still `job_applications.json` and GUIDE.md still says "Job Tracker"
- No global settings/preferences page
- No light theme option
- No search or filtering across modules
- No authentication — anyone who opens the URL can access everything
- SMTP email config is duplicated across portfolio_tracker.py and report_generator.py
- No keyboard shortcuts or accessibility considerations
- No data validation on JSON load — missing keys cause crashes
- API calls (Yahoo Finance, CoinGecko) have no caching, no rate limit handling, no graceful failure
- Demo app (`demo/app_demo.py`) needs updating after each significant version

### Dependencies (requirements.txt)
```
streamlit==1.45.0
pandas==2.2.3
plotly==6.0.1
pdfplumber==0.11.6
PyPDF2==3.0.1
pytesseract==0.3.13
Pillow==11.1.0
openpyxl==3.1.5
yfinance==0.2.54
requests==2.32.3
rapidfuzz==3.12.2
fpdf2==2.8.3
xlsxwriter==3.2.2
kaleido==0.2.1
```

---

## V2.2 — Housekeeping, Settings Module & Structural Cleanup

**Theme:** Eliminate all tech debt, centralize configuration, and lay a clean foundation for every future version.

### Tasks

#### 1. Fix naming inconsistencies
- Rename data file `job_applications.json` → `freelance_data.json`
  - Add migration code in `modules/job_tracker.py`: on startup, if `job_applications.json` exists and `freelance_data.json` doesn't, copy it over (don't delete the old one — just ignore it going forward)
  - Update all `load_json` / `save_json` calls in that module to use `freelance_data.json`
- Update `GUIDE.md`: rename "Job Tracker" section → "Freelance Dashboard", fully rewrite the walkthrough to match the current client/invoice/project workflow (not the old job application tracking)
- Add missing `GUIDE.md` sections for **Budget Tracker** and **Goal Tracker** with the same level of detail as existing sections (screenshots not required, but describe every button and feature)
- Audit every module for any hardcoded strings that say "Job Tracker" and replace with "Freelance Dashboard"

#### 2. Create Settings module (`modules/settings.py`)
- Add "⚙️ Settings" as the 9th nav option in `app.py` (at the bottom of the sidebar, separated visually from the 7 modules with a `st.divider()` or spacing)
- Settings page sections:

  **Profile**
  - User display name (used in report headers, invoice "from" field, dashboard greeting)
  - User email (prefilled in email-related features)
  - Currency preference: dropdown with USD ($), EUR (€), GBP (£), CAD (C$), AUD (A$), JPY (¥) — store the symbol and code. All modules should read this and display the chosen currency symbol instead of hardcoded "$"
  - Date format preference: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD — all date displays across the app should respect this
  - Stored in `data/settings.json`

  **Email (SMTP)**
  - Server, port, email, app password fields — currently duplicated across portfolio_tracker.py and report_generator.py. Centralize here. Both modules should read from `settings.json` and only show inline email fields as fallback if settings are empty
  - "Send Test Email" button that sends a simple test to the configured address
  - Show a help expander: "How to get a Gmail App Password" with step-by-step instructions (since this is the most common use case)

  **Data Management**
  - "Export All Data" button → creates a single `.zip` of all JSON files in `data/` (excluding backups/) and triggers `st.download_button`
  - "Import Data" `st.file_uploader` → accepts a previously exported zip, extracts to `data/`, shows a confirmation of which files were restored and how many records each contains
  - "Reset All Data" with two-click confirmation (first click shows warning, second click actually deletes) → deletes all JSON files in `data/` (keeps backups/)
  - Show current data file sizes and record counts in a table (e.g., "budgets.json — 2.1 KB — 11 categories", "receipts.json — 4.3 KB — 12 receipts")

  **About**
  - Version number (v2.2)
  - Python version detected at runtime (`sys.version`)
  - Streamlit version (`st.__version__`)
  - Link to GitHub repo
  - Link to Gumroad product page
  - "Check for Updates" — compare current version against a simple version string fetched from the GitHub repo's README (or a `version.txt` file at repo root). Show "You're up to date" or "v3.0 available — visit Gumroad to download"

- `data/settings.json` schema:
  ```json
  {
    "user_name": "",
    "user_email": "",
    "currency": {"code": "USD", "symbol": "$"},
    "date_format": "MM/DD/YYYY",
    "email_smtp": {
      "server": "",
      "port": 587,
      "email": "",
      "password": ""
    },
    "theme": "dark",
    "version": "2.2"
  }
  ```

#### 3. Centralize currency and date formatting
- Create `utils/formatting.py` with:
  - `format_currency(amount: float) -> str` — reads currency from settings, returns e.g., "$1,234.56" or "€1.234,56"
  - `format_date(date_str_or_obj) -> str` — reads date format from settings, returns formatted string
  - `parse_date(date_str) -> datetime` — smart date parsing that handles multiple input formats
- Update every module to use these functions instead of hardcoded `$` and date formatting
- This is important for international users and makes the product feel polished

#### 4. Create `version.txt` at project root
- Contains just the version string: `2.2`
- `app.py` reads this file to display the version (single source of truth instead of hardcoded strings in multiple places)
- Settings "Check for Updates" compares against this

#### 5. Version bump
- Update version string everywhere to v2.2 (via `version.txt`)
- Update `demo/app_demo.py` version reference

### Files to modify
`app.py`, `modules/job_tracker.py`, `modules/report_generator.py`, `modules/portfolio_tracker.py`, `modules/budget_tracker.py`, `modules/goal_tracker.py`, `modules/receipt_scanner.py`, `modules/subscription_auditor.py`, `GUIDE.md`, `demo/app_demo.py`

### Files to create
`modules/settings.py`, `utils/formatting.py`, `version.txt`

### Acceptance criteria
- [ ] Opening the app with old `job_applications.json` auto-migrates to `freelance_data.json`
- [ ] All references to "Job Tracker" replaced with "Freelance Dashboard" across entire codebase
- [ ] GUIDE.md has complete, detailed walkthroughs for all 7 modules + Settings
- [ ] Settings page saves/loads all fields correctly
- [ ] Currency symbol from settings appears in every module (not hardcoded $)
- [ ] Date format from settings is respected everywhere dates are displayed
- [ ] Export creates a downloadable zip with all data; Import restores from it
- [ ] Reset All Data requires two clicks and works
- [ ] Data file sizes/counts table renders in Settings
- [ ] Email config in Settings is used by Report Generator and Portfolio Tracker
- [ ] "Send Test Email" works with valid SMTP config
- [ ] "Check for Updates" correctly compares versions
- [ ] Version is read from `version.txt` (single source of truth)
- [ ] All files pass `py_compile`
- [ ] App launches without errors

---

## V2.3 — UI/UX Overhaul & Theming

**Theme:** Make the app feel like a premium product. Light/dark toggle, micro-interactions, polished navigation, keyboard shortcuts, and a mobile-first audit.

### Tasks

#### 1. Light/dark theme toggle
- Add a theme toggle in the sidebar (🌙/☀️ icon button) that saves to `settings.json` → `theme: "dark" | "light"`
- Create two complete CSS variable sets:
  - **Dark** (current): bg #0f1117, card #1a1a2e, card-hover #252540, text #e2e8f0, text-muted #94a3b8, border #2a2a40, accent #6366f1, accent-light #a78bfa, success #22c55e, warning #f59e0b, danger #ef4444, input-bg #1e1e2f
  - **Light**: bg #f8fafc, card #ffffff, card-hover #f1f5f9, text #1e293b, text-muted #64748b, border #e2e8f0, accent #6366f1, accent-light #818cf8, success #16a34a, warning #d97706, danger #dc2626, input-bg #f8fafc
- Refactor ALL inline CSS across `app.py` and every module to use CSS custom properties (`var(--fk-bg)`, `var(--fk-card)`, etc.). This is a significant refactor — every `st.markdown` with custom HTML/CSS needs updating
- Ensure Plotly charts respect the theme: create `get_chart_layout(theme)` in `chart_config.py` that returns matching bg/font/grid colors
- Theme should apply immediately on toggle via `st.rerun()`
- The welcome wizard / onboarding should also respect the theme

#### 2. Loading states, feedback & micro-interactions
- Add `st.spinner("Fetching live prices...")` around all API calls in portfolio_tracker.py
- Add `st.spinner("Generating PDF...")` around PDF generation in report_generator.py and job_tracker.py
- Add `st.spinner("Processing receipt...")` around OCR/parsing in receipt_scanner.py
- Add `st.toast()` confirmations for every user action: saving settings, adding a transaction, adding a goal, uploading a receipt, exporting data, sending an email, deleting an item, updating a holding, marking an invoice paid
- Add subtle CSS transitions on card hover states (transform: translateY(-2px), box-shadow increase) — already partially exists, ensure consistency
- Add CSS transition on theme switch (0.3s ease for background-color and color properties)
- Empty state illustrations: when a module has no data yet, show a friendly message with an icon and a call-to-action button instead of just a blank page. For example, Portfolio Tracker with no holdings should show: "📈 No holdings yet — Add your first stock or crypto to get started" with an "Add Holding" button

#### 3. Comprehensive mobile audit
- Test every single `st.columns()` call across every module:
  - Any row with 4+ columns → use CSS to collapse to 2 columns on mobile (<768px)
  - Any row with 3 columns that contains wide content → collapse to stacked on mobile
  - Metric cards on dashboard → 2 per row on tablet, 1 per row on phone
- Ensure all HTML tables have `overflow-x: auto` wrapper for horizontal scroll
- Dashboard module cards: 4→2 columns on tablet, 1 column on phone via CSS grid media queries
- Sidebar: verify Streamlit's auto-collapse works. Add a small "☰" hint on mobile
- Charts: ensure Plotly charts have `config={"responsive": True}` and reasonable min-height
- Forms: ensure all `st.text_input`, `st.number_input`, `st.selectbox` are usable on touch (adequate tap targets, no tiny buttons)
- Test at these widths: 375px (iPhone SE), 390px (iPhone 14), 768px (iPad), 1024px (iPad landscape), 1440px (desktop)

#### 4. Sidebar redesign
- **Top section**: FinanceKit logo text with the gradient effect + version badge (e.g., "v2.3" in small muted text)
- **Navigation grouping** with small gray uppercase headers:
  - `OVERVIEW` → 🏠 Dashboard
  - `MODULES` → the 7 modules
  - `SYSTEM` → ⚙️ Settings
- Add a **"Quick Actions"** expander at the bottom of sidebar with shortcut buttons:
  - "➕ Add Transaction" → navigates to Budget Tracker with auto-focus on add form
  - "📄 Import CSV" → navigates to Report Generator
  - "🎯 New Goal" → navigates to Goal Tracker with auto-focus on add form
  - "🧾 Scan Receipt" → navigates to Receipt Scanner
- Each quick action should set a session state flag (e.g., `st.session_state.auto_open_form = True`) that the target module checks on load

#### 5. Keyboard shortcuts
- Add a small keyboard shortcut handler using Streamlit's `st.query_params` or custom JavaScript injection:
  - `?` → Show shortcuts help modal
  - `1-7` → Navigate to modules 1-7
  - `0` → Dashboard
  - `9` → Settings
  - `n` → New (context-dependent: new transaction, new goal, new holding, depending on current module)
- Show a "Keyboard shortcuts" link in the sidebar footer that opens the help modal
- Implement via a small JavaScript snippet injected through `st.markdown` with `<script>` tag that listens for keydown events and triggers Streamlit reruns with query params

#### 6. Global search
- Add a `st.text_input` search bar at the top of the sidebar (or top of the main content area)
- Search across all data files simultaneously:
  - Receipts: vendor name, date, amount
  - Transactions: description, category, amount
  - Portfolio: ticker, company name
  - Goals: goal name
  - Freelance: client name, project name, invoice number
  - Subscriptions: subscription name
- Show results in a dropdown-style list grouped by module, with clickable links that navigate to the relevant module and highlight the matched item
- Implement as a reusable `utils/search.py` utility that queries all JSON data files
- Search should be fast — it's searching local JSON, not an API

### Files to modify
`app.py` (major CSS refactor), `utils/chart_config.py`, `modules/settings.py`, all 7 module files (CSS variables + empty states + mobile fixes), `demo/app_demo.py`

### Files to create
`utils/search.py`

### Acceptance criteria
- [ ] Light/dark toggle works, persists across sessions, and looks polished in both modes
- [ ] ALL custom HTML/CSS across every file uses CSS variables (no hardcoded colors remain)
- [ ] All Plotly charts adapt colors to match current theme
- [ ] Spinners appear during every API call, PDF generation, and OCR processing
- [ ] Toast confirmations fire for every save/create/delete/update action
- [ ] Empty states with friendly messages + CTAs in every module when no data exists
- [ ] App is fully usable on 375px-wide screen (all content readable, no overflow, all buttons tappable)
- [ ] Dashboard cards reflow correctly at tablet and phone breakpoints
- [ ] Sidebar has logo, version, grouped navigation headers, quick actions
- [ ] Quick action buttons navigate to correct module and auto-open the relevant form
- [ ] At least 5 keyboard shortcuts work (dashboard, 2 modules, settings, help)
- [ ] Global search finds items across all modules and navigates to them
- [ ] CSS transitions on theme switch and card hovers
- [ ] All files pass `py_compile`

---

## V2.4 — Authentication & Multi-User System

**Theme:** Add secure sign-in via Google, GitHub, and email/password. Isolate each user's data. Make it feel like a real web app.

### Tasks

#### 1. Choose and implement auth framework
- Evaluate these options in order of preference:
  1. `streamlit-authenticator` — check if it supports OAuth
  2. `streamlit-oauth` + custom local auth — if #1 doesn't support OAuth
  3. Custom build with `authlib` + `bcrypt` — if neither package works well
- Add chosen packages to `requirements.txt`
- **Supported sign-in methods:**
  - **Email/password** — local accounts stored in `data/users.json` with bcrypt-hashed passwords, email used as unique identifier
  - **Google OAuth 2.0** — requires client ID/secret (user configures in Settings)
  - **GitHub OAuth** — requires client ID/secret (user configures in Settings)
- The auth system should be in `utils/auth.py` with clean separation from UI code

#### 2. Login page design
- Create a full-screen login page that appears before any app content when auth is enabled
- Must match the current dark/light theme and feel professional — this is the first thing users see
- Layout:
  - Centered card (max-width 420px) with subtle shadow and border
  - FinanceKit logo + "Welcome back" or "Get started" heading
  - **OAuth buttons** at the top (most prominent):
    - "Continue with Google" — white bg, Google 'G' logo colors, standard Google button style
    - "Continue with GitHub" — dark bg, GitHub octocat icon
  - Horizontal divider: "─── or continue with email ───"
  - **Email/password form**:
    - Email input
    - Password input (with show/hide toggle)
    - "Remember me" checkbox (extends session to 30 days)
    - "Sign In" button (indigo, full width)
  - Below form:
    - "Don't have an account? **Create one**" → switches to registration view
    - "Forgot password?" → password reset view
- **Registration form** (same card, different content):
  - Display name
  - Email
  - Password (with strength indicator: weak/medium/strong based on length + character variety)
  - Confirm password
  - "Create Account" button
  - "Already have an account? **Sign in**"
- **Forgot password flow** (for local accounts):
  - Enter email → if email exists, show a security question or generate a reset token
  - Since this is a local app without a mail server requirement, implement a simple reset: show the reset token on screen that the admin/user can use (or, if SMTP is configured in settings, email it)

#### 3. Per-user data isolation
- Each user gets their own data directory: `data/users/{user_id}/`
  - `user_id` = sanitized email (replace `@` and `.` with underscores) or OAuth provider ID
- On first login, create the user's data folder with empty default JSON files (copy the schema, not any existing data)
- Modify `utils/data_persistence.py`:
  - Add `_user_data_dir: str | None = None` module-level variable
  - Add `set_user_context(user_id: str)` that sets the base path to `data/users/{user_id}/`
  - Add `clear_user_context()` for sign-out
  - `_path(filename)` should use the user-specific directory when context is set, fall back to `data/` when not
  - Backups go to `data/users/{user_id}/backups/`
- When auth is **disabled**, data stays in `data/` as before (fully backwards compatible)
- When auth is **enabled** and a user signs in, their data is completely isolated
- `data/users.json` stores the user registry (outside any user's folder):
  ```json
  {
    "users": [
      {
        "id": "user_example_com",
        "email": "user@example.com",
        "name": "John",
        "password_hash": "$2b$12$...",
        "auth_method": "local",
        "created_at": "2026-03-29T...",
        "last_login": "2026-03-29T..."
      }
    ]
  }
  ```

#### 4. OAuth configuration in Settings
- Add an "🔐 Authentication" section to Settings:
  - Master toggle: "Require authentication" (on/off) — when off, app works without login. Default: off
  - When toggled on for the first time, prompt the user to create the first (admin) account
  - Google OAuth section:
    - Client ID input
    - Client Secret input (password field)
    - Redirect URI (auto-detected from current URL)
    - Status indicator: ✅ Configured / ⚠️ Not configured
    - Help expander: step-by-step guide to creating a Google OAuth app
  - GitHub OAuth section:
    - Client ID input
    - Client Secret input (password field)
    - Callback URL (auto-detected)
    - Status indicator
    - Help expander: step-by-step guide to creating a GitHub OAuth app
  - Store in `data/auth_config.json` (separate from settings, since it contains secrets):
    ```json
    {
      "require_auth": false,
      "google": {"client_id": "", "client_secret": ""},
      "github": {"client_id": "", "client_secret": ""},
      "session_expiry_hours": 24
    }
    ```
  - ⚠️ Warning text: "auth_config.json contains secrets. Do not share this file or commit it to version control."
  - Add `auth_config.json` to `.gitignore` if not already there

#### 5. Session management
- Store session info in `st.session_state`: `authenticated`, `user_id`, `user_name`, `user_email`, `auth_method`, `login_time`
- **Sidebar when authenticated**:
  - Show user avatar/initial circle + name at the very top of sidebar (above navigation)
  - "Sign Out" button at the bottom of sidebar
- **Session expiry**: Check `login_time` on every page load. If `> session_expiry_hours` has passed, auto sign-out and redirect to login
- "Remember me" extends expiry to 720 hours (30 days)
- On sign-out: `clear_user_context()`, clear all session state keys, `st.rerun()` to show login page

#### 6. Account management
- In Settings → Profile section, add:
  - "Change Password" (for local accounts only) — current password + new password + confirm
  - "Delete Account" — two-click confirmation, deletes user's data directory and removes from users.json
  - Show "Signed in via Google/GitHub" badge for OAuth users (no password change option)

#### 7. Documentation
- Add a comprehensive new section to `GUIDE.md`: **"Setting Up Authentication"** with:
  - How to enable auth in Settings
  - Creating a Google OAuth app (console.cloud.google.com): create project → configure consent screen → create credentials → set redirect URI → copy client ID/secret
  - Creating a GitHub OAuth app (github.com/settings/developers/new): app name → homepage URL → callback URL → copy client ID/secret
  - Where to paste credentials in FinanceKit Settings
  - Troubleshooting: common OAuth errors and fixes
  - Security notes: keeping auth_config.json safe

### Files to modify
`app.py` (login gate + sidebar user display), `utils/data_persistence.py` (user context), `modules/settings.py` (auth config + account management), `GUIDE.md`, `requirements.txt`, `.gitignore`

### Files to create
`utils/auth.py` (AuthManager class: register, login, verify, OAuth flows, password reset, session management)

### Acceptance criteria
- [ ] When auth is disabled (default), app works exactly as before — zero change in behavior
- [ ] When auth is enabled, login page appears before any content
- [ ] Login page looks professional and matches the current theme (dark/light)
- [ ] Can create a local email/password account with password strength validation
- [ ] Can sign in with email/password
- [ ] Google OAuth flow works end-to-end (with valid credentials)
- [ ] GitHub OAuth flow works end-to-end (with valid credentials)
- [ ] Each user's data is completely isolated in their own directory
- [ ] Existing data in `data/` is preserved (backwards compatible)
- [ ] User avatar/name shows in sidebar when authenticated
- [ ] Sign-out clears everything and returns to login
- [ ] Session expires after configured duration
- [ ] "Remember me" extends session to 30 days
- [ ] Password change works for local accounts
- [ ] Account deletion removes all user data
- [ ] auth_config.json is in .gitignore
- [ ] GUIDE.md has complete OAuth setup instructions with screenshots-ready descriptions
- [ ] All files pass `py_compile`

---

## V2.5 — Notification Center & Smart Alerts

**Theme:** Keep users proactively informed. In-app notification center, contextual alerts across every module, and optional email digests.

### Tasks

#### 1. Notification engine (`utils/notifications.py`)
- Create a centralized notification system:
  - `create_notification(type, module, title, message, action_module=None)` — saves to notifications.json
  - `get_notifications(unread_only=False, limit=50)` — returns sorted list
  - `mark_read(notification_id)` / `mark_all_read()`
  - `clear_old(days=30)` — auto-clean notifications older than 30 days
  - `get_unread_count() -> int`
- Notification schema:
  ```json
  {
    "id": "uuid4",
    "type": "info|warning|success|alert",
    "module": "budget|portfolio|goals|subscriptions|receipts|freelance|system",
    "title": "Short title",
    "message": "Detailed message with context",
    "timestamp": "ISO datetime",
    "read": false,
    "action_module": "budget_tracker"
  }
  ```
- Stored in the user's data directory (respects per-user isolation from v2.4)
- Auto-clean on every app startup: remove notifications older than 30 days

#### 2. Notification bell UI
- Add a 🔔 icon in the top-right area of the main content (or in the sidebar header next to the user name)
- Show unread count as a red badge number (e.g., "🔔 3")
- Clicking opens a notification panel (use `st.expander` or `@st.dialog`):
  - Grouped by: **Today** / **This Week** / **Earlier**
  - Each notification shows: colored icon (🔵 info, 🟡 warning, 🟢 success, 🔴 alert), title, message preview, timestamp ("2 hours ago", "Yesterday", etc.)
  - Click a notification → mark as read + navigate to the relevant module (if `action_module` is set)
  - "Mark all as read" button
  - "Clear all" button with confirmation
- Notification bell should update on every page load (check data file)

#### 3. Automatic alert triggers — implement in each module
These should fire automatically when conditions are met, NOT require user action:

**Budget Tracker (`modules/budget_tracker.py`)**:
- When any category reaches **80%** of budget → ⚠️ warning: "Housing is at 80% of your $1,000 budget — $200 remaining"
- When any category **exceeds** budget → 🔴 alert: "You've exceeded your Dining Out budget by $45"
- When total monthly spending exceeds 90% of total budget → ⚠️ "You've used 90% of your total monthly budget with 12 days remaining"
- On first day of each month → 🔵 info: "New month started — your budgets have been reset. Last month you were $X under/over budget"
- Check triggers: on every transaction add AND on dashboard load

**Goal Tracker (`modules/goal_tracker.py`)**:
- When a goal passes **25%**, **50%**, **75%** → 🟢 success: "Emergency Fund is 50% funded — halfway there!"
- When a goal reaches **100%** → 🎉 success: "Congratulations! You've fully funded your Emergency Fund!"
- When a goal is **behind schedule** (projected date > deadline) → ⚠️ warning: "Vacation fund is behind schedule — increase monthly contribution by $X to stay on track"
- When a goal's deadline is **within 30 days** and it's below 90% → 🔴 alert: "New Laptop deadline is in 28 days but you're only at 65%"

**Portfolio Tracker (`modules/portfolio_tracker.py`)**:
- When a price alert triggers → 🔴 alert: "AAPL crossed above $200 (current: $203.50)" — integrate with existing price alert feature
- When any single holding drops **>5% in a day** → ⚠️ warning: "TSLA is down 7.2% today"
- When any single holding gains **>10% in a day** → 🟢 success: "BTC is up 12.4% today!"
- When total portfolio value changes **>3%** in a day (up or down) → 🔵 info with the change amount

**Subscription Auditor (`modules/subscription_auditor.py`)**:
- **7 days before** a detected annual renewal → 🔵 info: "Netflix annual renewal coming up on April 5 — $185.88"
- When a new upload detects a **price increase** on a known subscription → ⚠️ warning: "Adobe CC increased from $54.99 to $59.99/mo (+$60/yr)"
- When total monthly subscription cost exceeds a configurable threshold (default $200/mo) → ⚠️ warning
- After initial analysis → 🟢 info summary: "Found 8 subscriptions totaling $127/mo. Potential savings: $540/yr"

**Freelance Dashboard (`modules/job_tracker.py`)**:
- When an invoice is **>30 days** unpaid → ⚠️ warning: "Invoice #1042 for Client ABC is 35 days overdue — $2,500 outstanding"
- When an invoice is **>60 days** unpaid → 🔴 alert: "Invoice #1042 is 62 days overdue — consider following up"
- When a new invoice is marked **paid** → 🟢 success: "Payment received: $2,500 from Client ABC"
- Monthly revenue milestone → 🟢: "You've earned $X this month — your best month yet!" (compare to previous months)

**Receipt Scanner (`modules/receipt_scanner.py`)**:
- When a receipt total exceeds **$500** → 🔵 info: "Large receipt logged: $847 at Best Buy — don't forget to categorize it"
- After batch upload → 🟢: "Successfully processed 5 receipts totaling $234.50"

#### 4. Notification preferences in Settings
- Add a "🔔 Notifications" section to Settings:
  - Master toggle: Notifications on/off
  - Per-module toggles: enable/disable notifications for each module
  - Threshold settings:
    - Budget warning threshold (default 80%)
    - Portfolio daily change alert threshold (default 5%)
    - Subscription monthly cost warning threshold (default $200)
    - Invoice overdue alert days (default 30)
  - Store in `settings.json` under a `notifications` key

#### 5. Email digest
- In Settings → Notifications, add "Email Digest" section:
  - Toggle: On/Off
  - Frequency: Daily / Weekly / Off
  - Time preference: Morning (8am) / Evening (6pm) — informational only since Streamlit can't schedule
- `send_digest_email()` function in notifications.py:
  - Collects all unread notifications since last digest
  - Formats into a clean, branded HTML email (dark bg, indigo accents, matching the app's style)
  - Sections: Summary stats at top, then notifications grouped by module
  - Sends via SMTP config from Settings
  - Records `last_digest_sent` timestamp in settings
- **Trigger**: Since Streamlit can't run background tasks, check on every app startup: if digest is enabled and enough time has passed since `last_digest_sent`, send the digest automatically
- If there are no unread notifications, skip sending (don't send empty digests)

#### 6. Dashboard integration
- Add a "📋 Recent Alerts" section to the dashboard between the metric cards and the module cards
- Show the **5 most recent unread** notifications with:
  - Color-coded left border (blue/yellow/green/red)
  - Title + short message + relative timestamp
  - Click → navigate to relevant module
- "View All Notifications →" link at bottom opens the full notification panel
- If there are no unread notifications, show a subtle "✅ All clear — no new alerts" message

### Files to modify
`app.py` (bell UI + dashboard alerts section), `modules/settings.py` (notification preferences), `modules/budget_tracker.py`, `modules/goal_tracker.py`, `modules/portfolio_tracker.py`, `modules/subscription_auditor.py`, `modules/job_tracker.py`, `modules/receipt_scanner.py`

### Files to create
`utils/notifications.py`

### Acceptance criteria
- [ ] Notification bell visible on every page with unread count badge
- [ ] Notification panel opens with grouped, timestamped notifications
- [ ] Clicking a notification marks it as read and navigates to the module
- [ ] Budget 80%/exceeded alerts trigger automatically
- [ ] Goal 25/50/75/100% milestone notifications trigger
- [ ] Portfolio price alert creates a notification
- [ ] Portfolio >5% daily drop triggers a warning
- [ ] Subscription renewal reminder triggers 7 days before
- [ ] Subscription price increase detected and flagged
- [ ] Overdue invoice warnings at 30 and 60 days
- [ ] Large receipt notification fires for >$500
- [ ] Notification preferences in Settings save correctly
- [ ] Per-module notification toggles work
- [ ] Email digest sends when enabled and due (not empty)
- [ ] Dashboard shows 5 most recent unread alerts
- [ ] Old notifications (>30 days) auto-cleaned on startup
- [ ] All notifications respect per-user data isolation
- [ ] All files pass `py_compile`

---

## V2.6 — Advanced Budget Analytics & Financial Health

**Theme:** Transform FinanceKit from a tracker into a financial intelligence tool. Deep analytics, net worth tracking, spending forecasting, and a financial health score.

### Tasks

#### 1. Budget analytics tab
- Add a tabbed interface to Budget Tracker: **"Track"** (existing UI) | **"Analyze"** (new)
- The Analyze tab contains:

  **Month-over-Month Comparison**
  - Grouped bar chart: this month vs last month, per category
  - Show the delta ($ and %) next to each category name
  - Highlight categories that increased >20% in red

  **Budget vs Actual Table**
  - Full table: Category | Budget | Actual | Remaining | Variance ($) | Variance (%) | Status
  - Status column: 🟢 Under Budget / 🟡 Near Limit (>80%) / 🔴 Over Budget
  - Sortable by any column (use `st.dataframe` with column config)
  - Total row at bottom

  **Spending Trends (6 months)**
  - Line chart with one line per top-5 categories + a "Total" line
  - Data source: aggregate from `budget_transactions.json` by month
  - Show trend direction arrow (↑↗→↘↓) next to each category in the legend

  **Top 10 Merchants**
  - Horizontal bar chart of top merchants by total spend
  - Data: group transactions by vendor name (normalize with fuzzy matching to merge "AMAZON" / "Amazon.com" / "AMZN")
  - Show transaction count next to each merchant

  **Day-of-Week Spending Pattern**
  - Bar chart showing average daily spend by day of week (Mon-Sun)
  - Highlight the most expensive day
  - Useful insight: "You spend 40% more on weekends than weekdays"

  **Category Trend Sparklines**
  - For each category, show a tiny sparkline (last 6 months) next to the category name
  - Uses Plotly subplots or small individual charts

#### 2. Net worth tracker
- Add a new section to the Dashboard: **"Net Worth"** (between metrics and module cards)
- Auto-calculate from existing data:
  - **Assets**:
    - Portfolio total market value (from `portfolio.json` holdings × current prices)
    - Savings goals current amounts (sum from `goals.json`)
    - Cash / bank balance (new manual input field on dashboard, stored in `settings.json`)
  - **Liabilities**:
    - Manual entry fields: Credit cards, Student loans, Mortgage, Car loan, Other
    - Stored in `data/liabilities.json` as a list of `{name, balance, interest_rate, monthly_payment}`
  - **Net Worth** = Total Assets − Total Liabilities
- Display:
  - Big net worth number at top with up/down arrow vs last month
  - Asset/liability breakdown donut chart
  - "Update Liabilities" expander with editable table
- **Monthly snapshots**: `data/net_worth_history.json`
  - On dashboard load, check if a snapshot exists for this month
  - If not, auto-save: `{date, assets, liabilities, net_worth, breakdown}`
  - Line chart showing net worth over time (all historical months)
  - Show the rate of change: "Your net worth grew $X (+Y%) this month"

#### 3. Financial health score
- Create a **Financial Health Score** (0-100) displayed on the dashboard as a gauge/meter
- Score components (weighted):
  - **Budget adherence** (25%): What % of categories are under budget? Score 0-100
  - **Savings rate** (25%): (Monthly savings goal contributions / Monthly income) × 100. Score 0-100 based on rate (>20% = 100, 10-20% = 75, 5-10% = 50, <5% = 25)
  - **Emergency fund progress** (20%): Highest priority goal's % completion. Score = % funded (capped at 100)
  - **Debt ratio** (15%): Total liabilities / Total assets. Score: <0.3 = 100, 0.3-0.5 = 75, 0.5-0.8 = 50, >0.8 = 25
  - **Subscription efficiency** (15%): % of subscriptions marked "Keep" that have usage notes. Score based on how many "Cancel" decisions have been actioned
- Display as a circular gauge: Red (<40), Yellow (40-70), Green (>70)
- Below the gauge, show 3 personalized tips based on the lowest-scoring components:
  - "Your savings rate is 8% — try increasing automatic contributions by $50/mo to reach the recommended 15%"
  - "You're over budget in 3 categories — review your Dining Out and Shopping spending"
  - "Your emergency fund is only 35% funded — prioritize this goal"

#### 4. Spending insights engine
- Rule-based insight generator in `utils/insights.py`:
  - Compares current month to last month, last 3 months, last 6 months
  - Detects patterns:
    - Increasing spending trends (3+ months in a row)
    - Unusual spikes (>50% above 3-month average for a category)
    - Consistent underspending (opportunity to reallocate budget)
    - Day-of-month patterns (more spending at beginning vs end)
  - Generates human-readable insight strings
- Display 3-5 insights on the Budget Tracker Analyze tab as styled cards
- Display the top insight on the Dashboard

#### 5. Custom categories
- In Budget Tracker (or Settings), add a "📂 Manage Categories" section:
  - View all categories (default 11 + any custom ones)
  - **Add category**: name + emoji + color picker
  - **Rename category**: updates all historical transactions too
  - **Merge categories**: select two → merge into one, all transactions reassigned
  - **Hide category**: don't delete, just hide from the tracker (can unhide)
  - **Reorder categories**: number input for display order
- Store in `settings.json` → `categories: [{name, emoji, color, hidden, order}]`
- Update `CATEGORY_MAP` in budget_tracker.py to include custom category keyword mappings (user can add keywords per category)
- Auto-categorization should check custom categories FIRST, then fall back to defaults

#### 6. Spending forecast
- Simple projection on the Budget Tracker Analyze tab:
  - Based on current spending rate, project end-of-month total per category
  - Show as a stacked bar: "Actual so far" (solid) + "Projected remaining" (striped/faded)
  - Warning highlight on any category projected to exceed budget
  - Overall projection: "At your current pace, you'll spend $X by end of month (budget: $Y)"

### Files to modify
`app.py` (net worth section, health score, top insight), `modules/budget_tracker.py` (Analyze tab, custom categories, forecast), `modules/settings.py` (liabilities, category management), `utils/chart_config.py` (new chart types)

### Files to create
`utils/insights.py`, `data/net_worth_history.json`, `data/liabilities.json`

### Acceptance criteria
- [ ] Budget Analyze tab with all 6 sub-sections renders correctly
- [ ] Month-over-month grouped bar chart shows comparison data
- [ ] Budget vs Actual table with variance and status
- [ ] Spending trends line chart shows 6-month history for top categories
- [ ] Top 10 merchants bar chart populates from transactions
- [ ] Day-of-week spending pattern chart renders
- [ ] Net worth auto-calculates from portfolio + goals + cash − liabilities
- [ ] Liabilities can be added/edited/removed
- [ ] Net worth monthly snapshots auto-save and chart renders
- [ ] Financial health score gauge displays (0-100) with color coding
- [ ] 3 personalized tips based on lowest-scoring components
- [ ] At least 5 rule-based insights generated from spending data
- [ ] Custom categories can be created, renamed, merged, hidden
- [ ] Custom category keywords work in auto-categorization
- [ ] Spending forecast projects end-of-month totals with visual
- [ ] All files pass `py_compile`

---

## V2.7 — Enhanced Portfolio & Subscription Modules

**Theme:** Make the Portfolio Tracker and Subscription Auditor best-in-class — features that rival dedicated apps.

### Tasks

#### 1. Portfolio Tracker enhancements

**Dividend tracking**
- New optional field when adding a holding: annual dividend yield %
- Dashboard metric: "Est. Annual Dividend Income: $X" (sum of all holdings × yield × shares)
- Dividend calendar: which months dividends are expected (most US stocks pay quarterly — let user set the pay months)
- Dividend reinvestment toggle: if on, simulate compound growth in the projection

**Multi-lot cost basis**
- Allow adding multiple purchase "lots" per ticker:
  - "Add lot" button on each holding → date, quantity, price per share
  - Display each lot separately OR aggregated (toggle)
- Cost basis methods: **Average Cost** (default) and **FIFO** (first in, first out)
  - Average: total cost / total shares
  - FIFO: for calculating gain/loss on partial sells, sell the oldest lots first
- Selection in Settings → "Cost Basis Method"

**Sell / realize gains**
- New "Sell" action on each holding (or lot):
  - Enter quantity sold and sale price
  - Calculate realized gain/loss based on cost basis method
  - Move to a "Trade History" section (new tab in Portfolio)
  - Record: date, ticker, quantity, buy price, sell price, gain/loss, method
- Running totals: Total realized gains/losses (short-term vs long-term if held >1 year)

**Sector allocation**
- Map common tickers to sectors using a built-in dictionary (top 200 tickers → sector)
  - Tech, Healthcare, Finance, Energy, Consumer, Industrial, Real Estate, Utilities, Materials, Crypto
- Allow user override: custom sector assignment per holding
- New donut chart: "Sector Allocation" alongside existing "Holdings Allocation"
- Diversification warning: if any sector >40% → notification

**Performance benchmarks**
- Overlay S&P 500 (^GSPC) performance on the same time-period chart as user's portfolio
- Show alpha: portfolio return vs benchmark return over selected period
- Fetch benchmark data via `yfinance` (same API already used)

**Portfolio export**
- "📥 Export Portfolio" button:
  - CSV with: Ticker, Type, Shares, Avg Cost, Current Price, Market Value, Gain/Loss ($), Gain/Loss (%), Sector, Dividend Yield
  - Summary row at bottom with totals

#### 2. Subscription Auditor enhancements

**Manual subscription entry**
- New "➕ Add Subscription" form (not just CSV detection):
  - Name, amount, frequency (Monthly/Quarterly/Annual), renewal date, category, cancel URL (optional), notes
- Manually added subs appear alongside detected ones in the main list
- Editable: click to update amount, frequency, notes
- Deletable: remove manually added subs

**Subscription categories**
- Assign each subscription to a category: Entertainment, Productivity, Cloud/Storage, News/Media, Health/Fitness, Education, Finance, Shopping, Communication, Other
- Category breakdown donut chart showing spend distribution
- Filter view by category

**Visual renewal calendar**
- Month grid (12 months) showing which subscriptions renew in each month
- Each month cell shows: list of sub names + total cost for that month
- Color intensity based on cost (darker = more expensive month)
- Useful for seeing cash flow impact: "April is your most expensive month at $XX due to annual renewals"

**Price change detection**
- When processing a new CSV upload, compare each subscription's detected amount to the previously saved amount
- If different, create a diff entry: `{name, old_amount, new_amount, change_pct, detected_date}`
- Show price changes as a highlighted section: "📈 Price Changes Detected"
- Historical price tracking: store amount history per subscription to show trends

**Cancel workflow**
- When user clicks "Cancel" on a subscription:
  1. Show the cancel URL (from known DB or user-entered) as a clickable link
  2. Show a "I've cancelled this" checkbox
  3. Once checked: record cancellation date, move to "Cancelled" section
  4. Show running total: "You've cancelled $X/month ($Y/year) in subscriptions"
- "Cancelled" tab showing all past cancellations with dates and savings

**Usage notes & ROI assessment**
- Each subscription gets a "Notes" field (free text) and a "Usage" rating: Daily / Weekly / Rarely / Never
- Auto-suggest cancellation for "Never" and "Rarely" used subscriptions
- ROI view: cost per use estimate (if user tracks usage frequency)

### Files to modify
`modules/portfolio_tracker.py`, `modules/subscription_auditor.py`, `utils/finance_api.py`, `modules/settings.py`

### Acceptance criteria
- [ ] Dividend yield field available on holdings; annual dividend income metric shows
- [ ] Multiple lots per ticker can be added and displayed
- [ ] Average cost and FIFO cost basis methods both calculate correctly
- [ ] Sell action records realized gain/loss with trade history
- [ ] Sector allocation donut chart renders with auto-mapping + user overrides
- [ ] Diversification warning when single sector >40%
- [ ] S&P 500 benchmark overlay on performance chart with alpha calculation
- [ ] Portfolio CSV export with all fields
- [ ] Manual subscription entry form adds/edits/deletes subscriptions
- [ ] Subscription categories with donut chart
- [ ] 12-month visual renewal calendar renders with cost per month
- [ ] Price change detection flags differences between uploads
- [ ] Cancel workflow with URL, confirmation checkbox, and cancelled section
- [ ] Usage notes and ratings saved per subscription
- [ ] "Rarely/Never used" auto-suggested for cancellation
- [ ] All files pass `py_compile`

---

## V2.8 — Freelance Dashboard Pro & Invoice System

**Theme:** Make the freelance tools professional enough to replace standalone invoicing apps. Time tracking, invoice templates, recurring billing, P&L, and client management.

### Tasks

#### 1. Invoice templates
- Create 3 invoice PDF templates in `utils/invoice_templates.py`:
  - **Minimal**: Clean black/white, modern sans-serif, minimal borders, focus on readability
  - **Professional**: Current branded style with indigo header bar, FinanceKit branding
  - **Creative**: Bold color blocks, large invoice number, modern asymmetric layout
- Each template supports:
  - Custom logo (uploaded in Settings, stored as base64 in `settings.json`)
  - From: company name, address, email, phone (from Settings)
  - To: client name, email, address (from client record)
  - Invoice number (auto-incrementing, format: INV-YYYY-0001)
  - Date issued + due date (auto-calculated from payment terms)
  - Line items table: description, quantity/hours, rate, subtotal
  - Subtotal, tax (configurable rate), discount (optional), total
  - Payment terms text (Net 30, etc.)
  - Payment details: bank name/account/routing OR PayPal email OR custom text
  - Footer: "Thank you for your business!" (customizable)
  - Notes field (free text, per invoice)
- Default template selection in Settings
- Preview before generating: show a rendered preview in-app before downloading PDF

#### 2. Time tracking
- New "⏱️ Time" tab in Freelance Dashboard
- Simple timer:
  - Start/stop button with running clock display
  - Associate with a client + project
  - Auto-log when stopped: date, start time, end time, duration, client, project, notes
- Manual time entry: date, hours, client, project, description
- Time log table with filters by client, project, date range
- Weekly time summary: hours per client, hours per project
- "Generate Invoice from Time" button:
  - Select client → select date range → auto-populate invoice line items from time entries
  - Each time entry becomes a line item: "Development work — March 15 (3.5 hrs × $75/hr = $262.50)"

#### 3. Recurring invoices
- When creating an invoice, toggle: "🔄 Make Recurring"
  - Frequency: Weekly / Bi-weekly / Monthly / Quarterly
  - Start date + end date (or "Indefinite")
- Recurring invoices stored separately in freelance data: `recurring_invoices: [...]`
- On module load, check if any recurring invoices are due:
  - If due, auto-generate the next invoice (copy line items, update dates, increment invoice number)
  - Show notification: "Auto-generated Invoice #INV-2026-0012 for Client ABC — $2,500"
- "Recurring" tab showing all recurring invoices:
  - Status: Active / Paused / Ended
  - Next due date
  - Pause/Resume/End buttons
  - History: link to all generated invoices from this recurring template

#### 4. Client management improvements
- **Client detail view**: click a client name to see a dedicated page:
  - Client info card: name, email, phone, address, notes, status
  - Revenue summary: total all-time, this year, this month
  - Project list with status and revenue per project
  - Invoice history with payment status and dates
  - Payment timeline chart (monthly revenue from this client)
  - Average days to payment
- **Client statuses**: Active / Inactive / Lead / Archived
- **Payment reliability score** (auto-calculated):
  - Compare each invoice's payment date to its due date
  - "Pays on time" (avg ≤ 0 days late), "Sometimes late" (avg 1-14 days), "Often late" (avg >14 days)
  - Display as a colored badge on the client card
- **Client notes**: rich text area (free text) stored per client
- **Quick contact**: if client email is set, show a "📧 Send Email" button that opens their default email client with a pre-filled subject line

#### 5. Financial overview tab
- New **"Overview"** tab at the top of Freelance Dashboard (first tab users see):
  - **Revenue metrics row**: This Month / This Quarter / This Year / All Time
  - **Average invoice value**
  - **Average days to payment** (across all clients)
  - **Top client by revenue** (with % of total)
  - **Outstanding receivables** total with list of unpaid invoices
  - **Revenue trend chart**: monthly revenue line chart for the last 12 months
  - **Client revenue breakdown**: horizontal bar chart, one bar per client, sorted by total revenue
  - **Invoice status pie chart**: Paid / Unpaid / Overdue
- **Tax estimate**:
  - User sets their tax rate in Settings (default 25%)
  - Show: "Estimated tax liability: $X based on $Y income at Z% rate"
  - Quarterly estimate: "Set aside $X per quarter for taxes"

#### 6. Expense tracking for freelancers
- New **"Expenses"** tab in Freelance Dashboard
- Add expense form: date, description, amount, category, client (optional — for billable expenses), receipt link (optional)
- Expense categories: Software, Hardware, Travel, Office Supplies, Marketing, Professional Services, Meals, Other
- Expense table with filters by category, client, date range
- Monthly expense summary chart
- **Profit & Loss view**:
  - Revenue (from paid invoices) − Expenses = Net Profit
  - P&L table by month for the last 12 months
  - P&L chart: revenue bars (green) vs expense bars (red) with net profit line
  - Profit margin calculation: Net Profit / Revenue × 100
- Export P&L as PDF (using ReportPDF class)

### Files to modify
`modules/job_tracker.py` (major expansion), `modules/settings.py` (invoice settings, logo upload, tax rate), `utils/report_builder.py` (template integration)

### Files to create
`utils/invoice_templates.py`

### Acceptance criteria
- [ ] 3 invoice templates render correctly as branded PDFs
- [ ] Custom logo appears on invoices when uploaded in Settings
- [ ] Invoice preview renders in-app before download
- [ ] Auto-incrementing invoice numbers (INV-YYYY-XXXX format)
- [ ] Tax, discount, and payment details on invoices
- [ ] Timer starts/stops and logs time entries correctly
- [ ] Manual time entry works
- [ ] "Generate Invoice from Time" creates correct line items
- [ ] Recurring invoices auto-generate when due
- [ ] Recurring invoices can be paused/resumed/ended
- [ ] Client detail view shows full history, revenue, and payment timeline
- [ ] Payment reliability score auto-calculated and displayed
- [ ] Overview tab shows all revenue metrics and charts
- [ ] Tax estimate calculates based on Settings rate
- [ ] Expense log with categories and client association
- [ ] P&L view shows revenue − expenses = net profit with chart
- [ ] P&L exportable as PDF
- [ ] All files pass `py_compile`

---

## V2.9 — Performance, Reliability, Testing & Data Integrity

**Theme:** Harden the entire app for production quality. Caching, graceful error handling, comprehensive test suite, data migrations, and logging.

### Tasks

#### 1. Performance optimization
- **API caching** — Add `@st.cache_data` decorators in `finance_api.py`:
  - `get_stock_price()`: TTL = 5 minutes
  - `get_crypto_price()`: TTL = 2 minutes
  - `get_stock_history()` / `get_crypto_history()`: TTL = 1 hour
  - Cache key should include the ticker and any parameters
- **Resource caching** — Add `@st.cache_resource` for:
  - Heavy imports or initializations
  - PDF template objects that don't change between renders
- **Lazy module loading**:
  - Currently all modules are imported on startup regardless of which page is active
  - Change `app.py` to only import the active module's render function on that page
  - Use `importlib.import_module()` for dynamic imports
- **Startup profiling**:
  - Add timing measurements to app startup (module imports, data loading, CSS injection)
  - Log results to help identify bottlenecks
  - Target: app should load in under 3 seconds on a modern machine
- **Data file caching**:
  - For read-heavy operations (e.g., dashboard loading multiple data files), cache the parsed data for the session
  - Use `st.session_state` with `get_mtime()` checks to invalidate when files change

#### 2. Comprehensive error handling
- **API resilience** — Wrap ALL external API calls (Yahoo Finance, CoinGecko, SMTP) in robust try/except:
  - `ConnectionError` / `Timeout` → "Unable to reach [service] — showing cached data" with a "Retry" button
  - `HTTPError 429` (rate limit) → "Rate limited by [service] — try again in 60 seconds" with countdown
  - `HTTPError 403/401` → "API access denied — check your configuration"
  - Any other exception → "Something went wrong fetching [data]. Error: [message]" with "Show Details" expander
  - ALWAYS fall back to last cached/known data rather than showing an empty state
- **JSON data validation** — Create `utils/validators.py`:
  - Schema definitions for every data file (required keys, types, defaults)
  - `validate_and_repair(filename, data)` function:
    - Checks all required keys exist
    - Adds missing keys with sensible defaults
    - Fixes type mismatches where possible (e.g., string "123" → int 123)
    - Logs all repairs made
    - Returns validated data
  - Call on every `load_json()` — never crash on malformed data
  - Schemas:
    - `budgets.json`: `{categories: {name: amount}}`
    - `goals.json`: `[{id, name, target, current, deadline, monthly, history}]`
    - `portfolio.json`: `{holdings: [...], alerts: [...], watchlist: [...]}`
    - `receipts.json`: `[{id, vendor, date, total, category, raw_text}]`
    - etc. for all data files
- **Graceful degradation**:
  - If a module fails to render (import error, data corruption), catch the exception and show a friendly error page with "Reset this module's data" option instead of crashing the whole app
  - Add a top-level try/except in `app.py` around the page routing

#### 3. Comprehensive test suite
- Create `tests/` directory with `pytest` configuration
- Add `pytest` and `pytest-cov` to `requirements.txt` (under a `[test]` extra or just directly)
- Test files:

  **`tests/test_data_persistence.py`** — most critical:
  - `test_save_load_roundtrip()`: save data → load → assert equal
  - `test_atomic_write_safety()`: simulate crash mid-write (mock os.replace to fail) → verify original file intact
  - `test_backup_creation()`: save 3 times → verify 3 backups exist
  - `test_backup_rotation()`: save 7 times → verify only 5 backups kept
  - `test_corruption_recovery()`: write corrupt JSON → load → verify it restores from backup
  - `test_empty_file_handling()`: load from non-existent file → returns default
  - `test_user_context_isolation()`: set user A context → save → set user B context → save → verify different directories

  **`tests/test_validators.py`**:
  - `test_valid_data_passes()`: well-formed data passes validation unchanged
  - `test_missing_keys_repaired()`: missing required key gets added with default
  - `test_type_mismatch_repaired()`: string number converted to int/float
  - `test_unknown_keys_preserved()`: extra keys not stripped (forward compatibility)

  **`tests/test_budget_tracker.py`**:
  - `test_category_mapping()`: known vendors map to correct categories
  - `test_template_loading()`: all 4 templates have correct structure
  - `test_spending_calculation()`: sum of transactions matches expected total
  - `test_custom_category_priority()`: custom categories checked before defaults

  **`tests/test_finance_api.py`** (with mocked HTTP responses):
  - `test_stock_price_success()`: mock yfinance → returns correct format
  - `test_stock_price_failure()`: mock failure → returns None / cached data
  - `test_crypto_price_success()`: mock CoinGecko → correct format
  - `test_rate_limit_handling()`: mock 429 → raises appropriate error
  - `test_history_data_format()`: verify returned DataFrame columns

  **`tests/test_fuzzy_matcher.py`**:
  - `test_normalize_description()`: removes dates, IDs, excess spaces
  - `test_group_similar()`: "NETFLIX INC" and "Netflix" grouped together
  - `test_threshold_sensitivity()`: different thresholds produce different groupings
  - `test_empty_input()`: empty list returns empty groups

  **`tests/test_pdf_parser.py`** (using sample PDFs):
  - `test_extract_vendor()`: correct vendor from sample receipt
  - `test_extract_total()`: correct total from various format receipts
  - `test_extract_date()`: correct date from various formats
  - `test_guess_category()`: known vendors categorized correctly

  **`tests/test_notifications.py`**:
  - `test_create_notification()`: creates and saves correctly
  - `test_unread_count()`: counts unread accurately
  - `test_mark_read()`: marks individual notification read
  - `test_auto_cleanup()`: notifications older than 30 days removed
  - `test_budget_alert_triggers()`: 80% threshold triggers warning

  **`tests/test_auth.py`** (if auth system exists from v2.4):
  - `test_register_user()`: creates user with hashed password
  - `test_login_success()`: correct credentials authenticate
  - `test_login_failure()`: wrong password rejects
  - `test_duplicate_email()`: second registration with same email fails
  - `test_password_hash_security()`: stored password is bcrypt hash, not plaintext
  - `test_user_context_sets_path()`: after login, data path points to user directory

  **`tests/test_formatting.py`**:
  - `test_format_currency_usd()`: 1234.56 → "$1,234.56"
  - `test_format_currency_eur()`: 1234.56 → "€1,234.56"
  - `test_format_date_us()`: datetime → "03/29/2026"
  - `test_format_date_iso()`: datetime → "2026-03-29"

  **`tests/test_insights.py`**:
  - `test_spending_increase_detected()`: 3-month increasing trend generates insight
  - `test_unusual_spike_detected()`: >50% above average triggers insight
  - `test_no_data_no_crash()`: empty data produces no insights (not an error)

- **`tests/conftest.py`**: shared fixtures (temp data directory, sample data, mock settings)
- **`pytest.ini`** or section in `pyproject.toml`:
  ```ini
  [pytest]
  testpaths = tests
  python_files = test_*.py
  python_functions = test_*
  addopts = -v --tb=short
  ```

#### 4. Data migration framework
- Create `utils/migrations.py`:
  - Each data file gets a `_schema_version` field (integer, starting at 1)
  - Migration registry: `MIGRATIONS = {filename: [(from_version, to_version, migration_fn), ...]}`
  - `run_migrations()` called on app startup:
    - For each data file, check current `_schema_version` vs expected version
    - Apply all pending migrations in order
    - Each migration function receives the data dict and returns the modified data dict
  - Migrations must be **idempotent** (safe to run twice — check before modifying)
  - Example migrations already needed:
    - `freelance_data.json`: v0→v1: add `_schema_version`, ensure `clients` and `invoices` keys exist
    - `portfolio.json`: v0→v1: add `_schema_version`, ensure `lots` key exists on each holding
    - `settings.json`: v0→v1: add `notifications` preferences, add `categories` array
  - Log all applied migrations
- On first run with migration framework, stamp all existing files with `_schema_version: 1`

#### 5. Logging system
- Create `utils/logger.py`:
  - Configured Python `logging` with `RotatingFileHandler`
  - Log file: `data/financekit.log`
  - Rotation: max 5MB per file, keep 3 rotated copies
  - Format: `[2026-03-29 14:30:00] [INFO] [module_name] Message`
  - Log levels: DEBUG, INFO, WARNING, ERROR
- Events to log:
  - **INFO**: App startup (with version), module navigation, data save/load, successful API calls, user login/logout, migration applied
  - **WARNING**: API fallback to cache, data validation repairs, deprecated feature usage
  - **ERROR**: API failures, JSON corruption, unhandled exceptions, auth failures
- Add logging calls throughout the codebase (non-intrusive — just add `.info()` / `.error()` calls alongside existing logic)
- **Settings → "🔍 Logs" section**:
  - Show last 100 log lines in a scrollable code block
  - Filter by level (ALL / INFO / WARNING / ERROR)
  - "Download Full Log" button
  - "Clear Logs" button with confirmation

#### 6. Health check endpoint
- Add a simple self-diagnostic that runs on Settings page or via a "Run Health Check" button:
  - ✅/❌ Python version compatible
  - ✅/❌ All required packages installed (check each import)
  - ✅/❌ Data directory writable
  - ✅/❌ All data files valid JSON
  - ✅/❌ Backup directory exists and has space
  - ✅/❌ Internet connectivity (ping CoinGecko API)
  - ✅/❌ SMTP configured and working (optional)
  - ✅/❌ All migrations applied
  - Show results as a checklist with green checks and red X's

### Files to modify
`app.py` (lazy loading, top-level error handling), `utils/finance_api.py` (caching + error handling), `utils/data_persistence.py` (validation on load), `modules/settings.py` (logs viewer, health check), `requirements.txt` (pytest)

### Files to create
`utils/validators.py`, `utils/migrations.py`, `utils/logger.py`, `tests/conftest.py`, `tests/test_data_persistence.py`, `tests/test_validators.py`, `tests/test_budget_tracker.py`, `tests/test_finance_api.py`, `tests/test_fuzzy_matcher.py`, `tests/test_pdf_parser.py`, `tests/test_notifications.py`, `tests/test_auth.py`, `tests/test_formatting.py`, `tests/test_insights.py`, `pytest.ini`

### Acceptance criteria
- [ ] API calls use `@st.cache_data` with correct TTLs
- [ ] API failures show friendly error + retry button, fallback to cached data
- [ ] Rate limit (429) detected and shown with countdown
- [ ] All data files validated on load — missing keys auto-repaired
- [ ] Module render failures caught and shown as friendly error page
- [ ] Lazy module loading reduces startup time measurably
- [ ] ALL tests pass with `pytest tests/ -v`
- [ ] Test coverage >80% on utility functions (check with `pytest --cov`)
- [ ] Data migrations apply automatically on startup
- [ ] Migrations are idempotent (running twice produces same result)
- [ ] Log file created with rotating handler
- [ ] Settings shows filterable log viewer
- [ ] Health check reports status of all system components
- [ ] App startup under 3 seconds on modern hardware
- [ ] All files pass `py_compile`

---

## V3.0 — Final Polish, Onboarding Redesign & Relaunch

**Theme:** The app should feel complete, professional, and worth every penny. Redesign the first-run experience, polish every surface, update all documentation, and prepare for Gumroad relaunch.

### Tasks

#### 1. Onboarding redesign
- Replace the current 3-step welcome wizard with a polished 5-step experience:
  - **Step 1 — Welcome**: FinanceKit logo animation (CSS), "Let's set up your financial toolkit" heading, "Get Started" button
  - **Step 2 — Profile**: Name, email, currency, date format (from Settings schema)
  - **Step 3 — Choose Your Modules**: Show all 7 modules as toggle cards with icon + description. Default: all on. User can disable any they don't need. Disabled modules hidden from sidebar (re-enable anytime in Settings)
  - **Step 4 — Import Data**: Three options presented as cards:
    - "📄 Import bank CSV" → file uploader with auto-detect
    - "📦 Import from backup" → upload a FinanceKit export zip
    - "🆕 Start fresh" → skip
  - **Step 5 — Quick Tour**: Animated walkthrough with 4 slides:
    - "Your dashboard shows everything at a glance" (with illustration)
    - "Track budgets and see where your money goes" (with illustration)
    - "Set goals and watch your progress" (with illustration)
    - "Generate reports and export PDFs anytime" (with illustration)
  - Each step should have a progress bar at top, back/next buttons, and a "Skip setup" link
- Save all preferences to `settings.json`:
  - `enabled_modules: ["budget", "goals", "receipts", ...]`
  - `onboarding_complete: true`
  - `onboarding_completed_at: "ISO datetime"`

#### 2. Dashboard final redesign
- Only show data from modules the user has enabled
- Layout:
  - **Top row**: Financial Health Score gauge + Net Worth card + Quick Stats (based on enabled modules)
  - **Alert bar**: Recent unread notifications (from v2.5)
  - **Quick Actions row**: 4 large icon buttons for the most common actions:
    - "➕ Transaction" → Budget Tracker
    - "🧾 Receipt" → Receipt Scanner
    - "📊 Report" → Report Generator
    - Custom 4th button (user-configurable in Settings)
  - **Module widgets**: Compact summary cards for each enabled module showing key stats
  - **Recent Activity feed**: Last 10 actions across all modules
    - Store in `data/activity_log.json`: `[{action, module, description, timestamp}]`
    - Log activity from: transaction added, receipt scanned, goal updated, invoice created, holding added/sold, subscription decision changed, report generated
    - Show as a timeline: "📈 Added 10 shares of AAPL — 2 hours ago"
- Widget order configurable in Settings (pick top 4 modules to show as large widgets, rest as compact)

#### 3. Print & export polish
- **PDF consistency**: Audit all PDF outputs (reports, invoices, guide) for:
  - Same header style (indigo bar + FinanceKit branding)
  - Same font sizing hierarchy
  - Charts at 300 DPI print resolution (increase `scale` in kaleido)
  - Proper page breaks (no cut-off tables or charts)
  - Footer with page numbers on every page
- **Browser print support**: Add `@media print` CSS:
  - Hide sidebar, navigation, buttons, and interactive elements
  - Show content in clean, readable layout
  - Adjust colors for print (darker text, lighter backgrounds, no dark theme)
  - Page break hints before each section
- **Bulk export**: "📥 Download All" button in Report Generator:
  - Generates all available reports as individual PDFs
  - Bundles into a single ZIP for download
  - Include a summary index page listing all included reports

#### 4. Accessibility sweep
- Ensure sufficient color contrast in both themes (WCAG AA: 4.5:1 for text, 3:1 for large text)
- Add `aria-label` attributes to all custom HTML interactive elements
- Ensure all charts have `alt` text or text descriptions
- Tab order should follow logical reading order
- Screen reader-friendly: all icons have text alternatives (not just emoji)
- Test with browser accessibility audit (Lighthouse)

#### 5. Demo app complete update
- Rewrite `demo/app_demo.py` to showcase v3.0:
  - Updated hero section with v3.0 features
  - New screenshots/mockups for: login page, notification center, budget analytics, net worth tracker, financial health score, invoice templates, time tracking
  - Updated feature comparison table with all new features
  - Updated FAQ with questions about auth, multi-user, data security
  - Updated pricing section
  - Social proof section: update numbers
  - The free Budget Tracker sample should include the Analytics tab (read-only demo data)

#### 6. Complete documentation rewrite
- **README.md** — full rewrite:
  - Product hero: name, one-liner, badges (version, Python, license)
  - "What's New in v3.0" highlights section
  - Feature overview with all modules listed
  - Screenshots section (placeholder paths — user will add actual screenshots)
  - Quick start instructions (Windows, Mac, Linux)
  - Authentication setup quick guide (link to GUIDE.md for details)
  - Requirements and dependencies
  - File structure tree (updated)
  - FAQ
  - License

- **GUIDE.md** — complete rewrite covering:
  - Getting started (installation, first run, onboarding)
  - Authentication setup (Google OAuth, GitHub OAuth, local accounts)
  - Each of the 7 modules (detailed walkthrough of every feature)
  - Settings (all sections)
  - Notifications (how they work, preferences)
  - Analytics (budget analysis, net worth, health score)
  - Freelance features (time tracking, invoicing, P&L)
  - Data management (backup, restore, export, import)
  - Keyboard shortcuts reference
  - Troubleshooting (common issues and fixes)

- **GUMROAD_GUIDE.md** — update with:
  - New v3.0 product description copy
  - Updated feature list for Gumroad listing
  - New comparison table

- **CHANGELOG.md** — create from scratch:
  - Entry for every version from v2.1 → v3.0
  - Format: `## v2.X — Title` with bullet points for each change
  - Group changes by: Added, Changed, Fixed

- **New Gumroad assets**: Update `assets/` HTML files:
  - Change version badge to v3.0 on thumbnail
  - Add new feature showcase images for: authentication, notifications, analytics dashboard, invoice templates
  - Keep the same 1280x720 format and dark theme style

#### 7. Code quality sweep
- Run through EVERY Python file and ensure:
  - No unused imports (remove all)
  - No commented-out code blocks (remove all)
  - No `# TODO` or `# FIXME` or `# HACK` comments
  - No placeholder text or "lorem ipsum" in user-facing strings
  - Consistent naming: snake_case for functions/variables, PascalCase for classes
  - All error messages are helpful and actionable
  - No hardcoded color values — all using CSS variables (from v2.3)
  - No hardcoded currency symbols — all using formatting utilities (from v2.2)
  - No duplicate code blocks — extract shared logic to utilities
  - Docstrings on all public functions (module-level and class-level)
- **requirements.txt** audit:
  - Pin ALL versions exactly (already done, but verify)
  - Add any new dependencies from v2.2-v2.9
  - Remove any unused dependencies
  - Add a comment next to each explaining what it's for:
    ```
    streamlit==1.45.0       # Web framework
    pandas==2.2.3           # Data manipulation
    ...
    ```
- **start.bat / start.sh** verification:
  - Test on fresh install (new machine simulation: delete `.deps_installed`, delete venv)
  - Ensure all new dependencies install correctly
  - Ensure the app starts without errors
  - Add `--server.port 8501` explicitly for predictable behavior

#### 8. Version finalization
- Update `version.txt` to `3.0`
- Verify version shows correctly in: app sidebar, app footer, Settings About page, demo app, README
- Final commit: `FinanceKit v3.0 — authentication, notifications, analytics, invoicing, professional polish`
- Push to both repos

### Files to modify
Essentially every file in the project — this is the final comprehensive sweep.

### Files to create
`CHANGELOG.md`, new `assets/` HTML images for v3.0 features, `data/activity_log.json` (schema)

### Acceptance criteria
- [ ] Onboarding wizard has 5 polished steps with progress bar
- [ ] Module selection during onboarding hides disabled modules from sidebar
- [ ] Dashboard shows only enabled modules' data
- [ ] Quick Actions row navigates correctly
- [ ] Recent Activity feed shows last 10 cross-module actions
- [ ] All PDFs have consistent branding, proper page breaks, 300 DPI charts
- [ ] `@media print` CSS hides UI chrome and formats content for printing
- [ ] Bulk export creates a zip of all reports
- [ ] Color contrast passes WCAG AA in both themes
- [ ] Demo app showcases all v3.0 features
- [ ] README.md is comprehensive and professional
- [ ] GUIDE.md covers every feature with detailed walkthroughs
- [ ] CHANGELOG.md covers all versions v2.1 → v3.0
- [ ] New Gumroad asset images created for v3.0 features
- [ ] Zero unused imports across entire codebase
- [ ] Zero TODO/FIXME/HACK comments
- [ ] Zero hardcoded colors or currency symbols
- [ ] All public functions have docstrings
- [ ] requirements.txt has comments and exact pins for all packages
- [ ] start.bat and start.sh work on fresh install
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] App feels professional, polished, and complete end-to-end
- [ ] Version 3.0 displayed correctly everywhere

---

## Execution Rules

1. **One version at a time.** Complete v2.2 fully before starting v2.3. Commit and push after each version.
2. **Ask before starting each version.** After completing one, summarize what was done and ask if I want to proceed, make changes, or adjust the roadmap.
3. **Commit message format:** `FinanceKit vX.Y — short description of what this version adds`
4. **Test after each version.** At minimum: all files pass `py_compile`, app launches without errors, and the new features work as described.
5. **Don't skip steps.** If a task in a version turns out to be more complex than expected, implement it properly — don't stub it out or leave TODO comments.
6. **Backwards compatibility is non-negotiable.** Each version must work with data from the previous version. If data schemas change, add a migration in `utils/migrations.py` (from v2.9, but add inline migration logic in earlier versions if needed).
7. **Keep it local-first.** Auth is optional (off by default). The app must always work fully without internet (except for live market prices in Portfolio Tracker). Never require a cloud service, external database, or paid API.
8. **Update the version number** in `version.txt` (and thus `app.py` sidebar + footer) at the end of each version.
9. **Read before writing.** Always read the current state of files you're about to modify. The codebase changes with each version — don't assume file contents from the roadmap description.
10. **Don't over-engineer.** Each task should be implemented in the simplest way that works correctly. Prefer readable code over clever code. If something doesn't need to be abstracted, don't abstract it.

Start with **v2.2**. Read the current state of all files you'll need to modify before making any changes.
