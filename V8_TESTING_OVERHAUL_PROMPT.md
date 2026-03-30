# FinanceKit v8.0–8.7 — Comprehensive Testing, Debugging & UI Overhaul

## Context

You are working on **FinanceKit**, a Streamlit personal finance web app at:
```
C:\Users\bzcni\OneDrive\Desktop\vs code projects\Finance Toolkit\
```

Current version: **7.2** (in `version.txt`). This overhaul spans **v7.3 through v8.7** (+1.5 versions). The SOLE focus is testing, debugging, fixing broken features, and polishing the UI. **No new features** — only fix what exists and make it bulletproof.

---

## Critical Rules (READ THESE FIRST)

- **Python 3.14** with `-X utf8` flag (Windows cp1252 encoding issues)
- **Streamlit 1.45.0** — use `width='stretch'` (NEVER `use_container_width`)
- **PowerShell** — use `;` not `&&` to chain commands
- Run with: `cd "C:\Users\bzcni\OneDrive\Desktop\vs code projects\Finance Toolkit" ; python -X utf8 -m streamlit run app.py`
- Be concise — go straight to code, skip unnecessary explanation
- The only permitted emojis in the entire app are: ☀️/🌙 (theme toggle) and 🔔 (notifications). Zero others anywhere.
- All buttons use the user's chosen accent color (default indigo `#6366f1`) with auto-contrast text via WCAG luminance
- CSS uses custom properties (`var(--fk-accent)`, `var(--fk-btn-bg)`, etc.) — never hardcode hex colors in component styles
- The word "FinanceKit" in the sidebar logo is exempt from translation

---

## Reference Repos (already cloned in the file tree)

Use these as debugging/testing references — read them when you need patterns:

| Directory | Repo | Use For |
|-----------|------|---------|
| `_python_guide_ref/` | realpython/python-guide (~28k stars) | Testing (docs/writing/tests.rst), logging (docs/writing/logging.rst), project structure (docs/writing/structure.rst) |
| `_streamlit_guide_ref/` | Packt Streamlit book | Session state (Chapter15), databases (Chapter13), file uploads (Chapter12), caching (Chapter05-06), page config (Chapter14) |
| `_expense_tracker_ref/` | Sven-Bo expense tracker | Clean Streamlit form patterns, Sankey charts |
| `_portfolio_tracker_ref/` | Python portfolio tracker | yfinance patterns, CAGR calculation |
| `_finance_dashboard_ref/` | Finance dashboard | SQL queries, Plotly patterns, time granularity |
| `_monkeytype_ref/` | MonkeyType | CSS variable theming patterns |

---

## File Structure Overview

```
app.py                          — ~4000 lines, main app (auth, routing, dashboard, CSS, sidebar)
modules/
  budget_tracker.py             — ~850 lines
  goal_tracker.py               — ~600 lines
  job_tracker.py                — ~1150 lines (Freelance Dashboard)
  portfolio_tracker.py          — ~650 lines
  receipt_scanner.py            — ~380 lines
  report_generator.py           — ~780 lines
  settings.py                   — ~1820 lines
  subscription_auditor.py       — ~500 lines
utils/
  i18n.py                       — ~790 lines (translations: en, es, fr, de)
  auth.py                       — ~520 lines
  data_persistence.py           — ~150 lines
  notifications.py              — ~430 lines
  chart_config.py               — ~75 lines
  formatting.py                 — ~160 lines
  finance_api.py                — ~160 lines
  insights.py                   — ~305 lines
  invoice_templates.py          — ~610 lines
  report_builder.py             — ~390 lines
  search.py                     — ~140 lines
  security.py                   — ~240 lines
  + 12 more utility files
```

---

## Phase 1 (v7.3–v7.5): Fix All Known Broken Features

### 1.1 — Authentication Persistence (CRITICAL)

**Problem:** Refreshing the browser tab sends authenticated users back to the landing/sign-in page. The current fix uses `st.stop()` with a JS localStorage check, but it's still unreliable.

**Files:** `app.py` lines 2160–2240

**What to do:**
- Read the current auth flow thoroughly (OAuth callback → token validation → JS localStorage → `_fk_token_check_done` flag → `st.stop()`)
- The JS redirect approach is fundamentally racy — Streamlit renders server-side before client JS executes
- Implement a **server-side session persistence** approach: write the session token to a file (`data/sessions/{token}.json`) on login, and check for it on every rerun before showing the landing page
- Remove the `st.stop()` / `_no_session` / `_fk_token_check_done` hack entirely
- Keep the localStorage JS as a secondary mechanism, but the PRIMARY check should be server-side
- Test: sign in → refresh tab → should stay on dashboard. Sign in → close tab → reopen → should auto-login if "Remember me" was checked

### 1.2 — Dashboard Navigation Buttons

**Problem:** Quick action buttons (Log Expense, Scan Receipt, Generate Report, Create Goal) and module card "Open X" buttons set `st.session_state.nav_target` + `st.rerun()`, but the nav_target processing happens before auth rebuilds `NAV_OPTIONS` with the correct user modules.

**Files:** `app.py` lines 210–214, 2246–2251, 3534–3550, 3870–3890

**What to do:**
- Verify nav_target processing works correctly after the fix at line 210 (only clears nav_target when found)
- Test every single navigation button on the dashboard: all 4 quick actions, all module card "Open X" buttons, the empty-state buttons (Add Expense, Import CSV, Set a Goal)
- Test that the sidebar radio updates to match the navigated page
- If any button still doesn't work, trace the issue and fix it

### 1.3 — Module Toggler in Settings

**Problem:** Toggling modules on/off in Settings doesn't update the sidebar navigation immediately.

**Files:** `modules/settings.py` lines 615–653, `app.py` `_get_enabled_modules()` and `_build_nav_options()`

**What to do:**
- `_get_enabled_modules()` now reads fresh from settings.json every time (no caching)
- Verify: toggle a module off in Settings → sidebar should immediately remove it → toggle back on → it reappears
- Ensure the dashboard module cards also respect the toggle

### 1.4 — Landing Page Polish

**Files:** `app.py` `_show_landing_page()` function (~line 1540)

**What to do:**
- Verify the 3x3 feature grid renders cleanly in both light and dark mode
- Cards should have consistent height within each row
- The "One-time $7.99" text stays in the social proof section
- Only 1 "Get Started" + 1 "Sign In" button (no duplicates)
- Test the landing page in both themes

---

## Phase 2 (v7.6–v7.8): Complete Internationalization

### 2.1 — Finish i18n for ALL Remaining Modules

The budget_tracker.py and portfolio_tracker.py are already using `t()`. The following modules still have **dozens of hardcoded English strings**:

**goal_tracker.py** — ~30+ hardcoded strings:
- Module header, form labels (Goal Name, Target Amount, Already Saved, Target Date, Monthly Contribution, Notes), button labels (Add Goal, Contribute, Edit, Delete), metric labels (Active Goals, Total Saved, Remaining), section headers, toast messages, error messages, empty states

**receipt_scanner.py** — ~25+ hardcoded strings:
- Module header, Upload Receipts header, file uploader label, Scan & Add button, spinner text, All Receipts header, column labels, Export header, toast messages, error messages, category options in SelectboxColumn

**job_tracker.py** — ~50+ hardcoded strings:
- All 6 tab names (Overview, Clients, Time, Invoices, Recurring, Expenses), every section header, every form label, every button, every metric label, every toast/error message

**report_generator.py** — ~30+ hardcoded strings:
- Import section headers, format detection messages, column mapping labels, report template names, PDF generation buttons, email sending UI, error messages

**subscription_auditor.py** — ~20+ hardcoded strings:
- Module header, statement upload UI, subscription table headers, Keep/Cancel labels, cost projections, category names

**settings.py** — ~40+ hardcoded strings:
- Many section headers partially use `t()` but validation errors, captions, info messages, and form labels are still hardcoded

**What to do for each module:**
1. Add `from utils.i18n import t` at the top (if not already there)
2. Replace every user-visible string with `t("descriptive_key")`
3. Add the English key to `utils/i18n.py` → `_STRINGS["en"]`
4. Add translations to `_STRINGS["es"]`, `_STRINGS["fr"]`, `_STRINGS["de"]`
5. Test in at least 2 languages to verify nothing breaks

### 2.2 — Dashboard Hardcoded Strings

**File:** `app.py` dashboard section (lines 3050–3900)

**Remaining hardcoded strings to fix:**
- Time-relative strings: "just now", "Xm ago", "Xh ago", "Xd ago" (lines ~3058–3064)
- "Day of Month" x-axis label
- Empty state text: "No savings goals yet", "Set your first goal...", "No receipts yet", "Upload a receipt..."
- "Household Overview", "Outstanding Balances", "Shared Goals"
- "Open Goal Tracker →", "View all receipts →", "Create a Goal"
- "SMART INSIGHT", "QUICK INSIGHT"
- Module card descriptions (9 strings in `_all_module_cards`)
- "What's New in FinanceKit" dialog content
- All `_HELP_TIPS` dict values

### 2.3 — Auth Pages

**File:** `app.py` `_show_login_page()` function

- "Welcome back", "Sign in to your account", "Create Account", "Start managing your finances"
- Form labels: Email, Password, Display Name
- "Remember me (30 days)", "Forgot password?"
- Error messages: "Invalid email or password", "Email already registered"
- OAuth button text: "Continue with Google", "Continue with GitHub"

### 2.4 — Verify Language Dropdown

Only 4 languages should appear: English, Espanol, Francais, Deutsch. Verify no others show up. Test switching between all 4 and confirm the ENTIRE UI updates — sidebar nav labels, dashboard headers, all button text, all form labels, all toast messages.

---

## Phase 3 (v7.9–v8.2): Create Test Suite

### 3.1 — Set Up Test Infrastructure

Reference: `_python_guide_ref/docs/writing/tests.rst`

Create the following structure:
```
tests/
  __init__.py
  context.py              — import path setup
  test_data_persistence.py
  test_formatting.py
  test_i18n.py
  test_auth.py
  test_category_learner.py
  test_validators.py
  test_budget_logic.py
  test_portfolio_logic.py
  test_notifications.py
  test_insights.py
  conftest.py             — pytest fixtures
```

Add to `requirements.txt`: `pytest`, `pytest-cov`

### 3.2 — Unit Tests for Utils

Write tests for every utility module. Priority order:

**test_data_persistence.py:**
- `load_json()` with valid file, missing file, corrupted JSON, empty file
- `save_json()` with valid data, atomic write verification
- User context isolation (`set_user_context` / `clear_user_context`)

**test_formatting.py:**
- `format_currency()` with positive, negative, zero, large numbers
- `format_currency_int()` rounds correctly
- `get_currency_symbol()` for USD, EUR, GBP, JPY, INR, BRL
- `format_date()` with different date format settings

**test_i18n.py:**
- `t("key")` returns English by default
- `t("key")` returns Spanish when language is "es"
- `t("missing_key")` falls back to English
- `t("completely_unknown")` returns the key itself
- `t("days_ago", n=5)` formats parameterized strings
- Every key in "en" exists in "es", "fr", "de" (completeness check)

**test_auth.py:**
- Password hashing and verification
- Session token creation and validation
- Rate limiting (account lockout after N failures)
- Token expiry

**test_validators.py:**
- Email validation
- Password strength requirements
- Data schema validation and repair

**test_category_learner.py:**
- Learning from corrections
- Retrieving learned categories
- Keyword fallback when no learned rule

**test_notifications.py:**
- Creating notifications (dedup check)
- Quiet hours filtering
- Rate limiting
- Mark as read/unread

**test_insights.py:**
- Anomaly detection with normal data (no alerts)
- Anomaly detection with spike (should alert)
- Top insight generation

### 3.3 — Integration Tests for Module Logic

**test_budget_logic.py:**
- Auto-categorization: "Starbucks" → "Dining Out", "Walmart" → "Food & Groceries"
- Budget template loading
- Over-budget detection
- Rollover calculation

**test_portfolio_logic.py:**
- Gain/loss calculation
- CAGR calculation with known values
- Sector allocation percentages
- Price alert triggering

### 3.4 — Run Tests and Fix Failures

```powershell
cd "C:\Users\bzcni\OneDrive\Desktop\vs code projects\Finance Toolkit" ; python -X utf8 -m pytest tests/ -v --tb=short
```

Fix any failures. Aim for **100% pass rate** and **>80% coverage** on utils/.

---

## Phase 4 (v8.3–v8.5): UI/UX Audit & Polish

### 4.1 — Light Mode Audit

Switch to light mode and verify every page:
- [ ] Landing page — cards readable, buttons visible
- [ ] Login/register page — form inputs have proper borders, labels visible
- [ ] Dashboard — all widgets, charts, cards readable
- [ ] Budget Tracker — progress bars, category breakdown, charts
- [ ] Goal Tracker — progress rings, milestone cards
- [ ] Portfolio Tracker — holdings table, allocation pies, gain/loss colors
- [ ] Receipt Scanner — upload area, receipt table
- [ ] Report Generator — import UI, report preview
- [ ] Freelance Dashboard — all 6 tabs
- [ ] Subscription Auditor — detection table, Keep/Cancel toggles
- [ ] Settings — all sections, toggles, forms

Fix any issues where text is unreadable, backgrounds blend, or elements are invisible.

### 4.2 — Dark Mode Audit

Same checklist as above but in dark mode. Pay special attention to:
- Chart backgrounds (should be transparent, not white)
- Table cell backgrounds
- Form input backgrounds
- Modal/dialog backgrounds

### 4.3 — Responsive Layout Check

Resize browser to common widths and verify nothing breaks:
- 1920px (full HD)
- 1440px (laptop)
- 1280px (small laptop)
- 768px (tablet — Streamlit's minimum usable width)

### 4.4 — Empty State Audit

For every module, verify what happens with ZERO data:
- Dashboard with no data → should show welcome empty state + quick action buttons
- Budget Tracker with no budgets, no transactions → should show setup guidance
- Goal Tracker with no goals → should show "Create your first goal"
- Portfolio with no holdings → should show "Add your first holding"
- Receipt Scanner with no receipts → should show upload prompt
- Each empty state should have a clear call-to-action button

### 4.5 — Error State Audit

Test what happens when things go wrong:
- Upload a non-CSV file to Budget Tracker import
- Upload a corrupted image to Receipt Scanner
- Enter an invalid ticker in Portfolio Tracker
- Set a goal with 0 target amount
- Try to generate a report with no data
- Check what happens when yfinance/CoinGecko API is unreachable

Every error should show a clear, translated error message — never a raw Python traceback.

---

## Phase 5 (v8.6–v8.7): Logging, Performance & Final Polish

### 5.1 — Implement Structured Logging

Reference: `_python_guide_ref/docs/writing/logging.rst`

**File:** `utils/logger.py` (already exists, ~67 lines — extend it)

- Configure logging with dictionary config
- Add log levels: DEBUG for development, INFO for production
- Log these events:
  - User login/logout (INFO)
  - Module navigation (DEBUG)
  - Data save/load operations (DEBUG)
  - API calls to yfinance/CoinGecko (INFO with timing)
  - Errors and exceptions (ERROR with traceback)
- Write logs to `data/logs/financekit.log` with rotation (max 5MB, keep 3 backups)
- Add timing decorator for expensive operations

### 5.2 — Performance Audit

- Check `@st.cache_data` usage — are expensive operations cached?
- Verify chart rendering doesn't block page load
- Check if `_load_json()` is called redundantly (same file read multiple times per rerun)
- Profile the dashboard rendering (it loads data from ~10 JSON files)
- Add `show_spinner=False` to caches that run in the background

### 5.3 — Final Cleanup

- Remove any dead code (unused imports, commented-out blocks, TODO comments)
- Remove the `_STRINGS` entries for languages not in `AVAILABLE_LANGUAGES` (it, pt, nl, pl, sv, da, no, fi) — they're dead weight
- Verify `.gitignore` includes: `_*_ref/`, `tests/__pycache__/`, `data/logs/`
- Update `version.txt` to `8.7`
- Update the "What's New" dialog in app.py with a v8.x entry summarizing the testing overhaul

---

## Verification Checklist (Run After Each Phase)

```powershell
# Compile check
python -X utf8 -c "import py_compile; [py_compile.compile(f, doraise=True) for f in ['app.py'] + [f'modules/{m}' for m in ['budget_tracker.py','goal_tracker.py','job_tracker.py','portfolio_tracker.py','receipt_scanner.py','report_generator.py','settings.py','subscription_auditor.py']] + [f'utils/{u}' for u in ['i18n.py','auth.py','data_persistence.py','notifications.py','formatting.py']]]; print('All OK')"

# Run tests (after Phase 3)
python -X utf8 -m pytest tests/ -v --tb=short

# Launch app
python -X utf8 -m streamlit run app.py
```

Manual checks after each phase:
1. Sign in → refresh tab → should stay logged in
2. Navigate to every module via sidebar
3. Navigate to every module via dashboard buttons
4. Switch language to Spanish → every visible string should be Spanish
5. Toggle a module off in Settings → it disappears from sidebar
6. Switch to light mode → everything readable
7. Switch to dark mode → everything readable

---

## Summary of Deliverables

| Phase | Version | Deliverable |
|-------|---------|-------------|
| 1 | v7.3–7.5 | Fix auth persistence, nav buttons, module toggler, landing page |
| 2 | v7.6–7.8 | Complete i18n for ALL 8 modules + dashboard + auth pages |
| 3 | v7.9–8.2 | Test suite with 50+ unit tests, >80% utils coverage |
| 4 | v8.3–8.5 | UI audit (light/dark/responsive/empty/error states) |
| 5 | v8.6–8.7 | Logging, performance, cleanup, version bump |

Work through each phase sequentially. Bump `version.txt` at the end of each phase. Do NOT skip phases or combine them — each one builds on the previous.
