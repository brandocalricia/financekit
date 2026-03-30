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

# --- Theme ---
def _load_theme():
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "settings.json")
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f).get("theme", "dark")
    except Exception:
        return "dark"

if "fk_theme" not in st.session_state:
    saved = _load_theme()
    # "system" defaults to dark; JS will override later if needed
    st.session_state.fk_theme = "dark" if saved == "system" else saved

if "fk_theme_setting" not in st.session_state:
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "settings.json")
    try:
        with open(fp, "r", encoding="utf-8") as f:
            st.session_state.fk_theme_setting = json.load(f).get("theme", "dark")
    except Exception:
        st.session_state.fk_theme_setting = "dark"

theme = st.session_state.fk_theme

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
    st.session_state.nav_target = None
    if target in NAV_OPTIONS:
        st.session_state.nav_index = NAV_OPTIONS.index(target)
        # Set the radio widget key directly so sidebar highlights correctly
        st.session_state["sidebar_nav"] = target

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
    --fk-btn-bg: #2a2a40;
    --fk-btn-text: #e2e8f0;
    --fk-btn-border: #3a3a5c;
    --fk-btn-hover-bg: #353550;
    --fk-btn-hover-text: #ffffff;
"""

_light_vars = f"""
    --fk-bg: #f8fafc;
    --fk-card: #ffffff;
    --fk-card-alt: #f1f5f9;
    --fk-card-hover: #e8ecf2;
    --fk-text: #0f172a;
    --fk-text-muted: #475569;
    --fk-text-dim: #64748b;
    --fk-border: #cbd5e1;
    --fk-border-light: #94a3b8;
    --fk-accent: {_darken_hex(_accent, 0.1)};
    --fk-accent-light: {_accent};
    --fk-accent-text: {_darken_hex(_accent, 0.3)};
    --fk-success: #15803d;
    --fk-warning: #b45309;
    --fk-danger: #b91c1c;
    --fk-input-bg: #ffffff;
    --fk-sidebar-bg: #eef2f7;
    --fk-sidebar-hr: #94a3b8;
    --fk-footer-text: #64748b;
    --fk-chart-grid: #cbd5e1;
    --fk-progress-bg: #cbd5e1;
    --fk-insight-bg1: #eef2ff;
    --fk-insight-bg2: #e0e7ff;
    --fk-insight-border: {_accent};
    --fk-insight-label: #3730a3;
    --fk-savings-bg1: #d1fae5;
    --fk-savings-bg2: #a7f3d0;
    --fk-savings-label: #065f46;
    --fk-savings-text: #064e3b;
    --fk-btn-bg: #ffffff;
    --fk-btn-text: #0f172a;
    --fk-btn-border: #cbd5e1;
    --fk-btn-hover-bg: #f1f5f9;
    --fk-btn-hover-text: #0f172a;
"""

_theme_vars = _dark_vars if theme == "dark" else _light_vars

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
    /* Primary buttons — accent background, white text always */
    .stApp .stButton button[kind="primary"],
    .stApp button[data-testid="baseButton-primary"],
    .stApp button[data-testid="baseButton-primaryFormSubmit"],
    .stApp .stFormSubmitButton button {{
        background-color: var(--fk-accent) !important;
        color: #ffffff !important;
        border: none !important;
        -webkit-text-fill-color: #ffffff !important;
    }}
    .stApp .stButton button[kind="primary"] *,
    .stApp button[data-testid="baseButton-primary"] *,
    .stApp button[data-testid="baseButton-primaryFormSubmit"] *,
    .stApp .stFormSubmitButton button * {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
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
    /* ── High Contrast Mode ──────────────────────────────────── */
    .stApp, [data-testid="stAppViewContainer"] {{
        --fk-text: #000000 !important;
        --fk-text-muted: #1a1a1a !important;
        --fk-text-dim: #333333 !important;
        --fk-border: #000000 !important;
        --fk-border-light: #333333 !important;
    }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp span, .stApp li, .stApp label, .stApp td, .stApp th {{
        color: #000000 !important;
    }}
    .stApp .stCaption, .stApp small {{
        color: #1a1a1a !important;
    }}
    .stApp button[data-testid="baseButton-secondary"],
    .stApp button[data-testid="baseButton-minimal"] {{
        border: 2px solid #000000 !important;
    }}
    .stApp [data-baseweb="select"] > div {{
        border: 2px solid #000000 !important;
    }}
    .stApp .stTextInput input, .stApp .stNumberInput input, .stApp textarea {{
        border: 2px solid #000000 !important;
    }}
""" if _high_contrast and theme == "light" else ""}
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
{f"""
    /* ── Light mode: exceptions only (everything else uses CSS vars) ── */
    /* Gradient text must stay transparent */
    .stApp .fk-logo .logo-text,
    .stApp .page-header-title {{
        color: transparent !important;
        -webkit-text-fill-color: transparent !important;
    }}
    .stApp .fk-logo .logo-badge {{
        color: var(--fk-accent) !important;
        -webkit-text-fill-color: var(--fk-accent) !important;
    }}
    /* Sidebar nav — muted default, accent when selected */
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {{
        color: var(--fk-text-muted) !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked) {{
        color: var(--fk-accent) !important;
    }}
""" if theme == "light" else ""}
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
st.markdown("""
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
""", unsafe_allow_html=True)

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
st.markdown("""
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
""", unsafe_allow_html=True)

# Handle keyboard nav via query params
_qp = st.query_params
if "nav" in _qp:
    nav_target = _qp["nav"]
    if nav_target in NAV_OPTIONS:
        st.session_state.nav_index = NAV_OPTIONS.index(nav_target)
        st.session_state["sidebar_nav"] = nav_target
    st.query_params.clear()


# --- Shared View Handler (v5.5) ---
_share_token = st.query_params.get("share")
if _share_token:
    try:
        from utils.sharing import validate_share_token, log_share_access
        _share_pw = st.query_params.get("pw")
        _share_data = validate_share_token(_share_token, _share_pw)

        if _share_data is None:
            st.error("This share link is invalid or has expired.")
            st.stop()
        elif _share_data.get("needs_password"):
            st.markdown("### This shared view is password-protected")
            pw = st.text_input("Enter password", type="password", key="share_pw_input")
            if st.button("Access", type="primary"):
                _share_data2 = validate_share_token(_share_token, pw)
                if _share_data2 and not _share_data2.get("wrong_password") and not _share_data2.get("needs_password"):
                    st.query_params["pw"] = pw
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            st.stop()
        elif _share_data.get("wrong_password"):
            st.error("Incorrect password.")
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

            st.info("This is a read-only shared view. No changes can be made.")

            # Show basic financial summary
            st.markdown("### Financial Summary")
            st.caption("Detailed data is available in the shared modules.")

            st.markdown(
                f'<div class="dash-footer">Shared via FinanceKit · Read-only view</div>',
                unsafe_allow_html=True,
            )
            st.stop()
    except ImportError:
        st.error("Sharing module not available.")
        st.stop()
    except Exception as _share_err:
        st.error(f"Could not load shared view: {_share_err}")
        st.stop()

# --- Authentication Gate ---
from utils.auth import is_auth_required, login_user, register_user, password_strength, is_session_valid, session_hours_remaining, generate_reset_token, reset_password_with_token, get_google_credentials, get_github_credentials, login_oauth_user, _sanitize_user_id, invalidate_all_sessions
from utils.data_persistence import set_user_context, clear_user_context


def _show_landing_page():
    """Show a professional landing page for unauthenticated visitors."""
    from utils.auth import get_user_count

    # Hero section
    st.markdown(
        '<div style="text-align:center;padding:3rem 0 2rem;max-width:900px;margin:0 auto;">'
        ''
        '<h1 class="page-header-title" style="font-size:2.5rem;margin:0 0 0.5rem;">FinanceKit</h1>'
        '<p style="color:var(--fk-text-muted);font-size:1.15rem;max-width:600px;margin:0 auto 2rem;line-height:1.6;">'
        'Your all-in-one personal finance toolkit. Track budgets, scan receipts, '
        'monitor investments, and take control of your money.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # CTA buttons
    col_l, col_c, col_r = st.columns([1.5, 2, 1.5])
    with col_c:
        if st.button("Get Started — Free", type="primary", width='stretch', key="landing_signup"):
            st.session_state.auth_view = "register"
            st.session_state.show_auth = True
            st.rerun()
        if st.button("Sign In", width='stretch', key="landing_signin"):
            st.session_state.auth_view = "login"
            st.session_state.show_auth = True
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Feature highlights — 3 columns
    _features = [
        ("$", "Budget & Spending", "Set budgets by category, track every dollar, and get alerts before you overspend."),
        ("I", "Investments", "Monitor stocks and crypto with live prices, alerts, and allocation charts."),
        ("R", "Smart Receipts", "Upload receipts and automatically extract merchant, amount, date, and category."),
    ]
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(_features):
        with cols[i]:
            st.markdown(
                f'<div class="module-card">'
                f'<div class="icon">{icon}</div>'
                f'<h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # More features — compact list
    _more = [
        ("S", "Subscription Auditor", "Find and cancel forgotten subscriptions."),
        ("G", "Goal Tracker", "Set savings goals and celebrate milestones."),
        ("F", "Freelance Dashboard", "Clients, invoices, time tracking, and tax estimates."),
        ("P", "Report Generator", "PDF and Excel exports with charts."),
        ("H", "Household Mode", "Split expenses with family or roommates."),
        ("D", "Smart Import", "YNAB, Mint, Monarch, or any bank CSV/OFX."),
    ]
    cols2 = st.columns(3)
    for i, (icon, title, desc) in enumerate(_more):
        with cols2[i % 3]:
            st.markdown(
                f'<div style="padding:0.6rem 0;border-bottom:1px solid var(--fk-border);">'
                f'<span style="font-size:1.2rem;margin-right:6px;">{icon}</span>'
                f'<span style="color:var(--fk-text);font-weight:600;font-size:0.9rem;">{title}</span>'
                f'<div style="color:var(--fk-text-muted);font-size:0.82rem;margin-left:28px;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Social proof
    _user_count = get_user_count()
    _display_count = f"{_user_count}+" if _user_count >= 10 else "100+"
    st.markdown(
        f'<div style="text-align:center;padding:1.5rem 0;">'
        f'<div style="color:var(--fk-text-muted);font-size:0.9rem;">Trusted by <strong style="color:var(--fk-accent);">{_display_count}</strong> users</div>'
        f'<div style="color:var(--fk-text-dim);font-size:0.82rem;margin-top:0.3rem;">Free forever. Your data stays private. Zero tracking.</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Bottom CTA
    col_l2, col_c2, col_r2 = st.columns([1.5, 2, 1.5])
    with col_c2:
        if st.button("Get Started — Free", type="primary", width='stretch', key="landing_bottom_cta"):
            st.session_state.auth_view = "register"
            st.session_state.show_auth = True
            st.rerun()

    # Footer
    st.markdown(
        f'<div class="dash-footer">Made for your finances &nbsp;·&nbsp; FinanceKit v{APP_VERSION}</div>',
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
        st.link_button("Sign in with Google", auth_url, width='stretch')
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
        st.link_button("Sign in with GitHub", gh_auth_url, width='stretch')
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
        with st.spinner("Signing you in with Google..."):
            token_resp = _req.post(_GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": _g_id,
                "client_secret": _g_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }, timeout=10)

            if token_resp.status_code != 200:
                st.error("Google sign-in failed. Please try again.")
                st.query_params.clear()
                return False

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                st.error("Google sign-in failed: no access token received.")
                st.query_params.clear()
                return False

            user_resp = _req.get(_GOOGLE_USERINFO_URL, headers={
                "Authorization": f"Bearer {access_token}",
            }, timeout=10)

            if user_resp.status_code != 200:
                st.error("Could not fetch Google profile. Please try again.")
                st.query_params.clear()
                return False

            user_info = user_resp.json()
            g_email = user_info.get("email", "")
            g_name = user_info.get("name", "")

            if not g_email:
                st.error("Google account has no email. Please try a different account.")
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
        with st.spinner("Signing you in with GitHub..."):
            # Exchange code for access token
            token_resp = _req.post(_GITHUB_TOKEN_URL, data={
                "code": code,
                "client_id": _gh_id,
                "client_secret": _gh_secret,
            }, headers={"Accept": "application/json"}, timeout=10)

            if token_resp.status_code != 200:
                st.error("GitHub sign-in failed. Please try again.")
                st.query_params.clear()
                return False

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                _err = token_data.get("error_description", "No access token received.")
                st.error(f"GitHub sign-in failed: {_err}")
                st.query_params.clear()
                return False

            # Fetch user profile
            user_resp = _req.get(_GITHUB_USERINFO_URL, headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }, timeout=10)

            if user_resp.status_code != 200:
                st.error("Could not fetch GitHub profile. Please try again.")
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
                st.error("GitHub account has no email. Please add a public email to your GitHub profile and try again.")
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
                '<div style="color:var(--fk-text);font-size:1.3rem;font-weight:600;">Welcome back</div>'
                '<div style="color:var(--fk-text-muted);font-size:0.9rem;">Sign in to your account</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            # OAuth sign-in buttons (Google + GitHub)
            _has_oauth = _oauth_sign_in_buttons()

            if _has_oauth:
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:8px;margin:1rem 0;">'
                    '<div style="flex:1;height:1px;background:var(--fk-border);"></div>'
                    '<span style="color:var(--fk-text-muted);font-size:0.82rem;">or sign in with email</span>'
                    '<div style="flex:1;height:1px;background:var(--fk-border);"></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                remember = st.checkbox("Remember me (30 days)")
                if st.form_submit_button("Sign In", type="primary", width='stretch'):
                    # Rate limiting check (v5.7)
                    from utils.security import is_account_locked, record_failed_login, clear_failed_attempts, log_audit_event, get_remaining_attempts
                    _locked, _lock_msg = is_account_locked(email)
                    if _locked:
                        st.error(f"Account locked — {_lock_msg}")
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
                                st.error(f"{result} ({remaining} attempt{'s' if remaining != 1 else ''} remaining)")
                            else:
                                st.error("Account locked for 30 minutes due to too many failed attempts.")

            # Forgot password link
            st.markdown(
                '<div style="text-align:right;margin-top:-0.5rem;margin-bottom:0.5rem;">',
                unsafe_allow_html=True,
            )
            if st.button("Forgot password?", key="forgot_pw_link"):
                st.session_state.auth_view = "reset"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # Create account link
            st.markdown(
                '<div style="text-align:center;margin-top:1rem;">'
                '<span style="color:var(--fk-text-muted);font-size:0.9rem;">Don\'t have an account?</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("Create one", width='stretch', key="create_acct_link"):
                st.session_state.auth_view = "register"
                st.rerun()

        elif view == "register":
            st.markdown(
                '<div style="text-align:center;margin-bottom:1rem;">'
                '<div style="color:var(--fk-text);font-size:1.3rem;font-weight:600;">Create Account</div>'
                '<div style="color:var(--fk-text-muted);font-size:0.9rem;">Start managing your finances</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            # OAuth sign-up buttons (also creates account automatically)
            _has_oauth = _oauth_sign_in_buttons()

            if _has_oauth:
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:8px;margin:1rem 0;">'
                    '<div style="flex:1;height:1px;background:var(--fk-border);"></div>'
                    '<span style="color:var(--fk-text-muted);font-size:0.82rem;">or sign up with email</span>'
                    '<div style="flex:1;height:1px;background:var(--fk-border);"></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with st.form("register_form"):
                name = st.text_input("Display Name", placeholder="Your name")
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("New Password", type="password",
                                          help="At least 8 characters with a mix of letters, numbers, and symbols")
                if password:
                    from utils.security import check_password_requirements
                    _reqs = check_password_requirements(password)
                    _req_labels = {
                        "length": "At least 8 characters",
                        "number": "Contains a number",
                        "upper_lower": "Contains uppercase and lowercase",
                        "special": "Contains a special character",
                        "not_common": "Not a common password",
                    }
                    _req_html = ""
                    for _rk, _rl in _req_labels.items():
                        _check = "+" if _reqs.get(_rk) else "-"
                        _color = "var(--fk-success)" if _reqs.get(_rk) else "var(--fk-text-muted)"
                        _req_html += f'<div style="font-size:0.78rem;color:{_color};">{_check} {_rl}</div>'
                    st.markdown(_req_html, unsafe_allow_html=True)
                confirm = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", type="primary", width='stretch'):
                    # Validate email
                    _email_clean = email.strip()
                    if not _email_clean or "@" not in _email_clean or "." not in _email_clean.split("@")[-1]:
                        st.error("Please enter a valid email address.")
                    elif password != confirm:
                        st.error("Passwords don't match.")
                    else:
                        success, msg = register_user(_email_clean, password, name)
                        if success:
                            with st.spinner("Signing you in..."):
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
                            st.toast("Account created! Welcome to FinanceKit.")
                            st.rerun()
                        else:
                            st.error(msg)

            st.markdown(
                '<div style="text-align:center;margin-top:0.5rem;">'
                '<span style="color:var(--fk-text-muted);font-size:0.9rem;">Already have an account?</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("← Sign In", width='stretch'):
                st.session_state.auth_view = "login"
                st.rerun()

        elif view == "reset":
            st.markdown("### Reset Password")
            reset_step = st.session_state.get("reset_step", 1)

            if reset_step == 1:
                with st.form("reset_email_form"):
                    email = st.text_input("Email", placeholder="you@example.com")
                    if st.form_submit_button("Send Reset Token", type="primary", width='stretch'):
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
                    if st.form_submit_button("Reset Password", type="primary", width='stretch'):
                        if new_pass != confirm_pass:
                            st.error("Passwords don't match.")
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

            if st.button("← Back to Sign In", width='stretch', key="back_reset"):
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
    st.markdown('<script>localStorage.removeItem("fk_session");</script>', unsafe_allow_html=True)
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
            # Remove token from URL for cleanliness
            st.query_params.pop("_session_token", None)

# Inject JS to persist session token in localStorage
_js_token = st.session_state.get("fk_session_token", "")
st.markdown(f"""
<script>
(function() {{
    var token = "{_js_token}";
    if (token) {{
        localStorage.setItem('fk_session', token);
    }}
    // On page load, if no session and we have a stored token, redirect with it
    if (!token && !window.location.search.includes('_session_token')) {{
        var stored = localStorage.getItem('fk_session');
        if (stored) {{
            var url = new URL(window.location);
            url.searchParams.set('_session_token', stored);
            window.location.replace(url.toString());
        }}
    }}
}})();
</script>
""", unsafe_allow_html=True)

# Auth gate: authenticated users get full app, others see landing or login page
if st.session_state.get("authenticated"):
    # Check session expiry
    login_time = st.session_state.get("login_time", "")
    remember = st.session_state.get("remember_me", False)
    if not is_session_valid(login_time, remember):
        st.toast("Session expired. Please sign in again.")
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
                st.toast("Session extended!")
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
    """Return list of enabled module keys from settings (cached per session)."""
    if "fk_enabled_modules" not in st.session_state:
        s = _load_json("settings.json", default={})
        st.session_state.fk_enabled_modules = s.get("enabled_modules", ALL_MODULE_KEYS.copy())
    return st.session_state.fk_enabled_modules


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
                    st.success("Backup restored!")
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

    # Top bar: theme toggle + notification bell (inline)
    from utils.notifications import get_unread_count, get_notifications, mark_read, mark_all_read, clear_all as _notif_clear_all, group_notifications, relative_time, notification_icon
    _unread = get_unread_count()
    # Minimalist symbols: sun/moon for theme, bell for notifications
    _theme_label = "☀️" if theme == "dark" else "🌙"
    _bell_label = f"🔔 {_unread}" if _unread > 0 else "🔔"

    _tb1, _tb2, _tb3 = st.columns([1, 1, 3])
    with _tb1:
        if st.button(_theme_label, key="theme_toggle", help="Toggle light/dark mode"):
            new_theme = "light" if theme == "dark" else "dark"
            st.session_state.fk_theme = new_theme
            st.session_state.fk_theme_setting = new_theme
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
    with _tb2:
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
        if st.button("Sign Out", key="sign_out", width='stretch'):
            _sign_out()

    # Keyboard shortcuts — JS injection (v4.7)
    _kb_nav_map = {str(i): nav for i, nav in enumerate(NAV_OPTIONS) if i < 10}
    _kb_js_cases = "\n".join(
        f'        case "{k}": target = "{v}"; break;'
        for k, v in _kb_nav_map.items()
    )
    st.markdown(f"""
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
    """, unsafe_allow_html=True)


# --- "What's New" dialog (v6.0) ---
@st.dialog("What's New in FinanceKit", width="large")
def _show_whats_new():
    _wn_items = [
        ("6.0", "Launch-Ready Polish", [
            "Open Graph meta tags for richer link previews",
            "What's New dialog on version updates",
            "Legal pages: Terms of Service, Privacy Policy, GDPR tools",
            "In-app help tooltips throughout the interface",
        ]),
        ("5.9", "Performance & Reliability", [
            "Cached data loading with smart cache-busting",
            "Health check endpoint (?health=1)",
            "Pagination for large data sets",
            "Startup time optimization and logging",
        ]),
        ("5.8", "Accessibility & i18n", [
            "Internationalization groundwork with t() function",
            "Locale-aware currency formatting (INR, BRL)",
            "Focus indicators, skip-to-content, reduced motion",
            "Font size selector and high contrast mode",
        ]),
        ("5.7", "Security Hardening", [
            "Rate limiting with account lockout",
            "Password strength requirements",
            "Session management and audit logging",
            "Input sanitization",
        ]),
    ]
    for _ver, _title, _bullets in _wn_items:
        st.markdown(f"**v{_ver} — {_title}**")
        for _b in _bullets:
            st.markdown(f"- {_b}")
        st.markdown("")
    if st.button("Got it!", type="primary", width='stretch'):
        _s = _load_json("settings.json", default={})
        _s["last_seen_version"] = APP_VERSION
        from utils.data_persistence import save_json as _wn_save
        _wn_save("settings.json", _s)
        st.session_state.fk_whats_new_dismissed = True
        st.rerun()


# --- In-app help system (v6.0) ---
_HELP_TIPS = {
    "dashboard": "Your financial overview — net worth, spending trends, and savings progress at a glance.",
    "budget": "Set monthly budgets per category. Import bank statements to auto-track spending.",
    "goals": "Create savings goals with deadlines. Contribute funds and track progress with projections.",
    "portfolio": "Track stocks and crypto with live prices, alerts, and allocation charts.",
    "receipts": "Upload receipt images or PDFs. FinanceKit extracts vendor, date, and total.",
    "reports": "Generate polished PDF reports from your transaction data.",
    "freelance": "Track clients, log billable hours, and generate invoices.",
    "subscriptions": "Detect recurring charges in your statements and decide what to keep or cancel.",
}


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
            _updated_ago = "just now"
        elif _mins_ago < 60:
            _updated_ago = f"{_mins_ago}m ago"
        elif _mins_ago < 1440:
            _updated_ago = f"{_mins_ago // 60}h ago"
        else:
            _updated_ago = f"{_mins_ago // 1440}d ago"
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
        _ec1, _ec2, _ec3 = st.columns(3)
        with _ec1:
            if st.button(f"{_t_dash('add_expense')}", key="empty_add_txn", width='stretch', type="primary"):
                st.session_state.nav_target = "Budget Tracker"
                st.session_state.auto_open_form = True
                st.rerun()
        with _ec2:
            if st.button(f"{_t_dash('import_csv')}", key="empty_import", width='stretch'):
                st.session_state.nav_target = "Report Generator"
                st.rerun()
        with _ec3:
            if st.button(f"{_t_dash('set_a_goal')}", key="empty_goal", width='stretch'):
                st.session_state.nav_target = "Goal Tracker"
                st.rerun()
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
        _spend_sub = f"{_spend_pct}% of your {format_currency_int(total_budget)} monthly budget" if total_budget > 0 else _t_dash("set_budget")
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
        _save_sub = f"{format_currency_int(g_saved)} saved of {format_currency_int(g_target)} target" if goals else _t_dash("create_goal_hint")
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
        _sub_sub = f"{_active_subs} active subscription{'s' if _active_subs != 1 else ''}" if _sub_decisions else _t_dash("import_statement_hint")
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
                    mode="lines", name="This Month",
                    line=dict(color=_accent, width=2),
                    fill="tozeroy", fillcolor="rgba(99,102,241,0.1)",
                ))
                if not _last_month.empty:
                    _last_month["day"] = _last_month["date"].dt.day
                    _daily_last = _last_month.groupby("day")["amount"].sum().sort_index().cumsum()
                    _sp_fig.add_trace(_sp_go.Scatter(
                        x=_daily_last.index, y=_daily_last.values,
                        mode="lines", name="Last Month",
                        line=dict(color="#94a3b8", width=1, dash="dash"),
                    ))
                _sp_apply(_sp_fig, height=220, margin=dict(t=10, b=30, l=10, r=10))
                _sp_fig.update_xaxes(title_text="Day of Month")
                st.markdown("**Spending Trend**")
                st.plotly_chart(_sp_fig, width='stretch')

    st.markdown("")

    # Account balance cards
    _dash_accounts = _load_json("accounts.json", default=[])
    if _dash_accounts:
        st.markdown("**Accounts**")
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
        st.markdown("**Recent Alerts**")
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
            st.markdown("**Spending Alerts**")
            for _anom in _anomalies[:3]:
                st.markdown(
                    f'<div class="fk-alert-card border-warning">'
                    f'<div style="font-size:1rem;color:var(--fk-warning);font-weight:700;">!</div>'
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
            st.markdown("**Bills Due This Week**")
            for _wb in _week_bills[:4]:
                days = _wb.get("_days_away", 0)
                auto_tag = " (auto-pay)" if _wb.get("auto_pay") else ""
                st.markdown(
                    f'<div class="fk-alert-card border-info">'
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

    # Household dashboard section
    try:
        from utils.household import is_household_enabled, get_household, get_balances, get_member_names
        if is_household_enabled():
            st.markdown("---")
            st.markdown("### Household Overview")
            _hh = get_household()
            st.caption(f"Household: **{_hh.get('name', '')}** — {len(_hh.get('members', []))} members")

            # Who owes whom
            _balances = get_balances()
            if _balances:
                st.markdown("**Outstanding Balances**")
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
                st.markdown("**Shared Goals**")
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

    # Quick Actions row — 4 large icon buttons
    st.markdown(f"**{_t_dash('quick_actions')}**")
    _qa1, _qa2, _qa3, _qa4 = st.columns(4)
    with _qa1:
        if st.button(f"{_t_dash('log_expense')}", key="dash_qa_txn", width='stretch'):
            st.session_state.nav_target = "Budget Tracker"
            st.session_state.auto_open_form = True
            st.rerun()
    with _qa2:
        if st.button(f"{_t_dash('scan_receipt')}", key="dash_qa_receipt", width='stretch'):
            st.session_state.nav_target = "Receipt Scanner"
            st.rerun()
    with _qa3:
        if st.button(f"{_t_dash('generate_report')}", key="dash_qa_report", width='stretch'):
            st.session_state.nav_target = "Report Generator"
            st.rerun()
    with _qa4:
        if st.button(f"{_t_dash('create_goal')}", key="dash_qa_goal", width='stretch'):
            st.session_state.nav_target = "Goal Tracker"
            st.session_state.auto_open_form = True
            st.rerun()

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
        with st.expander("Edit Cash / Liabilities"):
            _new_cash = st.number_input("Cash / Bank Balance ($)", value=_cash_balance, step=100.0, key="nw_cash")
            if _new_cash != _cash_balance:
                _user_settings["cash_balance"] = _new_cash
                from utils.data_persistence import save_json as _dp_save2
                _dp_save2("settings.json", _user_settings)
                st.toast("Cash balance updated!")
                st.rerun()

            if _liabilities:
                st.markdown("**Liabilities:**")
                for _li in _liabilities:
                    st.markdown(f"- {_li.get('name', 'Unnamed')}: {format_currency_int(float(_li.get('balance', 0)))}")
            st.caption("Manage liabilities in Settings → Data Management.")

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
            _health_label = "Healthy"
        elif _health_score >= 40:
            _gauge_color = "#f59e0b"
            _health_label = "Room to Improve"
        else:
            _gauge_color = "#ef4444"
            _health_label = "Needs Work"

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
            st.markdown("**Savings Goals**")
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
                st.session_state.nav_target = "Goal Tracker"
                st.rerun()
        else:
            st.markdown(
                '<div class="fk-empty">'
                '<div class="title">No savings goals yet</div>'
                '<div>Set your first goal to track progress here.</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Create a Goal", key="d_create_goal"):
                st.session_state.nav_target = "Goal Tracker"
                st.rerun()

    with col_right:
        # Recent receipts
        st.markdown("**Recent Receipts**")
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
                st.session_state.nav_target = "Receipt Scanner"
                st.rerun()
        else:
            st.markdown(
                '<div class="fk-empty">'
                '<div class="title">No receipts yet</div>'
                '<div>Upload a receipt to see it here.</div></div>',
                unsafe_allow_html=True,
            )

    # Insight — prefer analytics-based insight, fall back to static
    st.markdown("<br>", unsafe_allow_html=True)
    if _top_insight:
        _ins_cls = _top_insight.get("type", "tip")
        st.markdown(
            f'<div class="insight-card {_ins_cls}"><div class="insight-label">SMART INSIGHT</div>'
            f'<div class="insight-text">{_top_insight["text"]}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        insight = _generate_insight(budgets, goals, receipts_data, stmt_data)
        st.markdown(
            f'<div class="insight-card"><div class="insight-label">QUICK INSIGHT</div>'
            f'<div class="insight-text">{insight}</div></div>',
            unsafe_allow_html=True,
        )

    # Recent Activity feed
    from utils.activity_log import get_recent as _get_recent_activity, format_activity as _fmt_activity

    _recent_activity = _get_recent_activity(limit=10)
    if _recent_activity:
        st.markdown("**Recent Activity**")
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
        ("R", "Receipt Scanner", "Photograph or upload receipts and let OCR extract the details automatically.",
         "Receipt Scanner", f"{n_receipts} receipt{'s' if n_receipts != 1 else ''} scanned" if n_receipts else "", "receipts"),
        ("I", "Portfolio Tracker", "Monitor your stocks and crypto in real time with price alerts and allocation breakdowns.",
         "Portfolio Tracker", f"{n_holdings} holding{'s' if n_holdings != 1 else ''} tracked" if n_holdings else "", "portfolio"),
        ("P", "Report Generator", "Import bank statements and generate professional PDF financial reports.",
         "Report Generator", "", "reports"),
        ("F", "Freelance Dashboard", "Manage clients, track billable hours, and create professional invoices.",
         "Freelance Dashboard", f"{n_clients} client{'s' if n_clients != 1 else ''}" if n_clients else "", "freelance"),
        ("S", "Subscription Auditor", "Automatically detect recurring charges from your bank data and decide what to keep.",
         "Subscription Auditor", f"{n_stmt} transactions analyzed" if n_stmt else "", "subscriptions"),
        ("$", "Budget Tracker", "Set spending limits by category and see exactly where your money goes each month.",
         "Budget Tracker", f"{format_currency_int(total_budget)}/mo budgeted" if total_budget > 0 else "", "budget"),
        ("G", "Goal Tracker", "Set savings goals with target dates, track progress, and see milestone projections.",
         "Goal Tracker", f"{n_goals} active goal{'s' if n_goals != 1 else ''}" if n_goals else "", "goals"),
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
                if st.button(f"Open {title}", key=f"m_{row_start + i}", width='stretch'):
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
    st.session_state["sidebar_nav"] = "Dashboard"
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
