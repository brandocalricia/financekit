# FinanceKit v5.1 - v6.0 — Usability & Cross-Platform Prompt

> **For a new Claude Code session.** This prompt contains everything needed to implement versions 5.1 through 6.0 of FinanceKit. Each version should be implemented sequentially: code it, run tests, commit with the format `FinanceKit vX.X — Short Description`, and push. Do not skip versions. Do not ask questions — use your best judgment. Read the full codebase before starting.

---

## Project Context

**Repository**: `https://github.com/brandocalricia/financekit.git`
**Working directory**: `C:\Users\bzcni\OneDrive\Desktop\vs code projects\Finance Toolkit`
**Current version**: 5.0 (after UX overhaul)
**Python**: 3.11 (pinned in `runtime.txt` for Streamlit Cloud)
**Framework**: Streamlit 1.45.0
**Deployment**: Streamlit Community Cloud at `financekit.streamlit.app`
**Tests**: 123+ tests in `tests/` — all must pass after every version
**Total codebase**: ~13,200+ lines across 30+ Python files

### Critical Rules
- **NEVER use `use_container_width=True/False`** — deprecated in Streamlit 1.45. Use `width='stretch'` or `width='content'`.
- **NEVER hardcode dark-mode colors.** Always use CSS custom properties (`var(--fk-*)`).
- **NEVER add packages requiring C compilation** to `requirements.txt` (breaks Streamlit Cloud). Keep desktop-only packages commented out.
- **Commit format**: `FinanceKit vX.X — Short Description` with `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
- **All data files** in `data/` (gitignored). Per-user data in `data/users/{user_id}/`.
- **Google OAuth** via `st.secrets["google"]` (cloud) or `data/auth_config.json` (local).
- After the v4.2-5.0 UX overhaul, the theme system uses CSS custom properties with `!important` on all elements, Google Sign-In works via manual OAuth or `streamlit-google-auth`, and the settings page has been reorganized.

### Architecture Overview

```
app.py (~2200+ lines)        — Main app: CSS, auth, landing, login, sidebar, dashboard, routing
modules/
  budget_tracker.py (1530)   — Budget categories, transactions, spending charts, bills
  settings.py (1333)         — Reorganized settings (Appearance, Account, Modules, etc.)
  job_tracker.py (1313)      — Freelance: clients, invoices, time tracking
  subscription_auditor.py (869) — Subscription detection, price tracking
  report_generator.py (817)  — CSV/OFX import, PDF/Excel export
  portfolio_tracker.py (666) — Stock/crypto holdings, watchlist, alerts
  goal_tracker.py (360)      — Savings goals, milestones
  receipt_scanner.py (288)   — PDF/image upload, text extraction
utils/
  auth.py (369+)             — Email/password + Google OAuth, sessions
  data_persistence.py (147)  — JSON storage, per-user isolation, backups
  notifications.py (297)     — Notifications, email digest
  chart_config.py (71)       — Plotly theming, 12+ chart colors
  formatting.py (118)        — Currency/date formatting
  search.py (139)            — Global search
  + 15 other utility files
.streamlit/config.toml       — base="dark", primaryColor="#6366f1"
runtime.txt                  — python-3.11
requirements.txt             — Dependencies (loose version pins)
run_app.py                   — Desktop launcher (pywebview)
start.bat                    — Windows shortcut launcher
```

### What Users Can Currently Do
- Sign in via Google OAuth or Email/Password
- Track budgets and expenses by category
- Scan receipts (PDF/image upload)
- Monitor stock/crypto portfolio
- Track savings goals with milestones
- Manage freelance clients and invoices
- Detect and audit subscriptions
- Import bank data (CSV, OFX, YNAB, Mint, Monarch)
- Generate PDF/Excel financial reports
- Share expenses with household members
- Get notifications for bills, goals, price alerts
- Export all data as backup ZIP

### What Users CAN'T Do Yet (This Prompt Fixes These)
- Access the app on their phone (mobile browser works but no PWA/installable app)
- Use the app as a desktop program without command line
- Sync data between devices (currently per-device storage)
- Use the app offline
- Get push notifications on their phone
- Share a read-only view of their finances with a partner/advisor

---

## Version 5.1 — Progressive Web App (PWA) & Mobile-First

**Goal**: Users can "install" FinanceKit on their phone's home screen and use it like a native app. The mobile experience is first-class.

### Tasks

1. **Create PWA manifest and service worker**
   - Create a `static/` directory in the project root
   - Create `static/manifest.json`:
     ```json
     {
       "name": "FinanceKit",
       "short_name": "FinanceKit",
       "description": "Your all-in-one personal finance toolkit",
       "start_url": "/",
       "display": "standalone",
       "background_color": "#0f1117",
       "theme_color": "#6366f1",
       "orientation": "any",
       "icons": [
         {
           "src": "/app/static/icon-192.png",
           "sizes": "192x192",
           "type": "image/png",
           "purpose": "any maskable"
         },
         {
           "src": "/app/static/icon-512.png",
           "sizes": "512x512",
           "type": "image/png",
           "purpose": "any maskable"
         }
       ]
     }
     ```
   - Generate app icons programmatically using Pillow:
     ```python
     # In a setup script or inline generation
     from PIL import Image, ImageDraw, ImageFont
     # Create 192x192 and 512x512 icons with "💰" or "FK" text
     # on indigo (#6366f1) background with rounded corners
     ```
   - Create `static/sw.js` (service worker) for basic offline caching:
     ```javascript
     const CACHE_NAME = 'financekit-v5.1';
     const urlsToCache = ['/', '/app/static/manifest.json'];

     self.addEventListener('install', event => {
       event.waitUntil(
         caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
       );
     });

     self.addEventListener('fetch', event => {
       event.respondWith(
         caches.match(event.request).then(response => {
           return response || fetch(event.request);
         })
       );
     });
     ```

2. **Inject PWA meta tags into Streamlit**
   - In `app.py`, inject via `st.components.v1.html()` at the top of the page (after `st.set_page_config`):
     ```python
     st.components.v1.html("""
     <script>
     // Inject manifest link
     if (!document.querySelector('link[rel="manifest"]')) {
         const link = document.createElement('link');
         link.rel = 'manifest';
         link.href = '/app/static/manifest.json';
         document.head.appendChild(link);
     }
     // Inject theme-color meta
     if (!document.querySelector('meta[name="theme-color"]')) {
         const meta = document.createElement('meta');
         meta.name = 'theme-color';
         meta.content = '#6366f1';
         document.head.appendChild(meta);
     }
     // Inject apple-touch-icon
     if (!document.querySelector('link[rel="apple-touch-icon"]')) {
         const link = document.createElement('link');
         link.rel = 'apple-touch-icon';
         link.href = '/app/static/icon-192.png';
         document.head.appendChild(link);
     }
     // Register service worker
     if ('serviceWorker' in navigator) {
         navigator.serviceWorker.register('/app/static/sw.js').catch(() => {});
     }
     // Inject viewport meta for mobile
     const vp = document.querySelector('meta[name="viewport"]');
     if (vp) vp.content = 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover';
     </script>
     """, height=0)
     ```

3. **Mobile-optimized layout**
   - Detect mobile via CSS media queries (already partially done)
   - On screens ≤ 768px:
     - Single-column layout (no side-by-side columns for forms or cards)
     - Larger touch targets (minimum 48px height for all buttons and links)
     - Bottom navigation bar (fixed) with 5 icons: Home, Budget, Goals, Portfolio, More
     - "More" opens a sheet with remaining modules
     - Floating Action Button (FAB) for "Add Expense" — always visible
     - Pull-to-refresh hint (CSS animation)
   - Bottom nav bar implementation:
     ```css
     @media (max-width: 768px) {
       /* Hide sidebar */
       section[data-testid="stSidebar"] { display: none !important; }

       /* Bottom nav */
       .fk-bottom-nav {
         position: fixed;
         bottom: 0;
         left: 0;
         right: 0;
         height: 64px;
         background: var(--fk-card);
         border-top: 1px solid var(--fk-border);
         display: flex;
         justify-content: space-around;
         align-items: center;
         z-index: 999;
         padding-bottom: env(safe-area-inset-bottom);
       }
       .fk-bottom-nav-item {
         display: flex;
         flex-direction: column;
         align-items: center;
         font-size: 0.7rem;
         color: var(--fk-text-muted);
         cursor: pointer;
         padding: 8px 12px;
       }
       .fk-bottom-nav-item.active {
         color: var(--fk-accent);
       }
       .fk-bottom-nav-item .icon { font-size: 1.4rem; }

       /* Add padding at bottom so content isn't hidden behind nav */
       .main .block-container { padding-bottom: 80px !important; }

       /* FAB */
       .fk-fab {
         position: fixed;
         bottom: 80px;
         right: 16px;
         width: 56px;
         height: 56px;
         border-radius: 50%;
         background: var(--fk-accent);
         color: white;
         font-size: 1.5rem;
         display: flex;
         align-items: center;
         justify-content: center;
         box-shadow: 0 4px 12px rgba(99,102,241,0.4);
         z-index: 998;
         cursor: pointer;
       }
     }
     ```
   - Bottom nav rendered via `st.markdown()` with HTML/CSS
   - Use JavaScript click handlers to update `st.session_state` via Streamlit's `stSetComponentValue` or use hidden buttons

4. **Install prompt (Add to Home Screen)**
   - Detect if app is NOT running in standalone mode
   - Show a dismissible banner at the top: "Install FinanceKit on your phone for the best experience" with "Install" button
   - Use the `beforeinstallprompt` JavaScript event
   - Dismiss state saved in `localStorage` so it doesn't show again
   - On iOS, show manual instructions: "Tap the share button (⬆️) → Add to Home Screen"

5. **Safe area handling for notched phones**
   - Use `env(safe-area-inset-top)`, `env(safe-area-inset-bottom)` in CSS
   - Add `viewport-fit=cover` to viewport meta tag

6. **Touch gestures**
   - Swipe left on transaction to reveal "Delete" action (CSS + JS)
   - Swipe right on transaction to reveal "Edit" action
   - Long-press on a goal card to open edit dialog

### Verification
- Open the Streamlit Cloud URL on a phone
- "Add to Home Screen" prompt appears
- App launches in standalone mode (no browser UI)
- Bottom navigation works
- FAB opens Quick Entry dialog
- All modules are accessible on mobile
- Touch targets are large enough

---

## Version 5.2 — Desktop App Polish

**Goal**: Users can run FinanceKit as a native desktop application by double-clicking a file — no terminal, no browser, no setup.

### Tasks

1. **Improve `run_app.py`**
   - **Auto-install dependencies** on first run:
     ```python
     def _ensure_deps():
         """Check and install core + desktop deps on first run."""
         marker = os.path.join(_base_dir, ".deps_installed")
         if os.path.exists(marker):
             return
         print("Setting up FinanceKit (first time only)...")
         # Core deps
         subprocess.run([sys.executable, "-m", "pip", "install", "-r",
                        os.path.join(_base_dir, "requirements.txt")], check=True)
         # Desktop extras
         subprocess.run([sys.executable, "-m", "pip", "install",
                        "pywebview>=5.0"], check=False)
         Path(marker).touch()
     ```
   - **Splash screen** while Streamlit starts:
     - Use `pywebview` to show a small loading window (400x200) with the FinanceKit logo
     - Close splash when main window opens
   - **System tray icon** (optional — only if `pystray` is installed):
     - Minimize to tray instead of closing
     - Right-click menu: "Open", "Restart", "Quit"
     - Tray icon shows notification badge
   - **Window title**: "FinanceKit v{version}" (read from `version.txt`)
   - **Window icon**: Use the same icon as PWA
   - **Graceful shutdown**: On window close:
     - Stop the Streamlit subprocess
     - Wait up to 5 seconds for clean shutdown
     - Force-kill if still running
   - **Port conflict resolution**:
     - If port 8501 is busy, try 8502, 8503, etc. (up to 8510)
     - Pass the port to both Streamlit and pywebview

2. **Create `start.bat` (Windows)**
   ```batch
   @echo off
   title FinanceKit
   cd /d "%~dp0"
   python run_app.py
   if errorlevel 1 (
       echo.
       echo FinanceKit requires Python 3.11+. Download from python.org
       echo.
       pause
   )
   ```

3. **Create `start.sh` (Mac/Linux)**
   ```bash
   #!/bin/bash
   cd "$(dirname "$0")"
   python3 run_app.py || {
       echo ""
       echo "FinanceKit requires Python 3.11+. Install with: brew install python@3.11"
       echo ""
       read -p "Press Enter to exit..."
   }
   ```
   - Make it executable: `chmod +x start.sh`

4. **Create `start.command` (macOS double-click support)**
   ```bash
   #!/bin/bash
   cd "$(dirname "$0")"
   python3 run_app.py
   ```

5. **Desktop shortcut creator**
   - Add a script `create_shortcut.py` that:
     - On Windows: creates a `.lnk` shortcut on the Desktop pointing to `start.bat`
     - On macOS: creates an `.app` bundle in Applications
     - On Linux: creates a `.desktop` file in `~/.local/share/applications/`
   - Include the FinanceKit icon in the shortcut

6. **Auto-update checker**
   - On desktop launch, check the GitHub repo's latest release tag
   - If newer version available, show a notification: "FinanceKit {version} is available. Update?"
   - "Update" button runs `git pull` in the background and restarts

7. **Offline mode**
   - Desktop app should work offline for all features except:
     - Google Sign-In (needs internet)
     - Stock/crypto prices (show cached prices with "Last updated: X ago")
     - Update checker
   - Show "Offline" badge in the header when no internet connection
   - Detect connectivity: `requests.get("https://httpbin.org/get", timeout=3)` wrapped in try/except

### Verification
- Double-click `start.bat` on Windows → app opens in native window
- No terminal window visible (or minimized)
- System tray icon appears
- Window title shows correct version
- App works offline (with cached data)
- Closing the window shuts down cleanly

---

## Version 5.3 — Cloud Data Sync & Multi-Device Support

**Goal**: Users can sign in on any device (phone, laptop, work computer) and see the same data. Data syncs automatically.

### Tasks

1. **Design the sync architecture**
   - FinanceKit currently stores all data in local JSON files under `data/users/{user_id}/`
   - For cloud sync, we need a server-side storage backend
   - **Approach**: Use the Streamlit Cloud instance as the canonical data store
   - When users access via Streamlit Cloud → data is already server-side (in the container's filesystem)
   - When users access via desktop app → sync data to/from the cloud instance via API
   - **Sync endpoint**: Create a lightweight API in the Streamlit app that serves user data

2. **Create sync API endpoints**
   - Use Streamlit's query params as a poor-man's API (since Streamlit doesn't natively support REST APIs):
   - Better approach: Create a `sync.py` utility that uses a free cloud storage backend
   - **Option A**: Use GitHub Gist as storage (each user gets a private gist)
   - **Option B**: Use JSONBin.io (free tier: 10k requests/month)
   - **Option C (recommended)**: Use the Streamlit Cloud filesystem + user authentication
     - When logged in on cloud: data is already there (filesystem persists for the app)
     - When logged in on desktop: periodically push/pull data to cloud via HTTP

3. **Implement sync using Streamlit Cloud as the source of truth**
   - Add to `utils/data_persistence.py`:
     ```python
     def sync_to_cloud(user_id: str):
         """Push local user data to the cloud instance."""
         # Zip all user JSON files
         # POST to the cloud instance's sync endpoint
         pass

     def sync_from_cloud(user_id: str):
         """Pull user data from the cloud instance to local."""
         # GET from the cloud instance's sync endpoint
         # Unzip and overwrite local files
         pass

     def get_last_sync_time(user_id: str) -> str:
         """Return ISO timestamp of last successful sync."""
         pass
     ```

4. **Sync UI in Settings**
   - "Cloud Sync" section in Settings:
     - Toggle: "Enable Cloud Sync"
     - Last sync time: "Last synced: 5 minutes ago"
     - "Sync Now" button (manual sync)
     - Auto-sync frequency: "Every 5 minutes" / "Every 15 minutes" / "Manual only"
     - Conflict resolution: "Cloud wins" / "Local wins" / "Ask me" (keep it simple — default to "newest wins")

5. **Sync indicator in sidebar/header**
   - Small icon showing sync status:
     - ☁️ Synced (green dot)
     - 🔄 Syncing... (spinning)
     - ⚠️ Sync error (yellow)
     - 📴 Offline (gray)
   - Click to open sync details

6. **Handle data conflicts**
   - Track `last_modified` timestamp for each JSON file
   - On sync: compare timestamps
   - If both sides modified since last sync → flag as conflict
   - Simple merge strategy: newest timestamp wins (per-file, not per-record)
   - Show toast notification when conflict auto-resolved: "Budget data synced (cloud version was newer)"

7. **Secure sync**
   - Sync requests must include the user's session token
   - Data in transit is encrypted (HTTPS)
   - Data at rest uses the existing per-user directory isolation

### Verification
- Sign in on Streamlit Cloud and add a transaction
- Sign in on desktop app with same account
- Trigger sync → transaction appears on desktop
- Add a goal on desktop → sync → goal appears on cloud
- Works with network interruptions (queues sync for later)

---

## Version 5.4 — Notification System Overhaul

**Goal**: Users get timely, useful notifications across all platforms — in-app, email, and browser push.

### Tasks

1. **Redesign in-app notifications**
   - Create a notification center accessible from the header (not sidebar)
   - Bell icon with unread count badge
   - Click opens a dropdown/panel showing recent notifications
   - Each notification:
     - Icon (based on type: 💰 budget, 🎯 goal, 📈 portfolio, 🔔 bill)
     - Title + message
     - Relative time ("2 hours ago")
     - "Mark as read" on click
     - Action button (e.g., "View Budget" → navigates to module)
   - "Mark all as read" and "Clear all" at the top
   - "View all notifications" link at bottom → full notification history page

2. **Browser push notifications**
   - Request notification permission via JavaScript:
     ```javascript
     if ('Notification' in window && Notification.permission === 'default') {
         Notification.requestPermission();
     }
     ```
   - When a notification is created in Python, also trigger a browser notification:
     ```javascript
     function showNotification(title, body, icon) {
         if (Notification.permission === 'granted') {
             new Notification(title, { body, icon: '/app/static/icon-192.png' });
         }
     }
     ```
   - Inject via `st.components.v1.html()` when notifications are created
   - Works on desktop browsers and mobile PWA

3. **Email notification improvements**
   - Redesign email template to be theme-neutral (light background, dark text — readable everywhere)
   - Use proper HTML email template with inline CSS:
     ```html
     <div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;background:#ffffff;padding:32px;">
       <div style="text-align:center;margin-bottom:24px;">
         <h1 style="color:#6366f1;font-size:24px;">💰 FinanceKit</h1>
       </div>
       <h2 style="color:#1e293b;font-size:18px;">Your Daily Digest</h2>
       <!-- notification items -->
       <div style="padding:12px 16px;border-left:3px solid #6366f1;background:#f8fafc;margin-bottom:12px;border-radius:4px;">
         <strong style="color:#1e293b;">{title}</strong>
         <p style="color:#64748b;margin:4px 0 0;">{message}</p>
       </div>
       <!-- footer -->
       <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
       <p style="color:#94a3b8;font-size:12px;text-align:center;">
         You received this because you enabled email digests in FinanceKit settings.
       </p>
     </div>
     ```

4. **Smart notification timing**
   - Don't spam: max 1 notification per module per hour (dedup window)
   - Group similar notifications: "3 bills due this week" instead of 3 separate notifications
   - Quiet hours: respect user's "Do Not Disturb" settings (existing feature — verify it works)
   - Priority levels: Normal (in-app only), Important (in-app + browser), Urgent (in-app + browser + email)

5. **Notification preferences in Settings**
   - Per-module toggle: Budget, Goals, Portfolio, Bills, Subscriptions, Freelance
   - Per-channel toggle: In-app, Browser push, Email
   - Frequency: Real-time / Hourly digest / Daily digest
   - Quiet hours: Start time, End time
   - "Test Notification" button

### Verification
- Notifications appear in the notification center
- Browser push notifications work (after permission granted)
- Email digest sends with the new template
- Quiet hours are respected
- Notification grouping works

---

## Version 5.5 — Sharing & Collaboration

**Goal**: Users can share a read-only view of their finances with a partner, advisor, or accountant. Households can collaborate in real-time.

### Tasks

1. **Share link generation**
   - In Settings → "Sharing", add "Create Share Link" button
   - Generates a unique token: `https://financekit.streamlit.app/?share={token}`
   - Share link options:
     - What to share: Dashboard only / All modules / Specific modules (checkboxes)
     - Expiry: 24 hours / 7 days / 30 days / Never
     - Password protection (optional)
   - Store share tokens in `data/users/{user_id}/shares.json`

2. **Read-only shared view**
   - When app loads with `?share={token}` in URL:
     - Validate the token (check expiry, password if set)
     - Load the shared user's data (read-only)
     - Show a banner: "You're viewing {name}'s finances (read-only)"
     - Hide all edit/add/delete buttons
     - Hide Settings
     - Show only the modules the user selected for sharing
   - Do NOT create a session or require sign-in for shared views

3. **Household collaboration improvements**
   - Real-time balance tracking: when one member adds an expense, others see it immediately (on next page load)
   - "Request Payment" button: sends an in-app notification to another household member
   - Settlement history: track when balances were settled
   - Household dashboard showing:
     - Who owes whom (directed graph)
     - Shared expenses this month
     - Shared goal progress per member

4. **Advisor/Accountant access**
   - Special share type: "Financial Advisor"
   - Can view all financial data + reports
   - Can leave comments/notes (stored in shared view data)
   - Cannot modify any data
   - Audit log: track when the advisor accessed the data

5. **Export for sharing**
   - "Share as PDF" button on any report → generates a branded PDF
   - "Share as Excel" → downloadable spreadsheet
   - "Share as Link" → the share link system above

### Verification
- Generate a share link → open in incognito → see shared data
- Share link with password works
- Shared view is truly read-only (no edit capabilities)
- Household balances are accurate
- Settlement tracking works

---

## Version 5.6 — Report & Export Overhaul

**Goal**: Reports are professional-quality, exportable, and useful for tax prep, financial planning, and advisor meetings.

### Tasks

1. **Report templates**
   - Create 5 pre-built report templates:
     - **Monthly Summary**: spending by category, income vs expenses, savings rate
     - **Year-in-Review**: full year breakdown with charts, trends, highlights
     - **Tax Summary**: tax-deductible expenses by category, total deductions, quarterly breakdown
     - **Net Worth Statement**: assets, liabilities, net worth over time
     - **Cash Flow Analysis**: income sources, expense categories, net cash flow by month
   - Each template has a "Generate" button → creates PDF in-app

2. **PDF report quality**
   - Use `fpdf2` (already installed) for PDF generation
   - Professional layout:
     - FinanceKit logo + "Financial Report" header on page 1
     - User name, date range, generated date
     - Table of contents
     - Charts embedded as images (fallback to text tables if chart export fails)
     - Color-coded categories
     - Page numbers in footer
     - Summary/highlights section at the top of each report type

3. **Excel export improvements**
   - Multi-sheet workbook:
     - Sheet 1: Summary dashboard
     - Sheet 2: All transactions
     - Sheet 3: Budget vs Actual
     - Sheet 4: Goals progress
     - Sheet 5: Portfolio holdings
   - Formatted cells: currency formatting, date formatting, conditional coloring
   - Auto-filter enabled on data columns
   - Charts embedded in Excel (using `xlsxwriter` chart API)

4. **Scheduled reports**
   - "Schedule Report" option in Report Generator:
     - Frequency: weekly / monthly / quarterly / yearly
     - Report type: select from templates
     - Delivery: email (if SMTP configured) or in-app notification
   - Store schedule in `settings.json` → `scheduled_reports: [...]`
   - Check schedule on each app load (or on a background timer)

5. **Import improvements**
   - Support more bank formats:
     - Add: Discover, USAA, Navy Federal, PNC, TD Bank, Citi
     - Each bank has a column mapping profile in `utils/importers.py`
   - Smarter CSV detection:
     - Auto-detect delimiter (comma, tab, semicolon, pipe)
     - Auto-detect encoding (UTF-8, Latin-1, Windows-1252)
     - Handle quoted fields with commas inside
   - Import preview: show first 5 rows with detected column mapping, let user adjust before committing
   - Duplicate detection: warn if transactions appear to already exist (fuzzy match on date + amount + description)

### Verification
- Generate each of the 5 report templates → PDF downloads correctly
- Excel export has all sheets with proper formatting
- Import a bank CSV from Chase, BofA, Wells Fargo, Capital One → correct parsing
- Import detects duplicates
- Scheduled report settings persist

---

## Version 5.7 — Security Hardening

**Goal**: The app is secure enough for users to trust with their financial data.

### Tasks

1. **Rate limiting on auth endpoints**
   - Track failed login attempts per IP/email
   - After 5 failed attempts in 15 minutes → lock account for 30 minutes
   - Show remaining attempts: "3 attempts remaining before lockout"
   - Store attempt counts in `data/login_attempts.json` (gitignored)
   - Clear on successful login

2. **Password security improvements**
   - Minimum 8 characters (up from 6)
   - Check against common passwords list (top 1000)
   - Show strength requirements inline:
     - ✅ At least 8 characters
     - ✅ Contains a number
     - ✅ Contains uppercase and lowercase
     - ✅ Contains a special character
   - Each requirement turns green as met

3. **Session security**
   - Generate a secure session token (not just login timestamp)
   - Store active sessions: `data/users/{user_id}/sessions.json`
   - Show "Active Sessions" in Settings: device type, IP, last active time
   - "Sign out of all other devices" button
   - Sessions expire independently (one device's expiry doesn't affect others)

4. **Data encryption at rest** (optional, best-effort)
   - Encrypt sensitive JSON files (transactions, receipts, portfolio) using `cryptography.fernet`
   - Key derived from user's password hash (PBKDF2)
   - Transparent: `load_json()` decrypts, `save_json()` encrypts
   - If `cryptography` not installed, fall back to plaintext (current behavior)
   - Add `cryptography` to requirements.txt (it has pre-built wheels)

5. **Audit logging**
   - Log all security-relevant events to `data/users/{user_id}/audit.json`:
     - Login (success/failure), logout
     - Password change
     - Data export/import
     - Share link creation
     - Account deletion
   - Each entry: timestamp, event type, IP (if available), details
   - Show audit log in Settings → Account → "Security Activity"

6. **Input sanitization**
   - Sanitize all user inputs that are rendered as HTML:
     - Transaction descriptions, goal names, client names, invoice notes
     - Use `html.escape()` before any `st.markdown(unsafe_allow_html=True)` rendering
   - Prevent XSS via share links or injected descriptions

7. **Secrets management**
   - SMTP password: migrate from plaintext in `settings.json` to `st.secrets` or encrypted storage
   - OAuth secrets: already in `st.secrets` (good)
   - Add warning in Settings if SMTP password is stored in plaintext

### Verification
- Try logging in with wrong password 5+ times → account locks
- Password strength meter shows requirements
- Active sessions list shows current device
- "Sign out everywhere" works
- Audit log records events
- XSS attempt in transaction description is escaped

---

## Version 5.8 — Accessibility & Internationalization

**Goal**: The app is usable by everyone, regardless of ability or language preference. Currency formatting matches the user's locale.

### Tasks

1. **Accessibility (a11y)**
   - All images/icons have alt text
   - All form inputs have associated labels (not just placeholders)
   - Focus indicators are visible (outline on focused elements)
   - Color is never the sole indicator — use icons/text alongside:
     - ✅ Profit: green + "▲" arrow
     - ❌ Loss: red + "▼" arrow
     - ⚠️ Warning: yellow + "!" icon
   - Tab navigation works logically (top to bottom, left to right)
   - Screen reader support: use proper heading hierarchy (h1 → h2 → h3)
   - Skip-to-content link at the top of the page
   - Minimum touch targets: 48x48px on mobile
   - Reduced motion: respect `prefers-reduced-motion` CSS media query (disable celebrations, animations)

2. **Currency formatting per locale**
   - Update `utils/formatting.py`:
     - USD: $1,234.56 (comma thousands, period decimal)
     - EUR: 1.234,56 € (period thousands, comma decimal, symbol after)
     - GBP: £1,234.56 (same as USD but with £)
     - JPY: ¥1,234 (no decimals)
     - INR: ₹1,23,456.78 (Indian grouping: lakhs and crores)
     - BRL: R$ 1.234,56 (Brazilian Real)
   - Use Python's `locale` module or custom formatting logic
   - Add currency selection in onboarding AND Settings

3. **Date formatting per locale**
   - Already supports MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
   - Add relative dates: "Today", "Yesterday", "3 days ago" for recent items
   - Verify all date displays use `format_date()` from `utils/formatting.py`

4. **Responsive text sizing**
   - Use `rem` units throughout (not `px` for text)
   - Respect browser font size settings
   - In Settings → Appearance: "Font Size" slider (Small / Medium / Large)
   - Maps to root font size: 14px / 16px / 18px

5. **High contrast mode**
   - Add a "High Contrast" toggle in Settings → Appearance
   - When enabled: stronger borders, bolder text, higher contrast colors
   - Uses a third set of CSS variables (`_high_contrast_vars`)

6. **Language preparation** (i18n groundwork — NOT full translation)
   - Create `utils/i18n.py` with a `t()` function (translate):
     ```python
     _STRINGS = {
         "en": {
             "dashboard": "Dashboard",
             "settings": "Settings",
             "sign_in": "Sign In",
             "sign_out": "Sign Out",
             "add_expense": "Add Expense",
             # ... all UI strings
         }
     }

     def t(key: str) -> str:
         lang = st.session_state.get("language", "en")
         return _STRINGS.get(lang, _STRINGS["en"]).get(key, key)
     ```
   - Replace all hardcoded strings in navigation, buttons, headers with `t("key")`
   - Language selector in Settings → Appearance (only English for now, but infrastructure ready)
   - This is GROUNDWORK ONLY — don't translate to other languages yet

### Verification
- Tab through the entire app — all elements are reachable
- Screen reader can announce all elements
- Currency formatting changes when user selects different currencies
- High contrast mode is visually distinct
- `t()` function works and strings display correctly

---

## Version 5.9 — Performance & Reliability

**Goal**: The app is fast, reliable, and handles edge cases gracefully.

### Tasks

1. **Caching strategy**
   - `@st.cache_data(ttl=300)` on all data-loading functions (5-minute TTL)
   - `@st.cache_resource` for expensive initializations (database connections, API clients)
   - Stock/crypto price cache: 5-minute TTL with stale-while-revalidate pattern
   - Clear cache on data write (use `st.cache_data.clear()` after saving)
   - Add cache statistics in Settings → About → "Cache Info"

2. **Lazy loading**
   - Only import module code when the user navigates to that page:
     ```python
     if page == "💰 Budget Tracker":
         from modules.budget_tracker import render
         render()
     ```
   - This is partially done — verify ALL modules use lazy imports
   - Avoid top-level imports of heavy modules in `app.py`

3. **Background data processing**
   - Move expensive operations to run once per session, not on every render:
     - Bill reminder checks
     - Subscription detection
     - Auto-import folder monitoring
     - Recurring invoice generation
   - Use `if "startup_done" not in st.session_state:` pattern

4. **Error recovery**
   - Every module's render function wrapped in try/except:
     ```python
     try:
         module.render()
     except Exception as e:
         st.error("Something went wrong loading this module.")
         with st.expander("Error details"):
             st.code(traceback.format_exc())
         logger.error(f"Module error: {e}", exc_info=True)
     ```
   - Corrupted JSON recovery: if `load_json()` fails, try loading from the most recent backup
   - Show "Data recovered from backup" toast when recovery succeeds

5. **Memory management**
   - Limit dataframe sizes displayed in the UI (max 500 rows visible, paginate the rest)
   - Don't load entire transaction history into memory — use pagination
   - Clear large session state objects when navigating away from a module

6. **Startup time optimization**
   - Measure current startup time
   - Target: < 3 seconds from app load to first paint
   - Profile with `time.time()` at key points
   - Reduce CSS blob: combine duplicate rules, minify
   - Defer non-critical JavaScript injection

7. **Health check**
   - Add a hidden health check: `?health=1` in query params returns app version and status
   - Useful for monitoring uptime

### Verification
- App loads in under 3 seconds
- Navigate between all modules — no lag
- Corrupt a JSON file intentionally → app recovers from backup
- Stock prices load once and cache for 5 minutes
- Memory usage stays stable during extended use

---

## Version 6.0 — Launch-Ready Polish & Production Hardening

**Goal**: FinanceKit is ready for public launch. Every rough edge is smoothed, every error is handled, and the app feels like a professional product.

### Tasks

1. **Final visual polish**
   - Consistent spacing throughout: 16px between sections, 8px between related elements
   - All cards have the same border radius (12px), padding (16px), and shadow style
   - All buttons have consistent styling (primary: accent color, secondary: outlined)
   - Loading spinners on all data-fetching operations
   - Smooth transitions on theme change (CSS `transition: all 0.3s ease`)
   - Page transitions: smooth fade between modules

2. **Error pages**
   - 404 equivalent: if URL has unknown query params, show "Page not found" with back button
   - Network error: if API calls fail, show "Could not connect. Check your internet." with retry button
   - Server error: if module crashes, show friendly error with "Report Bug" button (opens GitHub issues)

3. **Onboarding improvements**
   - "What's New" modal after app update (checks `version.txt` against stored last-seen version)
   - Feature tour tooltips on first visit to each module:
     - Highlight key UI elements with a pulsing border
     - "Got it" button to dismiss
     - Stored in `settings.json` → `seen_tours: ["budget", "goals", ...]`
   - Quick-start video placeholder (YouTube embed link in Settings → About)

4. **Branding**
   - Consistent logo usage: "💰 FinanceKit" everywhere
   - Footer on all pages: "FinanceKit v{version} — Your finances, your control."
   - Favicon: set via `st.set_page_config(page_icon="💰")` (already done)
   - Open Graph meta tags for social sharing:
     ```html
     <meta property="og:title" content="FinanceKit — Personal Finance Toolkit">
     <meta property="og:description" content="Track budgets, investments, goals, and more.">
     <meta property="og:image" content="/app/static/og-image.png">
     ```

5. **Legal & compliance**
   - Terms of Service page (simple, accessible from login and Settings)
   - Privacy Policy page (what data is stored, how it's used, deletion policy)
   - Cookie consent (if applicable for Streamlit Cloud — check requirements)
   - GDPR compliance: "Download My Data" and "Delete My Account" buttons in Settings

6. **Analytics (privacy-respecting)**
   - Track anonymous usage metrics (stored locally, not sent anywhere):
     - Which modules are used most
     - Session duration
     - Feature adoption (how many users use each feature)
   - Show usage stats in Settings → About (for the user's own curiosity)
   - NO tracking cookies, NO third-party analytics, NO data sent to external servers

7. **Documentation**
   - In-app help system:
     - "?" button on each module header → opens help panel
     - Help content: what the module does, how to use it, tips & tricks
     - FAQ section in Settings → About
   - Create a `GUIDE.md` in the repo (comprehensive user guide)

8. **Final testing checklist**
   - [ ] All modules load without errors (both themes)
   - [ ] Google Sign-In works on Streamlit Cloud
   - [ ] Email sign-up and login work
   - [ ] Landing page converts (looks professional, clear CTA)
   - [ ] Onboarding works for new users
   - [ ] Dashboard shows correct data with correct calculations
   - [ ] Budget Tracker: add, edit, delete transactions; charts render
   - [ ] Goal Tracker: create, contribute, achieve, delete goals
   - [ ] Portfolio Tracker: add/remove holdings; prices update
   - [ ] Receipt Scanner: upload and extract data
   - [ ] Subscription Auditor: detect and manage subscriptions
   - [ ] Freelance Dashboard: full client/invoice lifecycle
   - [ ] Report Generator: import data, generate PDF/Excel
   - [ ] Settings: all sections functional, changes persist
   - [ ] Mobile: bottom nav, FAB, touch targets, PWA install
   - [ ] Desktop: native window opens, no terminal visible
   - [ ] Notifications: in-app, browser push, email digest
   - [ ] Share link: generate, access, read-only view
   - [ ] Cloud sync: data persists across sessions
   - [ ] Security: rate limiting, password requirements, audit log
   - [ ] Accessibility: keyboard nav, screen reader, high contrast
   - [ ] Performance: < 3s load, no lag between pages
   - [ ] All tests pass (123+)

9. **Update version.txt to 6.0**

10. **Final commit**: `FinanceKit v6.0 — Production Ready`

### Verification
- Complete the testing checklist above — every item must pass
- Deploy to Streamlit Cloud and test the live URL
- Test on: Chrome desktop, Safari mobile (iPhone), Chrome mobile (Android)
- Have someone else (non-technical) try to sign up and use the app — note any confusion points

---

## File Reference: New Files to Create

| File | Purpose |
|------|---------|
| `static/manifest.json` | PWA manifest |
| `static/sw.js` | Service worker for offline caching |
| `static/icon-192.png` | App icon (192x192) |
| `static/icon-512.png` | App icon (512x512) |
| `static/og-image.png` | Social sharing preview image |
| `start.sh` | Mac/Linux launcher |
| `start.command` | macOS double-click launcher |
| `create_shortcut.py` | Desktop shortcut creator |
| `utils/i18n.py` | Internationalization strings & `t()` function |
| `utils/sync.py` | Cloud data sync utilities |
| `utils/security.py` | Rate limiting, session tokens, audit logging |
| `GUIDE.md` | User guide (only if time permits) |

## Dependencies to Add

| Package | Version | Purpose | Cloud-safe? |
|---------|---------|---------|-------------|
| `cryptography` | >=42.0 | Data encryption at rest | ✅ Yes (pre-built wheels) |

All other new features use only built-in Python libraries or already-installed packages.

---

## Summary of User Access Points After v6.0

| Platform | Access Method | URL / Path |
|----------|--------------|------------|
| **Any browser** | Streamlit Cloud | `https://financekit.streamlit.app` |
| **Phone (iOS/Android)** | PWA (Add to Home Screen) | Same URL, installed as app |
| **Windows desktop** | Double-click `start.bat` | Native pywebview window |
| **macOS desktop** | Double-click `start.command` | Native pywebview window |
| **Linux desktop** | Run `./start.sh` | Native pywebview window |
| **Shared view** | Share link | `https://financekit.streamlit.app/?share={token}` |

All platforms use the same account, same data (via cloud sync), and the same feature set.
