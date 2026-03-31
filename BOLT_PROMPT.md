Build a personal finance web app called **FinanceKit** using the complete source code below.

## What it is
A personal finance dashboard where users track budgets, savings goals, investments, and subscriptions. Dark mode only. Clean, modern UI.

## Requirements
- **Framework**: Flask (Python) with Jinja2 HTML templates
- **Auth**: Email/password sign-in with bcrypt hashing, plus Google OAuth and GitHub OAuth
- **Database**: JSON file storage (one file per data type per user — transactions.json, goals.json, portfolio.json, etc.)
- **Theme**: Dark mode ONLY — no light mode. Color scheme: background #0f1117, cards #1e1e2f, accent #6366f1 (indigo)
- **Responsive**: Sidebar navigation on desktop, hamburger menu on mobile

## Pages to build
1. **Login / Register** — email + password, Google OAuth button, GitHub OAuth button
2. **Dashboard** — summary cards (monthly spending, income, portfolio value, subscription costs), goals progress bars, spending by category, recent transactions table
3. **Budget Tracker** — add/delete transactions with date, description, amount, category. Shows spending by category with progress bars
4. **Goal Tracker** — create savings goals with name, target amount, current amount, deadline. Cards with progress bars, update/delete buttons
5. **Portfolio Tracker** — add/remove stock/crypto holdings with ticker, quantity, avg price. Table showing value per holding
6. **Subscription Auditor** — add/remove recurring subscriptions. Shows monthly and yearly totals
7. **Settings** — change display name, currency (USD/EUR/GBP/JPY/etc), date format, password. Export all data as ZIP

## Design rules
- Font: Inter
- All buttons must actually work (submit forms, navigate, delete items)
- No emojis anywhere in the UI
- Sidebar with navigation links, user name/email at bottom, sign out button
- Cards use border-radius: 12px, subtle borders, no heavy shadows
- Progress bars for goals and budget categories
- Tables for transactions and holdings

## Deploy it with a live URL when done.

---

## FULL SOURCE CODE BELOW

Copy every file exactly as shown. The file paths are in the ### FILE: headers.

