"""Settings module — centralized configuration for FinanceKit."""
import streamlit as st
import json
import os
import sys
import zipfile
import io
from datetime import datetime
from utils.data_persistence import load_json, save_json, DATA_DIR, BACKUP_DIR
from utils.ui_helpers import render_module_header
from utils.formatting import format_currency, format_currency_int
from utils.i18n import t, AVAILABLE_LANGUAGES, set_language, get_language_label, get_current_language

SETTINGS_FILE = "settings.json"

CURRENCY_OPTIONS = {
    "USD ($)": {"code": "USD", "symbol": "$"},
    "EUR (\u20ac)": {"code": "EUR", "symbol": "\u20ac"},
    "GBP (\u00a3)": {"code": "GBP", "symbol": "\u00a3"},
    "CAD (C$)": {"code": "CAD", "symbol": "C$"},
    "AUD (A$)": {"code": "AUD", "symbol": "A$"},
    "JPY (\u00a5)": {"code": "JPY", "symbol": "\u00a5"},
    "INR (\u20b9)": {"code": "INR", "symbol": "\u20b9"},
    "BRL (R$)": {"code": "BRL", "symbol": "R$"},
}

DATE_FORMAT_OPTIONS = ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"]

DEFAULT_SETTINGS = {
    "user_name": "",
    "user_email": "",
    "currency": {"code": "USD", "symbol": "$"},
    "date_format": "MM/DD/YYYY",
    "email_smtp": {
        "server": "",
        "port": 587,
        "email": "",
        "password": "",
    },
    "theme": "dark",
    "version": "4.0",
}

# ── Settings sections (Discord-style nav) ───────────────────────────
_SECTIONS = [
    ("profile",        ">", "profile"),
    ("appearance",     ">", "appearance"),
    ("notifications_title", ">", "notifications_title"),
    ("modules",        ">", "modules"),
    ("data_privacy",   ">", "data_privacy"),
    ("authentication", ">", "authentication"),
    ("household",      ">", "household"),
    ("email_smtp",     ">", "email_smtp"),
    ("invoice_freelance", ">", "invoice_freelance"),
    ("sharing",        ">", "sharing"),
    ("cloud_sync",     ">", "cloud_sync"),
    ("legal_privacy",  ">", "legal_privacy"),
    ("about",          ">", "about"),
]


def _load_settings():
    return load_json(SETTINGS_FILE, default=DEFAULT_SETTINGS.copy())


def _save_settings(data):
    save_json(SETTINGS_FILE, data)


def _get_version():
    version_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "version.txt")
    try:
        with open(version_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "3.6"


def _data_file_stats():
    """Get stats for all JSON data files."""
    stats = []
    if not os.path.exists(DATA_DIR):
        return stats
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith(".json"):
            continue
        fp = os.path.join(DATA_DIR, fn)
        if not os.path.isfile(fp):
            continue
        size = os.path.getsize(fp)
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                count = f"{len(data)} records"
            elif isinstance(data, dict):
                parts = []
                for k, v in data.items():
                    if k.startswith("_"):
                        continue
                    if isinstance(v, list):
                        parts.append(f"{len(v)} {k}")
                    elif isinstance(v, dict):
                        parts.append(f"{len(v)} {k}")
                count = ", ".join(parts) if parts else "1 object"
            else:
                count = "---"
        except Exception:
            count = "invalid JSON"
        if size < 1024:
            size_str = f"{size} B"
        else:
            size_str = f"{size / 1024:.1f} KB"
        stats.append({"File": fn, "Size": size_str, "Contents": count})
    return stats


def _apply_theme(theme_value):
    """Apply a theme choice and persist it."""
    if theme_value == "system":
        st.session_state.fk_theme = "dark"
    else:
        st.session_state.fk_theme = theme_value
    st.session_state.fk_theme_setting = theme_value
    settings = _load_settings()
    settings["theme"] = theme_value
    _save_settings(settings)


# ── Section renderers ────────────────────────────────────────────────

def _render_profile(settings):
    """Profile & Account section."""
    st.markdown(f"### {t('profile')}")

    with st.form("profile_form"):
        pc1, pc2 = st.columns(2)
        with pc1:
            user_name = st.text_input(
                t("display_name"),
                value=settings.get("user_name", ""),
                placeholder=t("display_name"),
            )
            currency_labels = list(CURRENCY_OPTIONS.keys())
            current_code = settings.get("currency", {}).get("code", "USD")
            current_idx = next(
                (i for i, k in enumerate(currency_labels)
                 if CURRENCY_OPTIONS[k]["code"] == current_code),
                0,
            )
            currency_choice = st.selectbox(t("currency"), currency_labels, index=current_idx)
        with pc2:
            user_email = st.text_input(
                t("email_address"),
                value=settings.get("user_email", ""),
                placeholder="you@example.com",
            )
            current_date_fmt = settings.get("date_format", "MM/DD/YYYY")
            date_fmt_idx = DATE_FORMAT_OPTIONS.index(current_date_fmt) if current_date_fmt in DATE_FORMAT_OPTIONS else 0
            date_format = st.selectbox(t("date_format"), DATE_FORMAT_OPTIONS, index=date_fmt_idx)

        if st.form_submit_button(t("save_profile"), type="primary", width='stretch'):
            settings["user_name"] = user_name
            settings["user_email"] = user_email
            settings["currency"] = CURRENCY_OPTIONS[currency_choice]
            settings["date_format"] = date_format
            _save_settings(settings)
            st.toast(t("profile_saved"), icon="\u2705")
            st.rerun()

    # Current settings summary
    st.markdown(f"#### {t('current_settings')}")
    sym = settings.get("currency", {}).get("symbol", "$")
    code = settings.get("currency", {}).get("code", "USD")
    cs1, cs2, cs3, cs4 = st.columns(4)
    cs1.metric(t("display_name"), settings.get("user_name") or t("not_set"))
    cs2.metric(t("email"), settings.get("user_email") or t("not_set"))
    cs3.metric(t("currency"), f"{sym} ({code})")
    cs4.metric(t("date_format"), settings.get("date_format", "MM/DD/YYYY"))

    # Account management (for authenticated users)
    if st.session_state.get("authenticated"):
        st.markdown("---")
        _auth_method = st.session_state.get("auth_method", "local")

        if _auth_method == "local":
            with st.expander(t("change_password")):
                with st.form("change_pw_form"):
                    cur_pw = st.text_input(t("password"), type="password", key="cur_pw")
                    new_pw = st.text_input("New " + t("password"), type="password", key="new_pw")
                    confirm_pw = st.text_input(t("confirm") + " " + t("password"), type="password", key="confirm_pw")
                    if st.form_submit_button(t("change_password"), width='stretch'):
                        if new_pw != confirm_pw:
                            st.error("Passwords don't match.")
                        else:
                            from utils.auth import change_password
                            success, msg = change_password(
                                st.session_state.get("user_email", ""), cur_pw, new_pw
                            )
                            if success:
                                st.toast(msg, icon="\u2705")
                            else:
                                st.error(msg)
        else:
            st.info(f"Signed in via **{_auth_method.title()}**. Password is managed by your OAuth provider.")

        # Sign out everywhere
        if st.button(t("sign_out_everywhere"), width='stretch'):
            from utils.auth import invalidate_all_sessions
            success, msg = invalidate_all_sessions(st.session_state.get("user_email", ""))
            if success:
                st.toast(msg, icon="\u2705")
            else:
                st.error(msg)

        # Security activity
        with st.expander(t("security_activity")):
            try:
                from utils.security import get_audit_log
                _audit = get_audit_log(limit=20)
                if _audit:
                    for _ae in _audit:
                        _ae_icon = {"login_success": "\u2705", "login_failed": "\u274c",
                                    "password_change": "[PW]", "data_export": "[EXP]",
                                    "share_created": "[SHARE]", "account_deleted": "[DEL]"
                                    }.get(_ae.get("event", ""), "[-]")
                        _ae_ts = _ae.get("timestamp", "")[:19].replace("T", " ")
                        st.markdown(
                            f'<div style="padding:4px 0;border-bottom:1px solid var(--fk-border);font-size:0.82rem;">'
                            f'{_ae_icon} <span style="color:var(--fk-text);">{_ae.get("event", "").replace("_", " ").title()}</span>'
                            f' <span style="color:var(--fk-text-muted);">--- {_ae.get("details", "")}</span>'
                            f' <span style="color:var(--fk-text-dim);font-size:0.72rem;">{_ae_ts}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No security events recorded yet.")
            except Exception:
                st.caption("Audit log not available.")

        # Delete account
        st.markdown("---")
        with st.expander(t("delete_account")):
            st.warning("This will permanently delete your account and all your data.")
            if "confirm_delete_account" not in st.session_state:
                st.session_state.confirm_delete_account = False

            if not st.session_state.confirm_delete_account:
                if st.button(t("delete_account"), key="del_acct_btn", width='stretch'):
                    st.session_state.confirm_delete_account = True
                    st.rerun()
            else:
                dac1, dac2 = st.columns(2)
                with dac1:
                    if st.button(t("cancel"), key="cancel_del", width='stretch'):
                        st.session_state.confirm_delete_account = False
                        st.rerun()
                with dac2:
                    if st.button(t("confirm_delete"), type="primary", key="confirm_del", width='stretch'):
                        from utils.auth import delete_user
                        success, msg = delete_user(st.session_state.get("user_email", ""))
                        if success:
                            st.toast("Account deleted.")
                            st.session_state.confirm_delete_account = False
                            from utils.data_persistence import clear_user_context
                            clear_user_context()
                            for k in list(st.session_state.keys()):
                                st.session_state.pop(k, None)
                            st.rerun()
                        else:
                            st.error(msg)


def _render_appearance(settings):
    """Theme, font, language, accessibility."""
    st.markdown(f"### {t('appearance')}")

    # Theme selection
    st.markdown(f"**{t('theme')}**")
    current_theme_setting = st.session_state.get("fk_theme_setting", settings.get("theme", "dark"))
    current_theme = st.session_state.get("fk_theme", "dark")

    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        if st.button(f"{t('light')}", type="primary" if current_theme_setting == "light" else "secondary",
                      key="theme_light", width='stretch'):
            _apply_theme("light")
            st.rerun()
    with tc2:
        if st.button(f"{t('dark')}", type="primary" if current_theme_setting == "dark" else "secondary",
                      key="theme_dark", width='stretch'):
            _apply_theme("dark")
            st.rerun()
    with tc3:
        if st.button(f"{t('system')}", type="primary" if current_theme_setting == "system" else "secondary",
                      key="theme_system", width='stretch'):
            _apply_theme("system")
            st.rerun()

    # Preview swatch
    _preview_bg = "#f8fafc" if current_theme == "light" else "#0f1117"
    _preview_text = "#1e293b" if current_theme == "light" else "#e2e8f0"
    _preview_card = "#ffffff" if current_theme == "light" else "#1e1e2f"
    st.markdown(
        f'<div style="display:flex;gap:8px;margin:8px 0 16px;">'
        f'<div style="width:40px;height:24px;border-radius:4px;background:{_preview_bg};border:1px solid var(--fk-border);"></div>'
        f'<div style="width:40px;height:24px;border-radius:4px;background:{_preview_card};border:1px solid var(--fk-border);"></div>'
        f'<div style="width:40px;height:24px;border-radius:4px;background:{_preview_text};border:1px solid var(--fk-border);"></div>'
        f'<div style="width:40px;height:24px;border-radius:4px;background:#6366f1;border:1px solid var(--fk-border);"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if current_theme_setting == "system":
        st.components.v1.html("""
        <script>
        (function() {
            var isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            var currentTheme = isDark ? 'dark' : 'light';
            var url = new URL(window.parent.location);
            if (url.searchParams.get('_sys_theme') !== currentTheme) {
                url.searchParams.set('_sys_theme', currentTheme);
                var body = window.parent.document.querySelector('.stApp');
            }
        })();
        </script>
        """, height=0)

    st.markdown("---")

    # Font size and Language side by side
    ac1, ac2 = st.columns(2)
    with ac1:
        font_sizes = {
            f"{t('small')} (14px)": "14px",
            f"{t('medium')} (16px)": "16px",
            f"{t('large')} (18px)": "18px",
        }
        current_font = settings.get("font_size", "16px")
        font_labels = list(font_sizes.keys())
        font_values = list(font_sizes.values())
        current_font_idx = font_values.index(current_font) if current_font in font_values else 1
        font_choice = st.selectbox(t("font_size"), font_labels, index=current_font_idx, key="font_size_sel")
        new_font = font_sizes[font_choice]
        if new_font != current_font:
            settings["font_size"] = new_font
            _save_settings(settings)
            st.session_state.fk_font_size = new_font
            st.rerun()

    with ac2:
        lang_labels = list(AVAILABLE_LANGUAGES.keys())
        current_lang_code = settings.get("language", get_current_language())
        current_lang_label = get_language_label(current_lang_code)
        current_lang_idx = lang_labels.index(current_lang_label) if current_lang_label in lang_labels else 0
        lang_choice = st.selectbox(t("language"), lang_labels, index=current_lang_idx, key="lang_sel")
        new_lang_code = AVAILABLE_LANGUAGES[lang_choice]
        if new_lang_code != current_lang_code:
            settings["language"] = new_lang_code
            set_language(new_lang_code)
            _save_settings(settings)
            st.rerun()

    st.markdown("---")

    # Accent color picker
    st.markdown("**Accent Color**")
    st.caption("Choose a custom accent color for buttons, highlights, and navigation.")
    current_accent = settings.get("accent_color", "#6366f1")
    # Preset colors + custom picker
    _presets = {
        "Indigo": "#6366f1",
        "Blue": "#3b82f6",
        "Emerald": "#10b981",
        "Rose": "#f43f5e",
        "Amber": "#f59e0b",
        "Violet": "#8b5cf6",
        "Cyan": "#06b6d4",
        "Orange": "#f97316",
    }
    pc_cols = st.columns(len(_presets))
    for i, (name, color) in enumerate(_presets.items()):
        with pc_cols[i]:
            is_sel = current_accent == color
            if st.button(
                "●" if not is_sel else "◉",
                key=f"accent_{name}",
                help=name,
                width='stretch',
            ):
                settings["accent_color"] = color
                _save_settings(settings)
                import streamlit as _st2
                _st2.session_state.fk_accent_color = color
                st.rerun()
            st.markdown(
                f'<div style="width:100%;height:6px;border-radius:3px;background:{color};'
                f'{"border:2px solid var(--fk-text);" if is_sel else ""}'
                f'margin-top:-8px;"></div>',
                unsafe_allow_html=True,
            )

    new_accent = st.color_picker("Custom color", value=current_accent, key="accent_picker")
    if new_accent != current_accent:
        settings["accent_color"] = new_accent
        _save_settings(settings)
        st.session_state.fk_accent_color = new_accent
        st.rerun()

    st.markdown("---")

    # High contrast
    high_contrast = st.toggle(t("high_contrast"), value=settings.get("high_contrast", False), key="high_contrast_toggle")
    if high_contrast != settings.get("high_contrast", False):
        settings["high_contrast"] = high_contrast
        _save_settings(settings)
        st.session_state.fk_high_contrast = high_contrast
        st.rerun()


def _render_notifications(settings):
    """Notification preferences."""
    st.markdown(f"### {t('notifications_title')}")

    notif_prefs = settings.get("notifications", {})

    notif_enabled = st.toggle(
        t("notifications_title"),
        value=notif_prefs.get("enabled", True),
        help="Master toggle for all in-app notifications.",
    )

    if notif_enabled != notif_prefs.get("enabled", True):
        notif_prefs["enabled"] = notif_enabled
        settings["notifications"] = notif_prefs
        _save_settings(settings)
        st.rerun()

    if not notif_enabled:
        st.info("All notifications are currently disabled.")
        return

    st.markdown("---")

    # Per-module toggles
    st.markdown(f"**{t('modules')}**")
    _modules = {
        "budget": t("budget_tracker"),
        "goals": t("goal_tracker"),
        "portfolio": t("portfolio_tracker"),
        "subscriptions": t("subscription_auditor"),
        "freelance": t("freelance_dashboard"),
        "receipts": t("receipt_scanner"),
        "bills": "Bill Reminders",
    }
    module_toggles = notif_prefs.get("modules", {})
    _changed = False
    for _mk, _ml in _modules.items():
        _val = st.toggle(_ml, value=module_toggles.get(_mk, True), key=f"notif_mod_{_mk}")
        if _val != module_toggles.get(_mk, True):
            module_toggles[_mk] = _val
            _changed = True
    if _changed:
        notif_prefs["modules"] = module_toggles
        settings["notifications"] = notif_prefs
        _save_settings(settings)
        st.rerun()

    st.markdown("---")

    # Alert thresholds
    st.markdown(f"**{t('alert_thresholds')}**")
    with st.form("notif_thresholds_form"):
        tc1, tc2 = st.columns(2)
        with tc1:
            budget_warn = st.number_input(
                "Budget warning (%)",
                min_value=50, max_value=100,
                value=int(notif_prefs.get("budget_warn_pct", 80)),
                step=5, help="Notify when a budget category reaches this % of limit.",
            )
            portfolio_change = st.number_input(
                "Portfolio daily change alert (%)",
                min_value=1, max_value=50,
                value=int(notif_prefs.get("portfolio_change_pct", 5)),
                step=1,
            )
        with tc2:
            sub_threshold = st.number_input(
                "Subscription monthly cost warning ($)",
                min_value=50, max_value=5000,
                value=int(notif_prefs.get("sub_cost_threshold", 200)),
                step=25,
            )
            invoice_overdue = st.number_input(
                "Invoice overdue alert (days)",
                min_value=7, max_value=180,
                value=int(notif_prefs.get("invoice_overdue_days", 30)),
                step=7,
            )

        if st.form_submit_button(t("save"), type="primary", width='stretch'):
            notif_prefs["budget_warn_pct"] = budget_warn
            notif_prefs["portfolio_change_pct"] = portfolio_change
            notif_prefs["sub_cost_threshold"] = sub_threshold
            notif_prefs["invoice_overdue_days"] = invoice_overdue
            settings["notifications"] = notif_prefs
            _save_settings(settings)
            st.toast("Thresholds saved!", icon="\u2705")
            st.rerun()

    st.markdown("---")

    # Email digest
    st.markdown("**Email Digest**")
    smtp_configured = bool(
        settings.get("email_smtp", {}).get("server")
        and settings.get("email_smtp", {}).get("email")
        and settings.get("email_smtp", {}).get("password")
    )

    if not smtp_configured:
        st.info("Configure SMTP in the Email section to enable email digests.")
    else:
        digest_enabled = st.toggle(
            "Enable email digest",
            value=notif_prefs.get("email_digest", False),
            key="notif_digest_toggle",
        )
        if digest_enabled != notif_prefs.get("email_digest", False):
            notif_prefs["email_digest"] = digest_enabled
            settings["notifications"] = notif_prefs
            _save_settings(settings)
            st.rerun()

        if digest_enabled:
            freq = st.selectbox(
                "Frequency",
                ["daily", "weekly"],
                index=0 if notif_prefs.get("digest_frequency", "daily") == "daily" else 1,
            )
            if freq != notif_prefs.get("digest_frequency", "daily"):
                notif_prefs["digest_frequency"] = freq
                settings["notifications"] = notif_prefs
                _save_settings(settings)

            last_sent = notif_prefs.get("last_digest_sent", "")
            if last_sent:
                st.caption(f"Last sent: {last_sent[:19].replace('T', ' ')}")

            if st.button("Send Digest Now", width='stretch'):
                from utils.notifications import send_digest_email
                success, msg = send_digest_email(settings)
                if success:
                    notif_prefs["last_digest_sent"] = datetime.now().isoformat()
                    settings["notifications"] = notif_prefs
                    _save_settings(settings)
                    st.toast(msg, icon="\u2705")
                else:
                    st.warning(msg)

    st.markdown("---")

    # Quiet hours
    st.markdown(f"**{t('quiet_hours')}**")
    st.caption("Suppress non-urgent notifications during these hours.")
    quiet_prefs = notif_prefs.get("quiet_hours", {})
    quiet_enabled = st.toggle(
        t("quiet_hours"),
        value=quiet_prefs.get("enabled", False),
        key="notif_quiet_toggle",
    )
    if quiet_enabled:
        qc1, qc2 = st.columns(2)
        with qc1:
            quiet_start = st.number_input(
                "Start hour (24h)", min_value=0, max_value=23,
                value=int(quiet_prefs.get("start", 22)), key="quiet_start",
            )
        with qc2:
            quiet_end = st.number_input(
                "End hour (24h)", min_value=0, max_value=23,
                value=int(quiet_prefs.get("end", 7)), key="quiet_end",
            )
        if (quiet_enabled != quiet_prefs.get("enabled", False)
                or quiet_start != quiet_prefs.get("start", 22)
                or quiet_end != quiet_prefs.get("end", 7)):
            quiet_prefs["enabled"] = quiet_enabled
            quiet_prefs["start"] = quiet_start
            quiet_prefs["end"] = quiet_end
            notif_prefs["quiet_hours"] = quiet_prefs
            settings["notifications"] = notif_prefs
            _save_settings(settings)
    elif quiet_enabled != quiet_prefs.get("enabled", False):
        quiet_prefs["enabled"] = False
        notif_prefs["quiet_hours"] = quiet_prefs
        settings["notifications"] = notif_prefs
        _save_settings(settings)

    st.markdown("---")
    if st.button(t("test_notification"), width='stretch'):
        from utils.notifications import create_notification
        create_notification(
            "info", "system", "Test Notification",
            "This is a test notification from FinanceKit settings.",
            priority="important",
        )
        st.toast("Test notification sent!")
        st.rerun()


def _render_modules(settings):
    """Module toggles."""
    st.markdown(f"### {t('enabled_modules')}")
    st.caption("Toggle modules on or off. Disabled modules are hidden from the sidebar and dashboard.")

    ALL_MODULES = [
        {"key": "budget", "name": t("budget_tracker"),
         "desc": "Set monthly budgets by category and track spending."},
        {"key": "goals", "name": t("goal_tracker"),
         "desc": "Savings goals with projections, milestones, and progress charts."},
        {"key": "receipts", "name": t("receipt_scanner"),
         "desc": "Scan PDFs & photos. Extract vendor, date, total with OCR."},
        {"key": "portfolio", "name": t("portfolio_tracker"),
         "desc": "Track stocks & crypto with live prices, alerts, and allocation charts."},
        {"key": "reports", "name": t("report_generator"),
         "desc": "Upload transactions, get a polished PDF report with charts."},
        {"key": "freelance", "name": t("freelance_dashboard"),
         "desc": "Track clients, log work, generate invoices."},
        {"key": "subscriptions", "name": t("subscription_auditor"),
         "desc": "Find recurring charges and forgotten subscriptions."},
    ]
    ALL_KEYS = [m["key"] for m in ALL_MODULES]

    enabled = settings.get("enabled_modules", ALL_KEYS.copy())
    _mod_changed = False

    for m in ALL_MODULES:
        val = st.toggle(
            f"**{m['name']}** --- {m['desc']}",
            value=m["key"] in enabled,
            key=f"settings_mod_{m['key']}",
        )
        if val and m["key"] not in enabled:
            enabled.append(m["key"])
            _mod_changed = True
        elif not val and m["key"] in enabled:
            enabled.remove(m["key"])
            _mod_changed = True

    if _mod_changed:
        settings["enabled_modules"] = enabled
        _save_settings(settings)
        # Clear the cached module list so sidebar picks up changes immediately
        st.session_state.pop("fk_enabled_modules", None)
        st.toast("Module preferences updated!", icon="\u2705")
        st.rerun()

    st.markdown("---")

    # Categories
    st.markdown(f"### {t('categories')}")
    st.caption("Manage categories used in the Budget Tracker.")

    from modules.budget_tracker import DEFAULT_CATEGORIES

    custom_cats = settings.get("custom_categories", [])
    if not custom_cats:
        custom_cats = [{"name": c, "hidden": False, "tax_deductible": False} for c in DEFAULT_CATEGORIES]
        settings["custom_categories"] = custom_cats
        _save_settings(settings)

    for i, cat in enumerate(custom_cats):
        c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
        with c1:
            st.markdown(f"{'~~' + cat['name'] + '~~' if cat.get('hidden') else cat['name']}")
        with c2:
            hidden = st.checkbox(
                "Hide", value=cat.get("hidden", False),
                key=f"hide_cat_{i}", label_visibility="collapsed",
                help="Hide from dropdowns",
            )
            if hidden != cat.get("hidden", False):
                custom_cats[i]["hidden"] = hidden
                settings["custom_categories"] = custom_cats
                _save_settings(settings)
                st.rerun()
        with c3:
            tax_ded = st.checkbox(
                "Tax", value=cat.get("tax_deductible", False),
                key=f"tax_cat_{i}", label_visibility="collapsed",
                help="Tax-deductible",
            )
            if tax_ded != cat.get("tax_deductible", False):
                custom_cats[i]["tax_deductible"] = tax_ded
                settings["custom_categories"] = custom_cats
                _save_settings(settings)
                st.rerun()
        with c4:
            if cat["name"] not in DEFAULT_CATEGORIES:
                if st.button("Delete", key=f"del_cat_{i}"):
                    custom_cats.pop(i)
                    settings["custom_categories"] = custom_cats
                    _save_settings(settings)
                    st.rerun()

    with st.form("add_category_form"):
        new_cat_name = st.text_input("New category name", placeholder="e.g. Pet Care")
        if st.form_submit_button(t("add")):
            if new_cat_name and new_cat_name.strip():
                existing_names = [c["name"].lower() for c in custom_cats]
                if new_cat_name.strip().lower() in existing_names:
                    st.error("Category already exists.")
                else:
                    custom_cats.append({
                        "name": new_cat_name.strip(),
                        "hidden": False,
                        "tax_deductible": False,
                    })
                    settings["custom_categories"] = custom_cats
                    _save_settings(settings)
                    st.toast(f"Category '{new_cat_name.strip()}' added!", icon="\u2705")
                    st.rerun()

    st.markdown("---")

    # Re-run onboarding
    if st.button("Re-run Onboarding Wizard", width='stretch'):
        settings.pop("onboarding_complete", None)
        settings.pop("onboarding_completed_at", None)
        _save_settings(settings)
        st.toast("Onboarding reset! Refresh the page.", icon="\u2705")


def _render_data_privacy(settings):
    """Data management, accounts, liabilities, import/export."""
    st.markdown(f"### {t('data_management')}")
    st.info("Your data is stored per-account and never shared. All data stays on this server.")

    # Accounts
    st.markdown(f"#### {t('accounts')}")
    st.caption("Track bank accounts, credit cards, and cash. Balances are included in your net worth.")

    accounts = load_json("accounts.json", default=[])
    ACCOUNT_TYPES = ["checking", "savings", "credit", "cash", "investment"]
    ACCOUNT_COLORS = ["#6366f1", "#22c55e", "#ef4444", "#f59e0b", "#8b5cf6",
                      "#06b6d4", "#ec4899", "#14b8a6"]

    with st.form("add_account_form", clear_on_submit=True):
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            acc_name = st.text_input("Account Name", placeholder="e.g. Chase Checking")
            acc_type = st.selectbox("Type", ACCOUNT_TYPES)
        with ac2:
            acc_inst = st.text_input("Institution", placeholder="e.g. Chase, Wells Fargo")
            acc_last4 = st.text_input("Last 4 Digits", placeholder="1234", max_chars=4)
        with ac3:
            acc_balance = st.number_input("Current Balance", step=100.0, format="%.2f")
            acc_color = st.selectbox("Color", ACCOUNT_COLORS,
                                     format_func=lambda c: f"{c}")
        if st.form_submit_button(t("add"), type="primary", width='stretch'):
            if acc_name.strip():
                import uuid
                accounts.append({
                    "id": str(uuid.uuid4())[:8],
                    "name": acc_name.strip(),
                    "type": acc_type,
                    "institution": acc_inst.strip(),
                    "last_four": acc_last4.strip(),
                    "balance": acc_balance,
                    "color": acc_color,
                    "is_default": len(accounts) == 0,
                    "created_at": datetime.now().isoformat(),
                })
                save_json("accounts.json", accounts)
                st.toast(f"Account '{acc_name.strip()}' added!", icon="\u2705")
                st.rerun()

    if accounts:
        type_icons = {"checking": "[CHK]", "savings": "[SAV]", "credit": "[CC]",
                      "cash": "[CASH]", "investment": "[INV]"}
        for i, acc in enumerate(accounts):
            ac1, ac2, ac3, ac4 = st.columns([3, 1, 1, 1])
            with ac1:
                icon = type_icons.get(acc.get("type", ""), "[CHK]")
                last4 = f" ····{acc['last_four']}" if acc.get("last_four") else ""
                default_tag = " (default)" if acc.get("is_default") else ""
                st.markdown(f"{icon} **{acc['name']}**{last4}{default_tag} --- "
                            f"{format_currency(acc.get('balance', 0))}")
            with ac2:
                if not acc.get("is_default"):
                    if st.button("Set Default", key=f"def_acc_{i}", width='stretch'):
                        for a in accounts:
                            a["is_default"] = False
                        accounts[i]["is_default"] = True
                        save_json("accounts.json", accounts)
                        st.rerun()
            with ac3:
                new_bal = st.number_input("Balance", value=float(acc.get("balance", 0)),
                                          key=f"bal_acc_{i}", label_visibility="collapsed",
                                          step=100.0, format="%.2f")
                if new_bal != acc.get("balance", 0):
                    accounts[i]["balance"] = new_bal
                    save_json("accounts.json", accounts)
            with ac4:
                if st.button("Delete", key=f"del_acc_{i}", width='stretch'):
                    accounts.pop(i)
                    save_json("accounts.json", accounts)
                    st.rerun()
    else:
        st.info("No accounts added yet. Add your bank accounts above.")

    st.markdown("---")

    # Liabilities
    st.markdown(f"#### {t('liabilities')}")
    st.caption("Track debts and loans. These are subtracted from assets to calculate net worth.")

    liabilities = load_json("liabilities.json", default=[])

    with st.form("add_liability_form", clear_on_submit=True):
        lc1, lc2, lc3, lc4 = st.columns(4)
        with lc1:
            l_name = st.text_input("Name", placeholder="Credit Card, Student Loan...")
        with lc2:
            l_balance = st.number_input("Balance ($)", min_value=0.0, step=100.0, format="%.2f")
        with lc3:
            l_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
        with lc4:
            l_payment = st.number_input("Monthly Payment ($)", min_value=0.0, step=25.0, format="%.2f")
        if st.form_submit_button(t("add"), key="add_liability_btn", width='stretch'):
            if l_name.strip():
                liabilities.append({
                    "name": l_name.strip(),
                    "balance": l_balance,
                    "interest_rate": l_rate,
                    "monthly_payment": l_payment,
                })
                save_json("liabilities.json", liabilities)
                st.toast(f"Added '{l_name.strip()}'!", icon="\u2705")
                st.rerun()

    if liabilities:
        import pandas as pd
        l_df = pd.DataFrame(liabilities)
        l_df.columns = ["Name", "Balance ($)", "Interest Rate (%)", "Monthly Payment ($)"]
        st.dataframe(l_df, width='stretch', hide_index=True)

        total_debt = sum(float(l.get("balance", 0)) for l in liabilities)
        total_monthly = sum(float(l.get("monthly_payment", 0)) for l in liabilities)
        lm1, lm2 = st.columns(2)
        lm1.metric("Total Debt", format_currency_int(total_debt))
        lm2.metric("Total Monthly Payments", format_currency_int(total_monthly))

        with st.expander("Edit Liabilities"):
            for i, l in enumerate(liabilities):
                _lc1, _lc2 = st.columns([4, 1])
                with _lc1:
                    st.markdown(f"**{l['name']}** --- {format_currency_int(l['balance'])}")
                with _lc2:
                    if st.button("Delete", key=f"del_liability_{i}", width='stretch'):
                        liabilities.pop(i)
                        save_json("liabilities.json", liabilities)
                        st.toast("Liability removed.")
                        st.rerun()

    st.markdown("---")

    # Data file stats
    st.markdown("**Data Files**")
    stats = _data_file_stats()
    if stats:
        import pandas as pd
        st.dataframe(pd.DataFrame(stats), width='stretch', hide_index=True)

    st.markdown("---")

    # Export / Import / Reset
    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        st.markdown(f"**{t('export_data')}**")
        if st.button(t("export_data"), key="export_btn", width='stretch'):
            try:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for fn in os.listdir(DATA_DIR):
                        fp = os.path.join(DATA_DIR, fn)
                        if os.path.isfile(fp) and fn.endswith(".json"):
                            zf.write(fp, fn)
                zip_buffer.seek(0)
                st.session_state["export_zip"] = zip_buffer.getvalue()
                st.toast("Export ready!", icon="\u2705")
            except Exception as e:
                st.error(f"Export failed: {e}")

        if "export_zip" in st.session_state:
            st.download_button(
                "Download ZIP",
                data=st.session_state["export_zip"],
                file_name=f"financekit_backup_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip",
                width='stretch',
            )

    with dc2:
        st.markdown(f"**{t('import_data')}**")
        import_file = st.file_uploader("Upload ZIP", type=["zip"], key="import_zip", label_visibility="collapsed")
        if import_file and st.button(t("import_data"), key="import_btn", width='stretch'):
            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                restored = []
                with zipfile.ZipFile(io.BytesIO(import_file.read()), "r") as zf:
                    for name in zf.namelist():
                        if name.endswith(".json"):
                            zf.extract(name, DATA_DIR)
                            restored.append(name)
                st.toast(f"Imported {len(restored)} file(s)!", icon="\u2705")
                if restored:
                    st.success("Restored: " + ", ".join(restored))
            except Exception as e:
                st.error(f"Import failed: {e}")

    with dc3:
        st.markdown(f"**{t('reset_data')}**")
        if "confirm_reset" not in st.session_state:
            st.session_state.confirm_reset = False

        if not st.session_state.confirm_reset:
            if st.button(t("reset_data"), key="reset_btn", width='stretch'):
                st.session_state.confirm_reset = True
                st.rerun()
        else:
            st.warning("This will delete ALL data files. Backups will be kept.")
            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button(t("cancel"), key="cancel_reset", width='stretch'):
                    st.session_state.confirm_reset = False
                    st.rerun()
            with rc2:
                if st.button(t("confirm_delete"), type="primary", key="confirm_reset_btn", width='stretch'):
                    deleted = 0
                    for fn in os.listdir(DATA_DIR):
                        fp = os.path.join(DATA_DIR, fn)
                        if os.path.isfile(fp) and fn.endswith(".json"):
                            os.remove(fp)
                            deleted += 1
                    st.session_state.confirm_reset = False
                    st.toast(f"Deleted {deleted} data file(s).")
                    st.rerun()

    # Auto-import folder
    st.markdown("---")
    st.markdown(f"### {t('auto_import')}")
    st.caption("Set a watch folder. FinanceKit checks for new bank statement CSVs on startup.")

    auto_import_settings = settings.get("auto_import", {"enabled": False, "folder": "", "last_check": ""})

    ai_enabled = st.checkbox("Enable auto-import",
                              value=auto_import_settings.get("enabled", False),
                              key="auto_import_enabled")
    ai_folder = st.text_input("Watch folder path",
                               value=auto_import_settings.get("folder", ""),
                               placeholder="C:/Users/you/Downloads",
                               key="auto_import_folder")

    if ai_enabled != auto_import_settings.get("enabled", False) or ai_folder != auto_import_settings.get("folder", ""):
        settings["auto_import"] = {
            "enabled": ai_enabled,
            "folder": ai_folder,
            "last_check": auto_import_settings.get("last_check", ""),
        }
        _save_settings(settings)
        st.toast("Auto-import settings saved!", icon="\u2705")

    if ai_enabled and ai_folder:
        if os.path.isdir(ai_folder):
            csv_files = [f for f in os.listdir(ai_folder)
                         if f.lower().endswith((".csv", ".ofx", ".qfx"))]
            st.caption(f"Found {len(csv_files)} importable file(s) in folder.")
        else:
            st.warning("Folder path does not exist.")


def _render_authentication(settings):
    """Authentication settings."""
    st.markdown(f"### {t('authentication')}")

    from utils.auth import (
        load_auth_config, save_auth_config, get_user_count,
        register_user,
    )

    auth_cfg = load_auth_config()

    # Master toggle
    require_auth = st.toggle(
        "Require authentication",
        value=auth_cfg.get("require_auth", False),
        help="When enabled, users must sign in before accessing the app.",
    )

    if require_auth != auth_cfg.get("require_auth", False):
        if require_auth and get_user_count() == 0:
            st.warning("No users exist yet. Create the first account below.")
            with st.form("first_user_form"):
                fu_name = st.text_input(t("display_name"))
                fu_email = st.text_input(t("email"))
                fu_pass = st.text_input(t("password"), type="password")
                fu_confirm = st.text_input(t("confirm") + " " + t("password"), type="password")
                if st.form_submit_button(t("create_account"), type="primary", width='stretch'):
                    if fu_pass != fu_confirm:
                        st.error("Passwords don't match.")
                    elif not fu_email or "@" not in fu_email:
                        st.error("Please enter a valid email.")
                    else:
                        success, msg = register_user(fu_email, fu_pass, fu_name)
                        if success:
                            auth_cfg["require_auth"] = True
                            save_auth_config(auth_cfg)
                            st.toast("Admin account created! Auth enabled.", icon="\u2705")
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            auth_cfg["require_auth"] = require_auth
            save_auth_config(auth_cfg)
            st.toast(f"Authentication {'enabled' if require_auth else 'disabled'}.", icon="\u2705")
            st.rerun()

    st.markdown(f"**Registered users:** {get_user_count()}")

    # Session expiry
    st.markdown("---")
    st.markdown("**Session Settings**")
    expiry = st.number_input(
        "Session expiry (hours)",
        min_value=1, max_value=720, value=int(auth_cfg.get("session_expiry_hours", 24)),
        step=1, help="How long before sign-in is required again.",
    )
    if expiry != auth_cfg.get("session_expiry_hours", 24):
        auth_cfg["session_expiry_hours"] = expiry
        save_auth_config(auth_cfg)
        st.toast("Session expiry updated.", icon="\u2705")

    # OAuth providers
    st.markdown("---")
    st.markdown("**OAuth Providers**")

    # Google
    with st.expander("Google OAuth 2.0"):
        google_cfg = auth_cfg.get("google", {})
        g_status = "\u2705 Configured" if google_cfg.get("client_id") and google_cfg.get("client_secret") else "Not configured"
        st.markdown(f"**Status:** {g_status}")
        with st.form("google_oauth_form"):
            g_id = st.text_input("Client ID", value=google_cfg.get("client_id", ""),
                                 placeholder="xxxx.apps.googleusercontent.com")
            g_secret = st.text_input("Client Secret", value=google_cfg.get("client_secret", ""),
                                      type="password")
            if st.form_submit_button(t("save"), width='stretch'):
                auth_cfg["google"] = {"client_id": g_id, "client_secret": g_secret}
                save_auth_config(auth_cfg)
                st.toast("Google OAuth saved!", icon="\u2705")
                st.rerun()

        with st.expander("Setup instructions"):
            st.markdown("""
1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create project > **APIs & Services** > **OAuth consent screen**
3. **Credentials** > **Create** > **OAuth 2.0 Client ID** > Web application
4. Add your URL to **Authorized redirect URIs**
5. Copy Client ID and Secret above
            """)

    # GitHub
    with st.expander("GitHub OAuth"):
        github_cfg = auth_cfg.get("github", {})
        gh_status = "\u2705 Configured" if github_cfg.get("client_id") and github_cfg.get("client_secret") else "Not configured"
        st.markdown(f"**Status:** {gh_status}")
        with st.form("github_oauth_form"):
            gh_id = st.text_input("Client ID", value=github_cfg.get("client_id", ""))
            gh_secret = st.text_input("Client Secret", value=github_cfg.get("client_secret", ""),
                                       type="password")
            if st.form_submit_button(t("save"), width='stretch'):
                auth_cfg["github"] = {"client_id": gh_id, "client_secret": gh_secret}
                save_auth_config(auth_cfg)
                st.toast("GitHub OAuth saved!", icon="\u2705")
                st.rerun()

        with st.expander("Setup instructions"):
            st.markdown("""
1. Go to [github.com/settings/developers](https://github.com/settings/developers)
2. **New OAuth App** > Set name, homepage URL, callback URL
3. Copy Client ID and generate Client Secret above
            """)


def _render_household(settings):
    """Household mode."""
    st.markdown(f"### {t('household_mode')}")
    st.caption("Share budgets, split expenses, and track goals with family members.")

    from utils.household import (
        get_household, enable_household, disable_household,
        add_member, remove_member, regenerate_invite_code,
    )
    hh = get_household()
    hh_enabled = hh.get("enabled", False)

    if not hh_enabled:
        with st.form("enable_household_form"):
            hh_name = st.text_input("Household Name", placeholder="The Smiths")
            owner_name = st.text_input("Your Name", value=settings.get("user_name", ""),
                                       placeholder="Your display name")
            if st.form_submit_button("Enable Household Mode", type="primary"):
                if hh_name and owner_name:
                    hh = enable_household(hh_name.strip(), owner_name.strip())
                    st.toast("Household mode enabled!", icon="\u2705")
                    st.rerun()
                else:
                    st.error("Please fill in both fields.")
    else:
        st.success(f"Household **{hh.get('name', '')}** is active.")

        # Invite code
        st.markdown("**Invite Code**")
        st.code(hh.get("invite_code", ""), language=None)
        st.caption("Share this code with family members.")
        if st.button("Regenerate Code"):
            new_code = regenerate_invite_code()
            st.toast(f"New invite code: {new_code}", icon="\u2705")
            st.rerun()

        # Join household
        with st.expander("Join a Household"):
            from utils.household import join_household
            with st.form("join_household_form"):
                join_code = st.text_input("Invite Code")
                join_name = st.text_input("Your Name")
                if st.form_submit_button("Join"):
                    if join_code and join_name:
                        member, msg = join_household(join_code.strip().upper(), join_name.strip())
                        if member:
                            st.toast(msg, icon="\u2705")
                            st.rerun()
                        else:
                            st.error(msg)

        # Members
        st.markdown("**Members**")
        members = hh.get("members", [])
        for m in members:
            mc1, mc2 = st.columns([4, 1])
            with mc1:
                role_badge = " (owner)" if m.get("role") == "owner" else ""
                st.markdown(f"**{m['name']}**{role_badge}")
            with mc2:
                if m.get("role") != "owner":
                    if st.button("Remove", key=f"rm_member_{m['id']}"):
                        remove_member(m["id"])
                        st.toast(f"Removed {m['name']}", icon="\u2705")
                        st.rerun()

        with st.form("add_member_form"):
            new_member_name = st.text_input(t("add") + " Member", placeholder="Partner, Child, etc.")
            if st.form_submit_button(t("add")):
                if new_member_name and new_member_name.strip():
                    add_member(new_member_name.strip())
                    st.toast(f"Added {new_member_name.strip()}!", icon="\u2705")
                    st.rerun()

        # Sharing preferences
        st.markdown("**Sharing Preferences**")
        from utils.household import _load_household, _save_household
        shared_budgets = st.checkbox("Share budgets", value=hh.get("shared_budgets", True),
                                      key="hh_share_budgets")
        shared_goals = st.checkbox("Share goals", value=hh.get("shared_goals", True),
                                    key="hh_share_goals")
        if shared_budgets != hh.get("shared_budgets", True) or shared_goals != hh.get("shared_goals", True):
            hh_data = _load_household()
            hh_data["shared_budgets"] = shared_budgets
            hh_data["shared_goals"] = shared_goals
            _save_household(hh_data)
            st.rerun()

        st.markdown("---")
        if st.button("Disable Household Mode"):
            disable_household()
            st.toast("Household mode disabled.", icon="\u2705")
            st.rerun()


def _render_email_smtp(settings):
    """Email / SMTP configuration."""
    st.markdown(f"### {t('email_config')}")
    st.caption("Configure SMTP for report emailing and notification digests.")

    smtp = settings.get("email_smtp", DEFAULT_SETTINGS["email_smtp"])

    with st.form("smtp_form"):
        ec1, ec2 = st.columns(2)
        with ec1:
            smtp_server = st.text_input("SMTP Server", value=smtp.get("server", ""), placeholder="smtp.gmail.com")
            smtp_email = st.text_input(t("email_address"), value=smtp.get("email", ""), placeholder="you@gmail.com")
        with ec2:
            smtp_port = st.number_input("Port", value=int(smtp.get("port", 587)), step=1, min_value=1)
            smtp_password = st.text_input("App Password", value=smtp.get("password", ""), type="password")

        if st.form_submit_button(t("save"), type="primary", width='stretch'):
            settings["email_smtp"] = {
                "server": smtp_server,
                "port": smtp_port,
                "email": smtp_email,
                "password": smtp_password,
            }
            _save_settings(settings)
            st.toast("Email settings saved!", icon="\u2705")
            st.rerun()

    if st.button(t("test_email"), width='stretch'):
        smtp = settings.get("email_smtp", {})
        if not all([smtp.get("server"), smtp.get("email"), smtp.get("password")]):
            st.error("Please fill in and save all SMTP fields first.")
        else:
            try:
                import smtplib
                from email.mime.text import MIMEText
                msg = MIMEText("This is a test email from FinanceKit. Your SMTP settings are working!")
                msg["Subject"] = "FinanceKit --- Test Email"
                msg["From"] = smtp["email"]
                msg["To"] = smtp["email"]
                with smtplib.SMTP(smtp["server"], int(smtp["port"])) as server:
                    server.starttls()
                    server.login(smtp["email"], smtp["password"])
                    server.send_message(msg)
                st.toast("Test email sent!", icon="\u2705")
            except Exception as e:
                st.error(f"Failed: {e}")

    with st.expander("How to get a Gmail App Password"):
        st.markdown("""
1. Go to [myaccount.google.com](https://myaccount.google.com/) > **Security**
2. Turn on **2-Step Verification**
3. Go back > **2-Step Verification** > scroll to **App passwords**
4. Generate for **Mail** > Copy the 16-character password
5. Use `smtp.gmail.com` / port `587`
        """)


def _render_invoice_freelance(settings):
    """Invoice & freelance settings."""
    st.markdown(f"### {t('invoice_freelance')}")

    inv_settings = settings.get("invoice", {})

    with st.form("invoice_settings_form"):
        st.markdown("**Company / Business Info**")
        ivc1, ivc2 = st.columns(2)
        with ivc1:
            inv_company = st.text_input(
                "Company Name",
                value=inv_settings.get("company_name", settings.get("user_name", "")),
                placeholder="Your Company LLC",
            )
            inv_address = st.text_input(
                "Address",
                value=inv_settings.get("company_address", ""),
                placeholder="123 Main St, City, State",
            )
            inv_email = st.text_input(
                "Business Email",
                value=inv_settings.get("company_email", settings.get("user_email", "")),
            )
        with ivc2:
            inv_phone = st.text_input(
                "Phone",
                value=inv_settings.get("company_phone", ""),
            )
            inv_payment = st.text_input(
                "Payment Details",
                value=inv_settings.get("payment_details", ""),
                placeholder="Bank: Acme / Acct: 1234 OR PayPal: you@email.com",
            )
            inv_footer = st.text_input(
                "Invoice Footer",
                value=inv_settings.get("footer_text", "Thank you for your business!"),
            )

        st.markdown("**Defaults**")
        dvc1, dvc2, dvc3 = st.columns(3)
        with dvc1:
            inv_tax_rate = st.number_input(
                "Default Tax Rate (%)",
                min_value=0.0, max_value=50.0, step=0.5,
                value=float(inv_settings.get("tax_rate", 0)),
            )
        with dvc2:
            from utils.invoice_templates import TEMPLATES
            template_names = list(TEMPLATES.keys())
            current_template = inv_settings.get("default_template", "Professional")
            t_idx = template_names.index(current_template) if current_template in template_names else 1
            inv_default_template = st.selectbox("Default Template", template_names, index=t_idx)
        with dvc3:
            inv_est_tax_rate = st.number_input(
                "Freelance Tax Estimate (%)",
                min_value=0.0, max_value=60.0, step=1.0,
                value=float(inv_settings.get("tax_rate", 25)),
            )

        if st.form_submit_button(t("save"), type="primary", width='stretch'):
            settings["invoice"] = {
                "company_name": inv_company,
                "company_address": inv_address,
                "company_email": inv_email,
                "company_phone": inv_phone,
                "payment_details": inv_payment,
                "footer_text": inv_footer,
                "tax_rate": inv_est_tax_rate,
                "default_template": inv_default_template,
                "logo_base64": inv_settings.get("logo_base64", ""),
            }
            _save_settings(settings)
            st.toast("Invoice settings saved!", icon="\u2705")
            st.rerun()

    # Logo upload
    st.markdown("---")
    st.markdown("**Logo**")
    st.caption("Upload a logo for your invoices (PNG or JPG, max 500KB).")
    logo_file = st.file_uploader("Upload Logo", type=["png", "jpg", "jpeg"], key="logo_upload")
    if logo_file:
        logo_bytes = logo_file.read()
        if len(logo_bytes) > 512000:
            st.error("Logo must be under 500KB.")
        else:
            import base64
            logo_b64 = base64.b64encode(logo_bytes).decode("utf-8")
            inv_settings["logo_base64"] = logo_b64
            settings["invoice"] = {**settings.get("invoice", {}), "logo_base64": logo_b64}
            _save_settings(settings)
            st.toast("Logo uploaded!", icon="\u2705")
            st.rerun()

    if inv_settings.get("logo_base64"):
        st.success("Logo is set.")
        if st.button("Remove Logo"):
            inv_settings.pop("logo_base64", None)
            settings["invoice"] = {**settings.get("invoice", {}), "logo_base64": ""}
            _save_settings(settings)
            st.toast("Logo removed.")
            st.rerun()


def _render_sharing(settings):
    """Sharing section."""
    st.markdown(f"### {t('sharing')}")
    st.caption("Share a read-only view of your finances with a partner or advisor.")

    from utils.sharing import create_share_link, get_active_shares, revoke_share

    with st.form("create_share_form"):
        share_name = settings.get("user_name", "") or st.session_state.get("user_name", "User")

        share_modules_opts = {
            "All modules": None,
            "Dashboard only": ["dashboard"],
            "Budget & Goals": ["budget", "goals"],
            "Portfolio only": ["portfolio"],
        }
        share_scope = st.selectbox("What to share", list(share_modules_opts.keys()), key="share_scope")

        sc1, sc2 = st.columns(2)
        with sc1:
            share_expiry = st.selectbox("Expires after", ["24 hours", "7 days", "30 days", "Never"], index=1, key="share_expiry")
        with sc2:
            share_password = st.text_input("Password (optional)", type="password", key="share_pw")

        share_type = st.selectbox("Share type", ["Standard (read-only)", "Financial Advisor"], key="share_type")

        if st.form_submit_button("Generate Share Link", type="primary", width='stretch'):
            from utils.sharing import EXPIRY_OPTIONS
            expiry_hrs = EXPIRY_OPTIONS.get(share_expiry, 168)
            share_type_val = "advisor" if "Advisor" in share_type else "standard"
            share = create_share_link(
                user_name=share_name,
                modules=share_modules_opts[share_scope],
                expiry_hours=expiry_hrs,
                password=share_password if share_password else None,
                share_type=share_type_val,
            )
            st.session_state["last_share_token"] = share["token"]
            st.success("Share link created!")

    if st.session_state.get("last_share_token"):
        _token = st.session_state["last_share_token"]
        # Build absolute URL so the link actually works when shared
        import streamlit as _st_share
        _base_url = os.environ.get("FINANCEKIT_URL", "").rstrip("/")
        if not _base_url:
            # Try to detect from Streamlit's server config
            try:
                from streamlit import config as _st_cfg
                _port = _st_cfg.get_option("server.port") or 8501
                _base_url = f"http://localhost:{_port}"
            except Exception:
                _base_url = "http://localhost:8501"
        _share_url = f"{_base_url}/?share={_token}"
        st.code(_share_url, language=None)
        st.caption("Copy this link and send it to the person you want to share with.")

    active_shares = get_active_shares()
    if active_shares:
        st.markdown("---")
        st.markdown(f"**Active Share Links** ({len(active_shares)})")
        for _sh in active_shares:
            _sh_token = _sh["token"][:12] + "..."
            _sh_type = "Advisor" if _sh.get("share_type") == "advisor" else "Read-only"
            _sh_expires = _sh.get("expiry", "Never")
            if _sh_expires and _sh_expires != "Never":
                try:
                    _sh_expires = datetime.fromisoformat(_sh_expires).strftime("%b %d, %Y")
                except Exception:
                    pass
            else:
                _sh_expires = "Never"
            _sh_views = _sh.get("access_count", 0)

            st.markdown(
                f'<div style="padding:8px 12px;background:var(--fk-card-alt);border-radius:8px;margin-bottom:6px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span style="color:var(--fk-text);font-size:0.88rem;">{_sh_type} · {_sh_token}</span>'
                f'<span style="color:var(--fk-text-muted);font-size:0.78rem;">{_sh_views} views · Expires: {_sh_expires}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Revoke", key=f"revoke_{_sh['token'][:8]}"):
                revoke_share(_sh["token"])
                st.toast("Share link revoked.")
                st.rerun()


def _render_cloud_sync(settings):
    """Cloud sync."""
    st.markdown(f"### {t('cloud_sync')}")
    st.caption("Sync your data across devices as a ZIP bundle.")

    from utils.sync import (
        get_sync_status, is_sync_enabled, get_sync_frequency,
        enable_sync, disable_sync, create_sync_bundle,
        apply_sync_bundle, mark_synced,
    )

    user_id = st.session_state.get("user_id")
    sync_status = get_sync_status(user_id)
    sync_enabled = is_sync_enabled(user_id)
    sync_freq = get_sync_frequency(user_id)

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;padding:8px 12px;'
        f'background:var(--fk-card-alt);border-radius:8px;margin-bottom:12px;">'
        f'<span style="font-size:1.2rem;">{sync_status["icon"]}</span>'
        f'<span style="color:var(--fk-text);font-size:0.9rem;">{sync_status["label"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    sync_toggle = st.toggle("Enable Cloud Sync", value=sync_enabled, key="sync_toggle")
    if sync_toggle != sync_enabled:
        if sync_toggle:
            enable_sync(user_id, sync_freq)
        else:
            disable_sync(user_id)
        st.rerun()

    if sync_enabled:
        freq_options = ["Manual only", "Every 5 minutes", "Every 15 minutes", "Every 30 minutes", "Every 60 minutes"]
        freq_values = ["manual", "5min", "15min", "30min", "60min"]
        current_idx = freq_values.index(sync_freq) if sync_freq in freq_values else 0
        new_freq = st.selectbox("Auto-sync frequency", freq_options, index=current_idx, key="sync_freq")
        new_freq_val = freq_values[freq_options.index(new_freq)]
        if new_freq_val != sync_freq:
            enable_sync(user_id, new_freq_val)

        conflict_options = ["Newest wins", "Cloud wins", "Local wins"]
        conflict_values = ["newest", "cloud", "local"]
        st.selectbox("Conflict resolution", conflict_options, key="sync_conflict")

        st.markdown("---")

        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("Export Sync Bundle", key="sync_export", width='stretch'):
                bundle = create_sync_bundle(user_id)
                if bundle:
                    st.download_button(
                        "Download Bundle",
                        data=bundle,
                        file_name=f"financekit_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        key="sync_download",
                    )
                    mark_synced(user_id)
                    st.success("Sync bundle created!")
                else:
                    st.warning("No data to sync.")

        with sc2:
            uploaded_bundle = st.file_uploader(
                "Import Sync Bundle",
                type=["zip"],
                key="sync_import",
                label_visibility="collapsed",
            )
            if uploaded_bundle:
                conflict_val = conflict_values[conflict_options.index(
                    st.session_state.get("sync_conflict", "Newest wins")
                )]
                result = apply_sync_bundle(
                    uploaded_bundle.read(), user_id, conflict_val
                )
                if result["updated"]:
                    st.success(f"Synced {len(result['updated'])} file(s)")
                if result["conflicts"]:
                    st.info(f"Resolved {len(result['conflicts'])} conflict(s)")
                if result["skipped"]:
                    st.caption(f"Skipped {len(result['skipped'])} unchanged file(s)")


def _render_legal_privacy(settings):
    """Legal & GDPR section."""
    st.markdown(f"### {t('legal_privacy')}")

    tab1, tab2, tab3 = st.tabs(["Terms of Service", "Privacy Policy", "Your Data (GDPR)"])

    with tab1:
        st.markdown("""### Terms of Service

**Last updated:** March 2026

1. **Use at your own risk.** FinanceKit is a personal finance tool, not a financial advisor.
2. **Data ownership.** All data belongs to you. We never sell or share it.
3. **Local storage.** Data is stored on the server where FinanceKit is deployed.
4. **No guarantees.** We do not guarantee uptime or accuracy.
5. **Modifications.** Terms may be updated with new versions.
""")

    with tab2:
        st.markdown("""### Privacy Policy

**Last updated:** March 2026

- **No telemetry.** No analytics, crash reports, or usage data sent externally.
- **Local-first.** All financial data stored as JSON files on your server.
- **No tracking.** No cookies, ad networks, or third-party analytics.
- **API calls.** Only ticker symbols sent to Yahoo Finance for prices.
- **Authentication.** Passwords hashed with bcrypt. Never stored in plain text.
- **Sharing.** Shared links contain only data you choose. Links expire automatically.
""")

    with tab3:
        st.markdown("### Your Data Rights")
        st.markdown("You can **access**, **export**, and **delete** all your data at any time.")

        st.markdown(f"**{t('export_data')}:**")
        if st.button("Download Data Export (ZIP)", key="gdpr_export"):
            try:
                from utils.sync import create_sync_bundle
                _gdpr_zip = create_sync_bundle()
                st.download_button(
                    label="Save ZIP File",
                    data=_gdpr_zip,
                    file_name=f"financekit_data_export_{datetime.now().strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                    key="gdpr_download",
                )
            except Exception as _err:
                st.error(f"Export failed: {_err}")

        st.markdown("---")
        st.markdown(f"**{t('delete')} all data:**")
        st.warning("Permanently deletes all your FinanceKit data. This cannot be undone.")
        _gdpr_confirm = st.text_input(
            t("type_delete"),
            key="gdpr_delete_confirm",
        )
        if st.button("Permanently Delete All Data", type="secondary", key="gdpr_delete"):
            if _gdpr_confirm == "DELETE MY DATA":
                _del_count = 0
                for _del_fn in os.listdir(DATA_DIR):
                    if _del_fn.endswith(".json") and _del_fn != "auth_config.json":
                        try:
                            os.remove(os.path.join(DATA_DIR, _del_fn))
                            _del_count += 1
                        except OSError:
                            pass
                st.success(f"Deleted {_del_count} data file(s). Please refresh.")
                try:
                    from utils.activity_log import log_activity
                    log_activity("deleted", "settings", "GDPR: All user data deleted")
                except Exception:
                    pass
            else:
                st.error('Please type "DELETE MY DATA" exactly to confirm.')


def _render_about(settings):
    """About, health check, logs."""
    st.markdown(f"### {t('about')}")

    version = _get_version()

    st.markdown(
        f"- **{t('version')}:** v{version}\n"
        f"- **Python:** {sys.version.split()[0]}\n"
        f"- **Streamlit:** {st.__version__}\n"
        f"- **Data Directory:** `{DATA_DIR}`"
    )

    st.markdown("---")
    st.markdown("**Links:**")
    st.markdown(
        "- [GitHub Repository](https://github.com/brandocalricia/financekit)\n"
        "- [Gumroad Product Page](https://5207453582610.gumroad.com/l/zbnsjc)"
    )

    st.markdown("---")

    # Check for updates
    if st.button(t("check_updates"), width='stretch'):
        try:
            import requests
            resp = requests.get(
                "https://raw.githubusercontent.com/brandocalricia/financekit/main/version.txt",
                timeout=5,
            )
            if resp.status_code == 200:
                remote_version = resp.text.strip()
                if remote_version == version:
                    st.success(f"{t('up_to_date')} (v{version})")
                else:
                    st.info(
                        f"Version **v{remote_version}** is available! "
                        f"You're on v{version}."
                    )
            else:
                st.warning("Could not check for updates.")
        except Exception:
            st.warning("Could not connect. Check your internet connection.")

    # Logs
    st.markdown("---")
    st.markdown(f"### {t('logs')}")

    from utils.logger import read_log_lines, clear_logs, get_log_path

    lc1, lc2 = st.columns([2, 1])
    with lc1:
        log_level = st.selectbox("Filter by level", ["ALL", "INFO", "WARNING", "ERROR"], key="log_level_filter")
    with lc2:
        log_lines_count = st.number_input("Lines", min_value=10, max_value=500, value=100, step=10)

    log_lines = read_log_lines(max_lines=log_lines_count, level_filter=log_level)
    if log_lines:
        st.code("".join(log_lines), language="text")
    else:
        st.info("No log entries found.")

    lbc1, lbc2 = st.columns(2)
    with lbc1:
        log_path = get_log_path()
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as _lf:
                    _log_content = _lf.read()
                st.download_button(
                    "Download Full Log",
                    data=_log_content.encode("utf-8"),
                    file_name="financekit.log",
                    mime="text/plain",
                    width='stretch',
                )
            except Exception:
                pass
    with lbc2:
        if st.button("Clear Logs", key="clear_logs_btn", width='stretch'):
            clear_logs()
            st.toast("Logs cleared.")
            st.rerun()

    # Health check
    st.markdown("---")
    st.markdown(f"### {t('health_check')}")

    if st.button(t("health_check"), type="primary", key="run_health", width='stretch'):
        checks = []

        py_ver = sys.version.split()[0]
        py_ok = sys.version_info >= (3, 10)
        checks.append(("Python version", py_ok, f"Python {py_ver}"))

        _required_pkgs = [
            ("streamlit", "streamlit"),
            ("pandas", "pandas"),
            ("plotly", "plotly"),
            ("fpdf2", "fpdf"),
            ("yfinance", "yfinance"),
            ("requests", "requests"),
            ("rapidfuzz", "rapidfuzz"),
        ]
        for pkg_name, import_name in _required_pkgs:
            try:
                __import__(import_name)
                checks.append((f"Package: {pkg_name}", True, "installed"))
            except ImportError:
                checks.append((f"Package: {pkg_name}", False, "NOT installed"))

        try:
            _test_fp = os.path.join(DATA_DIR, ".health_check_test")
            with open(_test_fp, "w") as _tf:
                _tf.write("test")
            os.remove(_test_fp)
            checks.append(("Data directory writable", True, DATA_DIR))
        except Exception as _hce:
            checks.append(("Data directory writable", False, str(_hce)))

        _json_ok = True
        _json_err = ""
        for fn in os.listdir(DATA_DIR) if os.path.exists(DATA_DIR) else []:
            fp = os.path.join(DATA_DIR, fn)
            if os.path.isfile(fp) and fn.endswith(".json"):
                try:
                    with open(fp, "r", encoding="utf-8") as _jf:
                        json.load(_jf)
                except json.JSONDecodeError:
                    _json_ok = False
                    _json_err += f"{fn}, "
        checks.append(("All data files valid JSON", _json_ok, _json_err.rstrip(", ") or "All valid"))
        checks.append(("Backup directory exists", os.path.exists(BACKUP_DIR), BACKUP_DIR))

        try:
            import requests as _req
            _ping = _req.get("https://api.coingecko.com/api/v3/ping", timeout=5)
            checks.append(("Internet connectivity", _ping.status_code == 200, "OK"))
        except Exception:
            checks.append(("Internet connectivity", False, "Could not reach external API"))

        _smtp = settings.get("email_smtp", {})
        _smtp_ok = bool(_smtp.get("server") and _smtp.get("email") and _smtp.get("password"))
        checks.append(("SMTP configured", _smtp_ok, "configured" if _smtp_ok else "not configured (optional)"))

        try:
            from utils.migrations import check_pending
            pending = check_pending()
            checks.append(("Migrations", len(pending) == 0,
                            f"{len(pending)} pending" if pending else "Up to date"))
        except Exception:
            checks.append(("Migrations", False, "Could not check"))

        for label, ok, detail in checks:
            icon = "\u2705" if ok else "\u274c"
            st.markdown(f"{icon} **{label}** --- {detail}")


# ── Main render function ─────────────────────────────────────────────

def render():
    render_module_header("\u2699\ufe0f", t("settings"),
                         "Configure your profile, preferences, and app settings.")

    settings = _load_settings()

    # Discord-style: section nav in sidebar-like pills at top
    if "settings_section" not in st.session_state:
        st.session_state.settings_section = "profile"

    # Build nav pills
    nav_cols = st.columns(len(_SECTIONS))
    for i, (key, icon, t_key) in enumerate(_SECTIONS):
        with nav_cols[i]:
            is_active = st.session_state.settings_section == key
            if st.button(
                f"{icon}",
                key=f"settings_nav_{key}",
                type="primary" if is_active else "secondary",
                help=t(t_key),
                width='stretch',
            ):
                st.session_state.settings_section = key
                st.rerun()

    # Show active section label
    active_section = st.session_state.settings_section
    active_label = next((t(t_key) for key, _, t_key in _SECTIONS if key == active_section), "")
    st.markdown(
        f'<div style="padding:4px 0 12px;border-bottom:2px solid #6366f1;margin-bottom:16px;">'
        f'<span style="color:var(--fk-text);font-size:1.1rem;font-weight:600;">{active_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Render active section
    section_map = {
        "profile": _render_profile,
        "appearance": _render_appearance,
        "notifications_title": _render_notifications,
        "modules": _render_modules,
        "data_privacy": _render_data_privacy,
        "authentication": _render_authentication,
        "household": _render_household,
        "email_smtp": _render_email_smtp,
        "invoice_freelance": _render_invoice_freelance,
        "sharing": _render_sharing,
        "cloud_sync": _render_cloud_sync,
        "legal_privacy": _render_legal_privacy,
        "about": _render_about,
    }

    renderer = section_map.get(active_section, _render_profile)
    renderer(settings)
