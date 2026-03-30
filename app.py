import streamlit as st
import json
import os
from datetime import datetime
from utils.formatting import format_currency_int, get_currency_symbol

def _read_version():
    vpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.txt")
    try:
        with open(vpath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "3.3"

APP_VERSION = _read_version()

st.set_page_config(
    page_title="FinanceKit",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Theme ---
def _load_theme():
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "settings.json")
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f).get("theme", "dark")
    except Exception:
        return "dark"

if "fk_theme" not in st.session_state:
    st.session_state.fk_theme = _load_theme()

theme = st.session_state.fk_theme

# --- Navigation (filtered by enabled modules) ---
_ALL_NAV = [
    "🏠 Dashboard",
    "🧾 Receipt Scanner",
    "📈 Portfolio Tracker",
    "📊 Report Generator",
    "💼 Freelance Dashboard",
    "🔄 Subscription Auditor",
    "💰 Budget Tracker",
    "🎯 Goal Tracker",
    "⚙️ Settings",
]

_NAV_MODULE_MAP = {
    "🧾 Receipt Scanner": "receipts",
    "📈 Portfolio Tracker": "portfolio",
    "📊 Report Generator": "reports",
    "💼 Freelance Dashboard": "freelance",
    "🔄 Subscription Auditor": "subscriptions",
    "💰 Budget Tracker": "budget",
    "🎯 Goal Tracker": "goals",
}


def _build_nav_options() -> list[str]:
    """Build nav options filtered by enabled modules."""
    _settings_fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "settings.json")
    try:
        with open(_settings_fp, "r", encoding="utf-8") as f:
            _s = json.load(f)
        enabled = _s.get("enabled_modules", None)
    except Exception:
        enabled = None

    if enabled is None:
        return _ALL_NAV

    result = []
    for nav in _ALL_NAV:
        mod_key = _NAV_MODULE_MAP.get(nav)
        if mod_key is None or mod_key in enabled:
            result.append(nav)
    return result


NAV_OPTIONS = _build_nav_options()

if "nav_target" in st.session_state and st.session_state.nav_target:
    target = st.session_state.nav_target
    st.session_state.nav_target = None
    if target in NAV_OPTIONS:
        st.session_state["sidebar_nav"] = target

if "nav_index" not in st.session_state:
    st.session_state.nav_index = 0

# --- CSS with theme variables ---
_dark_vars = """
    --fk-bg: #0f1117;
    --fk-card: #1e1e2f;
    --fk-card-alt: #2a2a40;
    --fk-card-hover: #252540;
    --fk-text: #e2e8f0;
    --fk-text-muted: #94a3b8;
    --fk-text-dim: #64748b;
    --fk-border: #2a2a40;
    --fk-border-light: #3a3a5c;
    --fk-accent: #6366f1;
    --fk-accent-light: #a78bfa;
    --fk-accent-text: #c4b5fd;
    --fk-success: #22c55e;
    --fk-warning: #f59e0b;
    --fk-danger: #ef4444;
    --fk-input-bg: #1e1e2f;
    --fk-sidebar-bg: #0f1117;
    --fk-sidebar-hr: #4a4a6c;
    --fk-footer-text: #4a4a6c;
    --fk-chart-grid: #2a2a40;
    --fk-progress-bg: #1e1e2f;
    --fk-insight-bg1: #312e81;
    --fk-insight-bg2: #1e1b4b;
    --fk-insight-border: #4338ca;
    --fk-insight-label: #a5b4fc;
    --fk-savings-bg1: #065f46;
    --fk-savings-bg2: #047857;
    --fk-savings-label: #86efac;
    --fk-savings-text: #ecfdf5;
"""

_light_vars = """
    --fk-bg: #f8fafc;
    --fk-card: #ffffff;
    --fk-card-alt: #f1f5f9;
    --fk-card-hover: #f1f5f9;
    --fk-text: #1e293b;
    --fk-text-muted: #64748b;
    --fk-text-dim: #94a3b8;
    --fk-border: #e2e8f0;
    --fk-border-light: #cbd5e1;
    --fk-accent: #6366f1;
    --fk-accent-light: #818cf8;
    --fk-accent-text: #4f46e5;
    --fk-success: #16a34a;
    --fk-warning: #d97706;
    --fk-danger: #dc2626;
    --fk-input-bg: #f8fafc;
    --fk-sidebar-bg: #f1f5f9;
    --fk-sidebar-hr: #cbd5e1;
    --fk-footer-text: #94a3b8;
    --fk-chart-grid: #e2e8f0;
    --fk-progress-bg: #e2e8f0;
    --fk-insight-bg1: #eef2ff;
    --fk-insight-bg2: #e0e7ff;
    --fk-insight-border: #818cf8;
    --fk-insight-label: #4f46e5;
    --fk-savings-bg1: #d1fae5;
    --fk-savings-bg2: #a7f3d0;
    --fk-savings-label: #065f46;
    --fk-savings-text: #064e3b;
"""

_theme_vars = _dark_vars if theme == "dark" else _light_vars

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {{
        {_theme_vars}
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        transition: background-color 0.3s ease, color 0.3s ease;
    }}
    .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{ background-color: var(--fk-sidebar-bg); min-width: 260px; }}
    section[data-testid="stSidebar"] .stRadio label {{
        font-size: 0.95rem; padding: 0.3rem 0;
        color: var(--fk-accent-text) !important; transition: color 0.15s;
    }}
    section[data-testid="stSidebar"] .stRadio label:hover {{ color: var(--fk-text) !important; }}
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span {{ color: var(--fk-text) !important; }}
    section[data-testid="stSidebar"] hr {{ border-color: var(--fk-sidebar-hr); }}
    section[data-testid="stSidebar"] .stElementContainer small {{ color: var(--fk-text-muted) !important; }}

    /* Logo — cross-browser gradient text */
    .fk-logo {{
        font-size: 1.5rem; font-weight: 700;
        background: linear-gradient(90deg, var(--fk-accent), var(--fk-accent-light));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; color: transparent;
    }}
    .fk-logo-line {{
        height: 1px; margin: 0.4rem 0 0.3rem 0;
        background: linear-gradient(90deg, var(--fk-accent), var(--fk-accent-light), transparent);
    }}

    /* Nav group headers */
    .nav-group {{
        font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 1.2px; color: var(--fk-text-muted); margin: 0.6rem 0 0.2rem 0;
    }}

    /* Dashboard widgets */
    .dash-widget {{
        background: linear-gradient(135deg, var(--fk-card) 0%, var(--fk-card-alt) 100%);
        border: 1px solid var(--fk-border-light); border-radius: 14px; padding: 1.2rem 1.4rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
    }}
    .dash-widget:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(99,102,241,0.15); }}
    .dash-widget .widget-title {{ font-size: 0.78rem; color: var(--fk-text-muted); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.4rem; }}
    .dash-widget .widget-value {{ font-size: 1.7rem; font-weight: 700; color: var(--fk-text); line-height: 1.1; }}
    .dash-widget .widget-sub {{ font-size: 0.8rem; color: var(--fk-text-dim); margin-top: 0.3rem; }}

    /* Module cards */
    .module-card {{
        background: linear-gradient(135deg, var(--fk-card) 0%, var(--fk-card-alt) 100%);
        border: 1px solid var(--fk-border-light); border-radius: 14px; padding: 1.5rem 1.3rem;
        text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.2s ease; height: 100%;
    }}
    .module-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba(99,102,241,0.2); }}
    .module-card .icon {{ font-size: 2.3rem; margin-bottom: 0.5rem; }}
    .module-card h3 {{ margin: 0.3rem 0 0.4rem 0; color: var(--fk-text); font-size: 1rem; }}
    .module-card p {{ color: var(--fk-text-muted); font-size: 0.83rem; line-height: 1.4; }}
    .module-card .activity {{ font-size: 0.72rem; color: var(--fk-accent); margin-top: 0.4rem; font-weight: 500; }}

    /* Page header — cross-browser gradient text */
    .page-header-title {{
        font-size: 2rem; font-weight: 700;
        background: linear-gradient(90deg, var(--fk-accent), var(--fk-accent-light));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; color: transparent;
        margin-bottom: 0.1rem;
    }}
    .page-header-sub {{ color: var(--fk-text-dim); font-size: 0.95rem; margin-bottom: 1rem; }}

    /* Module header (ui_helpers) */
    .fk-module-title {{ font-size: 1.6rem; font-weight: 700; color: var(--fk-text); }}
    .fk-module-desc {{ color: var(--fk-text-muted); font-size: 0.95rem; }}
    .fk-module-line {{ height: 2px; background: linear-gradient(90deg, var(--fk-accent), transparent); margin-bottom: 1rem; }}

    /* Insight card */
    .insight-card {{
        background: linear-gradient(135deg, var(--fk-insight-bg1) 0%, var(--fk-insight-bg2) 100%);
        border: 1px solid var(--fk-insight-border); border-radius: 12px; padding: 1rem 1.2rem;
        box-shadow: 0 2px 10px rgba(67,56,202,0.1);
    }}
    .insight-card.tip {{ border-left: 3px solid var(--fk-accent); }}
    .insight-card.warning {{ border-left: 3px solid var(--fk-warning); }}
    .insight-card.success {{ border-left: 3px solid var(--fk-success); }}
    .insight-label {{ color: var(--fk-insight-label); font-size: 0.78rem; margin-bottom: 0.2rem; }}
    .insight-text {{ color: var(--fk-text); font-size: 0.95rem; font-weight: 500; }}

    /* Progress bars */
    .prog-bar-bg {{ background: var(--fk-progress-bg); border-radius: 6px; height: 12px; overflow: hidden; margin: 4px 0; }}
    .prog-bar-fill {{ height: 100%; border-radius: 6px; transition: width 0.5s ease; }}

    /* Footer */
    .dash-footer {{ text-align: center; color: var(--fk-footer-text); font-size: 0.78rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--fk-card); }}

    /* Quick import banner */
    .quick-import-banner {{
        background: linear-gradient(135deg, var(--fk-card), var(--fk-card-alt));
        border: 1px dashed var(--fk-accent); border-radius: 10px; padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }}

    /* Savings banner (subscription auditor) */
    .fk-savings-banner {{
        background: linear-gradient(135deg, var(--fk-savings-bg1), var(--fk-savings-bg2));
        border-radius: 10px; padding: 0.8rem 1.2rem; margin-bottom: 1rem;
        display: flex; justify-content: space-around; text-align: center;
    }}
    .fk-savings-banner .label {{ color: var(--fk-savings-label); font-size: 0.75rem; text-transform: uppercase; }}
    .fk-savings-banner .value {{ color: var(--fk-savings-text); font-size: 1.3rem; font-weight: 700; }}

    /* Empty state */
    .fk-empty {{
        text-align: center; padding: 2.5rem 1rem; color: var(--fk-text-muted);
        border: 1px dashed var(--fk-border); border-radius: 12px; margin: 1rem 0;
    }}
    .fk-empty .icon {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
    .fk-empty .title {{ font-size: 1.1rem; font-weight: 600; color: var(--fk-text); margin-bottom: 0.3rem; }}

    /* Search results */
    .fk-search-result {{
        padding: 0.5rem 0.8rem; border-bottom: 1px solid var(--fk-border);
        display: flex; align-items: center; gap: 0.6rem; cursor: pointer;
    }}
    .fk-search-result:hover {{ background: var(--fk-card-hover); }}
    .fk-search-result .sr-title {{ color: var(--fk-text); font-weight: 500; font-size: 0.9rem; }}
    .fk-search-result .sr-detail {{ color: var(--fk-text-muted); font-size: 0.8rem; }}
    .fk-search-result .sr-module {{ color: var(--fk-accent); font-size: 0.72rem; font-weight: 600; text-transform: uppercase; }}

    /* Keyboard shortcuts modal */
    .fk-kbd {{ display: inline-block; background: var(--fk-card-alt); border: 1px solid var(--fk-border-light); border-radius: 4px; padding: 2px 7px; font-family: monospace; font-size: 0.82rem; color: var(--fk-text); }}

    /* Notification bell */
    .fk-notif-bell {{
        position: relative; display: inline-flex; align-items: center; gap: 4px;
        font-size: 1.1rem; cursor: pointer; padding: 4px 8px; border-radius: 8px;
        color: var(--fk-text); transition: background 0.15s;
    }}
    .fk-notif-bell:hover {{ background: var(--fk-card-hover); }}
    .fk-notif-badge {{
        position: absolute; top: -2px; right: -4px;
        background: var(--fk-danger); color: white; font-size: 0.65rem; font-weight: 700;
        min-width: 16px; height: 16px; border-radius: 8px; display: flex;
        align-items: center; justify-content: center; padding: 0 4px;
    }}

    /* Notification panel items */
    .fk-notif-item {{
        display: flex; align-items: flex-start; gap: 8px;
        padding: 8px 10px; border-bottom: 1px solid var(--fk-border);
        border-radius: 6px; margin-bottom: 2px; transition: background 0.15s;
    }}
    .fk-notif-item:hover {{ background: var(--fk-card-hover); }}
    .fk-notif-item.unread {{ background: var(--fk-card-alt); }}
    .fk-notif-icon {{ font-size: 1rem; flex-shrink: 0; margin-top: 2px; }}
    .fk-notif-content {{ flex: 1; min-width: 0; }}
    .fk-notif-title {{ color: var(--fk-text); font-weight: 600; font-size: 0.85rem; }}
    .fk-notif-msg {{ color: var(--fk-text-muted); font-size: 0.78rem; margin-top: 1px; }}
    .fk-notif-meta {{ color: var(--fk-text-dim); font-size: 0.7rem; margin-top: 2px; }}
    .fk-notif-group {{ color: var(--fk-text-muted); font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; margin: 8px 0 4px 0; }}

    /* Dashboard alert cards */
    .fk-alert-card {{
        display: flex; align-items: flex-start; gap: 10px;
        padding: 10px 14px; border-radius: 10px; margin-bottom: 6px;
        background: var(--fk-card); border: 1px solid var(--fk-border);
    }}
    .fk-alert-card.border-info {{ border-left: 3px solid #3b82f6; }}
    .fk-alert-card.border-warning {{ border-left: 3px solid #f59e0b; }}
    .fk-alert-card.border-success {{ border-left: 3px solid #22c55e; }}
    .fk-alert-card.border-alert {{ border-left: 3px solid #ef4444; }}

    /* Scrollable data tables on mobile */
    .stDataFrame, .stDataEditor {{ overflow-x: auto !important; }}

    /* Responsive — tablet */
    @media (max-width: 992px) {{
        .module-card {{ padding: 1.2rem 1rem; }}
        .module-card h3 {{ font-size: 0.9rem; }}
        .module-card p {{ font-size: 0.78rem; }}
    }}

    /* Responsive — mobile */
    @media (max-width: 768px) {{
        .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
        .dash-widget {{ padding: 1rem; }}
        .dash-widget .widget-value {{ font-size: 1.3rem; }}
        .page-header-title {{ font-size: 1.5rem; }}
        .module-card {{ padding: 1rem 0.8rem; }}
        .fk-module-title {{ font-size: 1.3rem; }}
    }}

    /* Responsive — collapse 4-col metric rows on mobile */
    @media (max-width: 768px) {{
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
            min-width: 48% !important;
            flex: 0 0 48% !important;
            margin-bottom: 0.5rem;
        }}
    }}

    /* Phone — single col */
    @media (max-width: 480px) {{
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
            min-width: 100% !important;
            flex: 0 0 100% !important;
        }}
    }}

    /* Print styles — hide chrome, format content */
    @media print {{
        section[data-testid="stSidebar"] {{ display: none !important; }}
        button, .stButton, .stFileUploader, .stTextInput, .stSelectbox {{ display: none !important; }}
        .block-container {{ padding: 0 !important; max-width: 100% !important; }}
        .dash-widget, .module-card, .insight-card {{ break-inside: avoid; }}
        .fk-notif-bell, .fk-kbd, .nav-group {{ display: none !important; }}
        body, html {{ color: #000 !important; background: #fff !important; }}
        .dash-widget {{ border: 1px solid #ccc; box-shadow: none; }}
        .dash-widget .widget-value {{ color: #000 !important; }}
        .dash-widget .widget-title {{ color: #555 !important; }}
        h1, h2, h3, h4 {{ color: #000 !important; page-break-after: avoid; }}
    }}
</style>
""", unsafe_allow_html=True)

# --- Keyboard shortcuts via JS ---
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    // Don't trigger if typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;

    var key = e.key;
    var shortcuts = {
        '0': '🏠 Dashboard',
        '1': '🧾 Receipt Scanner',
        '2': '📈 Portfolio Tracker',
        '3': '📊 Report Generator',
        '4': '💼 Freelance Dashboard',
        '5': '🔄 Subscription Auditor',
        '6': '💰 Budget Tracker',
        '7': '🎯 Goal Tracker',
        '9': '⚙️ Settings',
    };

    if (key === '?') {
        e.preventDefault();
        var el = document.getElementById('fk-shortcuts-toggle');
        if (el) el.click();
        return;
    }

    if (shortcuts[key]) {
        e.preventDefault();
        // Set query param to trigger navigation
        var url = new URL(window.location);
        url.searchParams.set('nav', shortcuts[key]);
        window.location.href = url.toString();
    }
});
</script>
""", unsafe_allow_html=True)

# --- Splash / loading screen (first render only) ---
if "splash_shown" not in st.session_state:
    _splash = st.empty()
    _splash.markdown(
        '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;'
        'min-height:60vh;text-align:center;">'
        '<div style="font-size:3.5rem;animation:fk-pulse 1.5s ease-in-out infinite;">💰</div>'
        '<div class="fk-logo" style="font-size:1.8rem;margin-top:0.8rem;">FinanceKit</div>'
        '<div style="color:var(--fk-text-muted);font-size:0.95rem;margin-top:0.5rem;">'
        'Loading your financial toolkit...</div>'
        '</div>'
        '<style>@keyframes fk-pulse{0%,100%{opacity:1;transform:scale(1)}'
        '50%{opacity:0.7;transform:scale(1.08)}}</style>',
        unsafe_allow_html=True,
    )
    import time as _splash_time
    _splash_time.sleep(1.2)
    _splash.empty()
    st.session_state.splash_shown = True

# Handle keyboard nav via query params
_qp = st.query_params
if "nav" in _qp:
    nav_target = _qp["nav"]
    if nav_target in NAV_OPTIONS:
        st.session_state["sidebar_nav"] = nav_target
        st.session_state.nav_index = NAV_OPTIONS.index(nav_target)
    st.query_params.clear()


# --- Authentication Gate ---
from utils.auth import is_auth_required, login_user, register_user, password_strength, is_session_valid, generate_reset_token, reset_password_with_token
from utils.data_persistence import set_user_context, clear_user_context


def _show_login_page():
    """Render the full-screen login page."""
    view = st.session_state.get("auth_view", "login")

    st.markdown(
        '<div style="max-width:420px;margin:2rem auto;">'
        '<div class="fk-logo" style="text-align:center;font-size:2rem;margin-bottom:0.3rem;">💰 FinanceKit</div>'
        '<div class="fk-logo-line" style="margin-bottom:1.5rem;"></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if view == "login":
            st.markdown("### Welcome back")
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                remember = st.checkbox("Remember me (30 days)")
                if st.form_submit_button("Sign In", type="primary", use_container_width=True):
                    success, result = login_user(email, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_id = result["id"]
                        st.session_state.user_name = result.get("name", "")
                        st.session_state.user_email = result["email"]
                        st.session_state.auth_method = result.get("auth_method", "local")
                        st.session_state.login_time = datetime.now().isoformat()
                        st.session_state.remember_me = remember
                        set_user_context(result["id"])
                        st.rerun()
                    else:
                        st.error(result)

            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("Create an account", use_container_width=True):
                    st.session_state.auth_view = "register"
                    st.rerun()
            with bc2:
                if st.button("Forgot password?", use_container_width=True):
                    st.session_state.auth_view = "reset"
                    st.rerun()

        elif view == "register":
            st.markdown("### Create Account")
            with st.form("register_form"):
                name = st.text_input("Display Name", placeholder="Your name")
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("New Password", type="password")
                if password:
                    strength = password_strength(password)
                    color = {"weak": "🔴", "medium": "🟡", "strong": "🟢"}[strength]
                    st.caption(f"Password strength: {color} {strength}")
                confirm = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                    if password != confirm:
                        st.error("Passwords don't match.")
                    else:
                        success, msg = register_user(email, password, name)
                        if success:
                            st.toast(msg, icon="✅")
                            st.session_state.auth_view = "login"
                            st.rerun()
                        else:
                            st.error(msg)

            if st.button("← Back to Sign In", use_container_width=True):
                st.session_state.auth_view = "login"
                st.rerun()

        elif view == "reset":
            st.markdown("### Reset Password")
            reset_step = st.session_state.get("reset_step", 1)

            if reset_step == 1:
                with st.form("reset_email_form"):
                    email = st.text_input("Email", placeholder="you@example.com")
                    if st.form_submit_button("Send Reset Token", type="primary", use_container_width=True):
                        success, result = generate_reset_token(email)
                        if success:
                            st.session_state.reset_email = email
                            st.session_state.reset_token_display = result
                            st.session_state.reset_step = 2
                            st.rerun()
                        else:
                            st.error(result)
            else:
                st.info(f"Reset token for **{st.session_state.get('reset_email', '')}**:")
                st.code(st.session_state.get("reset_token_display", ""), language=None)
                st.caption("Copy this token and paste it below. It expires in 1 hour.")
                with st.form("reset_password_form"):
                    token = st.text_input("Reset Token")
                    new_pass = st.text_input("New Password", type="password")
                    confirm_pass = st.text_input("Confirm Password", type="password")
                    if st.form_submit_button("Reset Password", type="primary", use_container_width=True):
                        if new_pass != confirm_pass:
                            st.error("Passwords don't match.")
                        else:
                            success, msg = reset_password_with_token(
                                st.session_state.get("reset_email", ""), token, new_pass
                            )
                            if success:
                                st.toast(msg, icon="✅")
                                st.session_state.reset_step = 1
                                st.session_state.auth_view = "login"
                                st.rerun()
                            else:
                                st.error(msg)

            if st.button("← Back to Sign In", use_container_width=True, key="back_reset"):
                st.session_state.auth_view = "login"
                st.session_state.reset_step = 1
                st.rerun()

    st.stop()


def _sign_out():
    """Sign out the current user."""
    clear_user_context()
    for key in ["authenticated", "user_id", "user_name", "user_email",
                "auth_method", "login_time", "remember_me"]:
        st.session_state.pop(key, None)
    # Clear module caches
    for key in list(st.session_state.keys()):
        if key not in ("fk_theme", "sidebar_nav", "nav_index"):
            st.session_state.pop(key, None)
    st.rerun()


# Auth gate: if auth is required and user is not authenticated, show login
if is_auth_required():
    if st.session_state.get("authenticated"):
        # Check session expiry
        login_time = st.session_state.get("login_time", "")
        remember = st.session_state.get("remember_me", False)
        if not is_session_valid(login_time, remember):
            st.toast("Session expired. Please sign in again.", icon="⏰")
            _sign_out()
        else:
            # Set user context for data isolation
            user_id = st.session_state.get("user_id", "")
            if user_id:
                set_user_context(user_id)
    else:
        _show_login_page()


# --- Notification startup tasks ---
from utils.notifications import clear_old as _notif_clean_old, check_and_send_digest as _notif_check_digest

if "notif_startup_done" not in st.session_state:
    _notif_clean_old(30)
    _startup_settings = load_json("settings.json", default={}) if "load_json" in dir() else {}
    try:
        from utils.data_persistence import load_json as _dp_load
        _startup_settings = _dp_load("settings.json", default={})
        _notif_check_digest(_startup_settings)
    except Exception:
        pass
    # Bill reminders
    try:
        from modules.budget_tracker import get_upcoming_bills, get_overdue_bills
        from utils.notifications import create_notification
        for _ob in get_overdue_bills():
            create_notification(
                "alert", "budget_tracker",
                f"Overdue: {_ob['name']}",
                f"{_ob['name']} ({format_currency_int(_ob['amount'])}) was due on day {_ob['due_day']}.",
            )
        for _ub in get_upcoming_bills(3):
            if not _ub.get("_overdue"):
                days = _ub.get("_days_away", 0)
                create_notification(
                    "info", "budget_tracker",
                    f"Bill Due: {_ub['name']}",
                    f"{_ub['name']} ({format_currency_int(_ub['amount'])}) is due in {days} day{'s' if days != 1 else ''}.",
                )
    except Exception:
        pass

    st.session_state.notif_startup_done = True

# --- Migrations & logging startup ---
if "migrations_done" not in st.session_state:
    try:
        from utils.logger import get_logger as _get_logger
        _app_log = _get_logger("app")
        _app_log.info(f"FinanceKit v{APP_VERSION} started")
    except Exception:
        pass
    try:
        from utils.migrations import run_migrations as _run_mig
        _applied = _run_mig()
    except Exception:
        pass
    st.session_state.migrations_done = True


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


ALL_MODULES = [
    {"key": "budget", "icon": "💰", "name": "Budget Tracker", "nav": "💰 Budget Tracker",
     "desc": "Set monthly budgets by category and track spending."},
    {"key": "goals", "icon": "🎯", "name": "Goal Tracker", "nav": "🎯 Goal Tracker",
     "desc": "Savings goals with projections, milestones, and progress charts."},
    {"key": "receipts", "icon": "🧾", "name": "Receipt Scanner", "nav": "🧾 Receipt Scanner",
     "desc": "Scan PDFs & photos. Extract vendor, date, total with OCR."},
    {"key": "portfolio", "icon": "📈", "name": "Portfolio Tracker", "nav": "📈 Portfolio Tracker",
     "desc": "Track stocks & crypto with live prices, alerts, and allocation charts."},
    {"key": "reports", "icon": "📊", "name": "Report Generator", "nav": "📊 Report Generator",
     "desc": "Upload transactions, get a polished PDF report with charts."},
    {"key": "freelance", "icon": "💼", "name": "Freelance Dashboard", "nav": "💼 Freelance Dashboard",
     "desc": "Track clients, log work, generate invoices."},
    {"key": "subscriptions", "icon": "🔄", "name": "Subscription Auditor", "nav": "🔄 Subscription Auditor",
     "desc": "Find recurring charges and forgotten subscriptions."},
]

ALL_MODULE_KEYS = [m["key"] for m in ALL_MODULES]


def _get_enabled_modules() -> list[str]:
    """Return list of enabled module keys from settings."""
    s = _load_json("settings.json", default={})
    return s.get("enabled_modules", ALL_MODULE_KEYS.copy())


def _is_module_enabled(key: str) -> bool:
    return key in _get_enabled_modules()


def _is_first_launch():
    s = _load_json("settings.json", default={})
    if s.get("onboarding_complete"):
        return False
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
    sym = get_currency_symbol()
    if goals:
        active = [g for g in goals if g.get("current", 0) < g.get("target", 1)]
        if active:
            closest = min(active, key=lambda g: g["target"] - g["current"])
            remaining = closest["target"] - closest["current"]
            return f"You're {format_currency_int(remaining)} away from your '{closest['name']}' goal. Keep going!"
    if budgets and any(float(v) > 0 for v in budgets.values()):
        top_cat = max(budgets, key=lambda k: float(budgets.get(k, 0)))
        return f"Your highest budget category is **{top_cat}** at {format_currency_int(float(budgets[top_cat]))}/mo. Import a bank statement to track spending against it."
    if receipts:
        return f"You've scanned **{len(receipts)}** receipt(s). Open the Receipt Scanner to export them all to Excel."
    if stmt_data:
        return f"You have **{len(stmt_data)}** statement transactions. Open Subscription Auditor to find recurring charges."
    return "Import a bank statement or add your first budget to see personalized insights here."


# --- Welcome dialog (5-step onboarding) ---
@st.dialog("Welcome to FinanceKit! 👋", width="large")
def show_welcome_dialog():
    step = st.session_state.get("setup_step", 1)

    st.progress(step / 5, text=f"Step {step} of 5")

    def _finish_onboarding():
        from utils.data_persistence import load_json as _dl, save_json as _ds
        s = _dl("settings.json", default={})
        s["onboarding_complete"] = True
        s["onboarding_completed_at"] = datetime.now().isoformat()
        if "ob_enabled_modules" in st.session_state:
            s["enabled_modules"] = st.session_state.ob_enabled_modules
        _ds("settings.json", s)
        st.session_state.setup_complete = True
        st.session_state.setup_step = 1
        st.rerun()

    if step == 1:
        # Welcome
        st.markdown(
            '<div style="text-align:center;padding:1rem 0;">'
            '<div style="font-size:3rem;">💰</div>'
            '<div style="font-size:1.6rem;font-weight:700;color:var(--fk-text);margin:0.5rem 0;">'
            "Let's set up your financial toolkit</div>"
            '<div style="color:var(--fk-text-muted);font-size:1rem;">'
            "7 modules, zero subscriptions, 100% local. This quick setup takes under a minute.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("")
        if st.button("Get Started →", type="primary", use_container_width=True):
            st.session_state.setup_step = 2
            st.rerun()
        if st.button("Skip setup", use_container_width=True):
            _finish_onboarding()

    elif step == 2:
        # Profile
        st.markdown("### Step 2 — Your Profile")
        from modules.settings import CURRENCY_OPTIONS, DATE_FORMAT_OPTIONS
        pc1, pc2 = st.columns(2)
        with pc1:
            ob_name = st.text_input("Your Name", placeholder="e.g. Alex", key="ob_name")
            currency_choice = st.selectbox("Currency", list(CURRENCY_OPTIONS.keys()), key="ob_currency")
        with pc2:
            ob_email = st.text_input("Email (optional)", placeholder="you@example.com", key="ob_email")
            date_fmt = st.selectbox("Date Format", DATE_FORMAT_OPTIONS, key="ob_date_fmt")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back", use_container_width=True, key="ob2_back"):
                st.session_state.setup_step = 1
                st.rerun()
        with c2:
            if st.button("Next →", type="primary", use_container_width=True, key="ob2_next"):
                from utils.data_persistence import load_json as _dl, save_json as _ds
                s = _dl("settings.json", default={})
                s["user_name"] = ob_name
                s["user_email"] = ob_email
                s["currency"] = CURRENCY_OPTIONS[currency_choice]
                s["date_format"] = date_fmt
                _ds("settings.json", s)
                st.session_state.setup_step = 3
                st.rerun()

    elif step == 3:
        # Choose Modules
        st.markdown("### Step 3 — Choose Your Modules")
        st.caption("Enable the modules you want. You can change this anytime in Settings.")
        if "ob_enabled_modules" not in st.session_state:
            st.session_state.ob_enabled_modules = ALL_MODULE_KEYS.copy()

        for m in ALL_MODULES:
            val = st.checkbox(
                f"{m['icon']} {m['name']} — {m['desc']}",
                value=m["key"] in st.session_state.ob_enabled_modules,
                key=f"ob_mod_{m['key']}",
            )
            if val and m["key"] not in st.session_state.ob_enabled_modules:
                st.session_state.ob_enabled_modules.append(m["key"])
            elif not val and m["key"] in st.session_state.ob_enabled_modules:
                st.session_state.ob_enabled_modules.remove(m["key"])

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back", use_container_width=True, key="ob3_back"):
                st.session_state.setup_step = 2
                st.rerun()
        with c2:
            if st.button("Next →", type="primary", use_container_width=True, key="ob3_next"):
                st.session_state.setup_step = 4
                st.rerun()

    elif step == 4:
        # Import Data
        st.markdown("### Step 4 — Import Data")
        st.caption("Choose how to get started:")

        import_choice = st.radio(
            "Import option",
            ["📄 Import bank CSV", "📦 Import from backup", "🆕 Start fresh"],
            label_visibility="collapsed",
            key="ob_import_choice",
        )

        if import_choice == "📄 Import bank CSV":
            uploaded = st.file_uploader("Upload CSV statement", type=["csv"], key="ob_csv")
            if uploaded:
                st.success(f"'{uploaded.name}' ready to import.")
                st.session_state["welcome_csv_pending"] = True
        elif import_choice == "📦 Import from backup":
            import_file = st.file_uploader("Upload FinanceKit ZIP backup", type=["zip"], key="ob_zip")
            if import_file:
                try:
                    import zipfile, io
                    os.makedirs(_data_dir(), exist_ok=True)
                    with zipfile.ZipFile(io.BytesIO(import_file.read()), "r") as zf:
                        for name in zf.namelist():
                            if name.endswith(".json"):
                                zf.extract(name, _data_dir())
                    st.success("Backup restored successfully!")
                except Exception as e:
                    st.error(f"Import failed: {e}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back", use_container_width=True, key="ob4_back"):
                st.session_state.setup_step = 3
                st.rerun()
        with c2:
            if st.button("Next →", type="primary", use_container_width=True, key="ob4_next"):
                st.session_state.setup_step = 5
                st.rerun()

    elif step == 5:
        # Quick Tour
        st.markdown("### Step 5 — Quick Tour")

        tour_slides = [
            ("🏠", "Your dashboard shows everything at a glance",
             "Net worth, financial health score, savings goals, recent activity — all in one place."),
            ("💰", "Track budgets and see where your money goes",
             "Set monthly limits by category, import bank CSVs, and see spending vs. budget with visual charts."),
            ("🎯", "Set goals and watch your progress",
             "Emergency fund, vacation, new car — track milestones and celebrate progress."),
            ("📊", "Generate reports and export PDFs anytime",
             "Professional financial reports, invoices, and data exports — all generated locally."),
        ]

        for icon, title, desc in tour_slides:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:12px;padding:0.6rem 0;'
                f'border-bottom:1px solid var(--fk-border);">'
                f'<div style="font-size:2rem;">{icon}</div>'
                f'<div><div style="font-weight:600;color:var(--fk-text);">{title}</div>'
                f'<div style="color:var(--fk-text-muted);font-size:0.88rem;">{desc}</div></div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back", use_container_width=True, key="ob5_back"):
                st.session_state.setup_step = 4
                st.rerun()
        with c2:
            if st.button("🚀 Launch Dashboard", type="primary", use_container_width=True, key="ob5_finish"):
                _finish_onboarding()


# --- Sidebar ---
with st.sidebar:
    st.markdown('<div class="fk-logo">💰 FinanceKit</div>', unsafe_allow_html=True)
    st.markdown('<div class="fk-logo-line"></div>', unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-size:0.75rem;color:var(--fk-footer-text);margin-bottom:0.5rem;'>v{APP_VERSION} · Your money, your machine.</div>",
        unsafe_allow_html=True,
    )

    # User display when authenticated
    if st.session_state.get("authenticated"):
        _uname = st.session_state.get("user_name", "User")
        _uemail = st.session_state.get("user_email", "")
        _initial = _uname[0].upper() if _uname else "U"
        _auth_badge = st.session_state.get("auth_method", "local")
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:0.5rem;">'
            f'<div style="width:32px;height:32px;border-radius:50%;background:var(--fk-accent);'
            f'display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:0.9rem;">{_initial}</div>'
            f'<div><div style="color:var(--fk-text);font-weight:600;font-size:0.88rem;">{_uname}</div>'
            f'<div style="color:var(--fk-text-muted);font-size:0.72rem;">{_uemail}</div></div></div>',
            unsafe_allow_html=True,
        )

    # Notification bell
    from utils.notifications import get_unread_count, get_notifications, mark_read, mark_all_read, clear_all as _notif_clear_all, group_notifications, relative_time, notification_icon
    _unread = get_unread_count()
    _bell_label = f"\U0001f514 {_unread}" if _unread > 0 else "\U0001f514"
    with st.expander(_bell_label):
        if _unread > 0:
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("Mark all read", key="notif_mark_all", use_container_width=True):
                    mark_all_read()
                    st.rerun()
            with bc2:
                if st.button("Clear all", key="notif_clear_all", use_container_width=True):
                    _notif_clear_all()
                    st.rerun()

        _all_notifs = get_notifications(limit=30)
        if _all_notifs:
            _grouped = group_notifications(_all_notifs)
            for _group_name, _group_items in _grouped.items():
                if not _group_items:
                    continue
                st.markdown(f'<div class="fk-notif-group">{_group_name}</div>', unsafe_allow_html=True)
                for _n in _group_items:
                    _icon = notification_icon(_n.get("type", "info"))
                    _cls = "unread" if not _n.get("read", False) else ""
                    _ts = relative_time(_n.get("timestamp", ""))
                    st.markdown(
                        f'<div class="fk-notif-item {_cls}">'
                        f'<div class="fk-notif-icon">{_icon}</div>'
                        f'<div class="fk-notif-content">'
                        f'<div class="fk-notif-title">{_n.get("title","")}</div>'
                        f'<div class="fk-notif-msg">{_n.get("message","")}</div>'
                        f'<div class="fk-notif-meta">{_n.get("module","").title()} \u00b7 {_ts}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                    _action = _n.get("action_module")
                    if _action and not _n.get("read", False):
                        if st.button(f"Go to {_action.replace('_', ' ').title()}", key=f"notif_go_{_n['id']}", use_container_width=True):
                            mark_read(_n["id"])
                            # Map action_module to nav target
                            _action_map = {
                                "budget_tracker": "\U0001f4b0 Budget Tracker",
                                "goal_tracker": "\U0001f3af Goal Tracker",
                                "portfolio_tracker": "\U0001f4c8 Portfolio Tracker",
                                "subscription_auditor": "\U0001f504 Subscription Auditor",
                                "job_tracker": "\U0001f4bc Freelance Dashboard",
                                "receipt_scanner": "\U0001f9fe Receipt Scanner",
                                "report_generator": "\U0001f4ca Report Generator",
                            }
                            _nav = _action_map.get(_action, "")
                            if _nav:
                                st.session_state.nav_target = _nav
                            st.rerun()
        else:
            st.caption("No notifications yet.")

    # Theme toggle
    theme_icon = "☀️" if theme == "dark" else "🌙"
    theme_label = "Light Mode" if theme == "dark" else "Dark Mode"
    if st.button(f"{theme_icon} {theme_label}", key="theme_toggle", use_container_width=True):
        new_theme = "light" if theme == "dark" else "dark"
        st.session_state.fk_theme = new_theme
        # Persist to settings.json
        settings_fp = os.path.join(_data_dir(), "settings.json")
        try:
            with open(settings_fp, "r", encoding="utf-8") as f:
                s = json.load(f)
        except Exception:
            s = {}
        s["theme"] = new_theme
        os.makedirs(_data_dir(), exist_ok=True)
        with open(settings_fp, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
        st.rerun()

    # Global search
    search_query = st.text_input("🔍 Search everything...", key="global_search", label_visibility="collapsed",
                                  placeholder="🔍 Search everything...")
    if search_query and len(search_query.strip()) >= 2:
        from utils.search import search_all
        results = search_all(search_query)
        if results:
            for r in results[:8]:
                if st.button(
                    f"{r['icon']} {r['title']}",
                    key=f"sr_{r['title'][:20]}_{r['module']}",
                    use_container_width=True,
                    help=f"{r['module']} · {r['detail']}",
                ):
                    st.session_state.nav_target = r["nav"]
                    st.rerun()
        else:
            st.caption("No results found.")

    st.markdown("---")

    # Grouped navigation
    st.markdown('<div class="nav-group">OVERVIEW</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigate",
        NAV_OPTIONS,
        index=st.session_state.nav_index,
        label_visibility="collapsed",
        key="sidebar_nav",
    )
    st.session_state.nav_index = NAV_OPTIONS.index(page)

    # Quick Actions
    st.markdown("---")
    with st.expander("⚡ Quick Actions"):
        if st.button("➕ Add Transaction", key="qa_txn", use_container_width=True):
            st.session_state.nav_target = "💰 Budget Tracker"
            st.session_state.auto_open_form = True
            st.rerun()
        if st.button("📄 Import CSV", key="qa_csv", use_container_width=True):
            st.session_state.nav_target = "📊 Report Generator"
            st.rerun()
        if st.button("🎯 New Goal", key="qa_goal", use_container_width=True):
            st.session_state.nav_target = "🎯 Goal Tracker"
            st.session_state.auto_open_form = True
            st.rerun()
        if st.button("🧾 Scan Receipt", key="qa_receipt", use_container_width=True):
            st.session_state.nav_target = "🧾 Receipt Scanner"
            st.rerun()

    st.markdown("---")
    st.caption("All data stored locally. Zero cloud. Zero tracking.")

    # Sign out button (when authenticated)
    if st.session_state.get("authenticated"):
        if st.button("🚪 Sign Out", key="sign_out", use_container_width=True):
            _sign_out()

    # Keyboard shortcuts
    with st.expander("⌨️ Keyboard Shortcuts"):
        st.markdown(
            '<div style="font-size:0.82rem;line-height:1.8;">'
            '<span class="fk-kbd">0</span> Dashboard<br>'
            '<span class="fk-kbd">1</span>-<span class="fk-kbd">7</span> Modules<br>'
            '<span class="fk-kbd">9</span> Settings<br>'
            '<span class="fk-kbd">?</span> This help'
            '</div>',
            unsafe_allow_html=True,
        )


# --- Page routing ---
if page == "🏠 Dashboard":
    if _is_first_launch() and not st.session_state.get("setup_complete"):
        show_welcome_dialog()

    # Time-of-day greeting
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    # Check if user has set their name in Settings
    _user_settings = _load_json("settings.json", default={})
    _user_name = _user_settings.get("user_name", "")
    _greeting_name = f", {_user_name}" if _user_name else ""

    st.markdown('<div class="page-header-title">FinanceKit</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="page-header-sub">{greeting}{_greeting_name}! 7 modules · zero subscriptions · runs 100% locally.</div>',
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
        b_val = f"{format_currency_int(total_budget)}/mo" if total_budget > 0 else "Not set"
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
        g_val = f"{format_currency_int(g_saved)} / {format_currency_int(g_target)}" if goals else "No goals"
        g_sub = f"{len(goals)} active goal{'s' if len(goals)!=1 else ''}" if goals else "Add goals in Goal Tracker"
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">🎯 Savings Goals</div>'
            f'<div class="widget-value">{g_val}</div><div class="widget-sub">{g_sub}</div></div>',
            unsafe_allow_html=True,
        )

    # Alert bar — recent unread notifications
    _dash_alerts = get_notifications(unread_only=True, limit=5)
    if _dash_alerts:
        st.markdown("**📋 Recent Alerts**")
        for _da in _dash_alerts:
            _da_icon = notification_icon(_da.get("type", "info"))
            _da_border = f"border-{_da.get('type', 'info')}"
            _da_ts = relative_time(_da.get("timestamp", ""))
            st.markdown(
                f'<div class="fk-alert-card {_da_border}">'
                f'<div style="font-size:1rem;">{_da_icon}</div>'
                f'<div style="flex:1;">'
                f'<div style="color:var(--fk-text);font-weight:600;font-size:0.88rem;">{_da.get("title","")}</div>'
                f'<div style="color:var(--fk-text-muted);font-size:0.8rem;">{_da.get("message","")}</div>'
                f'<div style="color:var(--fk-text-dim);font-size:0.72rem;margin-top:2px;">{_da_ts}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("---")
    else:
        st.markdown(
            '<div style="text-align:center;padding:0.6rem;color:var(--fk-text-muted);font-size:0.85rem;">'
            '✅ All clear — no new alerts</div>',
            unsafe_allow_html=True,
        )

    # Spending anomaly alerts
    try:
        from utils.insights import detect_anomalies
        _anomalies = detect_anomalies()
        if _anomalies:
            st.markdown("**⚠️ Spending Alerts**")
            for _anom in _anomalies[:3]:
                st.markdown(
                    f'<div class="fk-alert-card border-warning">'
                    f'<div style="font-size:1rem;">⚠️</div>'
                    f'<div style="flex:1;">'
                    f'<div style="color:var(--fk-text);font-weight:600;font-size:0.88rem;">'
                    f'Spending Alert: {_anom["category"]}</div>'
                    f'<div style="color:var(--fk-text-muted);font-size:0.8rem;">{_anom["description"]}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                # Create notification for anomaly (deduped by title)
                create_notification(
                    "warning", "budget_tracker",
                    f"Spending Alert: {_anom['category']}",
                    _anom["description"],
                )
            st.markdown("")
    except Exception:
        pass

    # Bills due this week
    try:
        from modules.budget_tracker import get_upcoming_bills
        _week_bills = [b for b in get_upcoming_bills(7) if not b.get("_overdue")]
        if _week_bills:
            st.markdown("**📅 Bills Due This Week**")
            for _wb in _week_bills[:4]:
                days = _wb.get("_days_away", 0)
                auto_tag = " (auto-pay)" if _wb.get("auto_pay") else ""
                st.markdown(
                    f'<div class="fk-alert-card border-info">'
                    f'<div style="font-size:1rem;">📅</div>'
                    f'<div style="flex:1;">'
                    f'<div style="color:var(--fk-text);font-weight:600;font-size:0.88rem;">'
                    f'{_wb["name"]} — {format_currency_int(_wb["amount"])}</div>'
                    f'<div style="color:var(--fk-text-muted);font-size:0.8rem;">'
                    f'Due in {days} day{"s" if days != 1 else ""}{auto_tag}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
            st.markdown("")
    except Exception:
        pass

    # Quick Actions row — 4 large icon buttons
    st.markdown("**⚡ Quick Actions**")
    _qa1, _qa2, _qa3, _qa4 = st.columns(4)
    with _qa1:
        if st.button("➕ Transaction", key="dash_qa_txn", use_container_width=True):
            st.session_state.nav_target = "💰 Budget Tracker"
            st.session_state.auto_open_form = True
            st.rerun()
    with _qa2:
        if st.button("🧾 Receipt", key="dash_qa_receipt", use_container_width=True):
            st.session_state.nav_target = "🧾 Receipt Scanner"
            st.rerun()
    with _qa3:
        if st.button("📊 Report", key="dash_qa_report", use_container_width=True):
            st.session_state.nav_target = "📊 Report Generator"
            st.rerun()
    with _qa4:
        if st.button("🎯 New Goal", key="dash_qa_goal", use_container_width=True):
            st.session_state.nav_target = "🎯 Goal Tracker"
            st.session_state.auto_open_form = True
            st.rerun()

    st.markdown("---")

    # ── Net Worth & Financial Health ────────────────────────────────────
    _nw_col, _fh_col = st.columns(2)

    with _nw_col:
        st.markdown("### 💎 Net Worth")
        # Assets
        _portfolio_value = 0
        _price_cache = st.session_state.get("price_cache", {})
        for h in holdings:
            key = f"{h['ticker']}_{h['type']}"
            pd_data = _price_cache.get(key)
            if pd_data:
                _portfolio_value += pd_data["price"] * h["quantity"]
            else:
                _portfolio_value += h["purchase_price"] * h["quantity"]

        _goals_saved = sum(g.get("current", 0) for g in goals)
        _settings_data = _load_json("settings.json", default={})
        _cash_balance = float(_settings_data.get("cash_balance", 0))
        _total_assets = _portfolio_value + _goals_saved + _cash_balance

        # Liabilities
        _liabilities = _load_json("liabilities.json", default=[])
        _total_liabilities = sum(float(l.get("balance", 0)) for l in _liabilities)
        _net_worth = _total_assets - _total_liabilities

        # Net worth history snapshot
        _nw_history = _load_json("net_worth_history.json", default=[])
        _current_month_key = datetime.now().strftime("%Y-%m")
        _has_snapshot = any(s.get("date", "").startswith(_current_month_key) for s in _nw_history)
        if not _has_snapshot and (_total_assets > 0 or _total_liabilities > 0):
            _nw_history.append({
                "date": _current_month_key,
                "assets": _total_assets,
                "liabilities": _total_liabilities,
                "net_worth": _net_worth,
            })
            from utils.data_persistence import save_json as _dp_save
            _dp_save("net_worth_history.json", _nw_history)

        # Display
        _nw_color = "var(--fk-success)" if _net_worth >= 0 else "var(--fk-danger)"
        # Compare to last month
        _prev_nw = None
        if len(_nw_history) >= 2:
            sorted_history = sorted(_nw_history, key=lambda x: x.get("date", ""))
            _prev_nw = sorted_history[-2].get("net_worth", 0) if len(sorted_history) >= 2 else None

        _nw_delta_html = ""
        if _prev_nw is not None and _prev_nw != 0:
            _nw_change = _net_worth - _prev_nw
            _nw_change_pct = (_nw_change / abs(_prev_nw)) * 100
            _arrow = "↑" if _nw_change >= 0 else "↓"
            _delta_color = "var(--fk-success)" if _nw_change >= 0 else "var(--fk-danger)"
            _nw_delta_html = (
                f'<div style="font-size:0.82rem;color:{_delta_color};margin-top:2px;">'
                f'{_arrow} {format_currency_int(abs(_nw_change))} ({_nw_change_pct:+.1f}%) vs last month</div>'
            )

        st.markdown(
            f'<div class="dash-widget">'
            f'<div class="widget-title">Net Worth</div>'
            f'<div class="widget-value" style="color:{_nw_color};">{format_currency_int(_net_worth)}</div>'
            f'{_nw_delta_html}'
            f'<div class="widget-sub" style="margin-top:6px;">'
            f'Assets: {format_currency_int(_total_assets)} · Liabilities: {format_currency_int(_total_liabilities)}'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # Net worth trend chart
        if len(_nw_history) >= 2:
            import plotly.graph_objects as _nw_go
            from utils.chart_config import apply_layout as _nw_apply, _theme_colors as _nw_tc
            _sorted_h = sorted(_nw_history, key=lambda x: x.get("date", ""))
            _nw_fig = _nw_go.Figure(_nw_go.Scatter(
                x=[s["date"] for s in _sorted_h],
                y=[s["net_worth"] for s in _sorted_h],
                mode="lines+markers",
                line=dict(color="#6366f1", width=2),
                marker=dict(size=6),
                fill="tozeroy",
                fillcolor="rgba(99,102,241,0.1)",
            ))
            _nw_apply(_nw_fig, height=180, margin=dict(t=10, b=20, l=10, r=10), showlegend=False)
            st.plotly_chart(_nw_fig, use_container_width=True)

        # Cash balance input
        with st.expander("Edit Cash / Liabilities"):
            _new_cash = st.number_input("Cash / Bank Balance ($)", value=_cash_balance, step=100.0, key="nw_cash")
            if _new_cash != _cash_balance:
                _settings_data["cash_balance"] = _new_cash
                from utils.data_persistence import save_json as _dp_save2
                _dp_save2("settings.json", _settings_data)
                st.toast("Cash balance updated!", icon="✅")
                st.rerun()

            if _liabilities:
                st.markdown("**Liabilities:**")
                for _li in _liabilities:
                    st.markdown(f"- {_li.get('name', 'Unnamed')}: {format_currency_int(float(_li.get('balance', 0)))}")
            st.caption("Manage liabilities in Settings → Data Management.")

    with _fh_col:
        st.markdown("### 🏥 Financial Health")
        # Calculate health score components
        _scores = {}

        # 1. Budget adherence (25%)
        if budgets and any(float(v) > 0 for v in budgets.values()):
            _budget_txns_data = _load_json("budget_transactions.json", default=[])
            if _budget_txns_data:
                import pandas as _fh_pd
                _fh_df = _fh_pd.DataFrame(_budget_txns_data)
                _fh_df["amount"] = _fh_pd.to_numeric(_fh_df.get("amount", 0), errors="coerce")
                _fh_df["category"] = _fh_df.get("category", "Other")
                _fh_spending = _fh_df.groupby("category")["amount"].sum()
                _under = sum(1 for cat, bgt in budgets.items()
                             if float(bgt) > 0 and _fh_spending.get(cat, 0) <= float(bgt))
                _total_budgeted = sum(1 for _, bgt in budgets.items() if float(bgt) > 0)
                _scores["Budget Adherence"] = int((_under / _total_budgeted * 100) if _total_budgeted > 0 else 50)
            else:
                _scores["Budget Adherence"] = 50
        else:
            _scores["Budget Adherence"] = 50

        # 2. Savings rate (25%)
        _monthly_savings = sum(g.get("monthly", 0) for g in goals)
        if total_budget > 0 and _monthly_savings > 0:
            _savings_rate = _monthly_savings / total_budget * 100
            if _savings_rate >= 20:
                _scores["Savings Rate"] = 100
            elif _savings_rate >= 10:
                _scores["Savings Rate"] = 75
            elif _savings_rate >= 5:
                _scores["Savings Rate"] = 50
            else:
                _scores["Savings Rate"] = 25
        else:
            _scores["Savings Rate"] = 25

        # 3. Emergency fund (20%)
        if goals:
            _top_goal = max(goals, key=lambda g: g.get("target", 0))
            _ef_pct = min(100, (_top_goal["current"] / _top_goal["target"] * 100) if _top_goal["target"] > 0 else 0)
            _scores["Emergency Fund"] = int(_ef_pct)
        else:
            _scores["Emergency Fund"] = 0

        # 4. Debt ratio (15%)
        if _total_assets > 0:
            _debt_ratio = _total_liabilities / _total_assets
            if _debt_ratio < 0.3:
                _scores["Debt Ratio"] = 100
            elif _debt_ratio < 0.5:
                _scores["Debt Ratio"] = 75
            elif _debt_ratio < 0.8:
                _scores["Debt Ratio"] = 50
            else:
                _scores["Debt Ratio"] = 25
        else:
            _scores["Debt Ratio"] = 50 if _total_liabilities == 0 else 25

        # 5. Subscription efficiency (15%)
        _sub_decisions = _load_json("sub_decisions.json", default={})
        if _sub_decisions:
            _cancel_count = sum(1 for v in _sub_decisions.values() if v == "Cancel")
            _total_subs = len(_sub_decisions)
            _scores["Sub Efficiency"] = min(100, int((_total_subs - _cancel_count) / max(1, _total_subs) * 100))
        else:
            _scores["Sub Efficiency"] = 50

        # Weighted score
        _weights = {
            "Budget Adherence": 0.25,
            "Savings Rate": 0.25,
            "Emergency Fund": 0.20,
            "Debt Ratio": 0.15,
            "Sub Efficiency": 0.15,
        }
        _health_score = sum(_scores.get(k, 50) * w for k, w in _weights.items())
        _health_score = int(min(100, max(0, _health_score)))

        # Color
        if _health_score >= 70:
            _gauge_color = "#22c55e"
            _health_label = "Good"
        elif _health_score >= 40:
            _gauge_color = "#f59e0b"
            _health_label = "Fair"
        else:
            _gauge_color = "#ef4444"
            _health_label = "Needs Attention"

        # Gauge display
        import plotly.graph_objects as _fh_go
        from utils.chart_config import _theme_colors as _fh_theme
        _tc = _fh_theme()
        _gauge_fig = _fh_go.Figure(_fh_go.Indicator(
            mode="gauge+number",
            value=_health_score,
            number={"suffix": "/100", "font": {"size": 28, "color": _tc["font_color"]}},
            gauge={
                "axis": {"range": [0, 100], "tickfont": {"color": _tc["font_color"]}},
                "bar": {"color": _gauge_color},
                "bgcolor": _tc["grid"],
                "steps": [
                    {"range": [0, 40], "color": "rgba(239,68,68,0.15)"},
                    {"range": [40, 70], "color": "rgba(245,158,11,0.15)"},
                    {"range": [70, 100], "color": "rgba(34,197,94,0.15)"},
                ],
            },
        ))
        _gauge_fig.update_layout(
            height=180,
            margin=dict(t=30, b=0, l=30, r=30),
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": _tc["font_color"]},
        )
        st.plotly_chart(_gauge_fig, use_container_width=True)
        st.markdown(
            f'<div style="text-align:center;color:{_gauge_color};font-weight:600;margin-top:-10px;">'
            f'{_health_label}</div>',
            unsafe_allow_html=True,
        )

        # Tips based on lowest-scoring components
        _sorted_scores = sorted(_scores.items(), key=lambda x: x[1])
        _tips = []
        for _comp, _score in _sorted_scores[:3]:
            if _comp == "Budget Adherence" and _score < 70:
                _over_cats = sum(1 for cat, bgt in budgets.items()
                                 if float(bgt) > 0 and _fh_spending.get(cat, 0) > float(bgt)) if '_fh_spending' in dir() else 0
                _tips.append(f"You're over budget in {_over_cats} categor{'y' if _over_cats == 1 else 'ies'} — review your spending.")
            elif _comp == "Savings Rate" and _score < 70:
                _tips.append(f"Your savings rate is low — try increasing automatic contributions.")
            elif _comp == "Emergency Fund" and _score < 70:
                _tips.append(f"Your top goal is only {_scores['Emergency Fund']}% funded — prioritize it.")
            elif _comp == "Debt Ratio" and _score < 70:
                _tips.append("Your debt-to-asset ratio is high — focus on paying down liabilities.")
            elif _comp == "Sub Efficiency" and _score < 70:
                _tips.append("Review subscriptions — cancel unused ones to save money.")

        if _tips:
            for _tip in _tips:
                st.markdown(f"<div style='font-size:0.82rem;color:var(--fk-text-muted);padding:2px 0;'>💡 {_tip}</div>",
                            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Top Insight ──────────────────────────────────────────────────────
    from utils.insights import get_top_insight
    _top_insight = get_top_insight()

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
                    st.markdown(f"<small style='color:var(--fk-text-muted);'>{goal['name']}</small>", unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="prog-bar-bg"><div class="prog-bar-fill" style="background:{bar_color};width:{pct:.1f}%;"></div></div>',
                        unsafe_allow_html=True,
                    )
                with gc2:
                    st.markdown(
                        f'<div style="text-align:right;font-size:0.82rem;color:var(--fk-text-muted);padding-top:12px;">{pct:.0f}%</div>',
                        unsafe_allow_html=True,
                    )
            if len(goals) > 3:
                st.caption(f"+ {len(goals)-3} more — open Goal Tracker")
            if st.button("Open Goal Tracker →", key="d_goals"):
                st.session_state.nav_target = "🎯 Goal Tracker"
                st.rerun()
        else:
            st.markdown(
                '<div class="fk-empty"><div class="icon">🎯</div>'
                '<div class="title">No savings goals yet</div>'
                '<div>Set your first goal to track progress here.</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("🎯 Create a Goal", key="d_create_goal"):
                st.session_state.nav_target = "🎯 Goal Tracker"
                st.rerun()

    with col_right:
        # Recent receipts
        st.markdown("**🧾 Recent Receipts**")
        if receipts_data:
            for r in (receipts_data[-5:])[::-1]:
                vendor = str(r.get("vendor", "Unknown"))[:35]
                total = r.get("total", "")
                sym = get_currency_symbol()
                total_str = f"{sym}{total}" if total and not str(total).startswith(sym) else (total or "—")
                dt = r.get("date", "")
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:5px 0;'
                    f'border-bottom:1px solid var(--fk-border);font-size:0.88rem;">'
                    f'<span style="color:var(--fk-accent-text);">{vendor}</span>'
                    f'<span style="color:var(--fk-accent);font-weight:600;">{total_str}</span></div>',
                    unsafe_allow_html=True,
                )
            if st.button("View all receipts →", key="d_receipts"):
                st.session_state.nav_target = "🧾 Receipt Scanner"
                st.rerun()
        else:
            st.markdown(
                '<div class="fk-empty"><div class="icon">🧾</div>'
                '<div class="title">No receipts yet</div>'
                '<div>Upload a receipt to see it here.</div></div>',
                unsafe_allow_html=True,
            )

    # Insight — prefer analytics-based insight, fall back to static
    st.markdown("<br>", unsafe_allow_html=True)
    if _top_insight:
        _ins_cls = _top_insight.get("type", "tip")
        st.markdown(
            f'<div class="insight-card {_ins_cls}"><div class="insight-label">💡 SMART INSIGHT</div>'
            f'<div class="insight-text">{_top_insight["text"]}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        insight = _generate_insight(budgets, goals, receipts_data, stmt_data)
        st.markdown(
            f'<div class="insight-card"><div class="insight-label">💡 QUICK INSIGHT</div>'
            f'<div class="insight-text">{insight}</div></div>',
            unsafe_allow_html=True,
        )

    # Recent Activity feed
    from utils.activity_log import get_recent as _get_recent_activity, format_activity as _fmt_activity

    _recent_activity = _get_recent_activity(limit=10)
    if _recent_activity:
        st.markdown("**📋 Recent Activity**")
        for _act in _recent_activity:
            st.markdown(
                f'<div style="padding:4px 0;font-size:0.85rem;color:var(--fk-text-muted);'
                f'border-bottom:1px solid var(--fk-border);">{_fmt_activity(_act)}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("")

    # Module cards — only show enabled modules
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Your Modules")

    _enabled_mods = _get_enabled_modules()

    # Build activity strings from data
    freelance_data = _load_json("freelance_data.json", default={"clients": [], "invoices": []})
    n_receipts = len(receipts_data) if receipts_data else 0
    n_holdings = len(holdings)
    n_goals = len(goals)
    n_clients = len(freelance_data.get("clients", [])) if isinstance(freelance_data, dict) else 0
    n_stmt = len(stmt_data) if stmt_data else 0

    _all_module_cards = [
        ("🧾", "Receipt Scanner", "Scan PDFs & photos. Extract vendor, date, total.",
         "🧾 Receipt Scanner", f"{n_receipts} receipt{'s' if n_receipts != 1 else ''}" if n_receipts else "", "receipts"),
        ("📈", "Portfolio Tracker", "Track stocks & crypto with live prices and alerts.",
         "📈 Portfolio Tracker", f"{n_holdings} holding{'s' if n_holdings != 1 else ''}" if n_holdings else "", "portfolio"),
        ("📊", "Report Generator", "Upload transactions, get a polished PDF report.",
         "📊 Report Generator", "", "reports"),
        ("💼", "Freelance Dashboard", "Track clients, log work, generate invoices.",
         "💼 Freelance Dashboard", f"{n_clients} client{'s' if n_clients != 1 else ''}" if n_clients else "", "freelance"),
        ("🔄", "Subscription Auditor", "Find recurring charges and forgotten subscriptions.",
         "🔄 Subscription Auditor", f"{n_stmt} transactions" if n_stmt else "", "subscriptions"),
        ("💰", "Budget Tracker", "Set monthly budgets and track spending by category.",
         "💰 Budget Tracker", f"{format_currency_int(total_budget)}/mo" if total_budget > 0 else "", "budget"),
        ("🎯", "Goal Tracker", "Savings goals with projections and milestones.",
         "🎯 Goal Tracker", f"{n_goals} goal{'s' if n_goals != 1 else ''}" if n_goals else "", "goals"),
    ]

    modules = [(ic, t, d, n, a) for ic, t, d, n, a, key in _all_module_cards if key in _enabled_mods]

    # Render in rows of 4
    for row_start in range(0, len(modules), 4):
        row = modules[row_start:row_start + 4]
        cols = st.columns(4)
        for i, (icon, title, desc, nav, activity) in enumerate(row):
            with cols[i]:
                activity_html = f'<div class="activity">{activity}</div>' if activity else ""
                st.markdown(
                    f'<div class="module-card"><div class="icon">{icon}</div>'
                    f'<h3>{title}</h3><p>{desc}</p>{activity_html}</div>',
                    unsafe_allow_html=True,
                )
                if st.button(f"Open {title}", key=f"m_{row_start + i}", use_container_width=True):
                    st.session_state.nav_target = nav
                    st.rerun()
        if row_start == 0 and len(modules) > 4:
            st.markdown("")

    # Footer with last-modified time from data files
    _last_mod = 0
    for _fn in ["receipts.json", "portfolio.json", "budgets.json", "goals.json", "transactions.json"]:
        _fp = os.path.join(_data_dir(), _fn)
        if os.path.exists(_fp):
            _last_mod = max(_last_mod, os.path.getmtime(_fp))
    _last_str = datetime.fromtimestamp(_last_mod).strftime("%b %d, %Y %H:%M") if _last_mod > 0 else "No data yet"
    st.markdown(
        f'<div class="dash-footer">FinanceKit v{APP_VERSION} &nbsp;·&nbsp; '
        f'Last updated: {_last_str}</div>',
        unsafe_allow_html=True,
    )

else:
    # Module routing with graceful error handling
    _module_map = {
        "🧾 Receipt Scanner": "modules.receipt_scanner",
        "📈 Portfolio Tracker": "modules.portfolio_tracker",
        "📊 Report Generator": "modules.report_generator",
        "💼 Freelance Dashboard": "modules.job_tracker",
        "🔄 Subscription Auditor": "modules.subscription_auditor",
        "💰 Budget Tracker": "modules.budget_tracker",
        "🎯 Goal Tracker": "modules.goal_tracker",
        "⚙️ Settings": "modules.settings",
    }
    _mod_path = _module_map.get(page)
    if _mod_path:
        try:
            import importlib
            _mod = importlib.import_module(_mod_path)
            _mod.render()
        except Exception as _mod_err:
            # Friendly error page
            try:
                from utils.logger import get_logger as _err_logger
                _err_logger("app").error(f"Module error in {page}: {_mod_err}", exc_info=True)
            except Exception:
                pass
            st.markdown(
                '<div style="text-align:center;padding:3rem 1rem;">'
                '<div style="font-size:3rem;margin-bottom:0.5rem;">😵</div>'
                '<h2 style="color:var(--fk-text);margin-bottom:0.5rem;">Something went wrong</h2>'
                '<p style="color:var(--fk-text-muted);max-width:500px;margin:0 auto 1.5rem;">'
                f'{page} ran into an unexpected error. This is usually temporary.</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            with st.expander("Technical details"):
                import traceback
                st.code(traceback.format_exc())
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                if st.button("🔄 Try refreshing the page", use_container_width=True, type="primary"):
                    st.rerun()
                st.caption(
                    "If this keeps happening, try running the **Health Check** in "
                    "Settings → Data Management. Errors are logged to `financekit.log`."
                )
