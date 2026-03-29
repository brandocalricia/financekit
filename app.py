import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="FinanceKit",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Navigation ---
NAV_OPTIONS = [
    "🏠 Dashboard",
    "🧾 Receipt Scanner",
    "📈 Portfolio Tracker",
    "📊 Report Generator",
    "💼 Freelance Dashboard",
    "🔄 Subscription Auditor",
    "💰 Budget Tracker",
    "🎯 Goal Tracker",
]

if "nav_target" in st.session_state and st.session_state.nav_target:
    target = st.session_state.nav_target
    st.session_state.nav_target = None
    if target in NAV_OPTIONS:
        st.session_state["sidebar_nav"] = target

if "nav_index" not in st.session_state:
    st.session_state.nav_index = 0

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #0f1117; min-width: 260px; }
    section[data-testid="stSidebar"] .stRadio label { font-size: 0.95rem; padding: 0.3rem 0; color: #c4b5fd !important; transition: color 0.15s; }
    section[data-testid="stSidebar"] .stRadio label:hover { color: #ffffff !important; }
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span { color: #e2e8f0 !important; }
    section[data-testid="stSidebar"] hr { border-color: #4a4a6c; }
    section[data-testid="stSidebar"] .stElementContainer small { color: #94a3b8 !important; }

    /* Logo — cross-browser gradient text */
    .fk-logo {
        font-size: 1.5rem; font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; color: transparent;
    }
    .fk-logo-line {
        height: 1px; margin: 0.4rem 0 0.3rem 0;
        background: linear-gradient(90deg, #6366f1, #a78bfa, transparent);
    }

    /* Dashboard widgets */
    .dash-widget {
        background: linear-gradient(135deg, #1e1e2f 0%, #2a2a40 100%);
        border: 1px solid #3a3a5c; border-radius: 14px; padding: 1.2rem 1.4rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        transition: all 0.2s ease;
    }
    .dash-widget:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(99,102,241,0.2); }
    .dash-widget .widget-title { font-size: 0.78rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.4rem; }
    .dash-widget .widget-value { font-size: 1.7rem; font-weight: 700; color: #e2e8f0; line-height: 1.1; }
    .dash-widget .widget-sub { font-size: 0.8rem; color: #8b9ab5; margin-top: 0.3rem; }

    /* Module cards */
    .module-card {
        background: linear-gradient(135deg, #1e1e2f 0%, #2a2a40 100%);
        border: 1px solid #3a3a5c; border-radius: 14px; padding: 1.5rem 1.3rem;
        text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        transition: all 0.2s ease; height: 100%;
    }
    .module-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(99,102,241,0.25); }
    .module-card .icon { font-size: 2.3rem; margin-bottom: 0.5rem; }
    .module-card h3 { margin: 0.3rem 0 0.4rem 0; color: #e2e8f0; font-size: 1rem; }
    .module-card p { color: #94a3b8; font-size: 0.83rem; line-height: 1.4; }
    .module-card .activity { font-size: 0.72rem; color: #6366f1; margin-top: 0.4rem; font-weight: 500; }

    /* Page header — cross-browser gradient text */
    .page-header-title {
        font-size: 2rem; font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; color: transparent;
        margin-bottom: 0.1rem;
    }
    .page-header-sub { color: #7c8ba0; font-size: 0.95rem; margin-bottom: 1rem; }

    /* Insight card */
    .insight-card {
        background: linear-gradient(135deg, #312e81 0%, #1e1b4b 100%);
        border: 1px solid #4338ca; border-radius: 12px; padding: 1rem 1.2rem;
        box-shadow: 0 2px 10px rgba(67,56,202,0.15);
    }
    .insight-card.tip { border-left: 3px solid #6366f1; }
    .insight-card.warning { border-left: 3px solid #f59e0b; }
    .insight-card.success { border-left: 3px solid #22c55e; }
    .insight-label { color: #a5b4fc; font-size: 0.78rem; margin-bottom: 0.2rem; }
    .insight-text { color: #e2e8f0; font-size: 0.95rem; font-weight: 500; }

    /* Progress bars */
    .prog-bar-bg { background: #1e1e2f; border-radius: 6px; height: 12px; overflow: hidden; margin: 4px 0; }
    .prog-bar-fill { height: 100%; border-radius: 6px; transition: width 0.5s ease; }

    /* Footer */
    .dash-footer { text-align: center; color: #4a4a6c; font-size: 0.78rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #1e1e2f; }

    /* Quick import banner */
    .quick-import-banner {
        background: linear-gradient(135deg, #1e1e2f, #2a2a40);
        border: 1px dashed #6366f1; border-radius: 10px; padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }

    /* Scrollable data tables on mobile */
    .stDataFrame, .stDataEditor { overflow-x: auto !important; }

    /* Responsive — tablet */
    @media (max-width: 992px) {
        .module-card { padding: 1.2rem 1rem; }
        .module-card h3 { font-size: 0.9rem; }
        .module-card p { font-size: 0.78rem; }
    }

    /* Responsive — mobile */
    @media (max-width: 768px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        .dash-widget { padding: 1rem; }
        .dash-widget .widget-value { font-size: 1.3rem; }
        .page-header-title { font-size: 1.5rem; }
        .module-card { padding: 1rem 0.8rem; }
    }
</style>
""", unsafe_allow_html=True)


# --- Data helpers ---
def _data_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load_json(filename, default=None):
    fp = os.path.join(_data_dir(), filename)
    if not os.path.exists(fp):
        return default
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _is_first_launch():
    data_dir = _data_dir()
    if not os.path.exists(data_dir):
        return True
    key_files = ["receipts.json", "portfolio.json", "transactions.json",
                 "statement_transactions.json", "budgets.json", "goals.json"]
    for fn in key_files:
        fp = os.path.join(data_dir, fn)
        if not os.path.exists(fp):
            continue
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = json.load(f)
            if isinstance(content, list) and len(content) > 0:
                return False
            if isinstance(content, dict):
                if content.get("holdings") and len(content["holdings"]) > 0:
                    return False
                if content.get("goals") and len(content["goals"]) > 0:
                    return False
                b = content.get("budgets", {})
                if isinstance(b, dict) and any(float(v) > 0 for v in b.values()):
                    return False
        except Exception:
            pass
    return True


def _generate_insight(budgets, goals, receipts, stmt_data):
    if goals:
        active = [g for g in goals if g.get("current", 0) < g.get("target", 1)]
        if active:
            closest = min(active, key=lambda g: g["target"] - g["current"])
            remaining = closest["target"] - closest["current"]
            return f"You're ${remaining:,.0f} away from your '{closest['name']}' goal. Keep going!"
    if budgets and any(float(v) > 0 for v in budgets.values()):
        top_cat = max(budgets, key=lambda k: float(budgets.get(k, 0)))
        return f"Your highest budget category is **{top_cat}** at ${float(budgets[top_cat]):,.0f}/mo. Import a bank statement to track spending against it."
    if receipts:
        return f"You've scanned **{len(receipts)}** receipt(s). Open the Receipt Scanner to export them all to Excel."
    if stmt_data:
        return f"You have **{len(stmt_data)}** statement transactions. Open Subscription Auditor to find recurring charges."
    return "Import a bank statement or add your first budget to see personalized insights here."


# --- Welcome dialog ---
@st.dialog("Welcome to FinanceKit! 👋", width="large")
def show_welcome_dialog():
    step = st.session_state.get("setup_step", 1)

    st.progress(step / 3, text=f"Step {step} of 3")

    if step == 1:
        st.markdown("### Step 1 — Import a Bank Statement")
        st.markdown(
            "Upload a CSV from your bank and we'll auto-detect the columns. "
            "Supports Chase, Bank of America, Wells Fargo, Capital One, Amex, and any CSV with date/description/amount."
        )
        uploaded = st.file_uploader("Upload CSV statement", type=["csv"], key="welcome_csv")
        if uploaded:
            st.success(f"'{uploaded.name}' ready to import.")
            st.session_state["welcome_csv_pending"] = True

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Skip", use_container_width=True):
                st.session_state.setup_step = 2
                st.rerun()
        with c2:
            if st.button("Next →", type="primary", use_container_width=True):
                st.session_state.setup_step = 2
                st.rerun()

    elif step == 2:
        st.markdown("### Step 2 — Pick a Budget Template")
        st.markdown("We'll set up your monthly budget based on your lifestyle. You can change every number later.")
        from modules.budget_tracker import BUDGET_TEMPLATES
        template = st.selectbox("Choose a template", ["— skip —"] + list(BUDGET_TEMPLATES.keys()))
        if template != "— skip —":
            tpl = BUDGET_TEMPLATES[template]
            st.caption(f"Total monthly: **${sum(tpl.values()):,.0f}**")
            preview_cols = st.columns(3)
            for i, (cat, amt) in enumerate(tpl.items()):
                with preview_cols[i % 3]:
                    st.markdown(
                        f"<div style='font-size:0.8rem;color:#94a3b8;'>{cat}</div>"
                        f"<div style='font-weight:600;color:#e2e8f0;'>${amt:,}</div>",
                        unsafe_allow_html=True,
                    )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back", use_container_width=True):
                st.session_state.setup_step = 1
                st.rerun()
        with c2:
            if st.button("Apply & Next →", type="primary", use_container_width=True):
                if template != "— skip —":
                    from utils.data_persistence import load_json, save_json
                    bd = load_json("budgets.json", default={"budgets": {}})
                    bd["budgets"] = BUDGET_TEMPLATES[template].copy()
                    save_json("budgets.json", bd)
                st.session_state.setup_step = 3
                st.rerun()

    elif step == 3:
        st.markdown("### Step 3 — Set Your First Savings Goal")
        st.markdown("A goal gives you a reason to open FinanceKit every day.")
        with st.form("welcome_goal"):
            g1, g2 = st.columns(2)
            with g1:
                gname = st.text_input("Goal name", placeholder="Emergency Fund, Vacation, Car...")
                gtarget = st.number_input("Target ($)", min_value=100.0, value=1000.0, step=100.0)
            with g2:
                gcurrent = st.number_input("Already saved ($)", min_value=0.0, value=0.0, step=50.0)
                gmonthly = st.number_input("Monthly contribution ($)", min_value=0.0, value=100.0, step=25.0)

            submitted = st.form_submit_button(
                "🚀 Save Goal & Launch Dashboard", type="primary", use_container_width=True
            )
            if submitted:
                if gname:
                    import uuid
                    from utils.data_persistence import load_json, save_json
                    from datetime import date as _date
                    goals_data = load_json("goals.json", default={"goals": []})
                    goals_data["goals"].append({
                        "id": str(uuid.uuid4())[:8],
                        "name": gname,
                        "target": float(gtarget),
                        "current": float(gcurrent),
                        "deadline": str(_date(_date.today().year + 1, _date.today().month, 1)),
                        "monthly": float(gmonthly),
                        "notes": "",
                        "created": str(_date.today()),
                        "history": [{"date": str(_date.today()), "amount": float(gcurrent)}],
                        "milestones_celebrated": [],
                    })
                    save_json("goals.json", goals_data)
                st.session_state.setup_complete = True
                st.session_state.setup_step = 1
                st.rerun()

        if st.button("Skip — take me to the dashboard", use_container_width=True):
            st.session_state.setup_complete = True
            st.session_state.setup_step = 1
            st.rerun()


# --- Sidebar ---
with st.sidebar:
    st.markdown('<div class="fk-logo">💰 FinanceKit</div>', unsafe_allow_html=True)
    st.markdown('<div class="fk-logo-line"></div>', unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.75rem;color:#4a4a6c;margin-bottom:0.5rem;'>v2.1 · Your money, your machine.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    page = st.radio(
        "Navigate",
        NAV_OPTIONS,
        index=st.session_state.nav_index,
        label_visibility="collapsed",
        key="sidebar_nav",
    )
    st.session_state.nav_index = NAV_OPTIONS.index(page)
    st.markdown("---")
    st.caption("All data stored locally. Zero cloud. Zero tracking.")


# --- Page routing ---
if page == "🏠 Dashboard":
    if _is_first_launch() and not st.session_state.get("setup_complete"):
        show_welcome_dialog()

    # Time-of-day greeting
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    # Check if user has set their name in Report Generator
    _rg_name = ""
    try:
        _rg_transactions = _load_json("transactions.json", default=[])
        if isinstance(_rg_transactions, list) and _rg_transactions:
            pass  # name not stored in transactions
    except Exception:
        pass

    st.markdown('<div class="page-header-title">FinanceKit</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="page-header-sub">{greeting}! 7 modules · zero subscriptions · runs 100% locally.</div>',
        unsafe_allow_html=True,
    )

    # Quick Import — prominent banner instead of expander
    st.markdown('<div class="quick-import-banner">', unsafe_allow_html=True)
    st.markdown("**⚡ Quick Import** — Drop a CSV here to send it to the Report Generator.")
    quick_file = st.file_uploader("Upload CSV", type=["csv"], key="dash_quick", label_visibility="collapsed")
    if quick_file and st.button("→ Open in Report Generator", type="primary"):
        import pandas as pd
        try:
            st.session_state["quick_import_df"] = pd.read_csv(quick_file)
            st.session_state["quick_import_name"] = quick_file.name
            st.toast("Ready! Navigate to Report Generator.", icon="📊")
        except Exception as e:
            st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Load data for widgets
    portfolio_data = _load_json("portfolio.json", default={"holdings": [], "alerts": []})
    budgets_data = _load_json("budgets.json", default={"budgets": {}})
    goals_data = _load_json("goals.json", default={"goals": []})
    receipts_data = _load_json("receipts.json", default=[])
    stmt_data = _load_json("statement_transactions.json", default=[])

    budgets = budgets_data.get("budgets", {})
    goals = goals_data.get("goals", [])
    holdings = portfolio_data.get("holdings", [])
    total_budget = sum(float(v) for v in budgets.values()) if budgets else 0

    # Widgets
    w1, w2, w3, w4 = st.columns(4)
    with w1:
        h_val = f"{len(holdings)} holding{'s' if len(holdings) != 1 else ''}" if holdings else "No holdings"
        h_sub = "Refresh prices in Portfolio Tracker" if holdings else "Add your first holding"
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">📈 Portfolio</div>'
            f'<div class="widget-value">{h_val}</div><div class="widget-sub">{h_sub}</div></div>',
            unsafe_allow_html=True,
        )
    with w2:
        b_val = f"${total_budget:,.0f}/mo" if total_budget > 0 else "Not set"
        b_sub = f"{len([k for k,v in budgets.items() if float(v)>0])} categories budgeted" if total_budget > 0 else "Set up in Budget Tracker"
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">💰 Monthly Budget</div>'
            f'<div class="widget-value">{b_val}</div><div class="widget-sub">{b_sub}</div></div>',
            unsafe_allow_html=True,
        )
    with w3:
        s_val = f"{len(stmt_data)} transactions" if stmt_data else "No data"
        s_sub = "Check Subscription Auditor for recurring charges" if stmt_data else "Import a statement"
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">🔄 Statements</div>'
            f'<div class="widget-value">{s_val}</div><div class="widget-sub">{s_sub}</div></div>',
            unsafe_allow_html=True,
        )
    with w4:
        g_saved = sum(g.get("current", 0) for g in goals)
        g_target = sum(g.get("target", 0) for g in goals)
        g_val = f"${g_saved:,.0f} / ${g_target:,.0f}" if goals else "No goals"
        g_sub = f"{len(goals)} active goal{'s' if len(goals)!=1 else ''}" if goals else "Add goals in Goal Tracker"
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">🎯 Savings Goals</div>'
            f'<div class="widget-value">{g_val}</div><div class="widget-sub">{g_sub}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Goals progress
        if goals:
            st.markdown("**🎯 Savings Goals**")
            for goal in goals[:3]:
                pct = min((goal["current"] / goal["target"] * 100) if goal["target"] > 0 else 0, 100)
                bar_color = "#22c55e" if pct >= 100 else "#6366f1" if pct >= 50 else "#a78bfa"
                gc1, gc2 = st.columns([5, 1])
                with gc1:
                    st.markdown(f"<small style='color:#94a3b8;'>{goal['name']}</small>", unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="prog-bar-bg"><div class="prog-bar-fill" style="background:{bar_color};width:{pct:.1f}%;"></div></div>',
                        unsafe_allow_html=True,
                    )
                with gc2:
                    st.markdown(
                        f'<div style="text-align:right;font-size:0.82rem;color:#94a3b8;padding-top:12px;">{pct:.0f}%</div>',
                        unsafe_allow_html=True,
                    )
            if len(goals) > 3:
                st.caption(f"+ {len(goals)-3} more — open Goal Tracker")
            if st.button("Open Goal Tracker →", key="d_goals"):
                st.session_state.nav_target = "🎯 Goal Tracker"
                st.rerun()
        else:
            st.markdown(
                '<div class="dash-widget"><div class="widget-title">🎯 Goals</div>'
                '<div style="color:#64748b;font-size:0.9rem;">No goals yet. Add your first in Goal Tracker.</div></div>',
                unsafe_allow_html=True,
            )

    with col_right:
        # Recent receipts
        st.markdown("**🧾 Recent Receipts**")
        if receipts_data:
            for r in (receipts_data[-5:])[::-1]:
                vendor = str(r.get("vendor", "Unknown"))[:35]
                total = r.get("total", "")
                total_str = f"${total}" if total and not str(total).startswith("$") else (total or "—")
                dt = r.get("date", "")
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:5px 0;'
                    f'border-bottom:1px solid #1e1e2f;font-size:0.88rem;">'
                    f'<span style="color:#c4b5fd;">{vendor}</span>'
                    f'<span style="color:#6366f1;font-weight:600;">{total_str}</span></div>',
                    unsafe_allow_html=True,
                )
            if st.button("View all receipts →", key="d_receipts"):
                st.session_state.nav_target = "🧾 Receipt Scanner"
                st.rerun()
        else:
            st.markdown(
                '<div style="color:#64748b;font-size:0.88rem;">No receipts yet. Upload one in Receipt Scanner.</div>',
                unsafe_allow_html=True,
            )

    # Insight
    st.markdown("<br>", unsafe_allow_html=True)
    insight = _generate_insight(budgets, goals, receipts_data, stmt_data)
    st.markdown(
        f'<div class="insight-card"><div class="insight-label">💡 QUICK INSIGHT</div>'
        f'<div class="insight-text">{insight}</div></div>',
        unsafe_allow_html=True,
    )

    # Module cards with activity indicators
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### All Modules")

    # Build activity strings from data
    freelance_data = _load_json("job_applications.json", default={"clients": [], "invoices": []})
    n_receipts = len(receipts_data) if receipts_data else 0
    n_holdings = len(holdings)
    n_goals = len(goals)
    n_clients = len(freelance_data.get("clients", [])) if isinstance(freelance_data, dict) else 0
    n_stmt = len(stmt_data) if stmt_data else 0

    modules = [
        ("🧾", "Receipt Scanner", "Scan PDFs & photos. Extract vendor, date, total.",
         "🧾 Receipt Scanner", f"{n_receipts} receipt{'s' if n_receipts != 1 else ''}" if n_receipts else ""),
        ("📈", "Portfolio Tracker", "Track stocks & crypto with live prices and alerts.",
         "📈 Portfolio Tracker", f"{n_holdings} holding{'s' if n_holdings != 1 else ''}" if n_holdings else ""),
        ("📊", "Report Generator", "Upload transactions, get a polished PDF report.",
         "📊 Report Generator", ""),
        ("💼", "Freelance Dashboard", "Track clients, log work, generate invoices.",
         "💼 Freelance Dashboard", f"{n_clients} client{'s' if n_clients != 1 else ''}" if n_clients else ""),
        ("🔄", "Subscription Auditor", "Find recurring charges and forgotten subscriptions.",
         "🔄 Subscription Auditor", f"{n_stmt} transactions" if n_stmt else ""),
        ("💰", "Budget Tracker", "Set monthly budgets and track spending by category.",
         "💰 Budget Tracker", f"${total_budget:,.0f}/mo" if total_budget > 0 else ""),
        ("🎯", "Goal Tracker", "Savings goals with projections and milestones.",
         "🎯 Goal Tracker", f"{n_goals} goal{'s' if n_goals != 1 else ''}" if n_goals else ""),
    ]

    # Row 1: 4 modules
    cols1 = st.columns(4)
    for i, (icon, title, desc, nav, activity) in enumerate(modules[:4]):
        with cols1[i]:
            activity_html = f'<div class="activity">{activity}</div>' if activity else ""
            st.markdown(
                f'<div class="module-card"><div class="icon">{icon}</div>'
                f'<h3>{title}</h3><p>{desc}</p>{activity_html}</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Open {title}", key=f"m_{i}", use_container_width=True):
                st.session_state.nav_target = nav
                st.rerun()

    st.markdown("")
    # Row 2: 3 modules
    cols2 = st.columns(4)
    for i, (icon, title, desc, nav, activity) in enumerate(modules[4:]):
        with cols2[i]:
            activity_html = f'<div class="activity">{activity}</div>' if activity else ""
            st.markdown(
                f'<div class="module-card"><div class="icon">{icon}</div>'
                f'<h3>{title}</h3><p>{desc}</p>{activity_html}</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Open {title}", key=f"m_{i+4}", use_container_width=True):
                st.session_state.nav_target = nav
                st.rerun()

    # Footer with last-modified time from data files
    _last_mod = 0
    for _fn in ["receipts.json", "portfolio.json", "budgets.json", "goals.json", "transactions.json"]:
        _fp = os.path.join(_data_dir(), _fn)
        if os.path.exists(_fp):
            _last_mod = max(_last_mod, os.path.getmtime(_fp))
    _last_str = datetime.fromtimestamp(_last_mod).strftime("%b %d, %Y %H:%M") if _last_mod > 0 else "No data yet"
    st.markdown(
        f'<div class="dash-footer">FinanceKit v2.1 &nbsp;·&nbsp; '
        f'Last updated: {_last_str}</div>',
        unsafe_allow_html=True,
    )

elif page == "🧾 Receipt Scanner":
    from modules.receipt_scanner import render
    render()

elif page == "📈 Portfolio Tracker":
    from modules.portfolio_tracker import render
    render()

elif page == "📊 Report Generator":
    from modules.report_generator import render
    render()

elif page == "💼 Freelance Dashboard":
    from modules.job_tracker import render
    render()

elif page == "🔄 Subscription Auditor":
    from modules.subscription_auditor import render
    render()

elif page == "💰 Budget Tracker":
    from modules.budget_tracker import render
    render()

elif page == "🎯 Goal Tracker":
    from modules.goal_tracker import render
    render()
