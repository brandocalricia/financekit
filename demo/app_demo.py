"""
FinanceKit — Free Demo Version (V2)
Deploy this to Streamlit Cloud as your public landing page.
Replace GUMROAD_URL below with your actual Gumroad product link.
"""
import streamlit as st

GUMROAD_URL = "https://5207453582610.gumroad.com/l/zbnsjc"
DEMO_URL = "https://financekit-demo-financekit.streamlit.app/"

st.set_page_config(
    page_title="FinanceKit \u2014 Personal Finance Toolkit",
    page_icon="\U0001f4b0",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 2rem; padding-bottom: 4rem; }

    section[data-testid="stSidebar"] { background-color: #0f1117; min-width: 260px; }
    section[data-testid="stSidebar"] .stRadio label { font-size: 1rem; padding: 0.35rem 0; color: #c4b5fd !important; }
    section[data-testid="stSidebar"] .stRadio label:hover { color: #ffffff !important; }
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span { color: #e2e8f0 !important; }
    section[data-testid="stSidebar"] hr { border-color: #3a3a5c; }
    section[data-testid="stSidebar"] .stElementContainer small { color: #94a3b8 !important; }

    .fk-logo {
        font-size: 1.5rem; font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .header-title {
        font-size: 2.8rem; font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .header-subtitle { color: #94a3b8; font-size: 1.15rem; margin-bottom: 1rem; }

    .dash-widget {
        background: linear-gradient(135deg, #1e1e2f 0%, #2a2a40 100%);
        border: 1px solid #3a3a5c; border-radius: 14px; padding: 1.2rem 1.4rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .dash-widget:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(99,102,241,0.2); }
    .dash-widget .widget-title { font-size: 0.78rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.4rem; }
    .dash-widget .widget-value { font-size: 1.7rem; font-weight: 700; color: #e2e8f0; line-height: 1.1; }
    .dash-widget .widget-sub { font-size: 0.8rem; color: #64748b; margin-top: 0.3rem; }

    .module-card {
        background: linear-gradient(135deg, #1e1e2f 0%, #2a2a40 100%);
        border: 1px solid #3a3a5c; border-radius: 14px;
        padding: 1.8rem 1.5rem; text-align: center;
        transition: transform 0.2s, box-shadow 0.2s; height: 100%;
    }
    .module-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(99,102,241,0.25); }
    .module-card .icon { font-size: 2.6rem; margin-bottom: 0.6rem; }
    .module-card h3 { margin: 0.4rem 0 0.6rem 0; color: #e2e8f0; font-size: 1.15rem; }
    .module-card p { color: #94a3b8; font-size: 0.88rem; line-height: 1.45; }

    .cta-box {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        border-radius: 14px; padding: 2rem; text-align: center; margin: 1.5rem 0;
    }
    .cta-box h2 { color: #fff; margin-bottom: 0.5rem; }
    .cta-box p { color: #e2e8f0; margin-bottom: 1rem; font-size: 1.05rem; }
    .cta-btn {
        display: inline-block; background: #fff; color: #4f46e5;
        font-weight: 700; font-size: 1.1rem; padding: 0.75rem 2rem;
        border-radius: 8px; text-decoration: none;
        transition: transform 0.15s;
    }
    .cta-btn:hover { transform: scale(1.05); color: #4f46e5; }

    .lock-overlay {
        background: rgba(15, 17, 23, 0.85); border: 1px solid #3a3a5c;
        border-radius: 12px; padding: 3rem 2rem; text-align: center; margin: 1rem 0;
    }
    .lock-overlay h3 { color: #c4b5fd; }
    .lock-overlay p { color: #94a3b8; }

    .price-tag {
        background: linear-gradient(135deg, #065f46, #047857);
        border-radius: 8px; padding: 0.4rem 1rem; display: inline-block;
        color: #ecfdf5; font-weight: 600; font-size: 0.85rem;
    }
    .price-old { text-decoration: line-through; color: #94a3b8; font-size: 0.85rem; }

    .floating-cta {
        position: fixed; bottom: 0; left: 0; right: 0; z-index: 999;
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        padding: 12px 20px; text-align: center;
        box-shadow: 0 -4px 20px rgba(99,102,241,0.4);
    }
    .floating-cta a {
        color: #fff; text-decoration: none; font-weight: 700; font-size: 1rem;
    }
    .floating-cta .price { color: #c4b5fd; font-size: 0.9rem; margin-left: 8px; }

    .prog-bar-bg { background: #1e1e2f; border-radius: 6px; height: 12px; overflow: hidden; margin: 4px 0; }
    .prog-bar-fill { height: 100%; border-radius: 6px; }

    .insight-card {
        background: linear-gradient(135deg, #312e81 0%, #1e1b4b 100%);
        border: 1px solid #4338ca; border-radius: 12px; padding: 1rem 1.2rem;
    }
    .insight-label { color: #a5b4fc; font-size: 0.78rem; margin-bottom: 0.2rem; }
    .insight-text { color: #e2e8f0; font-size: 0.95rem; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown('<div class="fk-logo">\U0001f4b0 FinanceKit</div>', unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.75rem;color:#3a3a5c;margin-bottom:0.5rem;'>v2.0 \u00b7 Your money, your machine.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    page = st.radio(
        "Navigate",
        [
            "\U0001f3e0 Dashboard",
            "\U0001f4b0 Budget Tracker",
            "\U0001f504 Subscription Auditor",
            "\U0001f9fe Receipt Scanner",
            "\U0001f4c8 Portfolio Tracker",
            "\U0001f4ca Report Generator",
            "\U0001f4bc Freelance Dashboard",
            "\U0001f3af Goal Tracker",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")

    # Sidebar CTA
    st.markdown(
        f"""<div style="text-align:center;margin-top:0.5rem;">
        <div class="price-old">$49.99</div>
        <a href="{GUMROAD_URL}" target="_blank" style="
        display:block;background:linear-gradient(135deg,#4f46e5,#7c3aed);
        color:#fff;text-align:center;padding:0.7rem 1rem;border-radius:8px;
        text-decoration:none;font-weight:600;font-size:0.95rem;margin-top:0.3rem;
        ">Launch Price: $29.99</a>
        <div style="color:#94a3b8;font-size:0.72rem;margin-top:4px;">One-time payment \u2022 No subscription</div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.caption("Free demo \u2022 FinanceKit v2.0")


def _cta_block():
    """Render the upgrade CTA banner."""
    st.markdown(
        f"""
        <div class="cta-box">
            <h2>\U0001f513 Unlock All 7 Modules</h2>
            <p><span class="price-old">$49.99</span> &rarr; <strong>$29.99</strong> launch price. One-time payment. No subscription. Runs 100% locally.</p>
            <a class="cta-btn" href="{GUMROAD_URL}" target="_blank">Get FinanceKit \u2014 $29.99</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _locked_module(title: str, features: list[str], preview_description: str = ""):
    """Show a locked module preview with feature list."""
    st.markdown(f"## {title}")
    if preview_description:
        st.markdown(preview_description)
    st.markdown("---")

    st.markdown(
        '<div class="lock-overlay">'
        '<h3>\U0001f512 Full Version Only</h3>'
        '<p>This module is available in the full version of FinanceKit.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("**What you get:**")
    for f in features:
        st.markdown(f"- {f}")
    _cta_block()


# --- Floating CTA ---
st.markdown(
    f"""<div class="floating-cta">
    <a href="{GUMROAD_URL}" target="_blank">
    \U0001f680 Get FinanceKit \u2014 <span class="price-old" style="text-decoration:line-through;color:#c4b5fd;">$49.99</span>
    $29.99 (Launch Price)
    </a>
    </div>""",
    unsafe_allow_html=True,
)


# --- Pages ---

if page == "\U0001f3e0 Dashboard":
    st.markdown('<div class="header-title">FinanceKit</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="header-subtitle">7 modules \u00b7 zero subscriptions \u00b7 runs 100% locally. '
        'Try the live demo below.</div>',
        unsafe_allow_html=True,
    )

    _cta_block()

    # Sample dashboard preview
    st.markdown("### Dashboard Preview")
    st.caption("This is what your dashboard looks like with real data loaded:")

    w1, w2, w3, w4 = st.columns(4)
    with w1:
        st.markdown(
            '<div class="dash-widget"><div class="widget-title">\U0001f4c8 Portfolio</div>'
            '<div class="widget-value">$24,830</div><div class="widget-sub">\u25b2 +2.4% today</div></div>',
            unsafe_allow_html=True,
        )
    with w2:
        st.markdown(
            '<div class="dash-widget"><div class="widget-title">\U0001f4b0 Monthly Budget</div>'
            '<div class="widget-value">$3,250/mo</div><div class="widget-sub">8 categories budgeted</div></div>',
            unsafe_allow_html=True,
        )
    with w3:
        st.markdown(
            '<div class="dash-widget"><div class="widget-title">\U0001f504 Subscriptions</div>'
            '<div class="widget-value">$127/mo</div><div class="widget-sub">9 recurring charges found</div></div>',
            unsafe_allow_html=True,
        )
    with w4:
        st.markdown(
            '<div class="dash-widget"><div class="widget-title">\U0001f3af Savings Goals</div>'
            '<div class="widget-value">$3,200 / $10,000</div><div class="widget-sub">3 active goals</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown("**\U0001f3af Sample Savings Goals**")
        sample_goals = [
            ("Emergency Fund", 3200, 5000, "#6366f1"),
            ("Vacation", 800, 2500, "#a78bfa"),
            ("New Laptop", 450, 1500, "#8b5cf6"),
        ]
        for name, current, target, color in sample_goals:
            pct = current / target * 100
            st.markdown(f"<small style='color:#94a3b8;'>{name}</small>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="prog-bar-bg"><div class="prog-bar-fill" style="background:{color};width:{pct:.0f}%;"></div></div>'
                f'<div style="font-size:0.8rem;color:#64748b;">${current:,} / ${target:,} ({pct:.0f}%)</div>',
                unsafe_allow_html=True,
            )

    with col_right:
        st.markdown("**\U0001f9fe Recent Receipts**")
        sample_receipts = [
            ("Whole Foods Market", "$87.43"),
            ("Shell Gas Station", "$52.10"),
            ("Amazon.com", "$34.99"),
            ("Starbucks", "$6.75"),
            ("CVS Pharmacy", "$23.40"),
        ]
        for vendor, amount in sample_receipts:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;'
                f'border-bottom:1px solid #1e1e2f;font-size:0.88rem;">'
                f'<span style="color:#c4b5fd;">{vendor}</span>'
                f'<span style="color:#6366f1;font-weight:600;">{amount}</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="insight-card"><div class="insight-label">\U0001f4a1 QUICK INSIGHT</div>'
        '<div class="insight-text">You\'re $1,800 away from your Emergency Fund goal. '
        'At $500/mo, you\'ll hit it by July 2026!</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Module cards
    st.markdown("### All 7 Modules")
    modules = [
        ("\U0001f9fe", "Receipt Scanner", "Scan PDFs & photos. Extract vendor, date, total with OCR."),
        ("\U0001f4c8", "Portfolio Tracker", "Track stocks & crypto with live prices, alerts, and allocation charts."),
        ("\U0001f4ca", "Report Generator", "Upload transactions, get a polished PDF report with charts."),
        ("\U0001f4bc", "Freelance Dashboard", "Track clients, generate invoices, monitor freelance income."),
        ("\U0001f504", "Subscription Auditor", "Find recurring charges, plan cancellations, project lifetime costs."),
        ("\U0001f4b0", "Budget Tracker", "Set monthly budgets by category and track spending."),
        ("\U0001f3af", "Goal Tracker", "Savings goals with projections, milestones, and progress charts."),
    ]

    cols1 = st.columns(4)
    for i, (icon, title, desc) in enumerate(modules[:4]):
        with cols1[i]:
            st.markdown(
                f'<div class="module-card"><div class="icon">{icon}</div>'
                f'<h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown("")
    cols2 = st.columns(4)
    for i, (icon, title, desc) in enumerate(modules[4:]):
        with cols2[i]:
            st.markdown(
                f'<div class="module-card"><div class="icon">{icon}</div>'
                f'<h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # How it works
    st.markdown("### How It Works")
    hc1, hc2, hc3 = st.columns(3)
    hc1.markdown("**1. Purchase & Download**\n\nOne-time $29.99 payment. No subscriptions. Download instantly.")
    hc2.markdown("**2. Double-Click to Launch**\n\nRun `start.bat` (Windows) or `start.sh` (Mac/Linux). Opens in your browser.")
    hc3.markdown("**3. Own Your Data**\n\nEverything runs locally. No cloud, no accounts, full privacy.")

    st.markdown("---")

    # Comparison table
    st.markdown("### What's Included")
    st.markdown("""
    | Feature | Free Demo | Full Version ($29.99) |
    |---------|:---------:|:---------------------:|
    | Browse all 7 modules | \u2705 | \u2705 |
    | Budget Tracker (limited) | \u2705 | \u2705 Unlimited |
    | Subscription Auditor (limited) | \u2705 | \u2705 Unlimited |
    | Receipt Scanner | \u274c | \u2705 |
    | Portfolio Tracker with alerts | \u274c | \u2705 |
    | PDF Report Generator | \u274c | \u2705 |
    | Freelance Dashboard + Invoices | \u274c | \u2705 |
    | Goal Tracker with milestones | \u274c | \u2705 |
    | Export to Excel / CSV / PDF | \u274c | \u2705 |
    | Lifetime updates | \u274c | \u2705 |
    """)

    _cta_block()


elif page == "\U0001f4b0 Budget Tracker":
    # Budget Tracker is the FREE demo module — hooks people on budgeting
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:0.5rem;">
        <span style="font-size:2rem;">\U0001f4b0</span>
        <div>
            <div style="font-size:1.6rem;font-weight:700;color:#e2e8f0;">Budget Tracker \u2014 Free Preview</div>
            <div style="color:#94a3b8;font-size:0.95rem;">Set monthly budgets and see where your money goes. <strong>Demo: limited to 3 categories.</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    DEMO_CATEGORIES = ["Food & Groceries", "Dining Out", "Entertainment"]

    with st.form("demo_budget"):
        st.markdown("### Set Your Budget (3 categories in demo)")
        bc1, bc2, bc3 = st.columns(3)
        budgets = {}
        with bc1:
            budgets["Food & Groceries"] = st.number_input("Food & Groceries", min_value=0.0, value=400.0, step=50.0)
        with bc2:
            budgets["Dining Out"] = st.number_input("Dining Out", min_value=0.0, value=200.0, step=50.0)
        with bc3:
            budgets["Entertainment"] = st.number_input("Entertainment", min_value=0.0, value=100.0, step=50.0)
        st.form_submit_button("Save Budget", type="primary")

    total_budget = sum(budgets.values())

    # Show sample spending data
    st.markdown("---")
    st.markdown("### Sample Spending vs Budget")
    sample_spending = {"Food & Groceries": 320, "Dining Out": 185, "Entertainment": 92}

    import plotly.graph_objects as go

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Total Budgeted", f"${total_budget:,.0f}")
    mc2.metric("Sample Spent", f"${sum(sample_spending.values()):,.0f}")
    mc3.metric("Remaining", f"${total_budget - sum(sample_spending.values()):,.0f}")

    for cat in DEMO_CATEGORIES:
        budget = budgets[cat]
        spent = sample_spending.get(cat, 0)
        pct = (spent / budget * 100) if budget > 0 else 0
        pct_capped = min(pct, 100)
        bar_color = "#22c55e" if pct < 50 else "#f59e0b" if pct < 80 else "#ef4444"
        status = "\U0001f7e2" if pct < 50 else "\U0001f7e1" if pct < 80 else "\U0001f534"

        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"**{status} {cat}**")
            st.markdown(
                f'<div style="background:#1e1e2f;border-radius:6px;height:16px;overflow:hidden;">'
                f'<div style="background:{bar_color};width:{pct_capped:.1f}%;height:100%;border-radius:6px;"></div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div style="text-align:right;font-size:0.85rem;color:#94a3b8;padding-top:6px;">'
                f'${spent:,.0f} / ${budget:,.0f}</div>',
                unsafe_allow_html=True,
            )

    # Donut chart
    fig = go.Figure(go.Pie(
        labels=["Spent", "Remaining"],
        values=[sum(sample_spending.values()), max(0, total_budget - sum(sample_spending.values()))],
        hole=0.65,
        marker_colors=["#6366f1", "#1e1e2f"],
        textinfo="percent",
    ))
    fig.update_layout(
        height=260, margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
        annotations=[{
            "text": f"${sum(sample_spending.values()):,.0f}<br><span style='font-size:11px'>spent</span>",
            "x": 0.5, "y": 0.5, "font_size": 18, "showarrow": False, "font_color": "#e2e8f0",
        }],
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown(
        '<div class="lock-overlay">'
        '<h3>\U0001f513 Want all 11 budget categories?</h3>'
        '<p>The full version includes CSV import, auto-categorization, month-over-month comparison, and all 11 budget categories.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    _cta_block()


elif page == "\U0001f504 Subscription Auditor":
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:0.5rem;">
        <span style="font-size:2rem;">\U0001f504</span>
        <div>
            <div style="font-size:1.6rem;font-weight:700;color:#e2e8f0;">Subscription Auditor \u2014 Free Preview</div>
            <div style="color:#94a3b8;font-size:0.95rem;">Upload a bank statement to find recurring charges. <strong>Demo: first 50 transactions.</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload a CSV statement", type=["csv"])

    if uploaded:
        import pandas as pd
        try:
            df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

        if len(df) > 50:
            st.warning(
                f"Your file has **{len(df):,}** transactions. "
                f"The free demo only processes the first 50. Get the full version for unlimited analysis."
            )
            df = df.head(50)

        st.success(f"Loaded **{len(df)}** transactions (demo limit: 50).")
        st.dataframe(df.head(20), use_container_width=True)
        _cta_block()
    else:
        st.info("Upload a CSV to try the demo.")

    st.markdown("---")
    st.markdown("**Full version includes:**")
    st.markdown("- Unlimited transactions\n- Known subscription database with direct cancellation links\n"
                "- Keep/Cancel toggle per subscription\n- Lifetime cost projections (1yr, 3yr, 5yr)\n"
                "- Annual renewal calendar visualization\n- Duplicate charge detection\n- CSV/Excel export")
    _cta_block()


elif page == "\U0001f9fe Receipt Scanner":
    _locked_module("\U0001f9fe Receipt & Invoice Scanner",
        [
            "Upload PDFs, JPG, or PNG receipt photos",
            "Camera input for mobile receipt scanning",
            "OCR-powered extraction: date, vendor, total, category",
            "Monthly spending summary chart",
            "Editable table with category correction",
            "Export to Excel (.xlsx) or CSV",
        ],
        "Snap a photo or upload a PDF \u2014 FinanceKit extracts the vendor, date, total, and auto-categorizes it.",
    )

elif page == "\U0001f4c8 Portfolio Tracker":
    _locked_module("\U0001f4c8 Stock & Crypto Portfolio Tracker",
        [
            "Track stocks (Yahoo Finance) and crypto (CoinGecko) with live prices",
            "Portfolio allocation pie charts (by holding and by type)",
            "Watchlist: monitor tickers without owning them",
            "Performance charts over 1mo / 3mo / 6mo / 1yr",
            "Top gainer and top loser at a glance",
            "Price alerts with optional email notifications",
        ],
        "Add your holdings and see real-time portfolio performance, allocation breakdowns, and price alerts.",
    )

elif page == "\U0001f4ca Report Generator":
    _locked_module("\U0001f4ca Financial Report Generator",
        [
            "Upload CSV/Excel transactions from any bank (auto-detects Chase, BofA, Wells Fargo, Capital One, Amex)",
            "Summary stats: income, expenses, net, top spending categories",
            "Charts: monthly spending, category breakdown, income vs expenses",
            "Net worth calculator (assets minus liabilities)",
            "Professional PDF report with title page, charts, and tables",
            "Email report directly via SMTP",
        ],
        "Upload your bank transactions and generate a polished financial report in seconds.",
    )

elif page == "\U0001f4bc Freelance Dashboard":
    _locked_module("\U0001f4bc Freelance Dashboard",
        [
            "Track clients, projects, rates, and job status",
            "Generate clean invoice PDFs with line items",
            "Payment tracking: mark invoices Paid/Unpaid, see outstanding balance",
            "Monthly freelance income bar chart",
            "Client profitability view: which clients have paid the most",
            "Export all invoices to CSV",
        ],
        "The complete freelance toolkit: client tracking, invoice generation, payment management, and income analytics.",
    )

elif page == "\U0001f3af Goal Tracker":
    _locked_module("\U0001f3af Savings Goal Tracker",
        [
            "Set multiple savings goals with deadlines and monthly contributions",
            "Visual progress bars with milestone celebrations (\U0001f388 at 25/50/75%, \u2744\ufe0f at 100%)",
            "Projected completion date calculator",
            "Savings progress history chart per goal",
            "On-track vs at-risk deadline warnings",
        ],
        "Set goals, track progress daily, and celebrate milestones. Your reason to open FinanceKit every day.",
    )
