# FinanceKit v8.8–9.1 — Deep Functional Audit & Hardening

## Context

You are working on **FinanceKit**, a Streamlit personal finance web app at:
```
C:\Users\bzcni\OneDrive\Desktop\vs code projects\Finance Toolkit\
```

Current version: **8.7** (in `version.txt`). This audit spans **v8.8 through v9.1** (+0.4 versions). The SOLE focus is a **deep functional audit** — systematically verifying that every feature, every flow, and every edge case in the entire app works correctly. You are not building new features. You are finding what's broken, fixing it, and proving it works.

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

## File Structure Overview

```
app.py                          — ~4200 lines, main app (auth, routing, dashboard, CSS, sidebar)
modules/
  budget_tracker.py             — ~1645 lines (budgets, transactions, bills, splits, scenarios)
  goal_tracker.py               — ~437 lines (savings goals, milestones, projections)
  job_tracker.py                — ~1316 lines (Freelance Dashboard: clients, time, invoices, recurring, expenses, P&L)
  portfolio_tracker.py          — ~705 lines (stocks, crypto, watchlist, alerts, allocation)
  receipt_scanner.py            — ~288 lines (OCR, PDF/image upload, categorization)
  report_generator.py           — ~857 lines (import, summary, year-in-review, tax, compare, email)
  settings.py                   — ~1775 lines (profile, appearance, notifications, modules, household, SMTP, auth, data, legal)
  subscription_auditor.py       — ~887 lines (recurring charge detection, keep/cancel, projections, calendar)
utils/
  i18n.py                       — ~3900+ lines (translations: en, es, fr, de)
  auth.py                       — ~520 lines (password hashing, session tokens, OAuth)
  data_persistence.py           — ~150 lines (load/save JSON, atomic writes, backups)
  notifications.py              — ~430 lines (alerts, quiet hours, dedup, digest)
  chart_config.py               — ~75 lines (Plotly theme-aware styling)
  formatting.py                 — ~160 lines (currency, date, number formatting)
  finance_api.py                — ~160 lines (yfinance, CoinGecko wrappers)
  insights.py                   — ~305 lines (financial insights, anomaly detection)
  invoice_templates.py          — ~610 lines (3 PDF invoice templates)
  report_builder.py             — ~390 lines (PDF report generation engine)
  search.py                     — ~140 lines (global cross-module search)
  security.py                   — ~240 lines (rate limiting, password validation, audit log)
  category_learner.py           — ~128 lines (ML-like category correction learning)
  fuzzy_matcher.py              — ~42 lines (merchant name normalization + grouping)
  importers.py                  — ~410 lines (YNAB, Mint, Monarch, OFX, auto-detect)
  household.py                  — ~196 lines (shared finance, invite codes, splits)
  sharing.py                    — ~154 lines (share links, access control)
  activity_log.py               — ~98 lines (user action logging)
  sync.py                       — ~286 lines (cloud sync, conflict resolution)
  migrations.py                 — ~155 lines (schema version upgrades)
  validators.py                 — ~229 lines (data schema validation + auto-repair)
  performance.py                — ~169 lines (health check, pagination, smart load)
  logger.py                     — ~85 lines (rotating file handler, @timed decorator)
  ui_helpers.py                 — ~40 lines (module header, empty state)
  pdf_parser.py                 — ~123 lines (PDF text extraction)
tests/                          — 21 test files, 155 tests, ~2000 lines
```

---

## Phase 1 (v8.8): Authentication & Session Deep Audit

### 1.1 — Full Auth Flow Verification

**Goal:** Verify every auth path works end-to-end with zero regressions.

**Files:** `app.py` (auth gate ~line 2140–2300, login page ~line 1894–2116), `utils/auth.py`, `utils/security.py`

**Test every flow manually by running the app:**

**Registration flow:**
- [ ] Register with valid email + strong password → account created, auto-login, session token stored
- [ ] Register with weak password (e.g., "pass") → proper error with strength requirements shown
- [ ] Register with mismatched confirm password → "Passwords don't match" error
- [ ] Register with invalid email (no `@`, no `.` in domain) → validation error
- [ ] Register with duplicate email → "An account with this email already exists"
- [ ] After registration, refresh tab → should stay logged in (session persistence)

**Login flow:**
- [ ] Login with correct credentials → success, redirects to dashboard
- [ ] Login with wrong password → error with remaining attempts shown
- [ ] Login 5 times with wrong password → account locked for 30 minutes
- [ ] Login with non-existent email → "No account found"
- [ ] Login with "Remember me" checked → 30-day session, survives tab close
- [ ] Login without "Remember me" → 24-hour session
- [ ] Refresh browser tab after login → should stay authenticated (no landing page flash)

**Password reset flow:**
- [ ] Click "Forgot password?" → shows reset token generation form
- [ ] Enter registered email → token displayed
- [ ] Use token to reset password → success message
- [ ] Use expired token (>1 hour) → "Token has expired"
- [ ] Use invalid token → "Invalid or expired reset token"
- [ ] Login with new password after reset → success

**Session management:**
- [ ] Sign out → clears all session state, localStorage cleared, redirects to landing
- [ ] "Sign Out Everywhere" in Settings → invalidates all sessions
- [ ] Session expiry warning appears 1 hour before expiry
- [ ] "Extend Session" button works and resets the timer

**Fix any failures before proceeding.**

### 1.2 — Auth Security Hardening Audit

**Files:** `utils/security.py`, `utils/auth.py`

**What to verify in code:**
- [ ] `_hash_password()` uses bcrypt when available, sha256+salt fallback
- [ ] `_verify_password()` handles both bcrypt and sha256 hashes
- [ ] `is_account_locked()` correctly calculates lockout window (30 min)
- [ ] `record_failed_login()` properly decrements remaining attempts
- [ ] `clear_failed_attempts()` runs on successful login
- [ ] `log_audit_event()` logs every login attempt (success + failure)
- [ ] Session token is created with `secrets.token_urlsafe(48)` — cryptographically strong
- [ ] Token stored as SHA-256 hash in sessions.json (never plaintext)
- [ ] Expired sessions are cleaned up on `create_session_token()` call
- [ ] `check_password_requirements()` enforces: 8+ chars, upper+lower, digit, special char, not common

**Write tests for any untested paths. Add to `tests/test_auth.py` and `tests/test_security.py` (create if missing).**

### 1.3 — OAuth Flow Audit

**Files:** `app.py` `_handle_oauth_callback()`, `_handle_google_callback()`, `_handle_github_callback()`, `_oauth_sign_in_buttons()`

**What to verify:**
- [ ] Google OAuth: redirect URI auto-detects localhost vs cloud
- [ ] GitHub OAuth: state parameter prevents CSRF
- [ ] OAuth callback correctly creates/finds user and sets session state
- [ ] OAuth user can't change password (correctly blocked with "This account uses OAuth sign-in")
- [ ] If OAuth credentials not configured, buttons don't appear (no broken links)
- [ ] Sign in with Google → creates session token for persistence

---

## Phase 2 (v8.9): Module-by-Module Functional Audit

For EACH module below, launch the app, navigate to the module, and systematically test every feature. Fix all bugs found.

### 2.1 — Budget Tracker (`modules/budget_tracker.py`)

**Tabs to test:** Track, Analyze, Scenarios, Bills, Splits

**Track tab:**
- [ ] Add transaction with all fields → appears in list, category correctly assigned
- [ ] Auto-categorization: "Starbucks" → "Dining Out", "Walmart" → "Food & Groceries", "Shell" → "Transportation"
- [ ] Edit a transaction → changes persist after rerun
- [ ] Delete a transaction → removed from list + totals update
- [ ] Import CSV file → format detected, preview shown, transactions added
- [ ] Import OFX file → parsed correctly, transactions added
- [ ] Budget progress bars update correctly when transactions are added
- [ ] Over-budget category shows warning color and notification created
- [ ] "Approaching limit" (>80%) shows yellow warning

**Analyze tab:**
- [ ] Category breakdown pie chart renders with correct percentages
- [ ] Month-over-month comparison chart shows correct data
- [ ] Spending trend line chart renders
- [ ] All charts respect current theme (transparent backgrounds, correct text colors)

**Scenarios tab:**
- [ ] "What if I reduce X by Y%" → shows projected savings
- [ ] Budget rollover calculation: unspent from last month carries forward
- [ ] Load template → pre-fills budget amounts from template

**Bills tab:**
- [ ] Add bill with name, amount, due day, frequency → appears in list
- [ ] Mark bill as paid → status updates, next due date calculates
- [ ] Overdue bill → notification created, red indicator in UI
- [ ] Upcoming bill within 3 days → notification created
- [ ] Delete bill → removed from list

**Splits tab (requires Household Mode enabled in Settings):**
- [ ] Create even split among members → amounts calculated correctly
- [ ] Create percentage split → amounts match percentages
- [ ] Create "one person paid" split → correct balance owed
- [ ] Settle split → marked as settled, balances update
- [ ] Verify household members appear in split dropdowns

### 2.2 — Goal Tracker (`modules/goal_tracker.py`)

- [ ] Add goal with all fields → goal appears with progress ring at 0%
- [ ] Add goal with "Already Saved" amount → progress ring shows correct percentage
- [ ] Shared household goal toggle (when household mode on) → shows contributor selector
- [ ] Quick-add funds (+$50, +$100, +$250, +$500) → amount updates, history entry added, toast shown
- [ ] Custom update amount → persists, history chart updates
- [ ] Delete goal (requires confirmation) → goal removed
- [ ] 25% milestone → balloons animation + toast + notification
- [ ] 50% milestone → "halfway there!" notification
- [ ] 75% milestone → notification
- [ ] 100% (goal complete) → snow animation + congratulations toast + notification
- [ ] Projection shows "On track!" when monthly contribution meets deadline
- [ ] Projection shows "may miss deadline" when contribution is insufficient
- [ ] "Never (set a monthly contribution)" shown when monthly = 0
- [ ] History chart renders with correct data points and goal line
- [ ] Milestone timeline shows checkmarks for reached milestones, circles for pending
- [ ] Empty state: "No savings goals yet" + "Add your first goal above..."
- [ ] Verify all strings use `t()` — switch to Spanish and verify the entire page translates

### 2.3 — Portfolio Tracker (`modules/portfolio_tracker.py`)

**Tabs to test:** Portfolio, Watchlist, Trade History, Price Alerts

**Portfolio tab:**
- [ ] Add stock (e.g., AAPL) → fetches live price from yfinance, shows gain/loss
- [ ] Add crypto (e.g., BTC) → fetches from CoinGecko
- [ ] Invalid ticker (e.g., "ZZZZZ") → graceful error, not raw traceback
- [ ] Summary cards: Portfolio Value, Cost Basis, Total Gain/Loss, CAGR all calculate correctly
- [ ] CAGR calculation: verify with known values (e.g., $100→$150 over 3 years ≈ 14.47%)
- [ ] Allocation pie chart: "By Holding" and "Sector" views both render
- [ ] Refresh Prices button → fetches fresh data
- [ ] Holdings table: editable, changes persist
- [ ] Delete holding → removed from portfolio, totals update
- [ ] Dividend yield displayed when available

**Watchlist tab:**
- [ ] Add ticker to watchlist → shows current price
- [ ] Remove from watchlist → removed
- [ ] Watchlist prices update on refresh

**Trade History tab:**
- [ ] Past trades logged when adding/removing holdings
- [ ] Export trade history

**Price Alerts tab:**
- [ ] Set price alert (above/below threshold) → saves
- [ ] When triggered → notification created
- [ ] Delete alert → removed

**When yfinance API is unreachable:**
- [ ] Graceful fallback — show cached data or friendly error, never a traceback

### 2.4 — Receipt Scanner (`modules/receipt_scanner.py`)

- [ ] Upload JPG/PNG image → OCR extracts text, attempts to parse vendor/amount/date
- [ ] Upload PDF receipt → pdfplumber extracts text, parses fields
- [ ] Upload multiple files at once → all processed with progress indicator
- [ ] Scan results show in editable data table
- [ ] Edit vendor/amount/date/category in table → changes persist
- [ ] Save changes button → saves to receipts.json
- [ ] Delete selected receipts → removed
- [ ] Clear all receipts (with confirmation) → empties receipt list
- [ ] Export CSV → downloads valid CSV file
- [ ] Export Excel → downloads valid XLSX file
- [ ] Monthly spending chart renders from receipt data
- [ ] Stats widgets (total receipts, total value, avg receipt) show correct numbers
- [ ] Category dropdown: all 9 categories appear (Groceries, Dining, Transport, etc.)
- [ ] Large receipt (>$500) → creates notification
- [ ] Empty state: "No receipts yet" + upload prompt
- [ ] When Tesseract is not installed → graceful message, not crash

### 2.5 — Report Generator (`modules/report_generator.py`)

**Sections to test:** Import, Quick Reports, Charts, Year-in-Review, Tax Summary, Compare Years, Generate PDF, Email

**Import section:**
- [ ] Upload Chase CSV → format auto-detected, preview shown
- [ ] Upload generic CSV → column mapping form appears
- [ ] Upload OFX/QFX file → parsed correctly
- [ ] Upload YNAB export → auto-detected and parsed
- [ ] Upload Mint export → auto-detected and parsed
- [ ] Upload Monarch export → auto-detected and parsed
- [ ] Unsupported file format → clear error message
- [ ] Import transactions → added to history, count shown
- [ ] Total transactions counter updates

**Quick Reports:**
- [ ] Summary stats (income, expenses, net, avg transaction) calculate correctly
- [ ] Period filter works (all time, specific date range)
- [ ] Top spending categories shown with correct percentages

**Charts:**
- [ ] Monthly spending bar chart renders
- [ ] Spending by category pie chart renders
- [ ] Income vs expenses over time chart renders
- [ ] All charts respect theme (transparent bg, correct colors)

**Net Worth Calculator:**
- [ ] Enter assets (checking, investments, real estate, other) and liabilities (mortgage, car, student, credit card, other)
- [ ] Net worth = total assets - total liabilities, displays correctly

**Year-in-Review:**
- [ ] Select year → shows annual income, expenses, net savings, savings rate
- [ ] Top spending categories for the year
- [ ] Monthly income vs expenses chart
- [ ] Generate YIR PDF → valid PDF downloads
- [ ] "No transactions for this year" shown when no data

**Tax Summary:**
- [ ] Income summary with 1099-likely flagging
- [ ] Deductible expense categories identified
- [ ] Quarterly breakdown
- [ ] Download tax CSV → valid CSV
- [ ] "No tax data" when no transactions

**Compare Years:**
- [ ] Select Year A and Year B → comparison chart renders
- [ ] "Need at least 2 years of data" when insufficient data

**Generate PDF:**
- [ ] Generate PDF report → valid PDF downloads
- [ ] Report includes summary stats, transaction details

**Email Report:**
- [ ] With SMTP configured: enter recipient → report sent → success toast
- [ ] Without SMTP: shows "configure SMTP in Settings" message
- [ ] No report generated yet → "Generate a report first"

### 2.6 — Freelance Dashboard (`modules/job_tracker.py`)

**6 tabs to test:** Overview, Clients, Time, Invoices, Recurring, Expenses

**Overview tab:**
- [ ] Revenue metrics: This Month, Quarter, Year, All Time calculate correctly
- [ ] Avg Invoice, Avg Days to Payment, Top Client display
- [ ] Unpaid invoices warning with count and total
- [ ] Tax estimate section: estimated liability, quarterly set-aside, adjustable rate
- [ ] Revenue trend chart (last 12 months) renders
- [ ] Client revenue breakdown pie chart renders
- [ ] Invoice status distribution (paid/unpaid/overdue) chart renders

**Clients tab:**
- [ ] Add client with name, project, rate, email → client appears in list
- [ ] Client without name → validation error
- [ ] Filter by job status and client status → filters work
- [ ] Client detail card shows total invoiced, total paid, payment history
- [ ] Edit client details → changes persist
- [ ] Delete client → removed from list (with confirmation)
- [ ] Send email button → opens email dialog (if SMTP configured)

**Time tab:**
- [ ] Start timer → shows elapsed time, timer running indicator
- [ ] Stop timer → logs hours automatically
- [ ] Manual time entry → adds to time log
- [ ] Filter by client and date range → works
- [ ] Weekly summary shows total hours per client
- [ ] Generate invoice from time entries → creates invoice with correct line items

**Invoices tab:**
- [ ] Create invoice with line items → invoice created, number auto-incremented
- [ ] At least 1 line item required → validation error if empty
- [ ] Tax rate and discount applied correctly to total
- [ ] Mark invoice as paid → status updates, paid date recorded
- [ ] Mark paid invoice as unpaid → status reverts
- [ ] Download invoice PDF → valid PDF with correct template
- [ ] Invoice numbered sequentially (INV-YYYY-NNNN)
- [ ] Overdue invoices (past due date + unpaid) → notification created

**Recurring tab:**
- [ ] Create recurring invoice (weekly/biweekly/monthly/quarterly) → saved
- [ ] Auto-generation: when recurring invoice is due → new invoice auto-created
- [ ] Pause recurring → stops auto-generation
- [ ] Resume recurring → restarts auto-generation
- [ ] End recurring → permanently stops
- [ ] Generated count shown correctly

**Expenses tab:**
- [ ] Add expense with category, amount, description → added to list
- [ ] Description required → validation error if empty
- [ ] Filter by category and client → works
- [ ] Total expenses metric shows correct sum
- [ ] P&L section: Net Profit = Total Paid Invoices - Total Expenses
- [ ] Profit margin calculated correctly
- [ ] Export P&L as PDF → valid PDF downloads
- [ ] Monthly expenses breakdown chart renders

### 2.7 — Subscription Auditor (`modules/subscription_auditor.py`)

**Tabs to test:** Review, Categories, Cancelled, Usage

- [ ] Upload bank statement CSV → transactions loaded, column mapping if needed
- [ ] Upload OFX → parsed correctly
- [ ] Fuzzy sensitivity slider → adjusts detection threshold
- [ ] Detected subscriptions shown with name, amount, frequency
- [ ] Keep/Cancel toggle for each → decision saved
- [ ] Add manual subscription → appears in list
- [ ] Delete manual subscription → removed
- [ ] Monthly cost, annual cost, potential savings cards show correct values
- [ ] Cost projection chart (1yr, 3yr, 5yr) renders
- [ ] Potential duplicate detection → flagged correctly
- [ ] Cancelled subscriptions tab → shows cancelled subs with cancel date
- [ ] Undo cancel → moves back to active
- [ ] Usage notes → can set frequency (daily/weekly/monthly/rarely/never) and notes
- [ ] "Consider cancelling" hint for rarely/never used subs
- [ ] Annual calendar view → shows renewals by month
- [ ] Spending by category chart renders
- [ ] Export CSV/Excel → valid file downloads
- [ ] Price change detection → flagged when subscription amount changes

### 2.8 — Settings (`modules/settings.py`)

**Sections to test (10+ sections):**

**Profile:**
- [ ] Display name, email shown correctly
- [ ] Save profile → success toast
- [ ] Change password → validates current password, enforces strength requirements
- [ ] OAuth users see "Password change not available for OAuth accounts"
- [ ] Delete account → requires typing "DELETE MY DATA", permanently removes user data

**Appearance:**
- [ ] Theme toggle (Light/Dark) → entire app switches immediately
- [ ] Accent color presets → buttons and links change color
- [ ] Custom accent color → picker works, WCAG contrast text auto-adjusts
- [ ] Font size (Small/Medium/Large) → text scales
- [ ] High contrast mode → increases contrast ratios
- [ ] Language dropdown → 4 options (English, Espanol, Francais, Deutsch)
- [ ] Switch language → ENTIRE UI translates (sidebar nav, dashboard, all modules, all buttons, all errors, all toasts)
- [ ] Currency selector → symbol changes across all modules
- [ ] Date format selector → dates format correctly

**Notifications:**
- [ ] Master toggle on/off → enables/disables all alerts
- [ ] Budget warning threshold slider → value persists
- [ ] Portfolio change threshold → value persists
- [ ] Subscription cost threshold → value persists
- [ ] Invoice overdue threshold → value persists
- [ ] Quiet hours (start/end) → notifications suppressed during window
- [ ] Email digest toggle → sends periodic digest
- [ ] Test notification → creates a test notification in bell

**Modules:**
- [ ] Toggle each module off → disappears from sidebar AND dashboard cards
- [ ] Toggle module back on → reappears immediately
- [ ] Category management → add custom category, hide category, delete category
- [ ] Reset onboarding → clears first-run flags

**Household:**
- [ ] Enable household mode → shows household name, invite code
- [ ] Add members by name → appear in member list
- [ ] Remove member → removed from list
- [ ] Share invite code → other accounts can join with it
- [ ] Disable household → shared features hidden
- [ ] Sharing preferences (budgets, goals, portfolio) → toggle each

**Email (SMTP):**
- [ ] Enter SMTP server, port, from email, password → save
- [ ] Send test email → sends successfully
- [ ] Invalid SMTP config → clear error message

**Data Management:**
- [ ] Accounts: add checking/savings/investment accounts with balances
- [ ] Liabilities: add mortgage/car/student/credit card debts
- [ ] Export full backup → downloads ZIP containing all JSON files
- [ ] Import backup → restores data
- [ ] Reset all data → requires confirmation, wipes user directory
- [ ] Auto-import folder → monitors folder for CSV files

**Authentication section:**
- [ ] Session settings (expiry hours)
- [ ] Sign Out Everywhere → invalidates all other sessions
- [ ] Security activity log shows recent login events
- [ ] OAuth provider configuration (Google client ID/secret, GitHub client ID/secret)

**About:**
- [ ] Version number matches version.txt
- [ ] Check for updates button
- [ ] Health check → runs diagnostic, shows pass/fail for each check
- [ ] Log viewer → shows recent log entries, filterable by level

---

## Phase 3 (v9.0): Cross-Cutting Concerns Audit

### 3.1 — Data Persistence Integrity

**Files:** `utils/data_persistence.py`, `utils/validators.py`, `utils/migrations.py`

**For EACH data file, verify the full lifecycle:**

| File | Module | Test: Create → Save → Reload → Verify |
|------|--------|----------------------------------------|
| `budgets.json` | Budget Tracker | Set budgets → reload page → budgets preserved |
| `budget_transactions.json` | Budget Tracker | Add transactions → reload → transactions preserved |
| `goals.json` | Goal Tracker | Add goal, contribute funds → reload → state preserved |
| `receipts.json` | Receipt Scanner | Scan receipt → reload → receipt preserved |
| `portfolio.json` | Portfolio Tracker | Add holding → reload → holding preserved |
| `transactions.json` | Report Generator | Import transactions → reload → data preserved |
| `statement_transactions.json` | Subscription Auditor | Import statement → reload → data preserved |
| `freelance_data.json` | Freelance Dashboard | Add client, invoice → reload → all preserved |
| `settings.json` | Settings | Change all settings → reload → all preserved |
| `sub_decisions.json` | Subscription Auditor | Make keep/cancel decisions → reload → preserved |
| `manual_subscriptions.json` | Subscription Auditor | Add manual sub → reload → preserved |
| `net_worth_history.json` | Dashboard | Net worth snapshot → reload → preserved |

**Corruption recovery test:**
- [ ] Manually corrupt a JSON file (write invalid JSON) → load_json should restore from backup
- [ ] Delete a JSON file → load_json returns default, no crash
- [ ] Write empty file → load_json returns default

**Atomic write test:**
- [ ] Verify `.tmp` file is written first, then renamed (check `save_json` implementation)
- [ ] On Windows, verify `os.replace()` is used for atomic rename

**User context isolation:**
- [ ] Login as User A → save data → logout → login as User B → User A's data NOT visible
- [ ] User B creates data → User A's data still intact after logging back in
- [ ] Data stored in `data/users/{user_id}/` directories

**Schema migration test:**
- [ ] Check `utils/migrations.py` for all registered migrations
- [ ] Verify `validate_and_repair()` is called on every `load_json()` — missing keys auto-repaired
- [ ] Create a data file WITHOUT `_schema_version` → migration should add it and upgrade

### 3.2 — Notification System Audit

**Files:** `utils/notifications.py`, every module that creates notifications

**Verify every notification path:**

| Trigger | Module | Expected Notification |
|---------|--------|----------------------|
| Budget >80% of limit | Budget Tracker | "Approaching limit: {category}" |
| Budget exceeded | Budget Tracker | "Over budget: {category}" |
| Bill overdue | Budget Tracker | "Overdue: {bill_name}" |
| Bill due within 3 days | Budget Tracker | "Upcoming bill: {name}" |
| Goal 25/50/75/100% milestone | Goal Tracker | "{name} is {pct}% funded" |
| Goal behind schedule | Goal Tracker | "{name} behind schedule" |
| Goal deadline approaching (<30d) + <90% | Goal Tracker | "{name} deadline in {days} days" |
| Large receipt (>$500) | Receipt Scanner | "Large receipt scanned" |
| Invoice overdue | Freelance Dashboard | "Invoice #{number} {days} days overdue" |
| Payment received | Freelance Dashboard | "Payment received: {amount}" |
| Recurring invoice auto-generated | Freelance Dashboard | "Auto-generated Invoice #{number}" |
| Subscription price change | Subscription Auditor | Price change notification |

**Notification mechanics:**
- [ ] Dedup: same notification not created twice in same session
- [ ] Quiet hours: notifications suppressed during configured window
- [ ] Mark as read → counter decrements, notification visually dismissed
- [ ] Mark all as read → all notifications cleared
- [ ] Old notifications (>30 days) auto-cleaned on startup
- [ ] Bell icon in sidebar shows unread count (🔔 is the ONLY allowed emoji here)
- [ ] Notification panel slides open, shows all notifications
- [ ] Each notification has correct icon based on type (alert/success/warning/info)

### 3.3 — i18n Completeness Audit

**Files:** `utils/i18n.py`, all modules, `app.py`

**Systematic verification:**

1. Run the existing `test_all_keys_complete` test — it checks every `en` key exists in `es`, `fr`, `de`:
   ```
   python -X utf8 -m pytest tests/test_i18n.py -v
   ```
   Fix ANY failures.

2. **Reverse check:** grep for ALL `t("...")` calls across the entire codebase and verify EVERY key exists in `_STRINGS["en"]`:
   ```powershell
   grep -roh 't("[^"]*")' modules/ app.py | sort -u
   ```
   Cross-reference against `_STRINGS["en"]`. Any key used in `t()` but missing from `_STRINGS["en"]` will silently show the raw key as text — find and fix these.

3. **Hardcoded string hunt:** Search for remaining English strings NOT wrapped in `t()`:
   ```powershell
   grep -n 'st\.error("' modules/*.py app.py
   grep -n 'st\.warning("' modules/*.py app.py
   grep -n 'st\.toast("' modules/*.py app.py
   grep -n 'st\.info("' modules/*.py app.py
   grep -n 'st\.success("' modules/*.py app.py
   grep -n 'st\.caption("' modules/*.py app.py
   grep -n 'st\.markdown("' modules/*.py | grep -v 'unsafe_allow_html'
   ```
   Any result containing a literal English string (not a `t()` call or HTML) needs wrapping.

4. **Visual verification:** Switch language to Spanish → navigate to EVERY module → verify no English text remains (except "FinanceKit" brand name). Repeat for French and German.

### 3.4 — Chart & Visualization Audit

**Files:** `utils/chart_config.py`, all modules with Plotly charts

**For every chart in the app, verify:**
- [ ] Chart renders without JavaScript errors (check browser console)
- [ ] Chart has transparent background (no white box in dark mode, no dark box in light mode)
- [ ] Chart text colors match theme (`_chart_font()` applied)
- [ ] Grid lines use theme color (`_theme_colors()["grid"]`)
- [ ] Hover tooltips show formatted values (currency symbol, commas)
- [ ] Chart is responsive (`width='stretch'` not `use_container_width`)
- [ ] Empty data state: no crash, shows empty state message instead

**Charts to verify:**
| Module | Chart | Type |
|--------|-------|------|
| Dashboard | Net worth trend | Line |
| Dashboard | Spending trend | Line/Bar |
| Dashboard | Spending by category | Pie |
| Dashboard | Monthly cash flow | Sankey |
| Dashboard | Financial health gauge | Gauge |
| Budget Tracker | Category breakdown | Pie |
| Budget Tracker | Month-over-month | Grouped bar |
| Budget Tracker | Spending over time | Line |
| Goal Tracker | History per goal | Area |
| Portfolio Tracker | Allocation by holding | Pie |
| Portfolio Tracker | Sector allocation | Pie |
| Receipt Scanner | Monthly spending | Bar |
| Report Generator | Monthly spending | Bar |
| Report Generator | Spending by category | Pie |
| Report Generator | Income vs expenses | Grouped bar |
| Freelance Dashboard | Revenue trend (12mo) | Line |
| Freelance Dashboard | Client revenue | Pie |
| Freelance Dashboard | Invoice status | Pie |
| Subscription Auditor | Cost projection | Bar |
| Subscription Auditor | Spending by category | Pie |
| Subscription Auditor | Annual calendar | Heatmap/bar |

### 3.5 — Error Handling Audit

**For every module, trigger error conditions and verify graceful handling:**

| Error Condition | Expected Behavior |
|----------------|-------------------|
| Upload non-CSV to Budget Tracker import | Clear error: "Unsupported file format" |
| Upload corrupted image to Receipt Scanner | Error message, not traceback |
| Upload empty file to any import | "File is empty" or similar |
| Enter invalid ticker in Portfolio Tracker | "Could not fetch data for ZZZZZ" |
| Set goal with 0 target amount | Validation: minimum $1 |
| Set goal with current > target | "Current amount cannot exceed target" |
| Generate report with no data | "No transaction data — import a statement first" |
| Send email with no SMTP config | "Configure SMTP in Settings" |
| yfinance API unreachable | Cached data shown or "Unable to connect" — no traceback |
| CoinGecko API unreachable | Same graceful fallback |
| JSON file corrupted | Auto-restore from backup, or clean default |
| Very long input text (>10000 chars) | Truncated or handled, no crash |
| Special characters in goal/client names | Handled without XSS or encoding errors |
| Date in far future (year 2099) | Handled correctly |
| Negative amounts where not expected | Validation prevents or handles gracefully |

### 3.6 — Empty State Audit

**For every module, verify what happens with ZERO data:**

| Module | Empty State Expected |
|--------|---------------------|
| Dashboard (no data at all) | Welcome message + quick action buttons |
| Budget Tracker (no budgets) | Setup guidance / "Set your first budget" |
| Budget Tracker (no transactions) | "No transactions yet" + import prompt |
| Goal Tracker (no goals) | "No savings goals yet" + "Add your first goal above" |
| Portfolio (no holdings) | "No holdings yet" + "Add your first stock or crypto" |
| Receipt Scanner (no receipts) | "No receipts yet" + upload prompt |
| Report Generator (no imports) | "No transaction data" + import prompt |
| Freelance Dashboard (no clients) | "No clients yet" + "Add your first client" |
| Freelance Time (no clients exist) | "Add a client first in the Clients tab" |
| Freelance Invoices (no clients) | "Add a client first" |
| Freelance Time (no entries) | "No time entries yet" |
| Freelance Invoices (no invoices) | "No invoices yet" |
| Freelance Expenses (no expenses) | "No expenses yet" |
| Subscription Auditor (no data) | "No subscriptions detected" + import prompt |
| Subscription Cancelled (none) | "No cancelled subscriptions" |

**Each empty state must have:**
- [ ] A clear title explaining the empty state
- [ ] A description or hint on what to do next
- [ ] A call-to-action button (where applicable)
- [ ] Translated via `t()` (verify in Spanish)

---

## Phase 4 (v9.1): Test Suite Hardening & Final Polish

### 4.1 — Expand Test Coverage

**Current state:** 155 tests passing. Target: **200+ tests**.

**Missing test coverage to add:**

**`tests/test_security.py`** (create new):
- `test_is_account_locked_fresh` — not locked initially
- `test_is_account_locked_after_failures` — locked after 5 failures
- `test_lockout_expires` — not locked after 30 minutes
- `test_clear_failed_attempts` — resets counter
- `test_check_password_requirements` — each requirement individually
- `test_sanitize_html` — strips dangerous HTML tags
- `test_audit_log_records_events` — events written to file

**`tests/test_sync.py`** (create new):
- `test_create_sync_bundle` — creates valid ZIP
- `test_should_auto_sync` — respects frequency setting
- `test_mark_synced` — updates timestamp

**`tests/test_search.py`** (create new):
- `test_search_finds_transactions`
- `test_search_finds_goals`
- `test_search_empty_query`
- `test_search_no_results`

**`tests/test_invoice_templates.py`** (create new):
- `test_classic_template_generates` — valid PDF bytes
- `test_modern_template_generates` — valid PDF bytes
- `test_minimal_template_generates` — valid PDF bytes
- `test_template_with_tax_and_discount` — amounts correct
- `test_template_unicode_safe` — handles accented characters

**Enhance existing test files:**

**`tests/test_budget_tracker.py`** (add):
- `test_over_budget_detection` — spending > budget returns True
- `test_budget_rollover_calculation` — unspent carries forward
- `test_template_loading` — templates load valid budget structures

**`tests/test_notifications.py`** (add):
- `test_quiet_hours_suppression` — notification created but not shown during quiet hours
- `test_rate_limiting` — same notification not duplicated rapidly

**`tests/test_i18n.py`** (add):
- `test_t_with_multiple_params` — `t("key", a=1, b=2)` formats both
- `test_set_and_get_language` — roundtrip language setting
- `test_get_language_label` — code→display name mapping

**`tests/test_formatting.py`** (add):
- `test_get_currency_symbol_usd` — returns "$"
- `test_get_currency_symbol_eur` — returns "€"
- `test_get_currency_symbol_gbp` — returns "£"
- `test_get_currency_symbol_jpy` — returns "¥"
- `test_format_currency_large_number` — handles millions correctly

**Run all tests and ensure 100% pass rate:**
```powershell
cd "C:\Users\bzcni\OneDrive\Desktop\vs code projects\Finance Toolkit" ; python -X utf8 -m pytest tests/ -v --tb=short
```

### 4.2 — Dead Code Removal

- [ ] Search for unused imports in every file: `python -X utf8 -c "import py_compile; ..."` won't catch these — use grep for imported names that aren't referenced
- [ ] Search for commented-out code blocks (`# ` followed by valid Python) and remove
- [ ] Search for `TODO`, `FIXME`, `HACK`, `XXX` comments — resolve or remove each one
- [ ] Search for unreachable code after `return` statements
- [ ] Verify no duplicate function definitions exist
- [ ] Check for unused variables (especially in long functions like dashboard rendering)

### 4.3 — Performance Verification

**Files:** `app.py` (dashboard), `utils/data_persistence.py`, `utils/finance_api.py`

- [ ] Check `@st.cache_data` usage — are expensive yfinance/CoinGecko calls cached?
- [ ] Check if `load_json()` is called redundantly (same file loaded multiple times in one rerun)
- [ ] Dashboard loads data from ~10 JSON files — verify each is loaded only ONCE
- [ ] Chart rendering: verify `show_spinner=False` on background caches
- [ ] Large dataset test: add 500+ transactions → verify budget tracker doesn't freeze
- [ ] Health check endpoint (`?health=1`) → responds in <2 seconds

### 4.4 — Logging Verification

**Files:** `utils/logger.py`, key integration points

- [ ] Verify log file created at `data/logs/financekit.log`
- [ ] Verify rotation: when file exceeds 5MB, rotates to `.log.1`, `.log.2`, `.log.3`
- [ ] Add logging calls to key events if missing:
  - Login success/failure: `logger.info(f"Login: {email}") / logger.warning(f"Failed login: {email}")`
  - Module navigation: `logger.debug(f"Navigate: {page}")`
  - Data save operations: `logger.debug(f"Saved: {filename}")`
  - API calls: `logger.info(f"API call: {endpoint} ({elapsed}ms)")`
  - Errors: `logger.error(f"Error in {module}: {traceback}")`
- [ ] Verify `@timed` decorator works by adding it to `load_json` and `save_json`
- [ ] Settings → About → Logs section shows recent entries correctly

### 4.5 — Final Version Bump & Verification

**Update `version.txt` to `9.1`.**

**Update "What's New" dialog** with v9.1 entry summarizing:
- Deep functional audit of all 8 modules
- Cross-module data persistence verified
- 200+ tests passing
- Notification system fully audited
- i18n completeness verified (4 languages)
- Error handling hardened for all edge cases
- Dead code removed, performance verified

**Run the full verification checklist:**
```powershell
# Compile check (all files)
python -X utf8 -c "import py_compile; [py_compile.compile(f, doraise=True) for f in ['app.py'] + [f'modules/{m}' for m in ['budget_tracker.py','goal_tracker.py','job_tracker.py','portfolio_tracker.py','receipt_scanner.py','report_generator.py','settings.py','subscription_auditor.py']] + [f'utils/{u}' for u in ['i18n.py','auth.py','data_persistence.py','notifications.py','formatting.py','logger.py','security.py','validators.py','insights.py','category_learner.py','importers.py','household.py','sync.py','invoice_templates.py','report_builder.py','search.py','finance_api.py','fuzzy_matcher.py']]]; print('All OK')"

# Run all tests
python -X utf8 -m pytest tests/ -v --tb=short

# Launch app
python -X utf8 -m streamlit run app.py
```

**Manual smoke test after all fixes:**
1. Register new account → login → refresh → still logged in
2. Navigate to every module via sidebar → no crashes
3. Navigate to every module via dashboard buttons → correct page opens
4. Add data in each module → data persists after refresh
5. Switch language to Spanish → everything translated
6. Toggle a module off in Settings → gone from sidebar + dashboard
7. Switch to light mode → everything readable
8. Switch to dark mode → everything readable
9. Check notifications bell → shows relevant alerts
10. Sign out → back to landing page, session cleared

---

## Summary of Deliverables

| Phase | Version | Deliverable |
|-------|---------|-------------|
| 1 | v8.8 | Auth & session deep audit — every auth path verified and hardened |
| 2 | v8.9 | Module-by-module functional audit — every feature in every module tested |
| 3 | v9.0 | Cross-cutting audit — data persistence, notifications, i18n, charts, errors, empty states |
| 4 | v9.1 | Test suite expansion to 200+, dead code removal, performance, logging, final polish |

Work through each phase sequentially. Bump `version.txt` at the end of each phase. Do NOT skip phases or combine them — each one builds on the previous. Fix ALL bugs found during auditing before moving to the next phase.
