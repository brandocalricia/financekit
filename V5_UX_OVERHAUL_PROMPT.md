# FinanceKit v4.2 - v5.0 — UX Overhaul Prompt

> **For a new Claude Code session.** This prompt contains everything needed to implement versions 4.2 through 5.0 of FinanceKit. Each version should be implemented sequentially: code it, run tests, commit with the format `FinanceKit vX.X — Short Description`, and push. Do not skip versions. Do not ask questions — use your best judgment. Read the full codebase before starting.

---

## Project Context

**Repository**: `https://github.com/brandocalricia/financekit.git`
**Working directory**: `C:\Users\bzcni\OneDrive\Desktop\vs code projects\Finance Toolkit`
**Current version**: 4.1 (version.txt says 4.0 — update it)
**Python**: 3.11 (pinned in `runtime.txt` for Streamlit Cloud)
**Framework**: Streamlit 1.45.0
**Deployment**: Streamlit Community Cloud at `financekit.streamlit.app`
**Tests**: 123 tests in `tests/` — all must pass after every version
**Total codebase**: ~13,200 lines across 30+ Python files

### Critical Rules
- **NEVER use `use_container_width=True/False`** — Streamlit 1.45 deprecated it. Use `width='stretch'` or `width='content'` instead.
- **NEVER hardcode dark-mode colors in CSS or inline styles.** Always use CSS custom properties (`var(--fk-*)`).
- **NEVER add packages that require C compilation** (like `kaleido`, `pytesseract`) to `requirements.txt` — they break Streamlit Cloud. Keep them commented out as desktop-only.
- **Commit format**: `FinanceKit vX.X — Short Description` with `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
- **All data files** are in `data/` (gitignored). Per-user data goes in `data/users/{user_id}/`.
- **Google OAuth** credentials come from `st.secrets["google"]` (cloud) or `data/auth_config.json` (local). The helper `get_google_credentials()` in `utils/auth.py` handles both.

### Architecture Overview

```
app.py (2167 lines)          — Main app: CSS, auth gate, landing page, login, sidebar, dashboard, routing
modules/
  budget_tracker.py (1530)   — Budget categories, transactions, spending charts, bills
  settings.py (1333)         — 9-tab settings page (Profile, Modules, Household, Email, Invoice, Auth, Notifications, Data, About)
  job_tracker.py (1313)      — Freelance: clients, invoices, time tracking, recurring invoices
  subscription_auditor.py (869) — Subscription detection, price tracking, cancellation
  report_generator.py (817)  — CSV/OFX import, bank detection, PDF/Excel export
  portfolio_tracker.py (666) — Stock/crypto holdings, watchlist, alerts
  goal_tracker.py (360)      — Savings goals, milestones, shared household goals
  receipt_scanner.py (288)   — PDF/image upload, text extraction, category guessing
utils/
  auth.py (369)              — Email/password + Google OAuth, session management
  data_persistence.py (147)  — JSON storage, per-user isolation, atomic writes, backups
  notifications.py (297)     — Notification system, email digest, deduplication
  chart_config.py (71)       — Plotly theme (dark/light), apply_layout(), CHART_COLORS
  formatting.py (118)        — format_currency(), format_date(), currency symbols
  search.py (139)            — Global full-text search across all modules
  invoice_templates.py (613) — Invoice PDF/HTML rendering
  importers.py (345)         — YNAB, Mint, Monarch, OFX importers
  insights.py (305)          — Financial insights engine
  household.py (196)         — Household expense splitting
  report_builder.py (199)    — PDF report generation (fpdf2)
  validators.py (229)        — Data schema validation
  migrations.py (155)        — Schema migrations
  category_learner.py (128)  — Auto-categorization rules
  finance_api.py (158)       — Stock/crypto price fetching
  activity_log.py (98)       — Activity logging
  pdf_parser.py (123)        — PDF text extraction
  fuzzy_matcher.py (42)      — Transaction deduplication
  ui_helpers.py (40)         — Module header rendering
  logger.py (67)             — Logging utilities
.streamlit/config.toml       — base="dark", primaryColor="#6366f1"
runtime.txt                  — python-3.11
requirements.txt             — 15 dependencies (loose version pins, no C-compiled packages)
```

### CSS Theme System (How It Works Now)

In `app.py` lines 95-157, two sets of CSS custom properties are defined:
- `_dark_vars` — 25 variables for dark mode (bg: #0f1117, text: #e2e8f0, cards: #1e1e2f, etc.)
- `_light_vars` — 25 variables for light mode (bg: #f8fafc, text: #1e293b, cards: #ffffff, etc.)

The active set is injected into `:root` based on `st.session_state.fk_theme`. Then ~400 lines of CSS use these variables for styling every component.

**Known theme issues** (YOU MUST FIX ALL OF THESE):
1. Text is unreadable in light mode — many elements don't pick up `var(--fk-text)` because Streamlit injects its own dark-mode colors that override CSS variables
2. `.stApp`, `[data-testid="stAppViewContainer"]`, `[data-testid="stMainBlockContainer"]` need explicit `color` and `background-color` with `!important`
3. All `<h1>` through `<h6>`, `<p>`, `<span>`, `<label>`, `<li>` inside `.stApp` must have `color: var(--fk-text) !important`
4. Form inputs (`stTextInput`, `stNumberInput`, `stSelectbox`, `stDateInput`) need `color` and `background-color`
5. Tabs, expanders, metric values, dataframe cells all need theme-aware colors
6. `.stApp header[data-testid="stHeader"]` needs matching background
7. Email digest HTML in `utils/notifications.py` (line ~236) hardcodes dark colors — must use neutral colors or detect theme

### Authentication System (How It Works Now)

- `is_auth_required()` always returns `True`
- Unauthenticated users see `_show_landing_page()` — a feature showcase with Sign In / Create Account CTAs
- Clicking either sets `st.session_state.show_auth = True` and shows `_show_login_page()`
- Login page has Google OAuth (via `streamlit-google-auth`) + email/password form
- Registration auto-logs in after account creation
- Password reset uses a local token system (no email — token displayed on screen)
- `login_oauth_user()` auto-creates accounts for first-time Google users

**Known auth issues** (YOU MUST FIX):
1. Google Sign-In button doesn't render — the `streamlit-google-auth` library's `.login()` method may not be rendering properly. Debug this. If the library is unreliable, implement Google OAuth manually using `requests` + Streamlit query params (authorization code flow).
2. The redirect URI is hardcoded to `http://localhost:8501` for local and tries to auto-detect for cloud — this is fragile. Make it configurable via `st.secrets` or `auth_config.json`.
3. `streamlit-google-auth` IS in `requirements.txt` but may fail to install on some platforms. Add a graceful fallback.

---

## Version 4.2 — Theme System Complete Overhaul

**Goal**: Light mode and dark mode both look polished and professional. Every single element on every single page must be readable and styled correctly in both themes. The theme toggle must be in Settings, not floating in the sidebar.

### Tasks

1. **Move theme toggle from sidebar to Settings page**
   - Remove the theme toggle button from the sidebar (currently at lines ~1355-1372 in `app.py`)
   - Add a "Theme" section at the TOP of the Settings page (first thing users see in Settings, before Profile tab)
   - Use a clean toggle or segmented control: `[☀️ Light]  [🌙 Dark]  [🖥️ System]`
   - "System" mode should detect browser preference via JavaScript injection: `window.matchMedia('(prefers-color-scheme: dark)').matches`
   - Persist theme choice to `settings.json` → `theme: "light" | "dark" | "system"`
   - Show a live preview swatch of the theme before applying

2. **Fix ALL light mode text readability issues**
   - Add comprehensive CSS rules that target every Streamlit element:
   ```css
   /* Main containers */
   .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"],
   .main, .block-container {
       background-color: var(--fk-bg) !important;
       color: var(--fk-text) !important;
   }

   /* Header */
   .stApp header[data-testid="stHeader"] {
       background-color: var(--fk-bg) !important;
   }

   /* ALL text elements */
   .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
   .stApp p, .stApp span, .stApp li, .stApp label, .stApp td, .stApp th,
   .stApp div, .stApp a {
       color: var(--fk-text) !important;
   }

   /* Muted text (captions, help text) */
   .stApp .stCaption, .stApp small, [data-testid="stCaptionContainer"] {
       color: var(--fk-text-muted) !important;
   }

   /* Form inputs */
   .stApp input, .stApp textarea, .stApp select,
   [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
   [data-testid="stDateInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"],
   .stSelectbox > div > div {
       background-color: var(--fk-input-bg) !important;
       color: var(--fk-text) !important;
       border-color: var(--fk-border) !important;
   }

   /* Tabs */
   .stTabs [data-baseweb="tab-list"] button {
       color: var(--fk-text-muted) !important;
   }
   .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
       color: var(--fk-accent) !important;
   }

   /* Expanders */
   .stExpander, [data-testid="stExpander"] {
       background-color: var(--fk-card) !important;
       border-color: var(--fk-border) !important;
   }
   .stExpander summary span {
       color: var(--fk-text) !important;
   }

   /* Metrics */
   [data-testid="stMetric"] label, [data-testid="stMetric"] [data-testid="stMetricValue"],
   [data-testid="stMetric"] [data-testid="stMetricDelta"] {
       color: var(--fk-text) !important;
   }

   /* Dataframes */
   .stDataFrame, [data-testid="stDataFrame"] th, [data-testid="stDataFrame"] td {
       color: var(--fk-text) !important;
       background-color: var(--fk-card) !important;
   }

   /* Sidebar */
   section[data-testid="stSidebar"] {
       background-color: var(--fk-sidebar-bg) !important;
       color: var(--fk-text) !important;
   }
   section[data-testid="stSidebar"] * {
       color: var(--fk-text) !important;
   }

   /* Buttons */
   .stButton button {
       color: var(--fk-text) !important;
       border-color: var(--fk-border) !important;
   }
   .stButton button[kind="primary"] {
       background-color: var(--fk-accent) !important;
       color: white !important;
       border: none !important;
   }

   /* Dialogs/modals */
   [data-testid="stModal"] > div {
       background-color: var(--fk-card) !important;
   }

   /* Tooltips */
   [data-testid="stTooltipContent"] {
       background-color: var(--fk-card) !important;
       color: var(--fk-text) !important;
   }

   /* Radio buttons, checkboxes */
   .stRadio label, .stCheckbox label {
       color: var(--fk-text) !important;
   }

   /* Toast notifications */
   [data-testid="stToast"] {
       background-color: var(--fk-card) !important;
       color: var(--fk-text) !important;
   }
   ```
   - **Test every single page** in both themes after applying. Go through Dashboard, Budget Tracker, Portfolio, Receipts, Goals, Freelance, Subscriptions, Reports, Settings — every one must be readable.

3. **Fix all inline hardcoded colors throughout the codebase**
   - Search every `.py` file for hardcoded hex colors in `st.markdown()` calls: `#0f1117`, `#1e1e2f`, `#e2e8f0`, `#2a2a40`, etc.
   - Replace them all with `var(--fk-*)` equivalents
   - Pay special attention to:
     - `utils/notifications.py` — email digest HTML uses hardcoded dark colors
     - `modules/job_tracker.py` — invoice preview HTML may hardcode colors
     - `utils/invoice_templates.py` — invoice HTML templates
     - `modules/budget_tracker.py` — spending alert boxes
     - `modules/portfolio_tracker.py` — gain/loss coloring
   - Exception: `var(--fk-success)` green, `var(--fk-danger)` red, `var(--fk-warning)` amber are fine for semantic colors (profit/loss indicators) — just make sure they have enough contrast against both light and dark backgrounds.

4. **Update `chart_config.py`**
   - Expand `CHART_COLORS` from 6 to at least 12 colors so categories don't repeat:
   ```python
   CHART_COLORS = [
       "#6366f1", "#a78bfa", "#8b5cf6", "#22c55e", "#f59e0b", "#ef4444",
       "#06b6d4", "#ec4899", "#14b8a6", "#f97316", "#84cc16", "#64748b",
   ]
   ```
   - Make sure `donut_layout()` legend text color is theme-aware

5. **Update `.streamlit/config.toml`**
   - Keep `base = "dark"` (Streamlit needs a base) but add a comment that the actual theme is handled by CSS variables
   - The CSS must override everything Streamlit sets, so `!important` is required on all rules

6. **Fix the `_data_dir()` theme persistence path**
   - The theme toggle in the sidebar (being moved to settings) currently uses `_data_dir()` which may not resolve correctly for unauthenticated users or before user context is set
   - Theme should persist to the global `data/settings.json` for default, and per-user `data/users/{user_id}/settings.json` for logged-in users

### Verification
- Launch the app locally (`streamlit run app.py`)
- Toggle between light and dark mode on EVERY page
- Take note of any element where text is invisible or hard to read — fix it
- Check charts, forms, tables, metrics, sidebar, modals, toasts, notifications

---

## Version 4.3 — Google Sign-In Fix & Auth Polish

**Goal**: Google Sign-In actually works. The login/registration flow is smooth, professional, and handles edge cases gracefully.

### Tasks

1. **Fix Google Sign-In**
   - Debug why the Google sign-in button isn't rendering on Streamlit Cloud
   - The `streamlit-google-auth` library uses `st.session_state["connected"]` — check if this conflicts with any other session state
   - **If `streamlit-google-auth` is unreliable**, implement Google OAuth manually:
     ```python
     # Manual Google OAuth flow:
     # 1. Generate authorization URL with client_id, redirect_uri, scope
     # 2. Show "Sign in with Google" button that links to the auth URL
     # 3. Google redirects back with ?code=... in query params
     # 4. Exchange code for access token via POST to googleapis.com/oauth2/v4/token
     # 5. Fetch user info from googleapis.com/oauth2/v3/userinfo
     # 6. Call login_oauth_user() and set session state

     import urllib.parse

     GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
     GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
     GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

     def _get_redirect_uri():
         """Get the correct redirect URI for the current environment."""
         # Check Streamlit secrets first
         try:
             return st.secrets.get("google", {}).get("redirect_uri", "")
         except:
             pass
         # Auto-detect
         if os.environ.get("STREAMLIT_SHARING_MODE"):
             return f"https://{os.environ.get('HOSTNAME', 'localhost')}"
         return "http://localhost:8501"

     def _google_auth_url():
         params = {
             "client_id": client_id,
             "redirect_uri": _get_redirect_uri(),
             "response_type": "code",
             "scope": "openid email profile",
             "access_type": "offline",
             "prompt": "select_account",
         }
         return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

     def _exchange_code(code):
         resp = requests.post(GOOGLE_TOKEN_URL, data={
             "code": code,
             "client_id": client_id,
             "client_secret": client_secret,
             "redirect_uri": _get_redirect_uri(),
             "grant_type": "authorization_code",
         })
         return resp.json()

     def _get_user_info(access_token):
         resp = requests.get(GOOGLE_USERINFO_URL, headers={
             "Authorization": f"Bearer {access_token}",
         })
         return resp.json()
     ```
   - Add `redirect_uri` to the secrets format:
     ```toml
     [google]
     client_id = "..."
     client_secret = "..."
     redirect_uri = "https://financekit.streamlit.app"
     ```
   - Update `get_google_credentials()` in `utils/auth.py` to also return `redirect_uri`

2. **Style the Google button properly**
   - Use Google's brand guidelines: white button with Google "G" logo, "Sign in with Google" text
   - SVG of Google logo inline or as base64
   - Match this exact style:
   ```html
   <button style="display:flex;align-items:center;gap:12px;padding:10px 24px;
     background:white;border:1px solid #dadce0;border-radius:8px;cursor:pointer;
     font-size:14px;font-weight:500;color:#3c4043;width:100%;justify-content:center;">
     <svg width="18" height="18" viewBox="0 0 18 18"><!-- Google G logo SVG --></svg>
     Sign in with Google
   </button>
   ```

3. **Handle OAuth callback in `app.py`**
   - On page load, check `st.query_params` for `code` parameter
   - If present, exchange for token, fetch user info, log in, clear query params
   - Show a spinner during the exchange ("Signing you in...")
   - Handle errors gracefully (expired code, invalid code, network error)

4. **Improve email registration UX**
   - Add password requirements hint below password field: "At least 8 characters with a mix of letters, numbers, and symbols"
   - Increase minimum password from 6 to 8 characters
   - Add email validation (must contain `@` and a `.` after the `@`)
   - Show "Signing you in..." spinner after successful registration
   - Add "Already have an account? Sign In" link below register form (currently exists but should be more prominent)

5. **Add "Remember me" for Google users**
   - Currently hardcoded to `remember_me = True` for Google — make this respect a checkbox

6. **Session management polish**
   - Show session expiry warning 1 hour before expiry: "Your session expires soon. Click to extend."
   - Add "Sign out of all devices" button in Settings > Authentication (clears all sessions by changing a per-user secret)

### Verification
- Deploy to Streamlit Cloud and test Google Sign-In end-to-end
- Test email registration and login
- Test session expiry behavior
- Verify the Google button renders correctly

---

## Version 4.4 — Settings Page Redesign

**Goal**: The Settings page is clean, organized, well-sectioned, and every setting works correctly in both themes. It should feel like a native app's settings, not a Streamlit demo.

### Tasks

1. **Reorganize Settings into clear sections**
   - Replace the current 9-tab layout with a single-page layout using `st.expander` groups:
     - **Appearance** (theme toggle, accent color picker, font size)
     - **Account** (profile info, change password, delete account)
     - **Modules** (enable/disable modules)
     - **Categories** (manage budget categories, tax-deductible toggles)
     - **Notifications** (per-module notification toggles, email digest, DND hours)
     - **Data & Privacy** (export data, import backup, clear data, file stats)
     - **Household** (if enabled — member management, splitting rules)
     - **Authentication** (OAuth credentials, session timeout — admin only)
     - **About** (version, changelog, links)
   - Each section header has an icon and description

2. **Appearance section** (new, top of page)
   - Theme toggle: `[☀️ Light]  [🌙 Dark]  [🖥️ System]` — 3 buttons in a row
   - Accent color picker: Let users choose from 6 preset accent colors (Indigo, Blue, Green, Purple, Orange, Rose) — this changes `--fk-accent`
   - Font size: Small / Medium / Large — adjusts base font size
   - Preview card that shows how the current theme looks

3. **Account section polish**
   - Show avatar circle with initials (or Google profile picture if OAuth user)
   - Clean form: Name, Email (read-only for OAuth users), Currency, Date Format
   - "Change Password" in a sub-expander (only for email users, hidden for Google users)
   - "Delete Account" with red button and confirmation dialog ("Type DELETE to confirm")

4. **Categories section**
   - Show categories in a clean card grid instead of a markdown table
   - Each card: category emoji + name, "Tax Deductible" badge, edit/delete buttons
   - Drag-to-reorder (use numbered columns as a workaround since Streamlit doesn't support drag)
   - "Add Category" button opens a form: name, emoji/icon, tax-deductible checkbox
   - Confirm before deleting a category that has transactions

5. **Notifications section**
   - Master toggle at top: "Enable Notifications"
   - Per-module toggles in a clean grid
   - Email digest settings: frequency, last sent time
   - "Test Notification" button that creates a sample notification

6. **Data & Privacy section**
   - File statistics: show each JSON file with record count and file size
   - "Export All Data" → downloads a ZIP of all user JSON files
   - "Import Backup" → upload a ZIP to restore
   - "Clear All Data" with confirmation dialog
   - Privacy note: "Your data is stored per-account and never shared."

7. **Fix all settings crashes**
   - Ensure all imports are at the top of `modules/settings.py`
   - Add try/except around every settings save operation
   - Validate all form inputs before saving

### Verification
- Every settings section loads without errors
- Changes persist after page reload
- Theme changes apply instantly across the app
- Category add/edit/delete works correctly
- Data export and import work

---

## Version 4.5 — Landing Page & Onboarding Redesign

**Goal**: The landing page converts visitors into users. The onboarding experience is smooth and gets users to their first "aha moment" fast.

### Tasks

1. **Redesign the landing page** (`_show_landing_page()` in app.py)
   - Hero section with app name, tagline, and CTA
   - Clean, centered layout (max-width 900px)
   - Feature section: 3 columns, each with icon, title, 1-line description
   - Social proof section: "Trusted by X users" (use `get_user_count()` or a minimum of "100+")
   - Testimonial/quote section (placeholder or generated)
   - Bottom CTA: large "Get Started — Free" button
   - Footer: "Made with [heart] for your finances" and version number
   - All CSS variables — must look good in both themes
   - Smooth, professional feel — no visual clutter

2. **Improve login page design**
   - Center the form vertically AND horizontally (not just column centering)
   - Google button on top, full width, with proper Google branding
   - Clean divider: "─── or ───"
   - Email form below with rounded inputs
   - "Forgot password?" as a link (not a button)
   - "Don't have an account? **Create one**" below the form (not side-by-side buttons)
   - Match the style of modern SaaS login pages (clean, spacious, trustworthy)

3. **Improve registration page**
   - Same centered layout as login
   - Google button on top (auto-creates account)
   - "─── or sign up with email ───"
   - Clean form: Name, Email, Password (with inline strength meter), Confirm Password
   - Terms checkbox: "I agree to the Terms of Service" (link to a simple terms modal)
   - "Already have an account? **Sign in**" link

4. **Redesign onboarding wizard** (in `app.py`, function `show_welcome_dialog`)
   - Trigger on FIRST LOGIN (not just first launch) — if user has no data, show onboarding
   - Step 1: "Welcome, {name}!" — brief intro, "Let's set up your finances in 2 minutes"
   - Step 2: Currency & Date Format — clean dropdown selector
   - Step 3: "What do you want to track?" — card grid of modules with checkboxes (pre-checked: Budget, Goals, Portfolio)
   - Step 4: "Import existing data?" — three cards: "Upload CSV", "Start Fresh", "Import from YNAB/Mint"
   - Step 5: "You're all set!" — dashboard preview with confetti animation, "Go to Dashboard" button
   - Progress dots at the bottom (● ● ○ ○ ○)
   - "Skip" link on every step
   - Compact, no scrolling needed on each step

5. **Create Terms of Service modal**
   - Use `@st.dialog("Terms of Service")` decorator
   - Simple terms: data storage, privacy, no warranty
   - "Close" button

### Verification
- Landing page looks professional on desktop and mobile
- Login/register flow is smooth
- Onboarding triggers for new users only
- All steps work and persist settings
- Terms modal opens and closes

---

## Version 4.6 — Dashboard Redesign

**Goal**: The dashboard is the first thing users see after login. It must be visually impressive, informative at a glance, and functional.

### Tasks

1. **Header redesign**
   - "Good morning/afternoon/evening, {Name}" greeting
   - Today's date (formatted per user preference)
   - "Last updated: X minutes ago" tag

2. **Financial summary cards** (top row, 4 columns)
   - **Net Worth**: total assets - liabilities, with month-over-month change arrow
   - **Monthly Spending**: current month total vs budget, progress ring
   - **Savings Progress**: total saved / total goal targets, percentage
   - **Active Subscriptions**: count and monthly total
   - Cards should use the `.dash-widget` class with clean gradients
   - Each card has an icon, value, label, and delta indicator

3. **Spending chart** (full width)
   - Line chart: daily cumulative spending for current month vs previous month
   - Clean, minimal design with theme-aware colors
   - Hover tooltips showing exact amounts

4. **Two-column layout below chart**
   - Left column:
     - **Recent Transactions** (last 5): icon, description, category badge, amount, date
     - "View All →" link to Budget Tracker
   - Right column:
     - **Upcoming Bills** (next 3): name, amount, due date, days until due
     - "View All →" link to Budget Tracker bills tab
     - **Goals Progress**: top 3 active goals with mini progress bars

5. **Quick Actions row** (bottom)
   - 4 action cards in a row: "Add Expense", "Scan Receipt", "New Goal", "Import Data"
   - Each card: icon + label, clicks navigate to the relevant module

6. **Empty state**
   - If user has no data yet, show a friendly illustration-style empty state
   - "Welcome to FinanceKit! Start by adding your first expense or importing a bank statement."
   - Three action buttons: "Add Expense", "Import CSV", "Take a Tour"

7. **Household section** (only if household is configured)
   - "Household" expander with:
     - Outstanding balances between members
     - Shared goals progress
     - Recent split expenses

### Verification
- Dashboard loads quickly (< 2 seconds)
- All metric calculations are correct
- Charts render in both themes
- Empty state shows for new users
- Quick actions navigate correctly

---

## Version 4.7 — Sidebar & Navigation Polish

**Goal**: The sidebar is clean, compact, and provides easy access to everything without clutter.

### Tasks

1. **Simplify sidebar layout**
   - Logo + version at top (keep current)
   - User card (avatar + name + email) — compact, single line
   - Navigation links styled as clean list items (not radio buttons)
   - Each nav item: emoji icon + module name
   - Active item has accent-colored left border and background highlight
   - Grouped: "MAIN" (Dashboard) → "MODULES" (all modules) → "SETTINGS"

2. **Move theme toggle to bottom of sidebar as a small icon button**
   - Just ☀️/🌙 icon, no label — tooltip explains it
   - This is a quick-access shortcut; the full theme settings are in Settings

3. **Remove notification bell from sidebar**
   - Notifications now show as a badge on the sidebar logo or as a top-bar indicator
   - Create a notification dropdown that appears when clicking the bell icon
   - Use `st.popover("🔔")` if available, otherwise an expander

4. **Remove Quick Actions from sidebar**
   - Quick Actions are now on the Dashboard (see v4.6)
   - Sidebar should only have navigation

5. **Global search**
   - Keep the search bar in the sidebar but make it collapsible
   - Add keyboard shortcut hint: "⌘K" or "Ctrl+K"
   - Search results appear in a dropdown overlay, not inline

6. **Sign Out**
   - Move to bottom of sidebar, small text link (not a full-width button)
   - Show "Signed in as {email}" + "Sign Out" link

7. **Mobile sidebar**
   - Auto-collapse on mobile (< 768px)
   - Hamburger menu icon to open
   - Sidebar overlays content on mobile (doesn't push it)
   - Current `initial_sidebar_state="expanded"` should be changed to `"collapsed"` on mobile
   - Add swipe-to-close gesture hint

8. **Keyboard shortcuts**
   - Remove the keyboard shortcuts expander from the sidebar
   - Instead, implement actual keyboard shortcuts using JavaScript injection:
   ```javascript
   document.addEventListener('keydown', function(e) {
       if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
       const key = e.key;
       if (key === '0') { /* navigate to Dashboard */ }
       if (key >= '1' && key <= '7') { /* navigate to modules */ }
       if (key === '9') { /* navigate to Settings */ }
       if (key === '?' || (e.ctrlKey && key === 'k')) { /* focus search */ }
   });
   ```
   - Inject via `st.components.v1.html()`

### Verification
- Sidebar is clean and compact
- Navigation works on all pages
- Mobile sidebar collapses correctly
- Keyboard shortcuts work
- Search works and results are clickable

---

## Version 4.8 — Module UX Polish (Part 1: Budget & Goals)

**Goal**: The two most-used modules — Budget Tracker and Goal Tracker — are polished, intuitive, and delightful to use.

### Budget Tracker Tasks

1. **Transaction entry redesign**
   - "Add Expense" button at top right → opens `@st.dialog`
   - Clean form: Amount (large number input), Category (selectbox with emojis), Description, Date
   - "Save" button with loading spinner
   - Success toast with undo option

2. **Spending overview**
   - Top metrics row: Total Spent, Budget Remaining, Daily Average, Top Category
   - Monthly spending vs budget bar chart (horizontal bars, one per category)
   - Each bar shows: category name, spent/budget, percentage, over/under indicator

3. **Transaction list redesign**
   - Clean list view (not data editor — data editors are confusing for non-technical users)
   - Each transaction: date, description, category badge (colored), amount
   - Swipe actions (on mobile): edit, delete
   - Filter bar: date range, category, search text
   - Sort: newest first, oldest first, highest amount, lowest amount
   - Pagination (20 per page) instead of showing all transactions

4. **Budget setup wizard**
   - If no budget is set, show "Set Up Your Budget" card
   - Template selection: Student, Freelancer, Family, Single Professional, Custom
   - Interactive slider for each category amount
   - Total budget display with real-time updates

5. **Bill management tab**
   - Clean list of recurring bills
   - "Add Bill" form: name, amount, due day, category, auto-pay toggle
   - Upcoming bills sorted by due date
   - Overdue bills highlighted in red
   - "Mark as Paid" button with date

6. **Category spending chart**
   - Donut chart with 12+ distinct colors
   - Legend below with category name and percentage
   - Click on category to filter transactions to that category

### Goal Tracker Tasks

1. **Goal card redesign**
   - Clean card layout with progress ring (circular progress bar, not linear)
   - Card shows: goal name, target amount, current amount, percentage, monthly contribution
   - Projected completion date with "X months to go"
   - "Add Contribution" button → inline form or dialog

2. **Add Goal flow**
   - "New Goal" button → `@st.dialog` with:
   - Goal name (text), Target amount (number), Starting amount (number), Monthly contribution (number)
   - Deadline (date, optional), Notes (text area, optional)
   - Category/icon picker (emoji grid)
   - "Create" button

3. **Goal detail view**
   - Click on a goal card to expand to full detail
   - Contribution history list (date + amount)
   - "Edit" and "Delete" buttons (with confirmation for delete)
   - Progress chart: line chart showing savings growth over time

4. **Milestone celebrations**
   - Streamlined — only celebrate 50% and 100% (not 25% and 75%)
   - Use `st.toast` instead of `st.balloons()`/`st.snow()` (less disruptive)
   - "🎯 Halfway there!" and "🎉 Goal achieved!" messages

5. **Shared goals** (if household enabled)
   - Show member contributions in a mini table on the goal card
   - "Add Contribution" auto-selects current user as contributor

### Verification
- Budget Tracker loads with all features working
- Transactions can be added, edited, deleted
- Charts render correctly in both themes
- Goal cards look polished
- Milestones trigger appropriately

---

## Version 4.9 — Module UX Polish (Part 2: Portfolio, Receipts, Subscriptions)

**Goal**: The remaining core modules are polished to the same standard as Budget and Goals.

### Portfolio Tracker Tasks

1. **Holdings dashboard**
   - Top row: Total Value, Total Cost, Total Gain/Loss ($ and %), Day Change
   - Holdings table: clean card list (not raw dataframe)
   - Each holding: ticker, name, quantity, current price, avg cost, gain/loss, allocation %
   - Color-coded: green for gain, red for loss

2. **Add holding flow**
   - "Add Holding" → `@st.dialog`
   - Ticker input with auto-complete/validation
   - Asset type (Stock/ETF/Crypto), Purchase price, Quantity, Date
   - "Add" button with validation

3. **Watchlist redesign**
   - Clean card grid of watched tickers
   - Each card: ticker, current price, day change (% and $), mini sparkline if possible
   - "Remove" and "Add to Portfolio" actions

4. **Price alerts**
   - "Add Alert" form: ticker, target price, direction (above/below)
   - Active alerts list with "Delete" action
   - Alert triggers create a notification

### Receipt Scanner Tasks

1. **Upload redesign**
   - Large drag-and-drop zone with dashed border
   - "Upload receipt (PDF, JPG, PNG)" label
   - Show thumbnail preview of uploaded image
   - Remove the broken "Camera" tab entirely

2. **Scan results**
   - After upload, show extracted data in editable form fields: Merchant, Amount, Date, Category
   - User can correct any field before saving
   - "Save Receipt" button
   - Auto-detection quality indicator: "High confidence" / "Review needed"

3. **Receipt history**
   - Clean list of saved receipts sorted by date
   - Each entry: date, merchant, amount, category badge
   - Click to expand and see the original image/PDF
   - Filter by date range and category
   - Export to CSV

### Subscription Auditor Tasks

1. **Subscription list redesign**
   - Clean card list of all subscriptions (detected + manual)
   - Each card: service name, icon/logo placeholder, amount, frequency (monthly/yearly), next billing date
   - Status: Active (green), Cancelled (gray), Trial (yellow)
   - "Cancel" button with cancellation URL link

2. **Add subscription manually**
   - "Add Subscription" → `@st.dialog`
   - Service name, amount, frequency (monthly/weekly/yearly), next billing date, category
   - "Save" button

3. **Spending summary**
   - Top metrics: Monthly total, Yearly total, Most expensive sub, Cheapest sub
   - Monthly cost breakdown chart (horizontal bar)

4. **Price change detection**
   - If a subscription amount changes, show an alert: "Netflix increased from $15.99 to $22.99"
   - Price history chart for each subscription

5. **Detection improvements**
   - Expand the known subscriptions list from 20 to 50+
   - Better fuzzy matching (use `rapidfuzz` with threshold 70)
   - Group similar charges (e.g., "SPOTIFY" and "Spotify USA")

### Verification
- All three modules load and function correctly
- Cards and lists render cleanly in both themes
- Add/edit/delete flows work
- Charts and metrics are accurate

---

## Version 5.0 — Final UX Polish, Performance & QA

**Goal**: Everything is polished, fast, and ready for public use. This is the release candidate.

### Tasks

1. **Performance optimization**
   - Add `@st.cache_data` to all data-loading functions (with appropriate TTL)
   - Cache stock prices for 5 minutes (currently re-fetches on every page load)
   - Lazy-load modules: only import a module's code when its page is navigated to
   - Reduce the CSS blob size: deduplicate rules, remove unused selectors

2. **Error handling**
   - Every module's `render()` function should be wrapped in try/except
   - On error: show a friendly message "Something went wrong. Try refreshing." with "Show details" expander
   - Log all errors to `data/financekit.log` via the existing logger

3. **Loading states**
   - Add `st.spinner("Loading...")` to every data-heavy operation
   - Show skeleton placeholders while charts render
   - Dashboard should show placeholder cards while data loads

4. **Confirmation dialogs**
   - Add "Are you sure?" confirmation before ALL destructive actions:
     - Delete transaction, Delete goal, Delete subscription, Delete client, Delete invoice
     - Clear all data, Delete account
   - Use `@st.dialog("Confirm")` with "Cancel" and "Delete" buttons

5. **Responsive design audit**
   - Test every page at 3 widths: 360px (phone), 768px (tablet), 1440px (desktop)
   - Fix any overflow, truncation, or layout breaking issues
   - Ensure all forms are usable on mobile
   - Touch targets: all buttons and links should be at least 44px tall on mobile

6. **Accessibility**
   - All form inputs have visible labels (not just placeholders)
   - Color is never the ONLY indicator (add icons/text alongside green/red)
   - Sufficient contrast ratio (4.5:1 minimum for text, 3:1 for large text)
   - Tab order is logical (top to bottom, left to right)

7. **Empty states for every module**
   - Budget Tracker: "No transactions yet. Add your first expense to start tracking."
   - Portfolio: "Your portfolio is empty. Add a holding to start tracking your investments."
   - Goals: "No goals set. Create your first savings goal to get started."
   - Receipts: "No receipts scanned. Upload a receipt to extract spending data."
   - Subscriptions: "No subscriptions detected. Import transactions or add manually."
   - Freelance: "No clients yet. Add your first client to start invoicing."
   - Each empty state has an icon, message, and action button

8. **Update version.txt to 5.0**

9. **Run full test suite** — all 123+ tests must pass

10. **Final commit**: `FinanceKit v5.0 — UX Overhaul Complete`

### Verification Checklist
- [ ] Every page loads without errors in both themes
- [ ] Google Sign-In works on Streamlit Cloud
- [ ] Email sign-up and login work
- [ ] Landing page looks professional
- [ ] Onboarding wizard works for new users
- [ ] Dashboard shows correct data
- [ ] All modules are functional and polished
- [ ] Settings page is organized and every setting works
- [ ] Mobile layout is usable
- [ ] No hardcoded dark-mode colors anywhere
- [ ] All destructive actions have confirmation dialogs
- [ ] Empty states show for modules with no data
- [ ] All 123+ tests pass

---

## File Reference: Current Bugs to Fix

| Bug | File | Line(s) | Fix |
|-----|------|---------|-----|
| Light mode text unreadable | `app.py` | 160-492 (CSS) | Add comprehensive `!important` rules for ALL text elements |
| Google Sign-In not rendering | `app.py` | 647-690 | Debug `streamlit-google-auth` or implement manual OAuth |
| Theme toggle in wrong place | `app.py` | 1355-1372 | Move to Settings page |
| Hardcoded dark colors in email HTML | `utils/notifications.py` | ~236 | Use neutral/theme-aware colors |
| Chart colors repeat (only 6) | `utils/chart_config.py` | 4 | Expand to 12+ colors |
| Camera tab non-functional | `modules/receipt_scanner.py` | ~45 | Remove the tab entirely |
| No confirmation on delete | Multiple modules | Various | Add `@st.dialog("Confirm")` |
| `version.txt` says 4.0 | `version.txt` | 1 | Update to match current version at each step |
| Recurring invoice runs every render | `modules/job_tracker.py` | 84-143 | Add check to run only once per session |
| Search has no relevance ranking | `utils/search.py` | All | Add basic scoring (exact match > substring > fuzzy) |
