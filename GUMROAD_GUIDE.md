# Gumroad Publishing Guide — FinanceKit V2.1

## Step 1: Screenshot Your Product Images

Open each HTML file in Chrome at **1280x720** and take a screenshot:

1. Open the file in Chrome (double-click or drag into browser)
2. Press **F12** → Console tab → paste:
   ```js
   document.body.style.overflow = 'hidden';
   ```
3. Press **Ctrl+Shift+M** (device toolbar) → set to **1280 x 720**
4. Press **Ctrl+Shift+P** → type "screenshot" → select **Capture screenshot**

Do this for all 6 files in `assets/`:
| File | Use As |
|------|--------|
| `gumroad_thumbnail.html` | **Product thumbnail** (cover image) |
| `gumroad_feature_1.html` | Gallery image 1 — Dashboard overview |
| `gumroad_feature_2.html` | Gallery image 2 — Subscription Auditor |
| `gumroad_feature_3.html` | Gallery image 3 — Cost comparison |
| `gumroad_feature_4.html` | Gallery image 4 — Budget Tracker |
| `gumroad_feature_5.html` | Gallery image 5 — All 7 modules |

---

## Step 2: Unpublish the Old Product

1. Go to [gumroad.com/dashboard](https://gumroad.com/dashboard)
2. Click on your existing FinanceKit product
3. Click **Edit product**
4. Scroll down → click **Unpublish**
5. Confirm unpublish — existing customers keep access, but no new purchases

> **Don't delete it** — just unpublish. This preserves existing customer access.

---

## Step 3: Create the New V2.1 Product

### Basic Info
1. Click **New product** on your dashboard
2. **Name:** `FinanceKit — Personal Finance Toolkit`
3. **Price:** `$29.99` (set old price as `$49.99` for the crossed-out effect)
4. **Product type:** Digital download

### Upload the Zip
1. Under **Content**, click **Add content** → **File**
2. Upload `FinanceKit_v2.1.zip` from your Desktop
3. The file is ~92 KB — buyers download this after purchase

### Thumbnail
1. Under **Thumbnail**, upload the screenshot of `gumroad_thumbnail.html`
2. This is the main image shown in search results and your profile

### Gallery Images
1. Under **Gallery**, upload screenshots 1-5 (the feature images) in order
2. These appear as a carousel on the product page

---

## Step 4: Product Description

Copy-paste this into the Gumroad description editor:

---

**FinanceKit v2.1** — 7 Python-powered finance modules in one local toolkit. No subscriptions. No cloud. Your data stays on your machine.

### What's Inside

- **💰 Budget Tracker** — Track spending across 8 categories with daily averages and persistent transaction history
- **🧾 Receipt Scanner** — Upload receipts, extract data, export to CSV
- **📈 Portfolio Tracker** — Real-time stock prices, allocation donuts, performance charts
- **📊 Report Generator** — Branded PDF financial reports with charts and tables
- **💼 Freelance Dashboard** — Track clients, projects, and generate professional invoices
- **🔄 Subscription Auditor** — Paste a bank statement, find every recurring charge, see annual savings
- **🎯 Goal Tracker** — Set savings goals, quick-add funds, celebrate milestones

### What's New in V2.1

- 🔒 **Atomic file writes** — your data never corrupts, even during a crash
- 💾 **Auto-backups** — last 5 saves kept automatically, auto-restore on corruption
- 🌐 **Cross-browser support** — works in Chrome, Firefox, Safari, Edge
- 📱 **Responsive design** — looks great on any screen size
- 📊 **Redesigned charts** — consistent dark theme with donut charts
- ⚡ **Persistent data** — budget transactions and subscription decisions survive between sessions

### Why FinanceKit?

| | FinanceKit | YNAB | QuickBooks |
|---|---|---|---|
| Price | **$29.99 once** | $99/year | $180/year |
| Budget Tracking | ✅ | ✅ | ✅ |
| Receipt Scanning | ✅ | ❌ | ✅ |
| Portfolio Tracker | ✅ | ❌ | ❌ |
| Freelance Invoices | ✅ | ❌ | ✅ |
| 100% Offline | ✅ | ❌ | ❌ |
| No Subscription | ✅ | ❌ | ❌ |

### Requirements

- Python 3.10+
- Windows, Mac, or Linux
- Run `pip install -r requirements.txt` then `streamlit run app.py`
- Or use the included `start.bat` (Windows) / `start.sh` (Mac/Linux)

### Includes

- Full source code (not obfuscated)
- Sample data files for testing
- User guide PDF
- Lifetime updates via re-download

---

## Step 5: Settings & Tags

1. **Tags:** `finance`, `python`, `budgeting`, `personal-finance`, `toolkit`, `streamlit`, `portfolio`, `invoicing`
2. **Call to action button text:** `Buy Now — $29.99`
3. **Summary** (short description shown in previews):
   > 7 Python finance modules — budget tracker, portfolio tracker, receipt scanner, report generator, freelance dashboard, subscription auditor, goal tracker. One-time purchase, runs 100% locally.

---

## Step 6: Publish

1. Review everything looks correct
2. Click **Publish** at the top
3. Share the product link!

---

## Quick Checklist

- [ ] Old product unpublished (not deleted)
- [ ] 6 screenshots taken from HTML files at 1280x720
- [ ] Thumbnail uploaded (gumroad_thumbnail.html screenshot)
- [ ] 5 gallery images uploaded in order
- [ ] Zip file uploaded (FinanceKit_v2.1.zip)
- [ ] Description pasted
- [ ] Price set to $29.99 (with $49.99 crossed out)
- [ ] Tags added
- [ ] Product published
