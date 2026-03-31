import streamlit as st
import json
import os
import time as _time
from datetime import datetime
from utils.formatting import format_currency_int, get_currency_symbol

_STARTUP_T = _time.perf_counter()

def _read_version():
    vpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.txt")
    try:
        with open(vpath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "3.6"

APP_VERSION = _read_version()

st.set_page_config(
    page_title="FinanceKit",
    page_icon="F",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Health Check Endpoint (v5.9) ---
if st.query_params.get("health") == "1":
    from utils.performance import render_health_page
    render_health_page()

# --- Theme (dark mode only) ---
def _load_theme():
    return "dark"

st.session_state.fk_theme = "dark"
theme = "dark"

# --- Font size, high contrast, and language from settings ---
def _load_ui_prefs():
    """Load font_size, high_contrast, and language from user or global settings."""
    _base = os.path.dirname(os.path.abspath(__file__))
    _uid = st.session_state.get("user_id", "")
    for _path in ([os.path.join(_base, "data", "users", _uid, "settings.json")] if _uid else []) + \
                  [os.path.join(_base, "data", "settings.json")]:
        try:
            with open(_path, "r", encoding="utf-8") as f:
                s = json.load(f)
                return s.get("font_size", "16px"), s.get("high_contrast", False), s.get("language", "en")
        except Exception:
            continue
    return "16px", False, "en"

_font_size, _high_contrast, _saved_lang = _load_ui_prefs()
st.session_state.setdefault("fk_font_size", _font_size)
st.session_state.setdefault("fk_high_contrast", _high_contrast)
_font_size = st.session_state.fk_font_size
_high_contrast = st.session_state.fk_high_contrast

# Restore language on every run so t() works site-wide
if _saved_lang and _saved_lang != "en":
    try:
        from utils.i18n import set_language as _set_lang_startup
        _set_lang_startup(_saved_lang)
    except Exception:
        pass

# --- Register supplementary i18n keys for dashboard, auth, and landing pages ---
try:
    from utils.i18n import _STRINGS as _i18n_strings
    _app_extra_keys = {
        # Auth page keys
        "auth_or_sign_in_email": "or sign in with email",
        "auth_or_sign_up_email": "or sign up with email",
        "auth_account_locked": "Account locked",
        "auth_attempts_remaining": "attempt(s) remaining",
        "auth_account_locked_30min": "Account locked for 30 minutes due to too many failed attempts.",
        "auth_create_one": "Create one",
        "auth_new_password": "New Password",
        "auth_password_hint": "At least 8 characters with a mix of letters, numbers, and symbols",
        "auth_confirm_password": "Confirm Password",
        "auth_req_length": "At least 8 characters",
        "auth_req_number": "Contains a number",
        "auth_req_upper_lower": "Contains uppercase and lowercase",
        "auth_req_special": "Contains a special character",
        "auth_req_not_common": "Not a common password",
        "auth_invalid_email": "Please enter a valid email address.",
        "auth_passwords_no_match": "Passwords don't match.",
        "auth_signing_in": "Signing you in...",
        "auth_account_created": "Account created! Welcome to FinanceKit.",
        "auth_reset_password": "Reset Password",
        "auth_send_reset_token": "Send Reset Token",
        "auth_reset_token": "Reset Token",
        "auth_reset_token_caption": "Copy this token and paste it below. It expires in 1 hour.",
        "auth_back_to_sign_in": "Back to Sign In",
        "auth_sign_in_google": "Sign in with Google",
        "auth_sign_in_github": "Sign in with GitHub",
        "auth_signing_in_google": "Signing you in with Google...",
        "auth_signing_in_github": "Signing you in with GitHub...",
        "auth_google_failed": "Google sign-in failed. Please try again.",
        "auth_google_no_token": "Google sign-in failed: no access token received.",
        "auth_google_profile_failed": "Could not fetch Google profile. Please try again.",
        "auth_google_no_email": "Google account has no email. Please try a different account.",
        "auth_github_failed": "GitHub sign-in failed. Please try again.",
        "auth_github_no_token": "No access token received.",
        "auth_github_profile_failed": "Could not fetch GitHub profile. Please try again.",
        "auth_github_no_email": "GitHub account has no email. Please add a public email to your GitHub profile and try again.",
        # Landing page keys
        "landing_hero_desc": "Your all-in-one personal finance toolkit. Track budgets, scan receipts, monitor investments, and take control of your money.",
        "landing_feat_budget_title": "Budget & Spending",
        "landing_feat_budget_desc": "Set budgets by category, track every dollar, and get alerts before you overspend.",
        "landing_feat_invest_title": "Investments",
        "landing_feat_invest_desc": "Monitor stocks and crypto with live prices, alerts, and allocation charts.",
        "landing_feat_receipts_title": "Smart Receipts",
        "landing_feat_receipts_desc": "Upload receipts and automatically extract merchant, amount, date, and category.",
        "landing_feat_subs_title": "Subscription Auditor",
        "landing_feat_subs_desc": "Find and cancel forgotten subscriptions.",
        "landing_feat_goals_title": "Goal Tracker",
        "landing_feat_goals_desc": "Set savings goals with deadlines and celebrate milestones.",
        "landing_feat_freelance_title": "Freelance Dashboard",
        "landing_feat_freelance_desc": "Clients, invoices, time tracking, and tax estimates.",
        "landing_feat_reports_title": "Report Generator",
        "landing_feat_reports_desc": "PDF and Excel exports with professional charts.",
        "landing_feat_household_title": "Household Mode",
        "landing_feat_household_desc": "Split expenses with family or roommates.",
        "landing_feat_import_title": "Smart Import",
        "landing_feat_import_desc": "YNAB, Mint, Monarch, or any bank CSV/OFX.",
        "landing_trusted_by": "Trusted by <strong style=\"color:var(--fk-accent);\">{count}</strong> users",
        "landing_pricing_note": "One-time $7.99. Your data stays private. Zero tracking.",
        "landing_footer": "Made for your finances",
        # Dashboard keys
        "dash_day_of_month": "Day of Month",
        "dash_household_overview": "Household Overview",
        "dash_members": "members",
        "dash_outstanding_balances": "Outstanding Balances",
        "dash_shared_goals": "Shared Goals",
        "dash_open_goal_tracker": "Open Goal Tracker \u2192",
        "dash_more_open_goal_tracker": "more \u2014 open Goal Tracker",
        "dash_no_goals_yet": "No savings goals yet",
        "dash_set_first_goal": "Set your first goal to track progress here.",
        "dash_create_a_goal": "Create a Goal",
        "dash_view_all_receipts": "View all receipts \u2192",
        "dash_no_receipts_yet": "No receipts yet",
        "dash_upload_receipt": "Upload a receipt to see it here.",
        "dash_auto_pay": "auto-pay",
        "dash_due_in_days": "Due in {n} day(s)",
        "dash_health_healthy": "Healthy",
        "dash_health_improve": "Room to Improve",
        "dash_health_needs_work": "Needs Work",
        "dash_tip_over_budget": "You're over budget in {n} category(ies) \u2014 review your spending.",
        "dash_tip_savings_low": "Your savings rate is low \u2014 try increasing automatic contributions.",
        "dash_tip_goal_underfunded": "Your top goal is only {pct}% funded \u2014 prioritize it.",
        "dash_tip_debt_high": "Your debt-to-asset ratio is high \u2014 focus on paying down liabilities.",
        "dash_tip_review_subs": "Review subscriptions \u2014 cancel unused ones to save money.",
        "dash_cash_balance": "Cash / Bank Balance ($)",
        "dash_cash_updated": "Cash balance updated!",
        "dash_unnamed": "Unnamed",
        "dash_manage_liabilities_hint": "Manage liabilities in Settings \u2192 Data Management.",
        # Module card descriptions
        "dash_mod_receipts_desc": "Photograph or upload receipts and let OCR extract the details automatically.",
        "dash_mod_portfolio_desc": "Monitor your stocks and crypto in real time with price alerts and allocation breakdowns.",
        "dash_mod_reports_desc": "Import bank statements and generate professional PDF financial reports.",
        "dash_mod_freelance_desc": "Manage clients, track billable hours, and create professional invoices.",
        "dash_mod_subs_desc": "Automatically detect recurring charges from your bank data and decide what to keep.",
        "dash_mod_budget_desc": "Set spending limits by category and see exactly where your money goes each month.",
        "dash_mod_goals_desc": "Set savings goals with target dates, track progress, and see milestone projections.",
        "dash_receipts_scanned": "receipt(s) scanned",
        "dash_holdings_tracked": "holding(s) tracked",
        "dash_clients": "client(s)",
        "dash_transactions_analyzed": "transactions analyzed",
        "dash_mo_budgeted": "mo budgeted",
        "dash_active_goals": "active goal(s)",
        # What's New dialog
        "dash_wn_v60_title": "Launch-Ready Polish",
        "dash_wn_v60_1": "Open Graph meta tags for richer link previews",
        "dash_wn_v60_2": "What's New dialog on version updates",
        "dash_wn_v60_3": "Legal pages: Terms of Service, Privacy Policy, GDPR tools",
        "dash_wn_v60_4": "In-app help tooltips throughout the interface",
        "dash_wn_v59_title": "Performance & Reliability",
        "dash_wn_v59_1": "Cached data loading with smart cache-busting",
        "dash_wn_v59_2": "Health check endpoint (?health=1)",
        "dash_wn_v59_3": "Pagination for large data sets",
        "dash_wn_v59_4": "Startup time optimization and logging",
        "dash_wn_v58_title": "Accessibility & i18n",
        "dash_wn_v58_1": "Internationalization groundwork with t() function",
        "dash_wn_v58_2": "Locale-aware currency formatting (INR, BRL)",
        "dash_wn_v58_3": "Focus indicators, skip-to-content, reduced motion",
        "dash_wn_v58_4": "Font size selector and high contrast mode",
        "dash_wn_v57_title": "Security Hardening",
        "dash_wn_v57_1": "Rate limiting with account lockout",
        "dash_wn_v57_2": "Password strength requirements",
        "dash_wn_v57_3": "Session management and audit logging",
        "dash_wn_v57_4": "Input sanitization",
        "dash_got_it": "Got it!",
        # Help tips
        "dash_help_dashboard": "Your financial overview \u2014 net worth, spending trends, and savings progress at a glance.",
        "dash_help_budget": "Set monthly budgets per category. Import bank statements to auto-track spending.",
        "dash_help_goals": "Create savings goals with deadlines. Contribute funds and track progress with projections.",
        "dash_help_portfolio": "Track stocks and crypto with live prices, alerts, and allocation charts.",
        "dash_help_receipts": "Upload receipt images or PDFs. FinanceKit extracts vendor, date, and total.",
        "dash_help_reports": "Generate polished PDF reports from your transaction data.",
        "dash_help_freelance": "Track clients, log billable hours, and generate invoices.",
        "dash_help_subscriptions": "Detect recurring charges in your statements and decide what to keep or cancel.",
        # Insight strings
        "dash_insight_goal_close": "You're {amount} away from your '{name}' goal. Keep going!",
        "dash_insight_top_budget": "Your highest budget category is **{category}** at {amount}/mo. Import a bank statement to track spending against it.",
        "dash_insight_receipts_scanned": "You've scanned **{n}** receipt(s). Open the Receipt Scanner to export them all to Excel.",
        "dash_insight_stmt_transactions": "You have **{n}** statement transactions. Open Subscription Auditor to find recurring charges.",
        "dash_insight_empty": "Import a bank statement or add your first budget to see personalized insights here.",
        "dash_budget_pct": "{pct}% of your {budget} monthly budget",
        "dash_active_subs": "{n} active subscription(s)",
        "dash_savings_sub": "{saved} saved of {target} target",
    }
    # Patch English strings
    _i18n_strings.setdefault("en", {}).update(_app_extra_keys)
    # Patch Spanish translations for supplementary keys
    _app_extra_keys_es = {
        "auth_or_sign_in_email": "o inicia sesion con correo",
        "auth_or_sign_up_email": "o registrate con correo",
        "auth_account_locked": "Cuenta bloqueada",
        "auth_attempts_remaining": "intento(s) restante(s)",
        "auth_account_locked_30min": "Cuenta bloqueada por 30 minutos por demasiados intentos fallidos.",
        "auth_create_one": "Crear una",
        "auth_new_password": "Nueva Contrasena",
        "auth_password_hint": "Al menos 8 caracteres con letras, numeros y simbolos",
        "auth_confirm_password": "Confirmar Contrasena",
        "auth_invalid_email": "Ingresa un correo valido.",
        "auth_passwords_no_match": "Las contrasenas no coinciden.",
        "auth_signing_in": "Iniciando sesion...",
        "auth_account_created": "Cuenta creada! Bienvenido a FinanceKit.",
        "auth_reset_password": "Restablecer Contrasena",
        "auth_send_reset_token": "Enviar Token",
        "auth_back_to_sign_in": "Volver a Iniciar Sesion",
        "auth_sign_in_google": "Iniciar sesion con Google",
        "auth_sign_in_github": "Iniciar sesion con GitHub",
        "landing_hero_desc": "Tu kit de finanzas personales todo en uno. Controla presupuestos, escanea recibos, monitorea inversiones y toma el control de tu dinero.",
        "landing_footer": "Hecho para tus finanzas",
        "dash_day_of_month": "Dia del Mes",
        "dash_household_overview": "Vista del Hogar",
        "dash_members": "miembros",
        "dash_outstanding_balances": "Saldos Pendientes",
        "dash_shared_goals": "Metas Compartidas",
        "dash_open_goal_tracker": "Abrir Metas \u2192",
        "dash_no_goals_yet": "Sin metas de ahorro aun",
        "dash_set_first_goal": "Crea tu primera meta para ver tu progreso aqui.",
        "dash_create_a_goal": "Crear una Meta",
        "dash_view_all_receipts": "Ver todos los recibos \u2192",
        "dash_no_receipts_yet": "Sin recibos aun",
        "dash_upload_receipt": "Sube un recibo para verlo aqui.",
        "dash_health_healthy": "Saludable",
        "dash_health_improve": "Puede Mejorar",
        "dash_health_needs_work": "Necesita Atencion",
        "dash_got_it": "Entendido!",
        "dash_insight_empty": "Importa un extracto o crea tu primer presupuesto para ver estadisticas aqui.",
    }
    if "es" in _i18n_strings:
        _i18n_strings["es"].update(_app_extra_keys_es)
except Exception:
    pass

# --- Accent color (user-selectable) ---
# Always read from the correct settings file (supports per-user data dirs)
def _load_accent_color():
    """Load accent color from settings, checking user-specific and global paths."""
    _base = os.path.dirname(os.path.abspath(__file__))
    # Try user-specific path first
    _uid = st.session_state.get("user_id", "")
    if _uid:
        _user_fp = os.path.join(_base, "data", "users", _uid, "settings.json")
        try:
            with open(_user_fp, "r", encoding="utf-8") as f:
                c = json.load(f).get("accent_color")
                if c:
                    return c
        except Exception:
            pass
    # Fall back to global settings
    _fp = os.path.join(_base, "data", "settings.json")
    try:
        with open(_fp, "r", encoding="utf-8") as f:
            return json.load(f).get("accent_color", "#6366f1")
    except Exception:
        return "#6366f1"

_accent = st.session_state.get("fk_accent_color", _load_accent_color())
st.session_state.fk_accent_color = _accent


def _hex_to_rgb(hex_color):
    """Convert hex to (r, g, b) tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _lighten_hex(hex_color, amount=0.3):
    """Lighten a hex color by mixing with white."""
    r, g, b = _hex_to_rgb(hex_color)
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def _contrast_text(hex_color):
    """Return white or black text based on background luminance (WCAG)."""
    r, g, b = _hex_to_rgb(hex_color)
    # Relative luminance per WCAG 2.0
    lum = 0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255)
    return "#ffffff" if lum < 0.45 else "#0f172a"


def _darken_hex(hex_color, amount=0.2):
    """Darken a hex color."""
    r, g, b = _hex_to_rgb(hex_color)
    r = int(r * (1 - amount))
    g = int(g * (1 - amount))
    b = int(b * (1 - amount))
    return f"#{r:02x}{g:02x}{b:02x}"


_accent_light = _lighten_hex(_accent, 0.35)
_accent_dark = _darken_hex(_accent, 0.25)
_accent_r, _accent_g, _accent_b = _hex_to_rgb(_accent)
_accent_on = _contrast_text(_accent)  # text color on accent background

# --- Navigation (filtered by enabled modules) ---
_ALL_NAV = [
    "Dashboard",
    "Receipt Scanner",
    "Portfolio Tracker",
    "Report Generator",
    "Freelance Dashboard",
    "Subscription Auditor",
    "Budget Tracker",
    "Goal Tracker",
    "Settings",
]

_NAV_MODULE_MAP = {
    "Receipt Scanner": "receipts",
    "Portfolio Tracker": "portfolio",
    "Report Generator": "reports",
    "Freelance Dashboard": "freelance",
    "Subscription Auditor": "subscriptions",
    "Budget Tracker": "budget",
    "Goal Tracker": "goals",
}


def _build_nav_options() -> list[str]:
    """Build nav options filtered by enabled modules."""
    _base = os.path.dirname(os.path.abspath(__file__))
    enabled = None
    # Try user-specific settings first
    _uid = st.session_state.get("user_id", "")
    if _uid:
        _user_fp = os.path.join(_base, "data", "users", _uid, "settings.json")
        try:
            with open(_user_fp, "r", encoding="utf-8") as f:
                enabled = json.load(f).get("enabled_modules", None)
        except Exception:
            pass
    # Fall back to global settings
    if enabled is None:
        _settings_fp = os.path.join(_base, "data", "settings.json")
        try:
            with open(_settings_fp, "r", encoding="utf-8") as f:
                enabled = json.load(f).get("enabled_modules", None)
        except Exception:
            pass

    if enabled is None:
        return list(_ALL_NAV)

    result = []
    for nav in _ALL_NAV:
        mod_key = _NAV_MODULE_MAP.get(nav)
        if mod_key is None or mod_key in enabled:
            result.append(nav)
    return result


# Rebuild NAV_OPTIONS every run so module toggles take effect immediately
NAV_OPTIONS = _build_nav_options()

if "nav_target" in st.session_state and st.session_state.nav_target:
    target = st.session_state.nav_target
    if target in NAV_OPTIONS:
        st.session_state.nav_target = None
        st.session_state.nav_index = NAV_OPTIONS.index(target)

if "nav_index" not in st.session_state:
    st.session_state.nav_index = 0

# --- CSS with theme variables ---
_dark_vars = f"""
    --fk-bg: #0f1117;
    --fk-card: #1e1e2f;
    --fk-card-alt: #2a2a40;
    --fk-card-hover: #252540;
    --fk-text: #e2e8f0;
    --fk-text-muted: #94a3b8;
    --fk-text-dim: #64748b;
    --fk-border: #2a2a40;
    --fk-border-light: #3a3a5c;
    --fk-accent: {_accent};
    --fk-accent-light: {_accent_light};
    --fk-accent-text: {_accent_light};
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
    --fk-btn-bg: {_accent};
    --fk-btn-text: {_accent_on};
    --fk-btn-border: {_accent};
    --fk-btn-hover-bg: {_accent_light};
    --fk-btn-hover-text: {_accent_on};
"""

_theme_vars = _dark_vars

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {{
        {_theme_vars}
        --primary-color: var(--fk-accent);
    }}

    /* Override Streamlit's accent color */
    .stApp button[data-testid="baseButton-primary"],
    .stApp button[data-testid="baseButton-primaryFormSubmit"] {{
        background-color: var(--fk-accent) !important;
        border-color: var(--fk-accent) !important;
    }}
    .stApp .stProgress > div > div > div {{
        background-color: var(--fk-accent) !important;
    }}
    .stApp a {{
        color: var(--fk-accent) !important;
    }}
    .stApp .stRadio > div[role="radiogroup"] > label:has(input:checked) p,
    .stApp .stRadio > div[role="radiogroup"] > label[data-checked="true"] p {{
        color: var(--fk-accent) !important;
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: {_font_size} !important;
        transition: background-color 0.3s ease, color 0.3s ease;
    }}

    /* Main content area — theme background and text */
    .stApp, [data-testid="stAppViewContainer"] {{
        background-color: var(--fk-bg) !important;
        color: var(--fk-text) !important;
    }}
    .main, [data-testid="stMainBlockContainer"] {{
        background-color: var(--fk-bg) !important;
        color: var(--fk-text) !important;
    }}
    .stApp header[data-testid="stHeader"] {{
        background-color: var(--fk-bg) !important;
    }}

    /* All text elements in main area */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
        color: var(--fk-text) !important;
    }}
    .stApp p, .stApp span, .stApp li, .stApp label, .stApp td, .stApp th {{
        color: var(--fk-text) !important;
    }}
    .stApp .stMarkdown, .stApp .stMarkdown p {{
        color: var(--fk-text) !important;
    }}
    .stApp .stCaption, .stApp small {{
        color: var(--fk-text-muted) !important;
    }}

    /* Form inputs themed */
    .stApp .stTextInput input, .stApp .stNumberInput input,
    .stApp .stSelectbox [data-baseweb="select"],
    .stApp .stMultiSelect [data-baseweb="select"],
    .stApp textarea {{
        background-color: var(--fk-input-bg) !important;
        color: var(--fk-text) !important;
        border-color: var(--fk-border) !important;
    }}
    .stApp [data-baseweb="popover"], .stApp [data-baseweb="menu"],
    .stApp [data-baseweb="list"] {{
        background-color: var(--fk-card) !important;
        color: var(--fk-text) !important;
    }}
    .stApp [data-baseweb="list"] li {{
        color: var(--fk-text) !important;
    }}

    /* Tabs themed */
    .stApp .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent;
    }}
    .stApp .stTabs [data-baseweb="tab"] {{
        color: var(--fk-text-muted) !important;
    }}
    .stApp .stTabs [aria-selected="true"] {{
        color: var(--fk-accent) !important;
    }}

    /* Tables, dataframes, expanders */
    .stApp [data-testid="stExpander"] {{
        background-color: var(--fk-card) !important;
        border-color: var(--fk-border) !important;
    }}
    .stApp [data-testid="stExpander"] summary span {{
        color: var(--fk-text) !important;
    }}
    .stApp .stDataFrame {{ color: var(--fk-text) !important; }}

    /* Metrics */
    .stApp [data-testid="stMetricValue"] {{
        color: var(--fk-text) !important;
    }}
    .stApp [data-testid="stMetricLabel"] {{
        color: var(--fk-text-muted) !important;
    }}

    .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{ background-color: var(--fk-sidebar-bg); min-width: 260px; }}
    /* Styled radio nav items (v4.7) */
    section[data-testid="stSidebar"] .stRadio > div {{
        gap: 1px !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {{
        display: flex !important; align-items: center; gap: 6px;
        padding: 0.4rem 0.7rem !important; margin: 1px 0 !important; border-radius: 8px !important;
        font-size: 0.9rem !important; color: var(--fk-text-muted) !important;
        transition: all 0.15s ease !important; cursor: pointer !important;
        background: transparent !important;
        border-left: 3px solid transparent !important;
        box-sizing: border-box !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {{
        background: var(--fk-card-hover) !important; color: var(--fk-text) !important;
    }}
    /* Active / selected nav item — uniform highlight */
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked) {{
        background: linear-gradient(135deg, rgba({_accent_r},{_accent_g},{_accent_b},0.15), rgba({_accent_r},{_accent_g},{_accent_b},0.08)) !important;
        color: var(--fk-accent) !important; font-weight: 600 !important;
        border-left: 3px solid var(--fk-accent) !important;
    }}
    /* Hide the radio circle indicator */
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child {{
        display: none !important;
    }}
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span {{ color: var(--fk-text) !important; }}
    section[data-testid="stSidebar"] hr {{ border-color: var(--fk-sidebar-hr); }}
    section[data-testid="stSidebar"] .stElementContainer small {{ color: var(--fk-text-muted) !important; }}

    /* Logo — premium brand identity */
    .fk-logo {{
        font-size: 1.5rem; font-weight: 700; letter-spacing: -0.5px;
        display: flex; align-items: center; gap: 8px;
    }}
    .fk-logo .logo-icon {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 32px; height: 32px; border-radius: 10px;
        background: linear-gradient(135deg, var(--fk-accent), var(--fk-accent-light));
        font-size: 0.95rem; font-weight: 800; color: #ffffff;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba({_accent_r},{_accent_g},{_accent_b},0.35);
    }}
    .fk-logo .logo-text {{
        background: linear-gradient(90deg, var(--fk-accent), var(--fk-accent-light));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; color: transparent;
    }}
    .fk-logo .logo-badge {{
        font-size: 0.55rem; font-weight: 600; letter-spacing: 0.5px;
        background: rgba({_accent_r},{_accent_g},{_accent_b},0.15);
        color: var(--fk-accent); padding: 1px 6px; border-radius: 4px;
        text-transform: uppercase; margin-left: -2px; align-self: flex-start; margin-top: 2px;
    }}
    .fk-logo-line {{
        height: 2px; margin: 0.5rem 0 0.4rem 0;
        background: linear-gradient(90deg, var(--fk-accent), var(--fk-accent-light), transparent);
        border-radius: 1px;
    }}

    /* Nav group headers */
    .nav-group {{
        font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 1.2px; color: var(--fk-text-muted); margin: 0.6rem 0 0.2rem 0;
    }}

    /* Styled nav items (v4.7) */
    .fk-nav-item {{
        display: flex; align-items: center; gap: 8px;
        padding: 0.45rem 0.7rem; margin: 1px 0; border-radius: 8px;
        font-size: 0.9rem; color: var(--fk-accent-text); cursor: pointer;
        transition: all 0.15s ease; text-decoration: none !important;
    }}
    .fk-nav-item:hover {{
        background: var(--fk-card-hover); color: var(--fk-text);
    }}
    .fk-nav-item.active {{
        background: linear-gradient(135deg, rgba({_accent_r},{_accent_g},{_accent_b},0.15), rgba({_accent_r},{_accent_g},{_accent_b},0.08));
        color: var(--fk-accent) !important; font-weight: 600;
        border-left: 3px solid var(--fk-accent);
    }}
    .fk-nav-item .nav-icon {{ font-size: 1.05rem; flex-shrink: 0; width: 22px; text-align: center; }}
    .fk-nav-item .nav-label {{ flex: 1; }}

    /* Dashboard widgets */
    .dash-widget {{
        background: linear-gradient(135deg, var(--fk-card) 0%, var(--fk-card-alt) 100%);
        border: 1px solid var(--fk-border-light); border-radius: 14px; padding: 1.2rem 1.4rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
    }}
    .dash-widget:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba({_accent_r},{_accent_g},{_accent_b},0.15); }}
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
    .module-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba({_accent_r},{_accent_g},{_accent_b},0.2); }}
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
        /* Compact sidebar on mobile */
        section[data-testid="stSidebar"] {{ min-width: 220px !important; max-width: 260px !important; }}
        .fk-nav-item {{ padding: 0.5rem 0.6rem; font-size: 0.88rem; }}
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

    /* Mobile quick-entry FAB */
    .fk-fab {{
        display: none;
        position: fixed; bottom: 24px; right: 24px; z-index: 999;
        width: 56px; height: 56px; border-radius: 50%;
        background: var(--fk-accent); color: white; border: none;
        font-size: 1.8rem; cursor: pointer;
        box-shadow: 0 4px 16px rgba({_accent_r},{_accent_g},{_accent_b},0.4);
        transition: transform 0.2s;
    }}
    .fk-fab:active {{ transform: scale(0.9); }}
    @media (max-width: 768px) {{
        .fk-fab {{ display: flex; align-items: center; justify-content: center; }}
    }}

    /* Touch-friendly: minimum 44px touch targets */
    @media (max-width: 768px) {{
        .stButton button {{ min-height: 44px; font-size: 0.9rem; }}
        .stSelectbox, .stTextInput, .stNumberInput {{ min-height: 44px; }}
        .stTabs [data-baseweb="tab"] {{ min-height: 44px; padding: 8px 12px; }}
    }}

    /* ── Mobile PWA — Bottom Nav, FAB, Install Banner (v5.1) ────── */

    /* Install banner */
    .fk-install-banner {{
        display: none;
        position: fixed; top: 0; left: 0; right: 0; z-index: 1001;
        background: linear-gradient(135deg, var(--fk-accent), #818cf8);
        color: white; padding: 12px 16px;
        align-items: center; justify-content: space-between; gap: 12px;
        font-size: 0.88rem; font-weight: 500;
        padding-top: calc(12px + env(safe-area-inset-top));
    }}
    .fk-install-banner button {{
        background: white; color: var(--fk-accent); border: none;
        padding: 6px 16px; border-radius: 6px; font-weight: 600;
        cursor: pointer; font-size: 0.82rem; white-space: nowrap;
    }}
    .fk-install-banner .dismiss {{
        background: transparent; color: rgba(255,255,255,0.8);
        padding: 4px 8px; font-size: 1.1rem;
    }}

    /* Bottom navigation bar — hidden on desktop */
    .fk-bottom-nav {{ display: none; }}

    /* Bottom navigation bar (mobile only) */
    @media (max-width: 768px) {{
        /* Hide sidebar on mobile when bottom nav is active */
        section[data-testid="stSidebar"] {{ display: none !important; }}
        [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

        .fk-bottom-nav {{
            position: fixed;
            bottom: 0; left: 0; right: 0;
            height: 64px;
            background: var(--fk-card);
            border-top: 1px solid var(--fk-border);
            display: flex;
            justify-content: space-around;
            align-items: center;
            z-index: 999;
            padding-bottom: env(safe-area-inset-bottom);
        }}
        .fk-bottom-nav-item {{
            display: flex; flex-direction: column; align-items: center;
            font-size: 0.65rem; color: var(--fk-text-muted);
            cursor: pointer; padding: 6px 10px; border-radius: 8px;
            transition: color 0.15s; text-decoration: none;
            min-width: 48px; min-height: 48px;
            justify-content: center;
        }}
        .fk-bottom-nav-item:hover {{ color: var(--fk-text); }}
        .fk-bottom-nav-item.active {{ color: var(--fk-accent); }}
        .fk-bottom-nav-item .icon {{ font-size: 1.3rem; margin-bottom: 2px; }}

        /* Add padding at bottom so content isn't hidden behind nav */
        .main .block-container {{ padding-bottom: 80px !important; }}

        /* FAB position adjusted for bottom nav */
        .fk-fab {{
            bottom: 80px !important;
            right: 16px !important;
        }}

        /* Safe area insets */
        .stApp {{
            padding-top: env(safe-area-inset-top) !important;
        }}
    }}

    /* Swipe action hints on transaction rows */
    .fk-swipeable {{
        position: relative; overflow: hidden;
        transition: transform 0.2s ease;
    }}
    .fk-swipe-action {{
        position: absolute; top: 0; bottom: 0; width: 80px;
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 0.8rem; font-weight: 600;
    }}
    .fk-swipe-action.delete {{ right: 0; background: var(--fk-danger); }}
    .fk-swipe-action.edit {{ left: 0; background: var(--fk-accent); }}

    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }}
        .dash-widget:hover {{ transform: none; }}
        .module-card:hover {{ transform: none; }}
        .fk-fab:active {{ transform: none; }}
    }}

    /* ── Accessibility (v5.8) ────────────────────────────────────── */

    /* Focus indicators */
    .stApp button:focus-visible,
    .stApp input:focus-visible,
    .stApp select:focus-visible,
    .stApp textarea:focus-visible,
    .stApp a:focus-visible {{
        outline: 2px solid var(--fk-accent) !important;
        outline-offset: 2px !important;
    }}

    /* Skip to content link */
    .fk-skip-link {{
        position: absolute; top: -40px; left: 0; z-index: 10000;
        background: var(--fk-accent); color: white; padding: 8px 16px;
        font-size: 0.9rem; text-decoration: none; border-radius: 0 0 8px 0;
        transition: top 0.2s;
    }}
    .fk-skip-link:focus {{ top: 0; }}

    /* ── Comprehensive theme overrides (v4.2) ────────────────────── */

    /* Ensure ALL text elements inherit theme color (not buttons) */
    .stApp div:not(button div):not(.stButton div), .stApp a {{
        color: var(--fk-text) !important;
    }}

    /* Preserve link styling */
    .stApp a {{
        text-decoration: none;
    }}

    /* Caption and muted text */
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{
        color: var(--fk-text-muted) !important;
    }}

    /* Date input */
    .stApp [data-testid="stDateInput"] input {{
        background-color: var(--fk-input-bg) !important;
        color: var(--fk-text) !important;
        border-color: var(--fk-border) !important;
    }}

    /* Multiselect tags */
    .stApp [data-baseweb="tag"] {{
        background-color: var(--fk-accent) !important;
        color: white !important;
    }}

    /* Number input buttons */
    .stApp .stNumberInput button {{
        color: var(--fk-text) !important;
        border-color: var(--fk-border) !important;
        background-color: var(--fk-card) !important;
    }}

    /* Toggle / checkbox / radio */
    .stApp .stRadio label, .stApp .stCheckbox label {{
        color: var(--fk-text) !important;
    }}
    .stApp .stToggle label span {{
        color: var(--fk-text) !important;
    }}

    /* Metric delta values — preserve green/red */
    .stApp [data-testid="stMetricDelta"] svg {{
        fill: currentColor;
    }}

    /* Dialogs and modals */
    .stApp [data-testid="stModal"] > div {{
        background-color: var(--fk-card) !important;
    }}
    .stApp [data-testid="stModal"] > div * {{
        color: var(--fk-text) !important;
    }}

    /* Tooltip content */
    [data-testid="stTooltipContent"] {{
        background-color: var(--fk-card) !important;
        color: var(--fk-text) !important;
    }}

    /* Toast notifications */
    [data-testid="stToast"] {{
        background-color: var(--fk-card) !important;
        color: var(--fk-text) !important;
    }}

    /* Buttons — all secondary/default buttons follow theme */
    .stApp .stButton button {{
        background-color: var(--fk-btn-bg) !important;
        color: var(--fk-btn-text) !important;
        border: 1px solid var(--fk-btn-border) !important;
        -webkit-text-fill-color: var(--fk-btn-text) !important;
    }}
    .stApp .stButton button * {{
        color: var(--fk-btn-text) !important;
        -webkit-text-fill-color: var(--fk-btn-text) !important;
    }}
    .stApp .stButton button:hover {{
        background-color: var(--fk-btn-hover-bg) !important;
        color: var(--fk-btn-hover-text) !important;
        border-color: var(--fk-border-light) !important;
    }}
    .stApp .stButton button:hover * {{
        color: var(--fk-btn-hover-text) !important;
        -webkit-text-fill-color: var(--fk-btn-hover-text) !important;
    }}
    /* Primary buttons — same accent, slightly more prominent */
    .stApp .stButton button[kind="primary"],
    .stApp button[data-testid="baseButton-primary"],
    .stApp button[data-testid="baseButton-primaryFormSubmit"],
    .stApp .stFormSubmitButton button {{
        background-color: var(--fk-accent) !important;
        color: {_accent_on} !important;
        border: none !important;
        -webkit-text-fill-color: {_accent_on} !important;
        font-weight: 600 !important;
    }}
    .stApp .stButton button[kind="primary"] *,
    .stApp button[data-testid="baseButton-primary"] *,
    .stApp button[data-testid="baseButton-primaryFormSubmit"] *,
    .stApp .stFormSubmitButton button * {{
        color: {_accent_on} !important;
        -webkit-text-fill-color: {_accent_on} !important;
    }}

    /* Link buttons (OAuth sign-in) — same accent styling */
    .stApp .stLinkButton a {{
        background-color: var(--fk-btn-bg) !important;
        color: var(--fk-btn-text) !important;
        border: 1px solid var(--fk-btn-border) !important;
        border-radius: 8px !important;
        -webkit-text-fill-color: var(--fk-btn-text) !important;
    }}
    .stApp .stLinkButton a * {{
        color: var(--fk-btn-text) !important;
        -webkit-text-fill-color: var(--fk-btn-text) !important;
    }}
    .stApp .stLinkButton a:hover {{
        background-color: var(--fk-btn-hover-bg) !important;
        color: var(--fk-btn-hover-text) !important;
    }}

    /* File uploader */
    .stApp [data-testid="stFileUploader"] {{
        color: var(--fk-text) !important;
    }}
    .stApp [data-testid="stFileUploader"] section {{
        background-color: var(--fk-card) !important;
        border-color: var(--fk-border) !important;
    }}
    .stApp [data-testid="stFileUploader"] small {{
        color: var(--fk-text-muted) !important;
    }}

    /* Alert / info / warning / error boxes */
    .stApp .stAlert {{
        color: var(--fk-text) !important;
    }}

    /* Download button */
    .stApp .stDownloadButton button {{
        background-color: var(--fk-btn-bg) !important;
        color: var(--fk-btn-text) !important;
        border: 1px solid var(--fk-btn-border) !important;
    }}
    .stApp .stDownloadButton button * {{
        color: var(--fk-btn-text) !important;
        -webkit-text-fill-color: var(--fk-btn-text) !important;
    }}

    /* Code blocks */
    .stApp .stCodeBlock {{
        background-color: var(--fk-card-alt) !important;
    }}
    .stApp .stCodeBlock code {{
        color: var(--fk-text) !important;
    }}

    /* Data editor */
    .stApp [data-testid="stDataFrameResizable"] {{
        color: var(--fk-text) !important;
    }}

    /* Selectbox dropdown option text */
    .stApp [data-baseweb="menu"] [role="option"] {{
        color: var(--fk-text) !important;
    }}
    .stApp [data-baseweb="menu"] [role="option"]:hover {{
        background-color: var(--fk-card-hover) !important;
    }}

    /* Progress bars */
    .stApp .stProgress > div > div {{
        background-color: var(--fk-progress-bg) !important;
    }}
    .stApp .stProgress > div > div > div {{
        background-color: var(--fk-accent) !important;
    }}

    /* Horizontal rule */
    .stApp hr {{
        border-color: var(--fk-border) !important;
    }}

    /* Sidebar — theme text but not buttons or logo icon */
    section[data-testid="stSidebar"] *:not(button):not(button *):not(.logo-icon) {{
        color: var(--fk-text) !important;
    }}
    /* Sidebar buttons follow theme btn vars */
    section[data-testid="stSidebar"] .stButton button {{
        background-color: var(--fk-btn-bg) !important;
        color: var(--fk-btn-text) !important;
        border: 1px solid var(--fk-btn-border) !important;
    }}
    section[data-testid="stSidebar"] .stButton button * {{
        color: var(--fk-btn-text) !important;
        -webkit-text-fill-color: var(--fk-btn-text) !important;
    }}
    section[data-testid="stSidebar"] .stButton button:hover {{
        background-color: var(--fk-btn-hover-bg) !important;
        color: var(--fk-btn-hover-text) !important;
    }}

    /* Colored accent text exceptions — keep accent colored */
    .stApp .fk-logo .logo-text {{
        -webkit-text-fill-color: transparent !important;
        color: transparent !important;
    }}
    .stApp .fk-logo .logo-icon,
    section[data-testid="stSidebar"] .fk-logo .logo-icon {{
        -webkit-text-fill-color: #ffffff !important;
        color: #ffffff !important;
    }}
    .stApp .fk-logo .logo-badge {{
        -webkit-text-fill-color: var(--fk-accent) !important;
        color: var(--fk-accent) !important;
    }}
    .stApp .page-header-title {{
        -webkit-text-fill-color: transparent !important;
        color: transparent !important;
    }}

    /* Ensure green/red semantic colors are preserved */
    .stApp .stAlert [data-testid="stAlertContentSuccess"] * {{
        color: inherit !important;
    }}

    /* Prevent text editing in selectbox dropdowns */
    .stApp [data-baseweb="select"] input {{
        caret-color: transparent !important;
        pointer-events: none !important;
    }}
    .stApp [data-baseweb="select"] [data-baseweb="input"] {{
        pointer-events: auto !important;
    }}

    /* ── Button text contrast (all themes) ──────────────────── */
    /* Handled by --fk-btn-* variables above — no hardcoded colors needed */

    /* ── Universal rule: light text on dark backgrounds ──────── */
    /* Dashboard widgets (dark card backgrounds in dark mode) */
    .dash-widget .widget-title {{
        color: var(--fk-text-muted) !important;
        -webkit-text-fill-color: var(--fk-text-muted) !important;
    }}
    .dash-widget .widget-value {{
        -webkit-text-fill-color: initial !important;
    }}
    .dash-widget .widget-sub {{
        color: var(--fk-text-dim) !important;
        -webkit-text-fill-color: var(--fk-text-dim) !important;
    }}
    /* Module cards */
    .module-card h3 {{
        color: var(--fk-text) !important;
        -webkit-text-fill-color: var(--fk-text) !important;
    }}
    .module-card p {{
        color: var(--fk-text-muted) !important;
        -webkit-text-fill-color: var(--fk-text-muted) !important;
    }}
    /* Insight cards (always dark bg) */
    .insight-card .insight-text {{
        color: var(--fk-text) !important;
        -webkit-text-fill-color: var(--fk-text) !important;
    }}
    /* Savings banner (dark green bg — always needs white) */
    .fk-savings-banner .label {{
        color: var(--fk-savings-label) !important;
    }}
    .fk-savings-banner .value {{
        color: var(--fk-savings-text) !important;
    }}
    /* Empty state containers */
    .fk-empty .title {{
        color: var(--fk-text) !important;
        -webkit-text-fill-color: var(--fk-text) !important;
    }}
    /* Alert cards */
    .fk-alert-card {{
        color: var(--fk-text) !important;
    }}
    /* Secondary buttons on hover — use theme variables */
    .stApp button[data-testid="baseButton-secondary"]:hover {{
        color: var(--fk-btn-hover-text) !important;
        background-color: var(--fk-btn-hover-bg) !important;
    }}

    /* ── Light mode hardening ──────────────────────────────────── */

    /* Form inputs — ensure high contrast border and text */
    .stApp .stTextInput input,
    .stApp .stNumberInput input,
    .stApp textarea {{
        color: var(--fk-text) !important;
        background-color: var(--fk-input-bg) !important;
        border: 1px solid var(--fk-border) !important;
    }}
    .stApp .stTextInput input::placeholder,
    .stApp textarea::placeholder {{
        color: var(--fk-text-dim) !important;
    }}

    /* Selectbox displayed value — ensure readable */
    .stApp [data-baseweb="select"] span {{
        color: var(--fk-text) !important;
    }}

    /* Toggle labels */
    .stApp .stCheckbox label span,
    .stApp [data-testid="stWidgetLabel"] {{
        color: var(--fk-text) !important;
    }}

    /* Info / success / warning / error boxes — ensure text contrast */
    .stApp .stAlert {{
        color: var(--fk-text) !important;
    }}

    /* Metric delta text */
    .stApp [data-testid="stMetricDelta"] {{
        opacity: 1 !important;
    }}

    /* Sidebar text — exclude buttons and logo */
    section[data-testid="stSidebar"] *:not(button):not(button *):not(.logo-icon) {{
        color: var(--fk-text);
    }}
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {{
        color: var(--fk-text) !important;
    }}

    /* Code blocks */
    .stApp .stCode, .stApp code {{
        color: var(--fk-text) !important;
        background-color: var(--fk-card-alt) !important;
    }}

    /* Remove ugly focus outline on dropdowns and inputs */
    .stApp [data-baseweb="select"] > div {{
        border-color: var(--fk-border) !important;
    }}
    .stApp [data-baseweb="select"] > div:focus-within {{
        border-color: var(--fk-accent) !important;
        box-shadow: 0 0 0 1px var(--fk-accent) !important;
    }}
    .stApp [data-baseweb="input"] {{
        border-color: var(--fk-border) !important;
    }}
    .stApp [data-baseweb="input"]:focus-within {{
        border-color: var(--fk-accent) !important;
        box-shadow: 0 0 0 1px var(--fk-accent) !important;
    }}
    .stApp .stTextInput input:focus,
    .stApp .stNumberInput input:focus,
    .stApp textarea:focus {{
        border-color: var(--fk-accent) !important;
        box-shadow: 0 0 0 1px var(--fk-accent) !important;
        outline: none !important;
    }}
{f"""
    /* ── High Contrast Mode (Dark) ───────────────────────────── */
    .stApp, [data-testid="stAppViewContainer"] {{
        --fk-text: #ffffff !important;
        --fk-text-muted: #e0e0e0 !important;
        --fk-text-dim: #cccccc !important;
        --fk-border: #ffffff !important;
        --fk-border-light: #cccccc !important;
    }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp span, .stApp li, .stApp label, .stApp td, .stApp th {{
        color: #ffffff !important;
    }}
    .stApp .stCaption, .stApp small {{
        color: #e0e0e0 !important;
    }}
    .stApp button[data-testid="baseButton-secondary"],
    .stApp button[data-testid="baseButton-minimal"] {{
        border: 2px solid #ffffff !important;
    }}
    .stApp [data-baseweb="select"] > div {{
        border: 2px solid #666666 !important;
    }}
    .stApp .stTextInput input, .stApp .stNumberInput input, .stApp textarea {{
        border: 2px solid #666666 !important;
    }}
""" if _high_contrast and theme == "dark" else ""}
</style>
""", unsafe_allow_html=True)

# --- Skip-to-content link (a11y v5.8) ---
st.markdown(
    '<a href="#main-content" class="fk-skip-link">Skip to content</a>'
    '<div id="main-content"></div>',
    unsafe_allow_html=True,
)

# --- PWA manifest, service worker, and mobile enhancements (v5.1) ---
st.components.v1.html("""
<script>
// Inject manifest link
if (!document.querySelector('link[rel="manifest"]')) {
    var link = document.createElement('link');
    link.rel = 'manifest';
    link.href = '/app/static/manifest.json';
    document.head.appendChild(link);
}
// Inject theme-color meta
if (!document.querySelector('meta[name="theme-color"]')) {
    var meta = document.createElement('meta');
    meta.name = 'theme-color';
    meta.content = '#6366f1';
    document.head.appendChild(meta);
}
// Apple mobile web app meta tags
if (!document.querySelector('meta[name="apple-mobile-web-app-capable"]')) {
    var m1 = document.createElement('meta');
    m1.name = 'apple-mobile-web-app-capable'; m1.content = 'yes';
    document.head.appendChild(m1);
    var m2 = document.createElement('meta');
    m2.name = 'apple-mobile-web-app-status-bar-style'; m2.content = 'black-translucent';
    document.head.appendChild(m2);
    var m3 = document.createElement('meta');
    m3.name = 'apple-mobile-web-app-title'; m3.content = 'FinanceKit';
    document.head.appendChild(m3);
}
// Apple touch icon
if (!document.querySelector('link[rel="apple-touch-icon"]')) {
    var atIcon = document.createElement('link');
    atIcon.rel = 'apple-touch-icon';
    atIcon.href = '/app/static/icons/icon-192.png';
    document.head.appendChild(atIcon);
}
// Open Graph meta tags (v6.0)
if (!document.querySelector('meta[property="og:title"]')) {
    var ogTags = [
        ['og:title', 'FinanceKit — Personal Finance Dashboard'],
        ['og:description', 'Track budgets, goals, portfolios, receipts, and subscriptions in one place.'],
        ['og:type', 'website'],
        ['og:image', '/app/static/icons/icon-512.png']
    ];
    ogTags.forEach(function(t) {
        var m = document.createElement('meta');
        m.setAttribute('property', t[0]);
        m.content = t[1];
        document.head.appendChild(m);
    });
}
// Register service worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/app/static/service-worker.js').catch(function() {});
}
// Viewport meta for mobile — safe area support
var vp = document.querySelector('meta[name="viewport"]');
if (vp) vp.content = 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover';

// --- Install prompt (Add to Home Screen) ---
var fkInstallPrompt = null;
window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    fkInstallPrompt = e;
    // Show install banner if not dismissed
    if (!localStorage.getItem('fk_install_dismissed')) {
        var banner = document.getElementById('fk-install-banner');
        if (banner) banner.style.display = 'flex';
    }
});
window.fkInstallApp = function() {
    if (fkInstallPrompt) {
        fkInstallPrompt.prompt();
        fkInstallPrompt.userChoice.then(function() { fkInstallPrompt = null; });
    }
    var banner = document.getElementById('fk-install-banner');
    if (banner) banner.style.display = 'none';
};
window.fkDismissInstall = function() {
    localStorage.setItem('fk_install_dismissed', '1');
    var banner = document.getElementById('fk-install-banner');
    if (banner) banner.style.display = 'none';
};
</script>
""", height=0)

# --- Keyboard shortcuts via JS ---
st.components.v1.html("""
<script>
document.addEventListener('keydown', function(e) {
    // Don't trigger if typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;

    var key = e.key;
    var shortcuts = {
        '0': 'Dashboard',
        '1': 'Receipt Scanner',
        '2': 'Portfolio Tracker',
        '3': 'Report Generator',
        '4': 'Freelance Dashboard',
        '5': 'Subscription Auditor',
        '6': 'Budget Tracker',
        '7': 'Goal Tracker',
        '9': 'Settings',
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
""", height=0)

# --- Splash / loading screen (first render only) ---
if "splash_shown" not in st.session_state:
    _splash = st.empty()
    _splash.markdown(
        '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;'
        'min-height:60vh;text-align:center;">'
        '<div class="logo-icon" style="width:56px;height:56px;border-radius:16px;font-size:1.6rem;font-weight:800;color:#fff;'
        'display:inline-flex;align-items:center;justify-content:center;'
        'background:linear-gradient(135deg,var(--fk-accent),var(--fk-accent-light));'
        'animation:fk-pulse 1.5s ease-in-out infinite;">F</div>'
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

# --- Install banner (PWA v5.1) ---
_is_standalone = False  # Can't detect server-side; JS handles visibility
st.markdown(
    '<div class="fk-install-banner" id="fk-install-banner">'
    '<span>Install FinanceKit for the best experience</span>'
    '<div>'
    '<button onclick="fkInstallApp()">Install</button>'
    '<button class="dismiss" onclick="fkDismissInstall()">&times;</button>'
    '</div></div>',
    unsafe_allow_html=True,
)

# iOS-specific install hint (shown via JS when on iOS Safari, not standalone)
st.components.v1.html("""
<script>
(function() {
    var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    var isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
    if (isIOS && !isStandalone && !localStorage.getItem('fk_install_dismissed')) {
        var banner = document.getElementById('fk-install-banner');
        if (banner) {
            banner.style.display = 'flex';
            banner.querySelector('span').textContent = 'Tap Share then Add to Home Screen to install FinanceKit';
            var installBtn = banner.querySelector('button:not(.dismiss)');
            if (installBtn) installBtn.style.display = 'none';
        }
    }
    // Hide banner if already installed
    if (isStandalone) {
        var banner = document.getElementById('fk-install-banner');
        if (banner) banner.style.display = 'none';
    }
})();
</script>
""", height=0)

# Handle keyboard nav via query params
_qp = st.query_params
if "nav" in _qp:
    nav_target = _qp["nav"]
    if nav_target in NAV_OPTIONS:
        st.session_state.nav_index = NAV_OPTIONS.index(nav_target)
    st.query_params.pop("nav", None)


# --- Shared View Handler (v5.5) ---
_share_token = st.query_params.get("share")
if _share_token:
    try:
        from utils.sharing import validate_share_token, log_share_access
        _share_pw = st.query_params.get("pw")
        _share_data = validate_share_token(_share_token, _share_pw)

        if _share_data is None:
            st.error(t("share_link_invalid"))
            st.stop()
        elif _share_data.get("needs_password"):
            st.markdown(f"### {t('share_password_protected')}")
            pw = st.text_input(t("share_enter_password"), type="password", key="share_pw_input")
            if st.button(t("share_access"), type="primary"):
                _share_data2 = validate_share_token(_share_token, pw)
                if _share_data2 and not _share_data2.get("wrong_password") and not _share_data2.get("needs_password"):
                    st.query_params["pw"] = pw
                    st.rerun()
                else:
                    st.error(t("share_incorrect_password"))
            st.stop()
        elif _share_data.get("wrong_password"):
            st.error(t("share_incorrect_password"))
            st.stop()
        else:
            # Valid share — show read-only view
            log_share_access(_share_token, "viewed")
            _sharer_name = _share_data.get("user_name", "Someone")
            _share_type = _share_data.get("share_type", "standard")
            _type_label = "Financial Advisor View" if _share_type == "advisor" else "Read-Only View"

            st.markdown(
                f'<div style="background:linear-gradient(135deg,var(--fk-accent),#818cf8);'
                f'padding:12px 16px;border-radius:8px;margin-bottom:1rem;color:white;">'
                f'<div style="font-weight:600;">{_type_label}</div>'
                f'<div style="font-size:0.88rem;opacity:0.9;">'
                f"You're viewing {_sharer_name}'s finances (read-only)</div>"
                f'</div>',
                unsafe_allow_html=True,
            )

            # Show dashboard data (read-only, no edit capabilities)
            st.markdown(f'<div class="page-header-title">{_sharer_name}\'s FinanceKit</div>', unsafe_allow_html=True)

            # Load shared user's data
            _shared_modules = _share_data.get("modules")

            st.info(t("share_readonly_notice"))

            # Show basic financial summary
            st.markdown(f"### {t('share_financial_summary')}")
            st.caption(t("share_detailed_data"))

            st.markdown(
                f'<div class="dash-footer">Shared via FinanceKit · Read-only view</div>',
                unsafe_allow_html=True,
            )
            st.stop()
    except ImportError:
        st.error(t("share_module_unavailable"))
        st.stop()
    except Exception as _share_err:
        st.error(f"{t('share_load_error')}: {_share_err}")
        st.stop()

# --- Authentication Gate ---
from utils.auth import is_auth_required, login_user, register_user, password_strength, is_session_valid, session_hours_remaining, generate_reset_token, reset_password_with_token, get_google_credentials, get_github_credentials, login_oauth_user, _sanitize_user_id, invalidate_all_sessions
from utils.data_persistence import set_user_context, clear_user_context


def _show_landing_page():
    """Show a professional landing page for unauthenticated visitors."""
    from utils.auth import get_user_count
    from utils.i18n import t as _t_land

    # Hero section
    st.markdown(
        '<div style="text-align:center;padding:3rem 0 2rem;max-width:900px;margin:0 auto;">'
        ''
        '<h1 class="page-header-title" style="font-size:2.5rem;margin:0 0 0.5rem;">FinanceKit</h1>'
        '<p style="color:var(--fk-text-muted);font-size:1.15rem;max-width:600px;margin:0 auto 2rem;line-height:1.6;">'
        f'{_t_land("landing_hero_desc")}</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # CTA buttons
    col_l, col_c, col_r = st.columns([1.5, 2, 1.5])
    with col_c:
        if st.button(_t_land("get_started"), type="primary", width='stretch', key="landing_signup"):
            st.session_state.auth_view = "register"
            st.session_state.show_auth = True
            st.rerun()
        if st.button(_t_land("sign_in"), width='stretch', key="landing_signin"):
            st.session_state.auth_view = "login"
            st.session_state.show_auth = True
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Feature highlights — 3x3 grid
    _features = [
        (_t_land("landing_feat_budget_title"), _t_land("landing_feat_budget_desc")),
        (_t_land("landing_feat_invest_title"), _t_land("landing_feat_invest_desc")),
        (_t_land("landing_feat_receipts_title"), _t_land("landing_feat_receipts_desc")),
        (_t_land("landing_feat_subs_title"), _t_land("landing_feat_subs_desc")),
        (_t_land("landing_feat_goals_title"), _t_land("landing_feat_goals_desc")),
        (_t_land("landing_feat_freelance_title"), _t_land("landing_feat_freelance_desc")),
        (_t_land("landing_feat_reports_title"), _t_land("landing_feat_reports_desc")),
        (_t_land("landing_feat_household_title"), _t_land("landing_feat_household_desc")),
        (_t_land("landing_feat_import_title"), _t_land("landing_feat_import_desc")),
    ]
    for row_start in range(0, len(_features), 3):
        _row = _features[row_start:row_start + 3]
        cols = st.columns(3)
        for i, (title, desc) in enumerate(_row):
            with cols[i]:
                st.markdown(
                    f'<div style="background:var(--fk-card);border:1px solid var(--fk-border);'
                    f'border-radius:12px;padding:1.2rem;height:100%;">'
                    f'<div style="color:var(--fk-text);font-weight:700;font-size:0.95rem;margin-bottom:0.4rem;">{title}</div>'
                    f'<div style="color:var(--fk-text-muted);font-size:0.82rem;line-height:1.5;">{desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # Social proof
    _user_count = get_user_count()
    _display_count = f"{_user_count}+" if _user_count >= 10 else "100+"
    st.markdown(
        f'<div style="text-align:center;padding:1.5rem 0;">'
        f'<div style="color:var(--fk-text-muted);font-size:0.9rem;">{_t_land("landing_trusted_by", count=_display_count)}</div>'
        f'<div style="color:var(--fk-text-dim);font-size:0.82rem;margin-top:0.3rem;">{_t_land("landing_pricing_note")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Footer
    st.markdown(
        f'<div class="dash-footer">{_t_land("landing_footer")} &nbsp;·&nbsp; FinanceKit v{APP_VERSION}</div>',
        unsafe_allow_html=True,
    )

    st.stop()


def _get_redirect_uri():
    """Get the correct redirect URI for OAuth (Google/GitHub).

    Auto-detects localhost vs Streamlit Cloud so the same secrets.toml
    works in both environments.
    """
    # If running on Streamlit Cloud, use the configured production URI
    _is_cloud = (
        os.environ.get("STREAMLIT_SHARING_MODE")
        or os.environ.get("HOSTNAME", "").endswith(".streamlit.app")
        or os.environ.get("IS_STREAMLIT_CLOUD")
    )
    if _is_cloud:
        # Use secrets redirect_uri on cloud
        try:
            uri = st.secrets.get("google", {}).get("redirect_uri", "")
            if uri:
                return uri
        except Exception:
            pass
        hostname = os.environ.get("HOSTNAME", "")
        if hostname:
            return f"https://{hostname}"

    # Running locally — always use localhost
    return "http://localhost:8501"


_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# Google "G" logo SVG
_GOOGLE_LOGO_SVG = (
    '<svg width="18" height="18" viewBox="0 0 48 48">'
    '<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>'
    '<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>'
    '<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>'
    '<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>'
    '</svg>'
)


_GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USERINFO_URL = "https://api.github.com/user"
_GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

# GitHub logo SVG (Invertocat)
_GITHUB_LOGO_SVG = (
    '<svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">'
    '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38'
    ' 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15'
    '-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07'
    '-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21'
    ' 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16'
    ' 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48'
    ' 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>'
    '</svg>'
)


def _oauth_sign_in_buttons():
    """Render Google and GitHub sign-in buttons using st.link_button. Returns True if any configured."""
    import urllib.parse

    from utils.i18n import t as _t_oauth
    has_any = False

    # --- Google ---
    _g_id, _g_secret = get_google_credentials()
    if _g_id and _g_secret:
        redirect_uri = _get_redirect_uri()
        params = {
            "client_id": _g_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
            "state": "financekit_google",
        }
        auth_url = f"{_GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
        st.link_button(_t_oauth("auth_sign_in_google"), auth_url, width='stretch')
        has_any = True

    # --- GitHub ---
    _gh_id, _gh_secret = get_github_credentials()
    if _gh_id and _gh_secret:
        redirect_uri = _get_redirect_uri()
        gh_params = {
            "client_id": _gh_id,
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": "financekit_github",
        }
        gh_auth_url = f"{_GITHUB_AUTH_URL}?{urllib.parse.urlencode(gh_params)}"
        st.link_button(_t_oauth("auth_sign_in_github"), gh_auth_url, width='stretch')
        has_any = True

    return has_any


def _handle_oauth_callback():
    """Check for Google/GitHub OAuth callback code in query params and complete login."""
    qp = st.query_params
    code = qp.get("code")
    state = qp.get("state")

    if not code or not state:
        return False

    # Determine provider from state
    if state == "financekit_google":
        return _handle_google_callback(code)
    elif state == "financekit_github":
        return _handle_github_callback(code)
    # Legacy state value for backward compat
    elif state == "financekit_oauth":
        return _handle_google_callback(code)
    return False


def _handle_google_callback(code: str):
    """Complete Google OAuth login."""
    _g_id, _g_secret = get_google_credentials()
    if not _g_id or not _g_secret:
        st.query_params.clear()
        return False

    redirect_uri = _get_redirect_uri()

    try:
        import requests as _req
        from utils.i18n import t as _t_gcb
        with st.spinner(_t_gcb("auth_signing_in_google")):
            token_resp = _req.post(_GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": _g_id,
                "client_secret": _g_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }, timeout=10)

            if token_resp.status_code != 200:
                st.error(_t_gcb("auth_google_failed"))
                st.query_params.clear()
                return False

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                st.error(_t_gcb("auth_google_no_token"))
                st.query_params.clear()
                return False

            user_resp = _req.get(_GOOGLE_USERINFO_URL, headers={
                "Authorization": f"Bearer {access_token}",
            }, timeout=10)

            if user_resp.status_code != 200:
                st.error(_t_gcb("auth_google_profile_failed"))
                st.query_params.clear()
                return False

            user_info = user_resp.json()
            g_email = user_info.get("email", "")
            g_name = user_info.get("name", "")

            if not g_email:
                st.error(_t_gcb("auth_google_no_email"))
                st.query_params.clear()
                return False

            g_picture = user_info.get("picture", "")
            _complete_oauth_login(g_email, g_name, "google", g_picture)

    except Exception as e:
        st.error(f"Google sign-in error: {e}")
        st.query_params.clear()
        return False

    return True


def _handle_github_callback(code: str):
    """Complete GitHub OAuth login."""
    _gh_id, _gh_secret = get_github_credentials()
    if not _gh_id or not _gh_secret:
        st.query_params.clear()
        return False

    try:
        import requests as _req
        from utils.i18n import t as _t_ghcb
        with st.spinner(_t_ghcb("auth_signing_in_github")):
            # Exchange code for access token
            token_resp = _req.post(_GITHUB_TOKEN_URL, data={
                "code": code,
                "client_id": _gh_id,
                "client_secret": _gh_secret,
            }, headers={"Accept": "application/json"}, timeout=10)

            if token_resp.status_code != 200:
                st.error(_t_ghcb("auth_github_failed"))
                st.query_params.clear()
                return False

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                _err = token_data.get("error_description", _t_ghcb("auth_github_no_token"))
                st.error(f"{_t_ghcb('auth_github_failed')}: {_err}")
                st.query_params.clear()
                return False

            # Fetch user profile
            user_resp = _req.get(_GITHUB_USERINFO_URL, headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }, timeout=10)

            if user_resp.status_code != 200:
                st.error(_t_ghcb("auth_github_profile_failed"))
                st.query_params.clear()
                return False

            gh_info = user_resp.json()
            gh_name = gh_info.get("name") or gh_info.get("login", "")
            gh_email = gh_info.get("email", "")

            # If email is private, fetch from /user/emails
            if not gh_email:
                emails_resp = _req.get(_GITHUB_EMAILS_URL, headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                }, timeout=10)
                if emails_resp.status_code == 200:
                    emails_list = emails_resp.json()
                    # Pick primary verified email
                    primary = next((e for e in emails_list if e.get("primary") and e.get("verified")), None)
                    if primary:
                        gh_email = primary["email"]
                    elif emails_list:
                        gh_email = emails_list[0].get("email", "")

            if not gh_email:
                st.error(_t_ghcb("auth_github_no_email"))
                st.query_params.clear()
                return False

            gh_avatar = gh_info.get("avatar_url", "")
            _complete_oauth_login(gh_email, gh_name, "github", gh_avatar)

    except Exception as e:
        st.error(f"GitHub sign-in error: {e}")
        st.query_params.clear()
        return False

    return True


def _complete_oauth_login(email: str, name: str, provider: str, avatar_url: str = ""):
    """Finish OAuth login (shared by Google and GitHub)."""
    user = login_oauth_user(email, name, provider)
    st.session_state.authenticated = True
    st.session_state.user_id = user["id"]
    st.session_state.user_name = user.get("name", "")
    st.session_state.user_email = user["email"]
    st.session_state.auth_method = provider
    st.session_state.user_avatar_url = avatar_url
    st.session_state.login_time = datetime.now().isoformat()
    st.session_state.remember_me = True
    set_user_context(user["id"])
    # Create persistent session token
    from utils.auth import create_session_token
    _token = create_session_token(user["id"], user["email"], user.get("name", ""), provider, True)
    st.session_state.fk_session_token = _token
    st.query_params.clear()
    st.rerun()


def _show_login_page():
    """Render the full-screen login / register / reset page."""
    from utils.i18n import t as _t_auth
    view = st.session_state.get("auth_view", "login")

    # Centered header
    st.markdown(
        '<div style="text-align:center;padding:2.5rem 0 1rem;">'
        ''
        '<div class="fk-logo" style="font-size:1.8rem;margin-bottom:0.2rem;">FinanceKit</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if view == "login":
            st.markdown(
                '<div style="text-align:center;margin-bottom:1rem;">'
                f'<div style="color:var(--fk-text);font-size:1.3rem;font-weight:600;">{_t_auth("welcome_back")}</div>'
                f'<div style="color:var(--fk-text-muted);font-size:0.9rem;">{_t_auth("sign_in_to_account")}</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            # OAuth sign-in buttons (Google + GitHub)
            _has_oauth = _oauth_sign_in_buttons()

            if _has_oauth:
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:8px;margin:1rem 0;">'
                    '<div style="flex:1;height:1px;background:var(--fk-border);"></div>'
                    f'<span style="color:var(--fk-text-muted);font-size:0.82rem;">{_t_auth("auth_or_sign_in_email")}</span>'
                    '<div style="flex:1;height:1px;background:var(--fk-border);"></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with st.form("login_form"):
                email = st.text_input(_t_auth("email"), placeholder="you@example.com")
                password = st.text_input(_t_auth("password"), type="password")
                remember = st.checkbox(_t_auth("remember_me"))
                if st.form_submit_button(_t_auth("sign_in"), type="primary", width='stretch'):
                    # Rate limiting check (v5.7)
                    from utils.security import is_account_locked, record_failed_login, clear_failed_attempts, log_audit_event, get_remaining_attempts
                    _locked, _lock_msg = is_account_locked(email)
                    if _locked:
                        st.error(f"{_t_auth('auth_account_locked')} — {_lock_msg}")
                    else:
                        success, result = login_user(email, password)
                        if success:
                            clear_failed_attempts(email)
                            log_audit_event(result["id"], "login_success", f"Email: {email}")
                            st.session_state.authenticated = True
                            st.session_state.user_id = result["id"]
                            st.session_state.user_name = result.get("name", "")
                            st.session_state.user_email = result["email"]
                            st.session_state.auth_method = result.get("auth_method", "local")
                            st.session_state.login_time = datetime.now().isoformat()
                            st.session_state.remember_me = remember
                            set_user_context(result["id"])
                            # Create persistent session token
                            from utils.auth import create_session_token
                            _token = create_session_token(
                                result["id"], result["email"],
                                result.get("name", ""), "local", remember
                            )
                            st.session_state.fk_session_token = _token
                            st.rerun()
                        else:
                            remaining = record_failed_login(email)
                            log_audit_event("", "login_failed", f"Email: {email}")
                            if remaining > 0:
                                st.error(f"{result} ({remaining} {_t_auth('auth_attempts_remaining')})")
                            else:
                                st.error(_t_auth("auth_account_locked_30min"))

            # Forgot password link
            st.markdown(
                '<div style="text-align:right;margin-top:-0.5rem;margin-bottom:0.5rem;">',
                unsafe_allow_html=True,
            )
            if st.button(_t_auth("forgot_password"), key="forgot_pw_link"):
                st.session_state.auth_view = "reset"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # Create account link
            st.markdown(
                '<div style="text-align:center;margin-top:1rem;">'
                f'<span style="color:var(--fk-text-muted);font-size:0.9rem;">{_t_auth("dont_have_account")}</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button(_t_auth("auth_create_one"), width='stretch', key="create_acct_link"):
                st.session_state.auth_view = "register"
                st.rerun()

        elif view == "register":
            st.markdown(
                '<div style="text-align:center;margin-bottom:1rem;">'
                f'<div style="color:var(--fk-text);font-size:1.3rem;font-weight:600;">{_t_auth("create_account")}</div>'
                f'<div style="color:var(--fk-text-muted);font-size:0.9rem;">{_t_auth("start_managing")}</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            # OAuth sign-up buttons (also creates account automatically)
            _has_oauth = _oauth_sign_in_buttons()

            if _has_oauth:
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:8px;margin:1rem 0;">'
                    '<div style="flex:1;height:1px;background:var(--fk-border);"></div>'
                    f'<span style="color:var(--fk-text-muted);font-size:0.82rem;">{_t_auth("auth_or_sign_up_email")}</span>'
                    '<div style="flex:1;height:1px;background:var(--fk-border);"></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with st.form("register_form"):
                name = st.text_input(_t_auth("display_name"), placeholder="Your name")
                email = st.text_input(_t_auth("email"), placeholder="you@example.com")
                password = st.text_input(_t_auth("auth_new_password"), type="password",
                                          help=_t_auth("auth_password_hint"))
                if password:
                    from utils.security import check_password_requirements
                    _reqs = check_password_requirements(password)
                    _req_labels = {
                        "length": _t_auth("auth_req_length"),
                        "number": _t_auth("auth_req_number"),
                        "upper_lower": _t_auth("auth_req_upper_lower"),
                        "special": _t_auth("auth_req_special"),
                        "not_common": _t_auth("auth_req_not_common"),
                    }
                    _req_html = ""
                    for _rk, _rl in _req_labels.items():
                        _check = "+" if _reqs.get(_rk) else "-"
                        _color = "var(--fk-success)" if _reqs.get(_rk) else "var(--fk-text-muted)"
                        _req_html += f'<div style="font-size:0.78rem;color:{_color};">{_check} {_rl}</div>'
                    st.markdown(_req_html, unsafe_allow_html=True)
                confirm = st.text_input(_t_auth("auth_confirm_password"), type="password")
                if st.form_submit_button(_t_auth("create_account"), type="primary", width='stretch'):
                    # Validate email
                    _email_clean = email.strip()
                    from utils.security import password_meets_requirements as _pw_ok
                    if not _email_clean or "@" not in _email_clean or "." not in _email_clean.split("@")[-1]:
                        st.error(_t_auth("auth_invalid_email"))
                    elif password != confirm:
                        st.error(_t_auth("auth_passwords_no_match"))
                    elif not _pw_ok(password):
                        st.error(_t_auth("auth_password_too_weak"))
                    else:
                        success, msg = register_user(_email_clean, password, name)
                        if success:
                            with st.spinner(_t_auth("auth_signing_in")):
                                # Auto-login after registration
                                login_success, login_result = login_user(_email_clean, password)
                                if login_success:
                                    st.session_state.authenticated = True
                                    st.session_state.user_id = login_result["id"]
                                    st.session_state.user_name = login_result.get("name", "")
                                    st.session_state.user_email = login_result["email"]
                                    st.session_state.auth_method = "local"
                                    st.session_state.login_time = datetime.now().isoformat()
                                    st.session_state.remember_me = False
                                    set_user_context(login_result["id"])
                                    # Create persistent session token
                                    from utils.auth import create_session_token
                                    _reg_token = create_session_token(
                                        login_result["id"], login_result["email"],
                                        login_result.get("name", ""), "local", False
                                    )
                                    st.session_state.fk_session_token = _reg_token
                            st.toast(_t_auth("auth_account_created"))
                            st.rerun()
                        else:
                            st.error(msg)

            st.markdown(
                '<div style="text-align:center;margin-top:0.5rem;">'
                f'<span style="color:var(--fk-text-muted);font-size:0.9rem;">{_t_auth("already_have_account")}</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"\u2190 {_t_auth('sign_in')}", width='stretch'):
                st.session_state.auth_view = "login"
                st.rerun()

        elif view == "reset":
            st.markdown(f"### {_t_auth('auth_reset_password')}")
            reset_step = st.session_state.get("reset_step", 1)

            if reset_step == 1:
                with st.form("reset_email_form"):
                    email = st.text_input(_t_auth("email"), placeholder="you@example.com")
                    if st.form_submit_button(_t_auth("auth_send_reset_token"), type="primary", width='stretch'):
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
                st.caption(_t_auth("auth_reset_token_caption"))
                with st.form("reset_password_form"):
                    token = st.text_input(_t_auth("auth_reset_token"))
                    new_pass = st.text_input(_t_auth("auth_new_password"), type="password")
                    confirm_pass = st.text_input(_t_auth("auth_confirm_password"), type="password")
                    if st.form_submit_button(_t_auth("auth_reset_password"), type="primary", width='stretch'):
                        if new_pass != confirm_pass:
                            st.error(_t_auth("auth_passwords_no_match"))
                        else:
                            success, msg = reset_password_with_token(
                                st.session_state.get("reset_email", ""), token, new_pass
                            )
                            if success:
                                st.toast(msg)
                                st.session_state.reset_step = 1
                                st.session_state.auth_view = "login"
                                st.rerun()
                            else:
                                st.error(msg)

            if st.button(f"\u2190 {_t_auth('auth_back_to_sign_in')}", width='stretch', key="back_reset"):
                st.session_state.auth_view = "login"
                st.session_state.reset_step = 1
                st.rerun()

    st.stop()


def _sign_out():
    """Sign out the current user."""
    # Revoke persistent session token
    _token = st.session_state.get("fk_session_token")
    if _token:
        from utils.auth import revoke_session_token
        revoke_session_token(_token)
    clear_user_context()
    for key in ["authenticated", "user_id", "user_name", "user_email",
                "auth_method", "login_time", "remember_me", "fk_session_token"]:
        st.session_state.pop(key, None)
    # Clear module caches
    for key in list(st.session_state.keys()):
        if key not in ("fk_theme", "sidebar_nav", "nav_index"):
            st.session_state.pop(key, None)
    # Inject JS to clear localStorage token
    st.components.v1.html('<script>localStorage.removeItem("fk_session");</script>', height=0)
    st.rerun()


# Handle OAuth callback (Google/GitHub) before auth gate
if not st.session_state.get("authenticated"):
    _handle_oauth_callback()

# ── Persistent session: auto-login from stored token ─────────────────
if not st.session_state.get("authenticated"):
    # Check if there's a session token in query params (from localStorage JS)
    _stored_token = st.query_params.get("_session_token")
    if _stored_token:
        from utils.auth import validate_session_token
        _sess = validate_session_token(_stored_token)
        if _sess:
            st.session_state.authenticated = True
            st.session_state.user_id = _sess["user_id"]
            st.session_state.user_name = _sess.get("name", "")
            st.session_state.user_email = _sess["email"]
            st.session_state.auth_method = _sess.get("auth_method", "local")
            st.session_state.login_time = _sess.get("login_time", datetime.now().isoformat())
            st.session_state.remember_me = _sess.get("remember", False)
            st.session_state.fk_session_token = _stored_token
            set_user_context(_sess["user_id"])
        # Always remove token from URL for cleanliness
        st.query_params.pop("_session_token", None)
        if st.session_state.get("authenticated"):
            st.rerun()

# Inject JS to persist/restore session token via localStorage
_js_token = st.session_state.get("fk_session_token", "")
_fk_checked = "_fk_checked" in st.query_params
# Clean up helper query params immediately
if _fk_checked:
    st.query_params.pop("_fk_checked", None)
st.components.v1.html(f"""
<script>
(function() {{
    var token = "{_js_token}";
    if (token) {{
        localStorage.setItem('fk_session', token);
    }}
    // On page load, if not authenticated and haven't checked yet, try localStorage
    var params = new URLSearchParams(window.location.search);
    if (!token && !params.has('_session_token') && !params.has('_fk_checked')) {{
        var stored = localStorage.getItem('fk_session');
        var url = new URL(window.location);
        if (stored) {{
            url.searchParams.set('_session_token', stored);
        }} else {{
            url.searchParams.set('_fk_checked', '1');
        }}
        window.location.replace(url.toString());
    }}
}})();
</script>
""", height=0)

# Auth gate: authenticated users get full app, others see landing or login page
if st.session_state.get("authenticated"):
    # Check session expiry
    login_time = st.session_state.get("login_time", "")
    remember = st.session_state.get("remember_me", False)
    if not is_session_valid(login_time, remember):
        st.toast(t("session_expired_toast"))
        _sign_out()
    else:
        # Set user context for data isolation
        user_id = st.session_state.get("user_id", "")
        if user_id:
            set_user_context(user_id)
        # ── Rebuild NAV_OPTIONS now that user_id is known ──
        # This is critical: on first load, NAV_OPTIONS was built before auth,
        # so user-specific module toggles weren't applied. Rebuild here.
        NAV_OPTIONS = _build_nav_options()
        if st.session_state.nav_index >= len(NAV_OPTIONS):
            st.session_state.nav_index = 0
        # ── Re-process nav_target with correct NAV_OPTIONS ──
        if "nav_target" in st.session_state and st.session_state.nav_target:
            _post_auth_target = st.session_state.nav_target
            st.session_state.nav_target = None
            if _post_auth_target in NAV_OPTIONS:
                st.session_state.nav_index = NAV_OPTIONS.index(_post_auth_target)
        # ── Reload user preferences for authenticated user ──
        _user_accent = _load_accent_color()
        if _user_accent != st.session_state.get("fk_accent_color"):
            st.session_state.fk_accent_color = _user_accent
        _u_font, _u_hc, _u_lang = _load_ui_prefs()
        st.session_state.fk_font_size = _u_font
        st.session_state.fk_high_contrast = _u_hc
        if _u_lang and _u_lang != "en":
            try:
                from utils.i18n import set_language as _set_lang_auth
                _set_lang_auth(_u_lang)
            except Exception:
                pass
        # ── Auto-sync: create backup if sync is enabled and due ──
        try:
            from utils.sync import should_auto_sync, create_sync_bundle, mark_synced
            _sync_uid = st.session_state.get("user_id")
            if should_auto_sync(_sync_uid):
                _bundle = create_sync_bundle(_sync_uid)
                if _bundle:
                    # Save backup bundle to data dir
                    _backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "backups")
                    os.makedirs(_backup_dir, exist_ok=True)
                    _backup_name = f"auto_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                    with open(os.path.join(_backup_dir, _backup_name), "wb") as _bf:
                        _bf.write(_bundle)
                    mark_synced(_sync_uid)
                    # Clean old auto-sync backups (keep last 10)
                    _existing = sorted(
                        [f for f in os.listdir(_backup_dir) if f.startswith("auto_sync_")],
                        reverse=True,
                    )
                    for _old in _existing[10:]:
                        try:
                            os.remove(os.path.join(_backup_dir, _old))
                        except Exception:
                            pass
        except Exception:
            pass

        # Session expiry warning (1 hour before expiry)
        _hrs_left = session_hours_remaining(login_time, remember)
        if 0 < _hrs_left <= 1:
            st.warning(
                f"Your session expires in {int(_hrs_left * 60)} minutes. "
                "Click to extend.",
            )
            if st.button("Extend Session", key="extend_session"):
                st.session_state.login_time = datetime.now().isoformat()
                st.toast(t("session_extended_toast"))
                st.rerun()
else:
    # Not authenticated — show login page or landing page
    if st.session_state.get("show_auth"):
        _show_login_page()
    else:
        _show_landing_page()


# --- Browser push notification permission (v5.4) ---
from utils.notifications import request_push_permission_js as _push_perm_js
st.markdown(_push_perm_js(), unsafe_allow_html=True)

# --- Notification startup tasks ---
from utils.notifications import clear_old as _notif_clean_old, check_and_send_digest as _notif_check_digest

if "notif_startup_done" not in st.session_state:
    _notif_clean_old(30)
    _startup_settings = load_json("settings.json", default={}) if "load_json" in dir() else {}
    try:
        from utils.data_persistence import load_json as _dp_load
        _startup_settings = _dp_load("settings.json", default={})
        _notif_check_digest(_startup_settings)
        # Restore saved language preference
        _saved_lang = _startup_settings.get("language", "en")
        if _saved_lang and _saved_lang != st.session_state.get("language", "en"):
            from utils.i18n import set_language as _set_lang
            _set_lang(_saved_lang)
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

    # Auto-import folder check
    try:
        _ai_settings = _startup_settings.get("auto_import", {})
        if _ai_settings.get("enabled") and _ai_settings.get("folder"):
            import os as _ai_os
            _ai_folder = _ai_settings["folder"]
            _ai_last = _ai_settings.get("last_check", "")
            if _ai_os.path.isdir(_ai_folder):
                _ai_files = [f for f in _ai_os.listdir(_ai_folder)
                             if f.lower().endswith((".csv", ".ofx", ".qfx"))]
                if _ai_files:
                    # Check for files newer than last check
                    _new_files = []
                    for _aif in _ai_files:
                        _aifp = _ai_os.path.join(_ai_folder, _aif)
                        _mtime = datetime.fromtimestamp(_ai_os.path.getmtime(_aifp)).isoformat()
                        if not _ai_last or _mtime > _ai_last:
                            _new_files.append(_aif)
                    if _new_files:
                        from utils.notifications import create_notification
                        create_notification(
                            "info", "reports",
                            f"New files detected: {len(_new_files)} importable file(s)",
                            f"Found in {_ai_folder}: {', '.join(_new_files[:3])}"
                            + (f" and {len(_new_files) - 3} more" if len(_new_files) > 3 else ""),
                        )
                        # Update last check time
                        _ai_settings["last_check"] = datetime.now().isoformat()
                        _startup_settings["auto_import"] = _ai_settings
                        try:
                            _dp_save = _dp_load.__module__ and save_json
                        except Exception:
                            pass
                        try:
                            save_json("settings.json", _startup_settings)
                        except Exception:
                            pass
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
    # v5.9: Log startup time on first load
    try:
        _startup_ms = int((_time.perf_counter() - _STARTUP_T) * 1000)
        _app_log = _get_logger("app")
        _app_log.info(f"Startup completed in {_startup_ms}ms")
    except Exception:
        pass


# --- Data helpers (v5.9: cached loading) ---
def _data_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@st.cache_data(ttl=300, show_spinner=False)
def _cached_load(filepath: str, _mtime: float):
    """Load JSON with st.cache_data; busted by file mtime change."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_json(filename, default=None):
    fp = os.path.join(_data_dir(), filename)
    if not os.path.exists(fp):
        return default
    try:
        mtime = os.path.getmtime(fp)
    except OSError:
        return default
    data = _cached_load(fp, mtime)
    return data if data is not None else default


_MODULE_DEFS = [
    {"key": "budget", "icon": "$", "t_key": "budget_tracker"},
    {"key": "goals", "icon": "G", "t_key": "goal_tracker"},
    {"key": "receipts", "icon": "R", "t_key": "receipt_scanner"},
    {"key": "portfolio", "icon": "I", "t_key": "portfolio_tracker"},
    {"key": "reports", "icon": "P", "t_key": "report_generator"},
    {"key": "freelance", "icon": "F", "t_key": "freelance_dashboard"},
    {"key": "subscriptions", "icon": "S", "t_key": "subscription_auditor"},
]

ALL_MODULE_KEYS = [m["key"] for m in _MODULE_DEFS]


def _get_all_modules():
    """Build ALL_MODULES list with translated names."""
    from utils.i18n import t as _t
    result = []
    for m in _MODULE_DEFS:
        name = _t(m["t_key"])
        result.append({
            "key": m["key"],
            "icon": m["icon"],
            "name": name,
            "nav": f"{m['icon']} {name}",
        })
    return result


# Backwards compat alias
ALL_MODULES = _MODULE_DEFS  # key list stays the same


def _get_enabled_modules() -> list[str]:
    """Return list of enabled module keys from settings (always fresh read)."""
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
    from utils.i18n import t as _t_ins
    sym = get_currency_symbol()
    if goals:
        active = [g for g in goals if g.get("current", 0) < g.get("target", 1)]
        if active:
            closest = min(active, key=lambda g: g["target"] - g["current"])
            remaining = closest["target"] - closest["current"]
            return _t_ins("dash_insight_goal_close", amount=format_currency_int(remaining), name=closest['name'])
    if budgets and any(float(v) > 0 for v in budgets.values()):
        top_cat = max(budgets, key=lambda k: float(budgets.get(k, 0)))
        return _t_ins("dash_insight_top_budget", category=top_cat, amount=format_currency_int(float(budgets[top_cat])))
    if receipts:
        return _t_ins("dash_insight_receipts_scanned", n=len(receipts))
    if stmt_data:
        return _t_ins("dash_insight_stmt_transactions", n=len(stmt_data))
    return _t_ins("dash_insight_empty")


# --- Welcome dialog (5-step onboarding) ---
# --- Mobile Quick Entry dialog ---
@st.dialog("Quick Entry", width="small")
def show_quick_entry():
    """Mobile-friendly compact expense entry form."""
    from utils.data_persistence import load_json as _qe_load, save_json as _qe_save
    from modules.budget_tracker import CATEGORIES, TRANSACTIONS_FILE
    import uuid

    amount = st.number_input("Amount", min_value=0.01, value=10.00, step=1.0, format="%.2f",
                              key="qe_amount")
    # Show recent/favorite categories first
    category = st.selectbox("Category", CATEGORIES, key="qe_category")
    description = st.text_input("Description (optional)", placeholder="Coffee, lunch, etc.",
                                 key="qe_desc")
    entry_date = st.date_input("Date", value=datetime.now().date(), key="qe_date")

    if st.button("Save Expense", type="primary", width='stretch', key="qe_save"):
        txns = _qe_load(TRANSACTIONS_FILE, default=[])
        txns.append({
            "date": entry_date.isoformat(),
            "description": description or category,
            "amount": amount,
            "category": category,
            "month": entry_date.strftime("%Y-%m"),
        })
        _qe_save(TRANSACTIONS_FILE, txns)
        try:
            from utils.activity_log import log_activity
            log_activity("added", "budget_tracker", f"Quick entry: {category} {amount:.2f}")
        except Exception:
            pass
        st.toast(f"Saved {category}: ${amount:.2f}")
        # Clear cached budget transactions so it reloads
        st.session_state.pop("budget_transactions", None)
        st.rerun()


@st.dialog("Welcome to FinanceKit", width="large")
def show_welcome_dialog():
    step = st.session_state.get("setup_step", 1)
    total_steps = 5
    _user_name = st.session_state.get("user_name", "")

    # Progress dots
    dots = " ".join("●" if i + 1 == step else "○" for i in range(total_steps))
    st.markdown(
        f'<div style="text-align:center;color:var(--fk-accent);font-size:0.9rem;letter-spacing:4px;margin-bottom:0.5rem;">{dots}</div>',
        unsafe_allow_html=True,
    )

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
        _greeting = f"Welcome, {_user_name}!" if _user_name else "Welcome!"
        st.markdown(
            f'<div style="text-align:center;padding:1rem 0;">'
            f'<div class="logo-icon" style="width:48px;height:48px;border-radius:14px;font-size:1.4rem;font-weight:800;color:#fff;display:inline-flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--fk-accent),var(--fk-accent-light));">F</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:var(--fk-text);margin:0.5rem 0;">'
            f'{_greeting}</div>'
            f'<div style="color:var(--fk-text-muted);font-size:1rem;">'
            f"Let's set up your finances in 2 minutes.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("Get Started →", type="primary", width='stretch'):
            st.session_state.setup_step = 2
            st.rerun()
        if st.button("Skip", key="ob1_skip"):
            _finish_onboarding()

    elif step == 2:
        st.markdown("### Currency & Date Format")
        from modules.settings import CURRENCY_OPTIONS, DATE_FORMAT_OPTIONS
        pc1, pc2 = st.columns(2)
        with pc1:
            currency_choice = st.selectbox("Currency", list(CURRENCY_OPTIONS.keys()), key="ob_currency")
        with pc2:
            date_fmt = st.selectbox("Date Format", DATE_FORMAT_OPTIONS, key="ob_date_fmt")

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("← Back", width='stretch', key="ob2_back"):
                st.session_state.setup_step = 1
                st.rerun()
        with c2:
            if st.button("Skip", key="ob2_skip"):
                _finish_onboarding()
        with c3:
            if st.button("Next →", type="primary", width='stretch', key="ob2_next"):
                from utils.data_persistence import load_json as _dl, save_json as _ds
                s = _dl("settings.json", default={})
                s["currency"] = CURRENCY_OPTIONS[currency_choice]
                s["date_format"] = date_fmt
                _ds("settings.json", s)
                st.session_state.setup_step = 3
                st.rerun()

    elif step == 3:
        st.markdown("### What do you want to track?")
        st.caption("Select the modules you'd like. You can change this anytime.")
        if "ob_enabled_modules" not in st.session_state:
            st.session_state.ob_enabled_modules = ALL_MODULE_KEYS.copy()

        # Card-style checkboxes
        _default_checked = {"budget", "goals", "portfolio"}
        for m in _get_all_modules():
            val = st.checkbox(
                f"{m['icon']} {m['name']}",
                value=m["key"] in st.session_state.ob_enabled_modules,
                key=f"ob_mod_{m['key']}",
            )
            if val and m["key"] not in st.session_state.ob_enabled_modules:
                st.session_state.ob_enabled_modules.append(m["key"])
            elif not val and m["key"] in st.session_state.ob_enabled_modules:
                st.session_state.ob_enabled_modules.remove(m["key"])

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("← Back", width='stretch', key="ob3_back"):
                st.session_state.setup_step = 2
                st.rerun()
        with c2:
            if st.button("Skip", key="ob3_skip"):
                _finish_onboarding()
        with c3:
            if st.button("Next →", type="primary", width='stretch', key="ob3_next"):
                st.session_state.setup_step = 4
                st.rerun()

    elif step == 4:
        st.markdown("### Import existing data?")

        ic1, ic2, ic3 = st.columns(3)
        with ic1:
            st.markdown(
                '<div class="module-card"><div class="icon"></div>'
                '<h3>Upload CSV</h3><p>Import a bank statement</p></div>',
                unsafe_allow_html=True,
            )
            uploaded = st.file_uploader("CSV", type=["csv"], key="ob_csv", label_visibility="collapsed")
            if uploaded:
                st.success(f"'{uploaded.name}' ready!")
                st.session_state["welcome_csv_pending"] = True
        with ic2:
            st.markdown(
                '<div class="module-card"><div class="icon">+</div>'
                '<h3>Start Fresh</h3><p>Begin with a clean slate</p></div>',
                unsafe_allow_html=True,
            )
        with ic3:
            st.markdown(
                '<div class="module-card"><div class="icon"></div>'
                '<h3>From Backup</h3><p>Restore a ZIP backup</p></div>',
                unsafe_allow_html=True,
            )
            import_file = st.file_uploader("ZIP", type=["zip"], key="ob_zip", label_visibility="collapsed")
            if import_file:
                try:
                    import zipfile, io
                    os.makedirs(_data_dir(), exist_ok=True)
                    with zipfile.ZipFile(io.BytesIO(import_file.read()), "r") as zf:
                        for name in zf.namelist():
                            if name.endswith(".json"):
                                zf.extract(name, _data_dir())
                    st.success(t("backup_restored_toast"))
                except Exception as e:
                    st.error(f"Import failed: {e}")

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("← Back", width='stretch', key="ob4_back"):
                st.session_state.setup_step = 3
                st.rerun()
        with c2:
            if st.button("Skip", key="ob4_skip"):
                _finish_onboarding()
        with c3:
            if st.button("Next →", type="primary", width='stretch', key="ob4_next"):
                st.session_state.setup_step = 5
                st.rerun()

    elif step == 5:
        st.markdown(
            '<div style="text-align:center;padding:1rem 0;">'
            '<div style="font-size:3rem;"></div>'
            '<div style="font-size:1.5rem;font-weight:700;color:var(--fk-text);margin:0.5rem 0;">'
            "You're all set!</div>"
            '<div style="color:var(--fk-text-muted);font-size:1rem;">'
            "Your financial toolkit is ready. Let's go.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.balloons()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back", width='stretch', key="ob5_back"):
                st.session_state.setup_step = 4
                st.rerun()
        with c2:
            if st.button("Go to Dashboard", type="primary", width='stretch', key="ob5_finish"):
                _finish_onboarding()


# --- Sidebar ---
with st.sidebar:
    st.markdown(
        f'<div class="fk-logo">'
        f'<span class="logo-icon">F</span>'
        f'<span class="logo-text">FinanceKit</span>'
        f'<span class="logo-badge">v{APP_VERSION}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="fk-logo-line"></div>', unsafe_allow_html=True)

    # User display when authenticated
    if st.session_state.get("authenticated"):
        _uname = st.session_state.get("user_name", "User")
        _uemail = st.session_state.get("user_email", "")
        _avatar_url = st.session_state.get("user_avatar_url", "")
        _initial = _uname[0].upper() if _uname else "U"
        if _avatar_url:
            _avatar_html = (
                f'<img src="{_avatar_url}" '
                f'style="width:30px;height:30px;border-radius:50%;object-fit:cover;" '
                f'referrerpolicy="no-referrer" alt="{_initial}" />'
            )
        else:
            _avatar_html = (
                f'<div style="width:30px;height:30px;border-radius:50%;background:var(--fk-accent);'
                f'display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:0.85rem;">{_initial}</div>'
            )
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:0.3rem;">'
            f'{_avatar_html}'
            f'<div><div style="color:var(--fk-text);font-weight:600;font-size:0.85rem;">{_uname}</div>'
            f'<div style="color:var(--fk-text-muted);font-size:0.7rem;">{_uemail}</div></div></div>',
            unsafe_allow_html=True,
        )

    # Notification bell
    from utils.notifications import get_unread_count, get_notifications, mark_read, mark_all_read, clear_all as _notif_clear_all, group_notifications, relative_time, notification_icon
    _unread = get_unread_count()
    _bell_label = f"🔔 {_unread}" if _unread > 0 else "🔔"

    if st.button(_bell_label, key="notif_toggle", help=f"{_unread} unread notifications"):
        st.session_state["show_notif_panel"] = not st.session_state.get("show_notif_panel", False)
        st.rerun()

    # Notification panel (toggleable)
    if st.session_state.get("show_notif_panel", False):
        with st.container():
            if _unread > 0:
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("Mark all read", key="notif_mark_all", width='stretch'):
                        mark_all_read()
                        st.rerun()
                with bc2:
                    if st.button("Clear all", key="notif_clear_all", width='stretch'):
                        _notif_clear_all()
                        st.rerun()

            _all_notifs = get_notifications(limit=20)
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
                            if st.button(f"Go to {_action.replace('_', ' ').title()}", key=f"notif_go_{_n['id']}", width='stretch'):
                                mark_read(_n["id"])
                                _action_map = {
                                    "budget_tracker": "Budget Tracker",
                                    "goal_tracker": "Goal Tracker",
                                    "portfolio_tracker": "Portfolio Tracker",
                                    "subscription_auditor": "Subscription Auditor",
                                    "job_tracker": "Freelance Dashboard",
                                    "receipt_scanner": "Receipt Scanner",
                                    "report_generator": "Report Generator",
                                }
                                _nav = _action_map.get(_action, "")
                                if _nav:
                                    st.session_state.nav_target = _nav
                                st.rerun()
            else:
                st.caption("No notifications yet.")
            st.markdown("---")

    # Global search
    search_query = st.text_input("Search...", key="global_search", label_visibility="collapsed",
                                  placeholder="Search...")
    if search_query and len(search_query.strip()) >= 2:
        from utils.search import search_all
        results = search_all(search_query)
        if results:
            for r in results[:6]:
                if st.button(
                    f"{r['icon']} {r['title']}",
                    key=f"sr_{r['title'][:20]}_{r['module']}",
                    width='stretch',
                    help=f"{r['module']} · {r['detail']}",
                ):
                    st.session_state.nav_target = r["nav"]
                    st.rerun()
        else:
            st.caption("No results found.")

    st.markdown("---")

    # Styled navigation (v4.7) — radio buttons restyled via CSS
    st.markdown('<div class="nav-group">NAVIGATE</div>', unsafe_allow_html=True)

    # Translate nav labels while keeping internal keys in English
    from utils.i18n import t as _t
    _nav_t_map = {
        "Dashboard": _t('dashboard'),
        "Receipt Scanner": _t('receipt_scanner'),
        "Portfolio Tracker": _t('portfolio_tracker'),
        "Report Generator": _t('report_generator'),
        "Freelance Dashboard": _t('freelance_dashboard'),
        "Subscription Auditor": _t('subscription_auditor'),
        "Budget Tracker": _t('budget_tracker'),
        "Goal Tracker": _t('goal_tracker'),
        "Settings": _t('settings'),
    }

    page = st.radio("Navigate", NAV_OPTIONS, index=st.session_state.nav_index,
                     label_visibility="collapsed", key="sidebar_nav",
                     format_func=lambda x: _nav_t_map.get(x, x))
    st.session_state.nav_index = NAV_OPTIONS.index(page)

    st.markdown("---")

    # Cloud sync status indicator (v5.3)
    try:
        from utils.sync import get_sync_status, is_sync_enabled
        _user_id_sync = st.session_state.get("user_id")
        _sync_st = get_sync_status(_user_id_sync)
        if is_sync_enabled(_user_id_sync):
            st.markdown(
                f'<div style="font-size:0.75rem;color:var(--fk-text-muted);padding:4px 0;">'
                f'{_sync_st["icon"]} {_sync_st["label"]}</div>',
                unsafe_allow_html=True,
            )
        # Don't show anything if sync is disabled — cleaner sidebar
    except Exception:
        pass

    # Footer info
    st.markdown(
        f'<div style="font-size:0.7rem;color:var(--fk-footer-text);line-height:1.5;">'
        f'v{APP_VERSION} · Private by design. No tracking, no telemetry.</div>',
        unsafe_allow_html=True,
    )

    # Sign out button (when authenticated)
    if st.session_state.get("authenticated"):
        if st.button(_t("sign_out"), key="sign_out", width='stretch'):
            _sign_out()

    # Keyboard shortcuts — JS injection (v4.7)
    _kb_nav_map = {str(i): nav for i, nav in enumerate(NAV_OPTIONS) if i < 10}
    _kb_js_cases = "\n".join(
        f'        case "{k}": target = "{v}"; break;'
        for k, v in _kb_nav_map.items()
    )
    st.components.v1.html(f"""
    <script>
    document.addEventListener('keydown', function(e) {{
        // Skip if user is typing in an input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
        let target = null;
        switch(e.key) {{
{_kb_js_cases}
        }}
        if (target) {{
            // Click the matching radio option in the sidebar
            const labels = document.querySelectorAll('section[data-testid="stSidebar"] .stRadio label');
            labels.forEach(label => {{
                if (label.textContent.trim() === target) {{
                    label.click();
                }}
            }});
        }}
    }});
    </script>
    """, height=0)


# --- "What's New" dialog (v6.0) ---
@st.dialog("What's New in FinanceKit", width="large")
def _show_whats_new():
    from utils.i18n import t as _t_wn
    _wn_items = [
        ("9.1", _t_wn("dash_wn_v91_title"), [
            _t_wn("dash_wn_v91_1"),
            _t_wn("dash_wn_v91_2"),
            _t_wn("dash_wn_v91_3"),
            _t_wn("dash_wn_v91_4"),
            _t_wn("dash_wn_v91_5"),
        ]),
        ("8.7", _t_wn("dash_wn_v87_title"), [
            _t_wn("dash_wn_v87_1"),
            _t_wn("dash_wn_v87_2"),
            _t_wn("dash_wn_v87_3"),
            _t_wn("dash_wn_v87_4"),
            _t_wn("dash_wn_v87_5"),
            _t_wn("dash_wn_v87_6"),
        ]),
        ("6.0", _t_wn("dash_wn_v60_title"), [
            _t_wn("dash_wn_v60_1"),
            _t_wn("dash_wn_v60_2"),
            _t_wn("dash_wn_v60_3"),
            _t_wn("dash_wn_v60_4"),
        ]),
        ("5.9", _t_wn("dash_wn_v59_title"), [
            _t_wn("dash_wn_v59_1"),
            _t_wn("dash_wn_v59_2"),
            _t_wn("dash_wn_v59_3"),
            _t_wn("dash_wn_v59_4"),
        ]),
        ("5.8", _t_wn("dash_wn_v58_title"), [
            _t_wn("dash_wn_v58_1"),
            _t_wn("dash_wn_v58_2"),
            _t_wn("dash_wn_v58_3"),
            _t_wn("dash_wn_v58_4"),
        ]),
        ("5.7", _t_wn("dash_wn_v57_title"), [
            _t_wn("dash_wn_v57_1"),
            _t_wn("dash_wn_v57_2"),
            _t_wn("dash_wn_v57_3"),
            _t_wn("dash_wn_v57_4"),
        ]),
    ]
    for _ver, _title, _bullets in _wn_items:
        st.markdown(f"**v{_ver} — {_title}**")
        for _b in _bullets:
            st.markdown(f"- {_b}")
        st.markdown("")
    if st.button(_t_wn("dash_got_it"), type="primary", width='stretch'):
        _s = _load_json("settings.json", default={})
        _s["last_seen_version"] = APP_VERSION
        from utils.data_persistence import save_json as _wn_save
        _wn_save("settings.json", _s)
        st.session_state.fk_whats_new_dismissed = True
        st.rerun()


# --- In-app help system (v6.0) ---
def _get_help_tips():
    from utils.i18n import t as _t_ht
    return {
        "dashboard": _t_ht("dash_help_dashboard"),
        "budget": _t_ht("dash_help_budget"),
        "goals": _t_ht("dash_help_goals"),
        "portfolio": _t_ht("dash_help_portfolio"),
        "receipts": _t_ht("dash_help_receipts"),
        "reports": _t_ht("dash_help_reports"),
        "freelance": _t_ht("dash_help_freelance"),
        "subscriptions": _t_ht("dash_help_subscriptions"),
    }
_HELP_TIPS = _get_help_tips()


# --- Page routing ---
if page == "Dashboard":
    if _is_first_launch() and not st.session_state.get("setup_complete"):
        show_welcome_dialog()

    # Show What's New if version changed
    _last_seen = _load_json("settings.json", default={}).get("last_seen_version", "")
    if _last_seen and _last_seen != APP_VERSION and not st.session_state.get("fk_whats_new_dismissed"):
        _show_whats_new()

    # Time-of-day greeting (translated)
    from utils.i18n import t as _t_dash
    hour = datetime.now().hour
    greeting = _t_dash("good_morning") if hour < 12 else _t_dash("good_afternoon") if hour < 18 else _t_dash("good_evening")
    _user_settings = _load_json("settings.json", default={})
    _user_name = _user_settings.get("user_name", "") or st.session_state.get("user_name", "")
    _greeting_name = f", {_user_name}" if _user_name else ""
    from utils.formatting import format_date
    _today_str = format_date(datetime.now().isoformat()[:10])

    # Header
    st.markdown(
        f'<div class="page-header-title">{greeting}{_greeting_name}</div>',
        unsafe_allow_html=True,
    )
    # Date + last updated
    _last_mod = 0
    for _fn in ["receipts.json", "portfolio.json", "budgets.json", "goals.json", "budget_transactions.json"]:
        _fp = os.path.join(_data_dir(), _fn)
        if os.path.exists(_fp):
            _last_mod = max(_last_mod, os.path.getmtime(_fp))
    _updated_ago = ""
    if _last_mod > 0:
        _mins_ago = int((datetime.now().timestamp() - _last_mod) / 60)
        if _mins_ago < 1:
            _updated_ago = _t_dash("just_now")
        elif _mins_ago < 60:
            _updated_ago = _t_dash("minutes_ago", n=_mins_ago)
        elif _mins_ago < 1440:
            _updated_ago = _t_dash("hours_ago", n=_mins_ago // 60)
        else:
            _updated_ago = _t_dash("days_ago", n=_mins_ago // 1440)
    st.markdown(
        f'<div class="page-header-sub">{_today_str}'
        f'{" · " + _t_dash("last_updated") + ": " + _updated_ago if _updated_ago else ""}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("")

    # Load data for widgets
    portfolio_data = _load_json("portfolio.json", default={"holdings": [], "alerts": []})
    budgets_data = _load_json("budgets.json", default={"budgets": {}})
    goals_data = _load_json("goals.json", default={"goals": []})
    if isinstance(goals_data, list):
        goals_data = {"goals": goals_data}
    receipts_data = _load_json("receipts.json", default=[])
    stmt_data = _load_json("statement_transactions.json", default=[])
    _budget_txns = _load_json("budget_transactions.json", default=[])
    _sub_decisions = _load_json("sub_decisions.json", default={})

    budgets = budgets_data.get("budgets", {})
    goals = goals_data.get("goals", [])
    holdings = portfolio_data.get("holdings", [])
    total_budget = sum(float(v) for v in budgets.values()) if budgets else 0

    # Check if user has ANY data at all
    _has_data = bool(holdings or goals or receipts_data or stmt_data or _budget_txns or
                     any(float(v) > 0 for v in budgets.values()))

    if not _has_data:
        # Empty state for new users
        st.markdown(
            f'<div class="fk-empty" style="padding:3rem 1.5rem;">'
            f'<div class="icon" style="font-size:3rem;"></div>'
            f'<div class="title" style="font-size:1.3rem;">{_t_dash("welcome_title")}</div>'
            f'<div style="color:var(--fk-text-muted);max-width:500px;margin:0.5rem auto;">{_t_dash("welcome_desc")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

    # Financial summary cards — 4 columns
    w1, w2, w3, w4 = st.columns(4)

    # Net Worth calculation
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
    _cash_balance = float(_user_settings.get("cash_balance", 0))
    _total_assets = _portfolio_value + _goals_saved + _cash_balance
    _liabilities = _load_json("liabilities.json", default=[])
    _total_liabilities = sum(float(l.get("balance", 0)) for l in _liabilities)
    _net_worth = _total_assets - _total_liabilities
    _nw_color = "var(--fk-success)" if _net_worth >= 0 else "var(--fk-danger)"

    with w1:
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">{_t_dash("net_worth")}</div>'
            f'<div class="widget-value" style="color:{_nw_color};">{format_currency_int(_net_worth)}</div>'
            f'<div class="widget-sub">{_t_dash("total_assets")}: {format_currency_int(_total_assets)}</div></div>',
            unsafe_allow_html=True,
        )

    # Monthly Spending
    _monthly_spent = 0
    _current_month = datetime.now().strftime("%Y-%m")
    for t in _budget_txns:
        if t.get("month", t.get("date", "")[:7]) == _current_month:
            _monthly_spent += float(t.get("amount", 0))
    _spend_pct = int((_monthly_spent / total_budget * 100) if total_budget > 0 else 0)

    with w2:
        _spend_sub = _t_dash("dash_budget_pct", pct=_spend_pct, budget=format_currency_int(total_budget)) if total_budget > 0 else _t_dash("set_budget")
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">{_t_dash("monthly_spending")}</div>'
            f'<div class="widget-value">{format_currency_int(_monthly_spent)}</div>'
            f'<div class="widget-sub">{_spend_sub}</div></div>',
            unsafe_allow_html=True,
        )

    # Savings Progress
    g_saved = sum(g.get("current", 0) for g in goals)
    g_target = sum(g.get("target", 0) for g in goals)
    _save_pct = int((g_saved / g_target * 100) if g_target > 0 else 0)

    with w3:
        _save_val = f"{_save_pct}%" if goals else "—"
        _save_sub = _t_dash("dash_savings_sub", saved=format_currency_int(g_saved), target=format_currency_int(g_target)) if goals else _t_dash("create_goal_hint")
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">{_t_dash("savings_progress")}</div>'
            f'<div class="widget-value">{_save_val}</div>'
            f'<div class="widget-sub">{_save_sub}</div></div>',
            unsafe_allow_html=True,
        )

    # Active Subscriptions
    _active_subs = sum(1 for v in _sub_decisions.values() if v == "Keep")
    _sub_total = 0  # Would need sub amounts; show count
    with w4:
        _sub_val = str(_active_subs) if _sub_decisions else "—"
        _sub_sub = _t_dash("dash_active_subs", n=_active_subs) if _sub_decisions else _t_dash("import_statement_hint")
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">{_t_dash("subscriptions")}</div>'
            f'<div class="widget-value">{_sub_val}</div>'
            f'<div class="widget-sub">{_sub_sub}</div></div>',
            unsafe_allow_html=True,
        )

    # Spending trend chart — daily cumulative this month vs last month
    if _budget_txns:
        import pandas as _sp_pd
        _sp_df = _sp_pd.DataFrame(_budget_txns)
        if "date" in _sp_df.columns and "amount" in _sp_df.columns:
            _sp_df["date"] = _sp_pd.to_datetime(_sp_df["date"], errors="coerce")
            _sp_df["amount"] = _sp_pd.to_numeric(_sp_df["amount"], errors="coerce")
            _sp_df = _sp_df.dropna(subset=["date", "amount"])
            _now = datetime.now()
            _cm = _now.month
            _cy = _now.year
            _lm = _cm - 1 if _cm > 1 else 12
            _ly = _cy if _cm > 1 else _cy - 1

            _this_month = _sp_df[(_sp_df["date"].dt.month == _cm) & (_sp_df["date"].dt.year == _cy)].copy()
            _last_month = _sp_df[(_sp_df["date"].dt.month == _lm) & (_sp_df["date"].dt.year == _ly)].copy()

            if not _this_month.empty:
                _this_month["day"] = _this_month["date"].dt.day
                _daily_this = _this_month.groupby("day")["amount"].sum().sort_index().cumsum()

                import plotly.graph_objects as _sp_go
                from utils.chart_config import apply_layout as _sp_apply
                _sp_fig = _sp_go.Figure()
                _sp_fig.add_trace(_sp_go.Scatter(
                    x=_daily_this.index, y=_daily_this.values,
                    mode="lines", name=_t_dash("this_month"),
                    line=dict(color=_accent, width=2),
                    fill="tozeroy", fillcolor="rgba(99,102,241,0.1)",
                ))
                if not _last_month.empty:
                    _last_month["day"] = _last_month["date"].dt.day
                    _daily_last = _last_month.groupby("day")["amount"].sum().sort_index().cumsum()
                    _sp_fig.add_trace(_sp_go.Scatter(
                        x=_daily_last.index, y=_daily_last.values,
                        mode="lines", name=_t_dash("last_month"),
                        line=dict(color="#94a3b8", width=1, dash="dash"),
                    ))
                _sp_apply(_sp_fig, height=220, margin=dict(t=10, b=30, l=10, r=10))
                _sp_fig.update_xaxes(title_text=_t_dash("dash_day_of_month"))
                st.markdown(f"**{_t_dash('spending_trend')}**")
                st.plotly_chart(_sp_fig, width='stretch')

    st.markdown("")

    # ── Spending Breakdown Donuts ─────────────────────────────────────
    if _budget_txns:
        import pandas as _db_pd
        _db_df = _db_pd.DataFrame(_budget_txns)
        if "category" in _db_df.columns and "amount" in _db_df.columns:
            _db_df["amount"] = _db_pd.to_numeric(_db_df["amount"], errors="coerce")
            _db_df = _db_df.dropna(subset=["amount"])
            _db_df["date"] = _db_pd.to_datetime(_db_df.get("date", ""), errors="coerce")
            _now_db = datetime.now()
            _db_this_month = _db_df[
                (_db_df["date"].dt.month == _now_db.month) & (_db_df["date"].dt.year == _now_db.year)
            ]

            if not _db_this_month.empty:
                _cat_spending = _db_this_month.groupby("category")["amount"].sum().reset_index()
                _cat_spending = _cat_spending[_cat_spending["amount"] > 0].sort_values("amount", ascending=False)

                if not _cat_spending.empty:
                    st.markdown(f"**{_t_dash('spending_by_category')}**")
                    _don_c1, _don_c2 = st.columns(2)

                    with _don_c1:
                        import plotly.express as _db_px
                        from utils.chart_config import apply_layout as _db_apply, CHART_COLORS as _db_colors
                        _donut_fig = _db_px.pie(
                            _cat_spending, names="category", values="amount",
                            color_discrete_sequence=_db_colors,
                        )
                        _donut_fig.update_traces(
                            hole=0.55,
                            textposition="inside",
                            textinfo="percent+label",
                            textfont_size=11,
                        )
                        _db_apply(_donut_fig, height=280, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
                        st.plotly_chart(_donut_fig, width='stretch')

                    with _don_c2:
                        # Top 5 categories bar chart
                        _top5 = _cat_spending.head(5)
                        import plotly.graph_objects as _db_go
                        _bar_fig = _db_go.Figure(_db_go.Bar(
                            x=_top5["amount"],
                            y=_top5["category"],
                            orientation="h",
                            marker_color=_accent,
                            text=[f"${v:,.0f}" for v in _top5["amount"]],
                            textposition="auto",
                        ))
                        _db_apply(_bar_fig, height=280, margin=dict(t=10, b=10, l=10, r=80))
                        _bar_fig.update_yaxes(autorange="reversed")
                        st.plotly_chart(_bar_fig, width='stretch')

                    st.markdown("")

    # ── Money Flow (Sankey) ───────────────────────────────────────────
    if _budget_txns:
        import pandas as _sk_pd
        _sk_df = _sk_pd.DataFrame(_budget_txns)
        _sk_df["amount"] = _sk_pd.to_numeric(_sk_df.get("amount", 0), errors="coerce")
        _sk_df["date"] = _sk_pd.to_datetime(_sk_df.get("date", ""), errors="coerce")
        _sk_now = datetime.now()
        _sk_month = _sk_df[
            (_sk_df["date"].dt.month == _sk_now.month) & (_sk_df["date"].dt.year == _sk_now.year)
        ]

        if not _sk_month.empty and "category" in _sk_month.columns:
            _sk_income = _sk_month[_sk_month.get("category", _sk_pd.Series()) == "Income"]["amount"].sum()
            _sk_expenses = _sk_month[_sk_month["category"] != "Income"]
            _sk_by_cat = _sk_expenses.groupby("category")["amount"].sum()
            _sk_by_cat = _sk_by_cat[_sk_by_cat > 0].sort_values(ascending=False)

            if len(_sk_by_cat) >= 2:
                st.markdown(f"**{_t_dash('money_flow')}**")
                _sk_labels = ["Income"] + list(_sk_by_cat.index)
                _sk_source = [0] * len(_sk_by_cat)  # all from Income
                _sk_target = list(range(1, len(_sk_by_cat) + 1))
                _sk_values = list(_sk_by_cat.values)

                import plotly.graph_objects as _sk_go
                from utils.chart_config import apply_layout as _sk_apply, _theme_colors as _sk_tc
                _tc = _sk_tc()
                _sk_fig = _sk_go.Figure(_sk_go.Sankey(
                    node=dict(
                        pad=20,
                        thickness=25,
                        label=_sk_labels,
                        color=[_accent] + [_tc.get("grid", "#334155")] * len(_sk_by_cat),
                    ),
                    link=dict(
                        source=_sk_source,
                        target=_sk_target,
                        value=_sk_values,
                        color="rgba(99,102,241,0.2)",
                    ),
                ))
                _sk_apply(_sk_fig, height=300, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(_sk_fig, width='stretch')
                st.markdown("")

    # ── Monthly Cash Flow ─────────────────────────────────────────────
    if _budget_txns:
        import pandas as _cf_pd
        _cf_df = _cf_pd.DataFrame(_budget_txns)
        _cf_df["amount"] = _cf_pd.to_numeric(_cf_df.get("amount", 0), errors="coerce")
        _cf_df["date"] = _cf_pd.to_datetime(_cf_df.get("date", ""), errors="coerce")
        _cf_df = _cf_df.dropna(subset=["date", "amount"])

        if not _cf_df.empty and "category" in _cf_df.columns:
            _cf_df["month"] = _cf_df["date"].dt.to_period("M").astype(str)
            _cf_months = sorted(_cf_df["month"].unique())[-6:]  # last 6 months
            _cf_monthly = []
            for mo in _cf_months:
                mo_data = _cf_df[_cf_df["month"] == mo]
                income = mo_data[mo_data["category"] == "Income"]["amount"].sum()
                expenses = mo_data[mo_data["category"] != "Income"]["amount"].sum()
                _cf_monthly.append({"Month": mo, "Income": income, "Expenses": expenses})

            if _cf_monthly and any(r["Income"] > 0 or r["Expenses"] > 0 for r in _cf_monthly):
                st.markdown(f"**{_t_dash('monthly_cash_flow')}**")
                import plotly.graph_objects as _cf_go
                from utils.chart_config import apply_layout as _cf_apply
                _cf_fig = _cf_go.Figure()
                _cf_fig.add_trace(_cf_go.Bar(
                    x=[r["Month"] for r in _cf_monthly],
                    y=[r["Income"] for r in _cf_monthly],
                    name=_t_dash("income"),
                    marker_color="#22c55e",
                ))
                _cf_fig.add_trace(_cf_go.Bar(
                    x=[r["Month"] for r in _cf_monthly],
                    y=[r["Expenses"] for r in _cf_monthly],
                    name=_t_dash("expenses"),
                    marker_color="#ef4444",
                ))
                _cf_fig.update_layout(barmode="group")
                _cf_apply(_cf_fig, height=250, margin=dict(t=10, b=30, l=10, r=10))
                st.plotly_chart(_cf_fig, width='stretch')
                st.markdown("")

    # Account balance cards
    _dash_accounts = _load_json("accounts.json", default=[])
    if _dash_accounts:
        st.markdown(f"**{_t_dash('accounts')}**")
        _acc_type_icons = {"checking": "B", "savings": "$", "credit": "C",
                           "cash": "$", "investment": "I"}
        _acc_cols = st.columns(min(len(_dash_accounts), 4))
        for _ai, _acc in enumerate(_dash_accounts[:4]):
            with _acc_cols[_ai]:
                _acc_icon = _acc_type_icons.get(_acc.get("type", ""), "B")
                _acc_color = _acc.get("color", "#6366f1")
                _last4 = f" ····{_acc['last_four']}" if _acc.get("last_four") else ""
                st.markdown(
                    f'<div class="dash-widget" style="border-left:3px solid {_acc_color};">'
                    f'<div class="widget-title">{_acc_icon} {_acc["name"]}{_last4}</div>'
                    f'<div class="widget-value">{format_currency_int(_acc.get("balance", 0))}</div>'
                    f'<div class="widget-sub">{_acc.get("type", "").title()}'
                    f'{" · " + _acc.get("institution", "") if _acc.get("institution") else ""}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("")

    # Alert bar — recent unread notifications
    _dash_alerts = get_notifications(unread_only=True, limit=5)
    if _dash_alerts:
        st.markdown(f"**{_t_dash('recent_alerts')}**")
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
            f'{_t_dash("all_caught_up")}</div>',
            unsafe_allow_html=True,
        )

    # Spending anomaly alerts
    try:
        from utils.insights import detect_anomalies
        _anomalies = detect_anomalies()
        if _anomalies:
            st.markdown(f"**{_t_dash('spending_alerts')}**")
            for _anom in _anomalies[:3]:
                st.markdown(
                    f'<div class="fk-alert-card border-warning">'
                    f'<div style="font-size:1rem;color:var(--fk-warning);font-weight:700;">!</div>'
                    f'<div style="flex:1;">'
                    f'<div style="color:var(--fk-text);font-weight:600;font-size:0.88rem;">'
                    f'{_t_dash("spending_alerts")}: {_anom["category"]}</div>'
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
            st.markdown(f"**{_t_dash('bills_due_this_week')}**")
            for _wb in _week_bills[:4]:
                days = _wb.get("_days_away", 0)
                auto_tag = f" ({_t_dash('dash_auto_pay')})" if _wb.get("auto_pay") else ""
                st.markdown(
                    f'<div class="fk-alert-card border-info">'
                    f'<div style="flex:1;">'
                    f'<div style="color:var(--fk-text);font-weight:600;font-size:0.88rem;">'
                    f'{_wb["name"]} — {format_currency_int(_wb["amount"])}</div>'
                    f'<div style="color:var(--fk-text-muted);font-size:0.8rem;">'
                    f'{_t_dash("dash_due_in_days", n=days)}{auto_tag}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
            st.markdown("")
    except Exception:
        pass

    # Household dashboard section
    try:
        from utils.household import is_household_enabled, get_household, get_balances, get_member_names
        if is_household_enabled():
            st.markdown("---")
            st.markdown(f"### {_t_dash('dash_household_overview')}")
            _hh = get_household()
            st.caption(f"{_t_dash('household')}: **{_hh.get('name', '')}** — {len(_hh.get('members', []))} {_t_dash('dash_members')}")

            # Who owes whom
            _balances = get_balances()
            if _balances:
                st.markdown(f"**{_t_dash('dash_outstanding_balances')}**")
                for (debtor, creditor), amount in _balances.items():
                    st.markdown(
                        f'<div class="fk-alert-card border-warning">'
                        f'<div style="flex:1;">'
                        f'<div style="color:var(--fk-text);font-weight:600;font-size:0.88rem;">'
                        f'{debtor} owes {creditor}</div>'
                        f'<div style="color:var(--fk-text-muted);font-size:0.8rem;">'
                        f'{format_currency(amount)}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )

            # Shared goals progress
            _shared_goals = [g for g in goals if g.get("shared")]
            if _shared_goals:
                st.markdown(f"**{_t_dash('dash_shared_goals')}**")
                for sg in _shared_goals[:3]:
                    _sg_pct = min(100, sg["current"] / sg["target"] * 100) if sg["target"] > 0 else 0
                    _contrib_parts = ""
                    if sg.get("contributions"):
                        _contrib_parts = " · ".join(
                            f"{n}: {format_currency_int(a)}" for n, a in sg["contributions"].items()
                        )
                    st.markdown(
                        f'<div class="fk-alert-card border-info">'
                        f'<div style="flex:1;">'
                        f'<div style="color:var(--fk-text);font-weight:600;font-size:0.88rem;">'
                        f'{sg["name"]} — {_sg_pct:.0f}%</div>'
                        f'<div style="color:var(--fk-text-muted);font-size:0.8rem;">'
                        f'{format_currency_int(sg["current"])} / {format_currency_int(sg["target"])}'
                        f'{" | " + _contrib_parts if _contrib_parts else ""}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                st.markdown("")
    except Exception:
        pass

    st.markdown("---")

    # ── Net Worth Trend & Financial Health ─────────────────────────────
    _nw_col, _fh_col = st.columns(2)

    with _nw_col:
        st.markdown(f"### {_t_dash('net_worth_trend')}")

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

        # Net worth trend chart
        if len(_nw_history) >= 2:
            import plotly.graph_objects as _nw_go
            from utils.chart_config import apply_layout as _nw_apply, _theme_colors as _nw_tc
            _sorted_h = sorted(_nw_history, key=lambda x: x.get("date", ""))
            _nw_fig = _nw_go.Figure(_nw_go.Scatter(
                x=[s["date"] for s in _sorted_h],
                y=[s["net_worth"] for s in _sorted_h],
                mode="lines+markers",
                line=dict(color=_accent, width=2),
                marker=dict(size=6),
                fill="tozeroy",
                fillcolor="rgba(99,102,241,0.1)",
            ))
            _nw_apply(_nw_fig, height=180, margin=dict(t=10, b=20, l=10, r=10), showlegend=False)
            st.plotly_chart(_nw_fig, width='stretch')

        # Cash balance input
        with st.expander(_t_dash("edit_cash_liabilities")):
            _new_cash = st.number_input(_t_dash("dash_cash_balance"), value=_cash_balance, step=100.0, key="nw_cash")
            if _new_cash != _cash_balance:
                _user_settings["cash_balance"] = _new_cash
                from utils.data_persistence import save_json as _dp_save2
                _dp_save2("settings.json", _user_settings)
                st.toast(_t_dash("dash_cash_updated"))
                st.rerun()

            if _liabilities:
                st.markdown(f"**{_t_dash('liabilities')}:**")
                for _li in _liabilities:
                    st.markdown(f"- {_li.get('name', _t_dash('dash_unnamed'))}: {format_currency_int(float(_li.get('balance', 0)))}")
            st.caption(_t_dash("dash_manage_liabilities_hint"))

    with _fh_col:
        st.markdown(f"### {_t_dash('financial_health')}")
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
            _health_label = _t_dash("dash_health_healthy")
        elif _health_score >= 40:
            _gauge_color = "#f59e0b"
            _health_label = _t_dash("dash_health_improve")
        else:
            _gauge_color = "#ef4444"
            _health_label = _t_dash("dash_health_needs_work")

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
        st.plotly_chart(_gauge_fig, width='stretch')
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
                _tips.append(_t_dash("dash_tip_over_budget", n=_over_cats))
            elif _comp == "Savings Rate" and _score < 70:
                _tips.append(_t_dash("dash_tip_savings_low"))
            elif _comp == "Emergency Fund" and _score < 70:
                _tips.append(_t_dash("dash_tip_goal_underfunded", pct=_scores['Emergency Fund']))
            elif _comp == "Debt Ratio" and _score < 70:
                _tips.append(_t_dash("dash_tip_debt_high"))
            elif _comp == "Sub Efficiency" and _score < 70:
                _tips.append(_t_dash("dash_tip_review_subs"))

        if _tips:
            for _tip in _tips:
                st.markdown(f"<div style='font-size:0.82rem;color:var(--fk-text-muted);padding:2px 0;'>{_tip}</div>",
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
            from utils.chart_config import CHART_COLORS as _goal_colors
            st.markdown(f"**{_t_dash('savings_goals')}**")
            for goal in goals[:3]:
                pct = min((goal["current"] / goal["target"] * 100) if goal["target"] > 0 else 0, 100)
                bar_color = _goal_colors[3] if pct >= 100 else _goal_colors[0] if pct >= 50 else _goal_colors[1]
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
                st.caption(f"+ {len(goals)-3} {_t_dash('dash_more_open_goal_tracker')}")
            if st.button(_t_dash("dash_open_goal_tracker"), key="d_goals"):
                st.session_state.nav_target = "Goal Tracker"
                st.rerun()
        else:
            st.markdown(
                '<div class="fk-empty">'
                f'<div class="title">{_t_dash("dash_no_goals_yet")}</div>'
                f'<div>{_t_dash("dash_set_first_goal")}</div></div>',
                unsafe_allow_html=True,
            )
            if st.button(_t_dash("dash_create_a_goal"), key="d_create_goal"):
                st.session_state.nav_target = "Goal Tracker"
                st.rerun()

    with col_right:
        # Recent receipts
        st.markdown(f"**{_t_dash('recent_receipts')}**")
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
            if st.button(_t_dash("dash_view_all_receipts"), key="d_receipts"):
                st.session_state.nav_target = "Receipt Scanner"
                st.rerun()
        else:
            st.markdown(
                '<div class="fk-empty">'
                f'<div class="title">{_t_dash("dash_no_receipts_yet")}</div>'
                f'<div>{_t_dash("dash_upload_receipt")}</div></div>',
                unsafe_allow_html=True,
            )

    # Insight — prefer analytics-based insight, fall back to static
    st.markdown("<br>", unsafe_allow_html=True)
    if _top_insight:
        _ins_cls = _top_insight.get("type", "tip")
        st.markdown(
            f'<div class="insight-card {_ins_cls}"><div class="insight-label">{_t_dash("smart_insight")}</div>'
            f'<div class="insight-text">{_top_insight["text"]}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        insight = _generate_insight(budgets, goals, receipts_data, stmt_data)
        st.markdown(
            f'<div class="insight-card"><div class="insight-label">{_t_dash("quick_insight")}</div>'
            f'<div class="insight-text">{insight}</div></div>',
            unsafe_allow_html=True,
        )

    # Recent Activity feed
    from utils.activity_log import get_recent as _get_recent_activity, format_activity as _fmt_activity

    _recent_activity = _get_recent_activity(limit=10)
    if _recent_activity:
        st.markdown(f"**{_t_dash('recent_activity')}**")
        for _act in _recent_activity:
            st.markdown(
                f'<div style="padding:4px 0;font-size:0.85rem;color:var(--fk-text-muted);'
                f'border-bottom:1px solid var(--fk-border);">{_fmt_activity(_act)}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("")

    # Module cards — only show enabled modules
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"### {_t_dash('your_modules')}")

    _enabled_mods = _get_enabled_modules()

    # Build activity strings from data
    freelance_data = _load_json("freelance_data.json", default={"clients": [], "invoices": []})
    n_receipts = len(receipts_data) if receipts_data else 0
    n_holdings = len(holdings)
    n_goals = len(goals)
    n_clients = len(freelance_data.get("clients", [])) if isinstance(freelance_data, dict) else 0
    n_stmt = len(stmt_data) if stmt_data else 0

    _all_module_cards = [
        ("R", _t_dash("receipt_scanner"), _t_dash("dash_mod_receipts_desc"),
         "Receipt Scanner", f"{n_receipts} {_t_dash('dash_receipts_scanned')}" if n_receipts else "", "receipts"),
        ("I", _t_dash("portfolio_tracker"), _t_dash("dash_mod_portfolio_desc"),
         "Portfolio Tracker", f"{n_holdings} {_t_dash('dash_holdings_tracked')}" if n_holdings else "", "portfolio"),
        ("P", _t_dash("report_generator"), _t_dash("dash_mod_reports_desc"),
         "Report Generator", "", "reports"),
        ("F", _t_dash("freelance_dashboard"), _t_dash("dash_mod_freelance_desc"),
         "Freelance Dashboard", f"{n_clients} {_t_dash('dash_clients')}" if n_clients else "", "freelance"),
        ("S", _t_dash("subscription_auditor"), _t_dash("dash_mod_subs_desc"),
         "Subscription Auditor", f"{n_stmt} {_t_dash('dash_transactions_analyzed')}" if n_stmt else "", "subscriptions"),
        ("$", _t_dash("budget_tracker"), _t_dash("dash_mod_budget_desc"),
         "Budget Tracker", f"{format_currency_int(total_budget)}/{_t_dash('dash_mo_budgeted')}" if total_budget > 0 else "", "budget"),
        ("G", _t_dash("goal_tracker"), _t_dash("dash_mod_goals_desc"),
         "Goal Tracker", f"{n_goals} {_t_dash('dash_active_goals')}" if n_goals else "", "goals"),
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
                if st.button(f"{_t_dash('open')} {title}", key=f"m_{row_start + i}", width='stretch'):
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
    _last_str = datetime.fromtimestamp(_last_mod).strftime("%b %d, %Y %H:%M") if _last_mod > 0 else _t_dash("no_data")
    st.markdown(
        f'<div class="dash-footer">FinanceKit v{APP_VERSION} &nbsp;·&nbsp; '
        f'{_t_dash("last_updated")}: {_last_str}</div>',
        unsafe_allow_html=True,
    )

else:
    # Module routing with graceful error handling
    _module_map = {
        "Receipt Scanner": "modules.receipt_scanner",
        "Portfolio Tracker": "modules.portfolio_tracker",
        "Report Generator": "modules.report_generator",
        "Freelance Dashboard": "modules.job_tracker",
        "Subscription Auditor": "modules.subscription_auditor",
        "Budget Tracker": "modules.budget_tracker",
        "Goal Tracker": "modules.goal_tracker",
        "Settings": "modules.settings",
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
                '<div style="font-size:3rem;margin-bottom:0.5rem;"></div>'
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
                if st.button("Try refreshing the page", width='stretch', type="primary"):
                    st.rerun()
                st.caption(
                    "If this keeps happening, try running the **Health Check** in "
                    "Settings → Data Management. Errors are logged to `financekit.log`."
                )

# --- Mobile Bottom Nav + FAB (v5.1) ---
# Rendered on all pages; CSS hides on desktop
_bottom_nav_items = [
    ("H", "Home", "Dashboard"),
    ("$", "Budget", "Budget Tracker"),
    ("G", "Goals", "Goal Tracker"),
    ("I", "Portfolio", "Portfolio Tracker"),
    ("...", "More", "__more__"),
]
_current_page = page
_bottom_nav_html = '<div class="fk-bottom-nav">'
for _bn_icon, _bn_label, _bn_nav in _bottom_nav_items:
    _bn_active = "active" if _bn_nav == _current_page else ""
    _bn_nav_param = _bn_nav.replace(" ", "%20") if _bn_nav != "__more__" else "__more__"
    _bottom_nav_html += (
        f'<a class="fk-bottom-nav-item {_bn_active}" '
        f'href="?nav={_bn_nav_param}" '
        f'onclick="event.preventDefault();'
        f'var url=new URL(window.location);url.searchParams.set(\'nav\',\'{_bn_nav}\');window.location.href=url.toString();">'
        f'<span class="icon">{_bn_icon}</span>{_bn_label}</a>'
    )
_bottom_nav_html += '</div>'

st.markdown(_bottom_nav_html, unsafe_allow_html=True)

# "More" menu — show all modules when __more__ nav is triggered (v6.1 fix)
_more_triggered = (
    st.session_state.get("sidebar_nav") == "__more__"
    or ("nav" in st.query_params and st.query_params["nav"] == "__more__")
)
if _more_triggered:
    st.query_params.clear()
    # Reset to Dashboard to avoid stuck state
    st.session_state.nav_index = 0
    st.session_state.fk_show_more_menu = True
    st.rerun()

if st.session_state.pop("fk_show_more_menu", False):
    @st.dialog("All Modules", width="large")
    def _show_more_menu():
        _more_nav_items = [
            ("R", "Receipt Scanner", "Receipt Scanner"),
            ("P", "Report Generator", "Report Generator"),
            ("F", "Freelance Dashboard", "Freelance Dashboard"),
            ("S", "Subscription Auditor", "Subscription Auditor"),
            ("$", "Budget Tracker", "Budget Tracker"),
            ("G", "Goal Tracker", "Goal Tracker"),
            ("I", "Portfolio Tracker", "Portfolio Tracker"),
            ("", "Settings", "Settings"),
        ]
        for _mi, _ml, _mn in _more_nav_items:
            if _mn in NAV_OPTIONS:
                if st.button(f"{_mi}  {_ml}", key=f"more_{_ml}", width='stretch'):
                    st.session_state.nav_target = _mn
                    st.rerun()
    _show_more_menu()

# FAB for quick expense entry (visible on mobile via CSS)
st.markdown(
    '<div class="fk-fab" onclick="'
    "var url=new URL(window.location);"
    "url.searchParams.set('fab','1');"
    "window.location.href=url.toString();"
    '">+</div>',
    unsafe_allow_html=True,
)

# Handle FAB click
if "fab" in st.query_params:
    st.query_params.clear()
    show_quick_entry()
