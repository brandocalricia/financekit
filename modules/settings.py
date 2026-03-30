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
                count = f"{len(data)} {t('st_records')}"
            elif isinstance(data, dict):
                parts = []
                for k, v in data.items():
                    if k.startswith("_"):
                        continue
                    if isinstance(v, list):
                        parts.append(f"{len(v)} {k}")
                    elif isinstance(v, dict):
                        parts.append(f"{len(v)} {k}")
                count = ", ".join(parts) if parts else f"1 {t('st_object')}"
            else:
                count = "---"
        except Exception:
            count = t("st_invalid_json")
        if size < 1024:
            size_str = f"{size} B"
        else:
            size_str = f"{size / 1024:.1f} KB"
        stats.append({t("st_file"): fn, t("st_size"): size_str, t("st_contents"): count})
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
                    new_pw = st.text_input(t("st_new_password"), type="password", key="new_pw")
                    confirm_pw = st.text_input(t("st_confirm_password"), type="password", key="confirm_pw")
                    if st.form_submit_button(t("change_password"), width='stretch'):
                        if new_pw != confirm_pw:
                            st.error(t("st_passwords_dont_match"))
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
            st.info(t("st_signed_in_via_oauth").format(provider=_auth_method.title()))

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
                    st.caption(t("st_no_security_events"))
            except Exception:
                st.caption(t("st_audit_log_unavailable"))

        # Delete account
        st.markdown("---")
        with st.expander(t("delete_account")):
            st.warning(t("st_delete_account_warning"))
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
                            st.toast(t("st_account_deleted"))
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
    st.markdown(f"**{t('st_accent_color')}**")
    st.caption(t("st_accent_color_caption"))
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

    new_accent = st.color_picker(t("st_custom_color"), value=current_accent, key="accent_picker")
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

    notif_prefs = settings.get("notifications", {})

    notif_enabled = st.toggle(
        t("notifications_title"),
        value=notif_prefs.get("enabled", True),
        help=t("st_notif_master_toggle_help"),
    )

    if notif_enabled != notif_prefs.get("enabled", True):
        notif_prefs["enabled"] = notif_enabled
        settings["notifications"] = notif_prefs
        _save_settings(settings)
        st.rerun()

    if not notif_enabled:
        st.info(t("st_notif_all_disabled"))
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
        "bills": t("st_bill_reminders"),
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
                t("st_budget_warning_pct"),
                min_value=50, max_value=100,
                value=int(notif_prefs.get("budget_warn_pct", 80)),
                step=5, help=t("st_budget_warning_help"),
            )
            portfolio_change = st.number_input(
                t("st_portfolio_change_alert_pct"),
                min_value=1, max_value=50,
                value=int(notif_prefs.get("portfolio_change_pct", 5)),
                step=1,
            )
        with tc2:
            sub_threshold = st.number_input(
                t("st_sub_cost_warning"),
                min_value=50, max_value=5000,
                value=int(notif_prefs.get("sub_cost_threshold", 200)),
                step=25,
            )
            invoice_overdue = st.number_input(
                t("st_invoice_overdue_alert_days"),
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
            st.toast(t("st_thresholds_saved"), icon="\u2705")
            st.rerun()

    st.markdown("---")

    # Email digest
    st.markdown(f"**{t('st_email_digest')}**")
    smtp_configured = bool(
        settings.get("email_smtp", {}).get("server")
        and settings.get("email_smtp", {}).get("email")
        and settings.get("email_smtp", {}).get("password")
    )

    if not smtp_configured:
        st.info(t("st_configure_smtp_for_digest"))
    else:
        digest_enabled = st.toggle(
            t("st_enable_email_digest"),
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
                t("st_frequency"),
                ["daily", "weekly"],
                index=0 if notif_prefs.get("digest_frequency", "daily") == "daily" else 1,
            )
            if freq != notif_prefs.get("digest_frequency", "daily"):
                notif_prefs["digest_frequency"] = freq
                settings["notifications"] = notif_prefs
                _save_settings(settings)

            last_sent = notif_prefs.get("last_digest_sent", "")
            if last_sent:
                st.caption(f"{t('st_last_sent')}: {last_sent[:19].replace('T', ' ')}")

            if st.button(t("st_send_digest_now"), width='stretch'):
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
    st.caption(t("st_quiet_hours_caption"))
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
                t("st_start_hour"), min_value=0, max_value=23,
                value=int(quiet_prefs.get("start", 22)), key="quiet_start",
            )
        with qc2:
            quiet_end = st.number_input(
                t("st_end_hour"), min_value=0, max_value=23,
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
            "info", "system", t("st_test_notification_title"),
            t("st_test_notification_body"),
            priority="important",
        )
        st.toast(t("st_test_notification_sent"))
        st.rerun()


def _render_modules(settings):
    """Module toggles."""
    st.caption(t("st_toggle_modules_caption"))

    ALL_MODULES = [
        {"key": "budget", "name": t("budget_tracker"),
         "desc": t("st_mod_desc_budget")},
        {"key": "goals", "name": t("goal_tracker"),
         "desc": t("st_mod_desc_goals")},
        {"key": "receipts", "name": t("receipt_scanner"),
         "desc": t("st_mod_desc_receipts")},
        {"key": "portfolio", "name": t("portfolio_tracker"),
         "desc": t("st_mod_desc_portfolio")},
        {"key": "reports", "name": t("report_generator"),
         "desc": t("st_mod_desc_reports")},
        {"key": "freelance", "name": t("freelance_dashboard"),
         "desc": t("st_mod_desc_freelance")},
        {"key": "subscriptions", "name": t("subscription_auditor"),
         "desc": t("st_mod_desc_subscriptions")},
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
        st.toast(t("st_module_prefs_updated"), icon="\u2705")
        st.rerun()

    st.markdown("---")

    # Categories
    st.markdown(f"### {t('categories')}")
    st.caption(t("st_manage_categories_caption"))

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
                t("st_hide"), value=cat.get("hidden", False),
                key=f"hide_cat_{i}", label_visibility="collapsed",
                help=t("st_hide_from_dropdowns"),
            )
            if hidden != cat.get("hidden", False):
                custom_cats[i]["hidden"] = hidden
                settings["custom_categories"] = custom_cats
                _save_settings(settings)
                st.rerun()
        with c3:
            tax_ded = st.checkbox(
                t("st_tax"), value=cat.get("tax_deductible", False),
                key=f"tax_cat_{i}", label_visibility="collapsed",
                help=t("st_tax_deductible"),
            )
            if tax_ded != cat.get("tax_deductible", False):
                custom_cats[i]["tax_deductible"] = tax_ded
                settings["custom_categories"] = custom_cats
                _save_settings(settings)
                st.rerun()
        with c4:
            if cat["name"] not in DEFAULT_CATEGORIES:
                if st.button(t("delete"), key=f"del_cat_{i}"):
                    custom_cats.pop(i)
                    settings["custom_categories"] = custom_cats
                    _save_settings(settings)
                    st.rerun()

    with st.form("add_category_form"):
        new_cat_name = st.text_input(t("st_new_category_name"), placeholder=t("st_new_category_placeholder"))
        if st.form_submit_button(t("add")):
            if new_cat_name and new_cat_name.strip():
                existing_names = [c["name"].lower() for c in custom_cats]
                if new_cat_name.strip().lower() in existing_names:
                    st.error(t("st_category_already_exists"))
                else:
                    custom_cats.append({
                        "name": new_cat_name.strip(),
                        "hidden": False,
                        "tax_deductible": False,
                    })
                    settings["custom_categories"] = custom_cats
                    _save_settings(settings)
                    st.toast(t("st_category_added").format(name=new_cat_name.strip()), icon="\u2705")
                    st.rerun()

    st.markdown("---")

    # Re-run onboarding
    if st.button(t("st_rerun_onboarding"), width='stretch'):
        settings.pop("onboarding_complete", None)
        settings.pop("onboarding_completed_at", None)
        _save_settings(settings)
        st.toast(t("st_onboarding_reset"), icon="\u2705")


def _render_data_privacy(settings):
    """Data management, accounts, liabilities, import/export."""
    st.info(t("st_data_privacy_info"))

    # Accounts
    st.markdown(f"#### {t('accounts')}")
    st.caption(t("st_accounts_caption"))

    accounts = load_json("accounts.json", default=[])
    ACCOUNT_TYPES = ["checking", "savings", "credit", "cash", "investment"]
    ACCOUNT_COLORS = ["#6366f1", "#22c55e", "#ef4444", "#f59e0b", "#8b5cf6",
                      "#06b6d4", "#ec4899", "#14b8a6"]

    with st.form("add_account_form", clear_on_submit=True):
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            acc_name = st.text_input(t("st_account_name"), placeholder=t("st_account_name_placeholder"))
            acc_type = st.selectbox(t("st_type"), ACCOUNT_TYPES)
        with ac2:
            acc_inst = st.text_input(t("st_institution"), placeholder=t("st_institution_placeholder"))
            acc_last4 = st.text_input(t("st_last_4_digits"), placeholder="1234", max_chars=4)
        with ac3:
            acc_balance = st.number_input(t("st_current_balance"), step=100.0, format="%.2f")
            acc_color = st.selectbox(t("st_color"), ACCOUNT_COLORS,
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
                st.toast(t("st_account_added").format(name=acc_name.strip()), icon="\u2705")
                st.rerun()

    if accounts:
        type_icons = {"checking": "[CHK]", "savings": "[SAV]", "credit": "[CC]",
                      "cash": "[CASH]", "investment": "[INV]"}
        for i, acc in enumerate(accounts):
            ac1, ac2, ac3, ac4 = st.columns([3, 1, 1, 1])
            with ac1:
                icon = type_icons.get(acc.get("type", ""), "[CHK]")
                last4 = f" ····{acc['last_four']}" if acc.get("last_four") else ""
                default_tag = f" ({t('st_default')})" if acc.get("is_default") else ""
                st.markdown(f"{icon} **{acc['name']}**{last4}{default_tag} --- "
                            f"{format_currency(acc.get('balance', 0))}")
            with ac2:
                if not acc.get("is_default"):
                    if st.button(t("st_set_default"), key=f"def_acc_{i}", width='stretch'):
                        for a in accounts:
                            a["is_default"] = False
                        accounts[i]["is_default"] = True
                        save_json("accounts.json", accounts)
                        st.rerun()
            with ac3:
                new_bal = st.number_input(t("st_balance"), value=float(acc.get("balance", 0)),
                                          key=f"bal_acc_{i}", label_visibility="collapsed",
                                          step=100.0, format="%.2f")
                if new_bal != acc.get("balance", 0):
                    accounts[i]["balance"] = new_bal
                    save_json("accounts.json", accounts)
            with ac4:
                if st.button(t("delete"), key=f"del_acc_{i}", width='stretch'):
                    accounts.pop(i)
                    save_json("accounts.json", accounts)
                    st.rerun()
    else:
        st.info(t("st_no_accounts_yet"))

    st.markdown("---")

    # Liabilities
    st.markdown(f"#### {t('liabilities')}")
    st.caption(t("st_liabilities_caption"))

    liabilities = load_json("liabilities.json", default=[])

    with st.form("add_liability_form", clear_on_submit=True):
        lc1, lc2, lc3, lc4 = st.columns(4)
        with lc1:
            l_name = st.text_input(t("st_name"), placeholder=t("st_liability_name_placeholder"))
        with lc2:
            l_balance = st.number_input(t("st_balance_amount"), min_value=0.0, step=100.0, format="%.2f")
        with lc3:
            l_rate = st.number_input(t("st_interest_rate_pct"), min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
        with lc4:
            l_payment = st.number_input(t("st_monthly_payment"), min_value=0.0, step=25.0, format="%.2f")
        if st.form_submit_button(t("add"), key="add_liability_btn", width='stretch'):
            if l_name.strip():
                liabilities.append({
                    "name": l_name.strip(),
                    "balance": l_balance,
                    "interest_rate": l_rate,
                    "monthly_payment": l_payment,
                })
                save_json("liabilities.json", liabilities)
                st.toast(t("st_liability_added").format(name=l_name.strip()), icon="\u2705")
                st.rerun()

    if liabilities:
        import pandas as pd
        l_df = pd.DataFrame(liabilities)
        l_df.columns = [t("st_name"), t("st_balance_amount"), t("st_interest_rate_pct"), t("st_monthly_payment")]
        st.dataframe(l_df, width='stretch', hide_index=True)

        total_debt = sum(float(l.get("balance", 0)) for l in liabilities)
        total_monthly = sum(float(l.get("monthly_payment", 0)) for l in liabilities)
        lm1, lm2 = st.columns(2)
        lm1.metric(t("st_total_debt"), format_currency_int(total_debt))
        lm2.metric(t("st_total_monthly_payments"), format_currency_int(total_monthly))

        with st.expander(t("st_edit_liabilities")):
            for i, l in enumerate(liabilities):
                _lc1, _lc2 = st.columns([4, 1])
                with _lc1:
                    st.markdown(f"**{l['name']}** --- {format_currency_int(l['balance'])}")
                with _lc2:
                    if st.button(t("delete"), key=f"del_liability_{i}", width='stretch'):
                        liabilities.pop(i)
                        save_json("liabilities.json", liabilities)
                        st.toast(t("st_liability_removed"))
                        st.rerun()

    st.markdown("---")

    # Data file stats
    st.markdown(f"**{t('st_data_files')}**")
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
                st.toast(t("st_export_ready"), icon="\u2705")
            except Exception as e:
                st.error(f"{t('st_export_failed')}: {e}")

        if "export_zip" in st.session_state:
            st.download_button(
                t("st_download_zip"),
                data=st.session_state["export_zip"],
                file_name=f"financekit_backup_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip",
                width='stretch',
            )

    with dc2:
        st.markdown(f"**{t('import_data')}**")
        import_file = st.file_uploader(t("st_upload_zip"), type=["zip"], key="import_zip", label_visibility="collapsed")
        if import_file and st.button(t("import_data"), key="import_btn", width='stretch'):
            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                restored = []
                with zipfile.ZipFile(io.BytesIO(import_file.read()), "r") as zf:
                    for name in zf.namelist():
                        if name.endswith(".json"):
                            zf.extract(name, DATA_DIR)
                            restored.append(name)
                st.toast(t("st_imported_files").format(count=len(restored)), icon="\u2705")
                if restored:
                    st.success(f"{t('st_restored')}: " + ", ".join(restored))
            except Exception as e:
                st.error(f"{t('st_import_failed')}: {e}")

    with dc3:
        st.markdown(f"**{t('reset_data')}**")
        if "confirm_reset" not in st.session_state:
            st.session_state.confirm_reset = False

        if not st.session_state.confirm_reset:
            if st.button(t("reset_data"), key="reset_btn", width='stretch'):
                st.session_state.confirm_reset = True
                st.rerun()
        else:
            st.warning(t("st_reset_data_warning"))
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
                    st.toast(t("st_deleted_data_files").format(count=deleted))
                    st.rerun()

    # Auto-import folder
    st.markdown("---")
    st.markdown(f"### {t('auto_import')}")
    st.caption(t("st_auto_import_caption"))

    auto_import_settings = settings.get("auto_import", {"enabled": False, "folder": "", "last_check": ""})

    ai_enabled = st.checkbox(t("st_enable_auto_import"),
                              value=auto_import_settings.get("enabled", False),
                              key="auto_import_enabled")
    ai_folder = st.text_input(t("st_watch_folder_path"),
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
        st.toast(t("st_auto_import_saved"), icon="\u2705")

    if ai_enabled and ai_folder:
        if os.path.isdir(ai_folder):
            csv_files = [f for f in os.listdir(ai_folder)
                         if f.lower().endswith((".csv", ".ofx", ".qfx"))]
            st.caption(t("st_found_importable_files").format(count=len(csv_files)))
        else:
            st.warning(t("st_folder_not_exist"))


def _render_authentication(settings):
    """Authentication settings."""
    from utils.auth import (
        load_auth_config, save_auth_config, get_user_count,
        register_user,
    )

    auth_cfg = load_auth_config()

    # Master toggle
    require_auth = st.toggle(
        t("st_require_authentication"),
        value=auth_cfg.get("require_auth", False),
        help=t("st_require_auth_help"),
    )

    if require_auth != auth_cfg.get("require_auth", False):
        if require_auth and get_user_count() == 0:
            st.warning(t("st_no_users_yet"))
            with st.form("first_user_form"):
                fu_name = st.text_input(t("display_name"))
                fu_email = st.text_input(t("email"))
                fu_pass = st.text_input(t("password"), type="password")
                fu_confirm = st.text_input(t("st_confirm_password"), type="password")
                if st.form_submit_button(t("create_account"), type="primary", width='stretch'):
                    if fu_pass != fu_confirm:
                        st.error(t("st_passwords_dont_match"))
                    elif not fu_email or "@" not in fu_email:
                        st.error(t("st_enter_valid_email"))
                    else:
                        success, msg = register_user(fu_email, fu_pass, fu_name)
                        if success:
                            auth_cfg["require_auth"] = True
                            save_auth_config(auth_cfg)
                            st.toast(t("st_admin_account_created"), icon="\u2705")
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            auth_cfg["require_auth"] = require_auth
            save_auth_config(auth_cfg)
            st.toast(t("st_auth_toggled").format(state=t("st_enabled") if require_auth else t("st_disabled")), icon="\u2705")
            st.rerun()

    st.markdown(f"**{t('st_registered_users')}:** {get_user_count()}")

    # Session expiry
    st.markdown("---")
    st.markdown(f"**{t('st_session_settings')}**")
    expiry = st.number_input(
        t("st_session_expiry_hours"),
        min_value=1, max_value=720, value=int(auth_cfg.get("session_expiry_hours", 24)),
        step=1, help=t("st_session_expiry_help"),
    )
    if expiry != auth_cfg.get("session_expiry_hours", 24):
        auth_cfg["session_expiry_hours"] = expiry
        save_auth_config(auth_cfg)
        st.toast(t("st_session_expiry_updated"), icon="\u2705")

    # OAuth providers
    st.markdown("---")
    st.markdown(f"**{t('st_oauth_providers')}**")

    # Google
    with st.expander(t("st_google_oauth")):
        google_cfg = auth_cfg.get("google", {})
        g_status = f"\u2705 {t('st_configured')}" if google_cfg.get("client_id") and google_cfg.get("client_secret") else t("st_not_configured")
        st.markdown(f"**{t('st_status')}:** {g_status}")
        with st.form("google_oauth_form"):
            g_id = st.text_input(t("st_client_id"), value=google_cfg.get("client_id", ""),
                                 placeholder="xxxx.apps.googleusercontent.com")
            g_secret = st.text_input(t("st_client_secret"), value=google_cfg.get("client_secret", ""),
                                      type="password")
            if st.form_submit_button(t("save"), width='stretch'):
                auth_cfg["google"] = {"client_id": g_id, "client_secret": g_secret}
                save_auth_config(auth_cfg)
                st.toast(t("st_google_oauth_saved"), icon="\u2705")
                st.rerun()

        with st.expander(t("st_setup_instructions")):
            st.markdown(t("st_google_oauth_instructions"))

    # GitHub
    with st.expander(t("st_github_oauth")):
        github_cfg = auth_cfg.get("github", {})
        gh_status = f"\u2705 {t('st_configured')}" if github_cfg.get("client_id") and github_cfg.get("client_secret") else t("st_not_configured")
        st.markdown(f"**{t('st_status')}:** {gh_status}")
        with st.form("github_oauth_form"):
            gh_id = st.text_input(t("st_client_id"), value=github_cfg.get("client_id", ""))
            gh_secret = st.text_input(t("st_client_secret"), value=github_cfg.get("client_secret", ""),
                                       type="password")
            if st.form_submit_button(t("save"), width='stretch'):
                auth_cfg["github"] = {"client_id": gh_id, "client_secret": gh_secret}
                save_auth_config(auth_cfg)
                st.toast(t("st_github_oauth_saved"), icon="\u2705")
                st.rerun()

        with st.expander(t("st_setup_instructions")):
            st.markdown(t("st_github_oauth_instructions"))


def _render_household(settings):
    """Household mode."""
    st.caption(t("st_household_caption"))

    from utils.household import (
        get_household, enable_household, disable_household,
        add_member, remove_member, regenerate_invite_code,
    )
    hh = get_household()
    hh_enabled = hh.get("enabled", False)

    if not hh_enabled:
        with st.form("enable_household_form"):
            hh_name = st.text_input(t("st_household_name"), placeholder=t("st_household_name_placeholder"))
            owner_name = st.text_input(t("st_your_name"), value=settings.get("user_name", ""),
                                       placeholder=t("st_your_name_placeholder"))
            if st.form_submit_button(t("st_enable_household_mode"), type="primary"):
                if hh_name and owner_name:
                    hh = enable_household(hh_name.strip(), owner_name.strip())
                    st.toast(t("st_household_enabled"), icon="\u2705")
                    st.rerun()
                else:
                    st.error(t("st_fill_both_fields"))
    else:
        st.success(t("st_household_active").format(name=hh.get('name', '')))

        # Invite code
        st.markdown(f"**{t('st_invite_code')}**")
        st.code(hh.get("invite_code", ""), language=None)
        st.caption(t("st_share_invite_code"))
        if st.button(t("st_regenerate_code")):
            new_code = regenerate_invite_code()
            st.toast(t("st_new_invite_code").format(code=new_code), icon="\u2705")
            st.rerun()

        # Join household
        with st.expander(t("st_join_household")):
            from utils.household import join_household
            with st.form("join_household_form"):
                join_code = st.text_input(t("st_invite_code"))
                join_name = st.text_input(t("st_your_name"))
                if st.form_submit_button(t("st_join")):
                    if join_code and join_name:
                        member, msg = join_household(join_code.strip().upper(), join_name.strip())
                        if member:
                            st.toast(msg, icon="\u2705")
                            st.rerun()
                        else:
                            st.error(msg)

        # Members
        st.markdown(f"**{t('st_members')}**")
        members = hh.get("members", [])
        for m in members:
            mc1, mc2 = st.columns([4, 1])
            with mc1:
                role_badge = f" ({t('st_owner')})" if m.get("role") == "owner" else ""
                st.markdown(f"**{m['name']}**{role_badge}")
            with mc2:
                if m.get("role") != "owner":
                    if st.button(t("st_remove"), key=f"rm_member_{m['id']}"):
                        remove_member(m["id"])
                        st.toast(t("st_member_removed").format(name=m['name']), icon="\u2705")
                        st.rerun()

        with st.form("add_member_form"):
            new_member_name = st.text_input(t("st_add_member"), placeholder=t("st_add_member_placeholder"))
            if st.form_submit_button(t("add")):
                if new_member_name and new_member_name.strip():
                    add_member(new_member_name.strip())
                    st.toast(t("st_member_added").format(name=new_member_name.strip()), icon="\u2705")
                    st.rerun()

        # Sharing preferences
        st.markdown(f"**{t('st_sharing_preferences')}**")
        from utils.household import _load_household, _save_household
        shared_budgets = st.checkbox(t("st_share_budgets"), value=hh.get("shared_budgets", True),
                                      key="hh_share_budgets")
        shared_goals = st.checkbox(t("st_share_goals"), value=hh.get("shared_goals", True),
                                    key="hh_share_goals")
        if shared_budgets != hh.get("shared_budgets", True) or shared_goals != hh.get("shared_goals", True):
            hh_data = _load_household()
            hh_data["shared_budgets"] = shared_budgets
            hh_data["shared_goals"] = shared_goals
            _save_household(hh_data)
            st.rerun()

        st.markdown("---")
        if st.button(t("st_disable_household_mode")):
            disable_household()
            st.toast(t("st_household_disabled"), icon="\u2705")
            st.rerun()


def _render_email_smtp(settings):
    """Email / SMTP configuration."""
    st.caption(t("st_smtp_caption"))

    smtp = settings.get("email_smtp", DEFAULT_SETTINGS["email_smtp"])

    with st.form("smtp_form"):
        ec1, ec2 = st.columns(2)
        with ec1:
            smtp_server = st.text_input(t("st_smtp_server"), value=smtp.get("server", ""), placeholder="smtp.gmail.com")
            smtp_email = st.text_input(t("email_address"), value=smtp.get("email", ""), placeholder="you@gmail.com")
        with ec2:
            smtp_port = st.number_input(t("st_port"), value=int(smtp.get("port", 587)), step=1, min_value=1)
            smtp_password = st.text_input(t("st_app_password"), value=smtp.get("password", ""), type="password")

        if st.form_submit_button(t("save"), type="primary", width='stretch'):
            settings["email_smtp"] = {
                "server": smtp_server,
                "port": smtp_port,
                "email": smtp_email,
                "password": smtp_password,
            }
            _save_settings(settings)
            st.toast(t("st_email_settings_saved"), icon="\u2705")
            st.rerun()

    if st.button(t("test_email"), width='stretch'):
        smtp = settings.get("email_smtp", {})
        if not all([smtp.get("server"), smtp.get("email"), smtp.get("password")]):
            st.error(t("st_fill_smtp_fields"))
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
                st.toast(t("st_test_email_sent"), icon="\u2705")
            except Exception as e:
                st.error(f"{t('st_failed')}: {e}")

    with st.expander(t("st_gmail_app_password_help")):
        st.markdown(t("st_gmail_app_password_instructions"))


def _render_invoice_freelance(settings):
    """Invoice & freelance settings."""
    inv_settings = settings.get("invoice", {})

    with st.form("invoice_settings_form"):
        st.markdown(f"**{t('st_company_business_info')}**")
        ivc1, ivc2 = st.columns(2)
        with ivc1:
            inv_company = st.text_input(
                t("st_company_name"),
                value=inv_settings.get("company_name", settings.get("user_name", "")),
                placeholder=t("st_company_name_placeholder"),
            )
            inv_address = st.text_input(
                t("st_address"),
                value=inv_settings.get("company_address", ""),
                placeholder=t("st_address_placeholder"),
            )
            inv_email = st.text_input(
                t("st_business_email"),
                value=inv_settings.get("company_email", settings.get("user_email", "")),
            )
        with ivc2:
            inv_phone = st.text_input(
                t("st_phone"),
                value=inv_settings.get("company_phone", ""),
            )
            inv_payment = st.text_input(
                t("st_payment_details"),
                value=inv_settings.get("payment_details", ""),
                placeholder=t("st_payment_details_placeholder"),
            )
            inv_footer = st.text_input(
                t("st_invoice_footer"),
                value=inv_settings.get("footer_text", t("st_thank_you_business")),
            )

        st.markdown(f"**{t('st_defaults')}**")
        dvc1, dvc2, dvc3 = st.columns(3)
        with dvc1:
            inv_tax_rate = st.number_input(
                t("st_default_tax_rate"),
                min_value=0.0, max_value=50.0, step=0.5,
                value=float(inv_settings.get("tax_rate", 0)),
            )
        with dvc2:
            from utils.invoice_templates import TEMPLATES
            template_names = list(TEMPLATES.keys())
            current_template = inv_settings.get("default_template", "Professional")
            t_idx = template_names.index(current_template) if current_template in template_names else 1
            inv_default_template = st.selectbox(t("st_default_template"), template_names, index=t_idx)
        with dvc3:
            inv_est_tax_rate = st.number_input(
                t("st_freelance_tax_estimate"),
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
            st.toast(t("st_invoice_settings_saved"), icon="\u2705")
            st.rerun()

    # Logo upload
    st.markdown("---")
    st.markdown(f"**{t('st_logo')}**")
    st.caption(t("st_logo_caption"))
    logo_file = st.file_uploader(t("st_upload_logo"), type=["png", "jpg", "jpeg"], key="logo_upload")
    if logo_file:
        logo_bytes = logo_file.read()
        if len(logo_bytes) > 512000:
            st.error(t("st_logo_too_large"))
        else:
            import base64
            logo_b64 = base64.b64encode(logo_bytes).decode("utf-8")
            inv_settings["logo_base64"] = logo_b64
            settings["invoice"] = {**settings.get("invoice", {}), "logo_base64": logo_b64}
            _save_settings(settings)
            st.toast(t("st_logo_uploaded"), icon="\u2705")
            st.rerun()

    if inv_settings.get("logo_base64"):
        st.success(t("st_logo_is_set"))
        if st.button(t("st_remove_logo")):
            inv_settings.pop("logo_base64", None)
            settings["invoice"] = {**settings.get("invoice", {}), "logo_base64": ""}
            _save_settings(settings)
            st.toast(t("st_logo_removed"))
            st.rerun()


def _render_sharing(settings):
    """Sharing section."""
    st.caption(t("st_sharing_caption"))

    from utils.sharing import create_share_link, get_active_shares, revoke_share

    with st.form("create_share_form"):
        share_name = settings.get("user_name", "") or st.session_state.get("user_name", "User")

        share_modules_opts = {
            t("st_all_modules"): None,
            t("st_dashboard_only"): ["dashboard"],
            t("st_budget_and_goals"): ["budget", "goals"],
            t("st_portfolio_only"): ["portfolio"],
        }
        share_scope = st.selectbox(t("st_what_to_share"), list(share_modules_opts.keys()), key="share_scope")

        sc1, sc2 = st.columns(2)
        with sc1:
            share_expiry = st.selectbox(t("st_expires_after"), ["24 hours", "7 days", "30 days", t("st_never")], index=1, key="share_expiry")
        with sc2:
            share_password = st.text_input(t("st_password_optional"), type="password", key="share_pw")

        share_type = st.selectbox(t("st_share_type"), [t("st_standard_read_only"), t("st_financial_advisor")], key="share_type")

        if st.form_submit_button(t("st_generate_share_link"), type="primary", width='stretch'):
            from utils.sharing import EXPIRY_OPTIONS
            expiry_hrs = EXPIRY_OPTIONS.get(share_expiry, 168)
            share_type_val = "advisor" if share_type == t("st_financial_advisor") else "standard"
            share = create_share_link(
                user_name=share_name,
                modules=share_modules_opts[share_scope],
                expiry_hours=expiry_hrs,
                password=share_password if share_password else None,
                share_type=share_type_val,
            )
            st.session_state["last_share_token"] = share["token"]
            st.success(t("st_share_link_created"))

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
        st.caption(t("st_copy_share_link"))

    active_shares = get_active_shares()
    if active_shares:
        st.markdown("---")
        st.markdown(f"**{t('st_active_share_links')}** ({len(active_shares)})")
        for _sh in active_shares:
            _sh_token = _sh["token"][:12] + "..."
            _sh_type = t("st_financial_advisor") if _sh.get("share_type") == "advisor" else t("st_read_only")
            _sh_expires = _sh.get("expiry", "")
            if _sh_expires:
                try:
                    _sh_expires = datetime.fromisoformat(_sh_expires).strftime("%b %d, %Y")
                except Exception:
                    pass
            else:
                _sh_expires = t("st_never")
            _sh_views = _sh.get("access_count", 0)

            st.markdown(
                f'<div style="padding:8px 12px;background:var(--fk-card-alt);border-radius:8px;margin-bottom:6px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span style="color:var(--fk-text);font-size:0.88rem;">{_sh_type} · {_sh_token}</span>'
                f'<span style="color:var(--fk-text-muted);font-size:0.78rem;">{_sh_views} views · Expires: {_sh_expires}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            if st.button(t("st_revoke"), key=f"revoke_{_sh['token'][:8]}"):
                revoke_share(_sh["token"])
                st.toast(t("st_share_link_revoked"))
                st.rerun()


def _render_cloud_sync(settings):
    """Cloud sync."""
    st.caption(t("st_cloud_sync_caption"))

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

    sync_toggle = st.toggle(t("st_enable_cloud_sync"), value=sync_enabled, key="sync_toggle")
    if sync_toggle != sync_enabled:
        if sync_toggle:
            enable_sync(user_id, sync_freq)
        else:
            disable_sync(user_id)
        st.rerun()

    if sync_enabled:
        freq_options = [t("st_manual_only"), t("st_every_5_min"), t("st_every_15_min"), t("st_every_30_min"), t("st_every_60_min")]
        freq_values = ["manual", "5min", "15min", "30min", "60min"]
        current_idx = freq_values.index(sync_freq) if sync_freq in freq_values else 0
        new_freq = st.selectbox(t("st_auto_sync_frequency"), freq_options, index=current_idx, key="sync_freq")
        new_freq_val = freq_values[freq_options.index(new_freq)]
        if new_freq_val != sync_freq:
            enable_sync(user_id, new_freq_val)

        conflict_options = [t("st_newest_wins"), t("st_cloud_wins"), t("st_local_wins")]
        conflict_values = ["newest", "cloud", "local"]
        st.selectbox(t("st_conflict_resolution"), conflict_options, key="sync_conflict")

        st.markdown("---")

        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button(t("st_export_sync_bundle"), key="sync_export", width='stretch'):
                bundle = create_sync_bundle(user_id)
                if bundle:
                    st.download_button(
                        t("st_download_bundle"),
                        data=bundle,
                        file_name=f"financekit_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        key="sync_download",
                    )
                    mark_synced(user_id)
                    st.success(t("st_sync_bundle_created"))
                else:
                    st.warning(t("st_no_data_to_sync"))

        with sc2:
            uploaded_bundle = st.file_uploader(
                t("st_import_sync_bundle"),
                type=["zip"],
                key="sync_import",
                label_visibility="collapsed",
            )
            if uploaded_bundle:
                conflict_val = conflict_values[conflict_options.index(
                    st.session_state.get("sync_conflict", t("st_newest_wins"))
                )]
                result = apply_sync_bundle(
                    uploaded_bundle.read(), user_id, conflict_val
                )
                if result["updated"]:
                    st.success(t("st_synced_files").format(count=len(result['updated'])))
                if result["conflicts"]:
                    st.info(t("st_resolved_conflicts").format(count=len(result['conflicts'])))
                if result["skipped"]:
                    st.caption(t("st_skipped_unchanged").format(count=len(result['skipped'])))


def _render_legal_privacy(settings):
    """Legal & GDPR section."""
    tab1, tab2, tab3 = st.tabs([t("st_terms_of_service"), t("st_privacy_policy"), t("st_your_data_gdpr")])

    with tab1:
        st.markdown(t("st_terms_of_service_content"))

    with tab2:
        st.markdown(t("st_privacy_policy_content"))

    with tab3:
        st.markdown(f"### {t('st_your_data_rights')}")
        st.markdown(t("st_data_rights_description"))

        st.markdown(f"**{t('export_data')}:**")
        if st.button(t("st_download_data_export_zip"), key="gdpr_export"):
            try:
                from utils.sync import create_sync_bundle
                _gdpr_zip = create_sync_bundle()
                st.download_button(
                    label=t("st_save_zip_file"),
                    data=_gdpr_zip,
                    file_name=f"financekit_data_export_{datetime.now().strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                    key="gdpr_download",
                )
            except Exception as _err:
                st.error(f"{t('st_export_failed')}: {_err}")

        st.markdown("---")
        st.markdown(f"**{t('delete')} all data:**")
        st.warning(t("st_permanent_delete_warning"))
        _gdpr_confirm = st.text_input(
            t("type_delete"),
            key="gdpr_delete_confirm",
        )
        if st.button(t("st_permanently_delete_all_data"), type="secondary", key="gdpr_delete"):
            if _gdpr_confirm == "DELETE MY DATA":
                _del_count = 0
                for _del_fn in os.listdir(DATA_DIR):
                    if _del_fn.endswith(".json") and _del_fn != "auth_config.json":
                        try:
                            os.remove(os.path.join(DATA_DIR, _del_fn))
                            _del_count += 1
                        except OSError:
                            pass
                st.success(t("st_deleted_data_refresh").format(count=_del_count))
                try:
                    from utils.activity_log import log_activity
                    log_activity("deleted", "settings", "GDPR: All user data deleted")
                except Exception:
                    pass
            else:
                st.error(t("st_type_delete_to_confirm"))


def _render_about(settings):
    """About, health check, logs."""
    version = _get_version()

    st.markdown(
        f"- **{t('version')}:** v{version}\n"
        f"- **Python:** {sys.version.split()[0]}\n"
        f"- **Streamlit:** {st.__version__}\n"
        f"- **Data Directory:** `{DATA_DIR}`"
    )

    st.markdown("---")
    st.markdown(f"**{t('st_links')}:**")
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
                    st.info(t("st_update_available").format(remote=remote_version, current=version))
            else:
                st.warning(t("st_could_not_check_updates"))
        except Exception:
            st.warning(t("st_could_not_connect"))

    # Logs
    st.markdown("---")
    st.markdown(f"### {t('logs')}")

    from utils.logger import read_log_lines, clear_logs, get_log_path

    lc1, lc2 = st.columns([2, 1])
    with lc1:
        log_level = st.selectbox(t("st_filter_by_level"), ["ALL", "INFO", "WARNING", "ERROR"], key="log_level_filter")
    with lc2:
        log_lines_count = st.number_input(t("st_lines"), min_value=10, max_value=500, value=100, step=10)

    log_lines = read_log_lines(max_lines=log_lines_count, level_filter=log_level)
    if log_lines:
        st.code("".join(log_lines), language="text")
    else:
        st.info(t("st_no_log_entries"))

    lbc1, lbc2 = st.columns(2)
    with lbc1:
        log_path = get_log_path()
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as _lf:
                    _log_content = _lf.read()
                st.download_button(
                    t("st_download_full_log"),
                    data=_log_content.encode("utf-8"),
                    file_name="financekit.log",
                    mime="text/plain",
                    width='stretch',
                )
            except Exception:
                pass
    with lbc2:
        if st.button(t("st_clear_logs"), key="clear_logs_btn", width='stretch'):
            clear_logs()
            st.toast(t("st_logs_cleared"))
            st.rerun()

    # Health check
    st.markdown("---")
    st.markdown(f"### {t('health_check')}")

    if st.button(t("health_check"), type="primary", key="run_health", width='stretch'):
        checks = []

        py_ver = sys.version.split()[0]
        py_ok = sys.version_info >= (3, 10)
        checks.append((t("st_python_version"), py_ok, f"Python {py_ver}"))

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
                checks.append((f"{t('st_package')}: {pkg_name}", True, t("st_installed")))
            except ImportError:
                checks.append((f"{t('st_package')}: {pkg_name}", False, t("st_not_installed")))

        try:
            _test_fp = os.path.join(DATA_DIR, ".health_check_test")
            with open(_test_fp, "w") as _tf:
                _tf.write("test")
            os.remove(_test_fp)
            checks.append((t("st_data_dir_writable"), True, DATA_DIR))
        except Exception as _hce:
            checks.append((t("st_data_dir_writable"), False, str(_hce)))

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
        checks.append((t("st_all_json_valid"), _json_ok, _json_err.rstrip(", ") or t("st_all_valid")))
        checks.append((t("st_backup_dir_exists"), os.path.exists(BACKUP_DIR), BACKUP_DIR))

        try:
            import requests as _req
            _ping = _req.get("https://api.coingecko.com/api/v3/ping", timeout=5)
            checks.append((t("st_internet_connectivity"), _ping.status_code == 200, "OK"))
        except Exception:
            checks.append((t("st_internet_connectivity"), False, t("st_could_not_reach_api")))

        _smtp = settings.get("email_smtp", {})
        _smtp_ok = bool(_smtp.get("server") and _smtp.get("email") and _smtp.get("password"))
        checks.append((t("st_smtp_configured"), _smtp_ok, t("st_configured") if _smtp_ok else t("st_not_configured_optional")))

        try:
            from utils.migrations import check_pending
            pending = check_pending()
            checks.append((t("st_migrations"), len(pending) == 0,
                            t("st_pending_count").format(count=len(pending)) if pending else t("up_to_date")))
        except Exception:
            checks.append((t("st_migrations"), False, t("st_could_not_check")))

        for label, ok, detail in checks:
            icon = "\u2705" if ok else "\u274c"
            st.markdown(f"{icon} **{label}** --- {detail}")


# ── Main render function ─────────────────────────────────────────────

def render():
    # Clean page title — no icon, just text
    st.markdown(
        f'<div class="fk-module-title">{t("st_settings_title")}</div>'
        f'<div class="fk-module-desc">{t("st_settings_desc")}</div>'
        '<div class="fk-module-line"></div>',
        unsafe_allow_html=True,
    )

    settings = _load_settings()

    # ── Quick nav — MonkeyType-style pill bar ──────────────────────────
    _section_labels = [
        ("profile", t("profile")),
        ("appearance", t("appearance")),
        ("notifications_title", t("notifications_title")),
        ("modules", t("modules")),
        ("data_privacy", t("data_privacy")),
        ("authentication", t("authentication")),
        ("household", t("household")),
        ("email_smtp", t("email_smtp")),
        ("invoice_freelance", t("invoice_freelance")),
        ("sharing", t("sharing")),
        ("cloud_sync", t("cloud_sync")),
        ("legal_privacy", t("legal_privacy")),
        ("about", t("about")),
    ]
    _nav_links = " ".join(
        f'<a href="#{key}" style="padding:0.5em 0.8em;color:var(--fk-text-muted);'
        f'text-decoration:none;font-size:0.78rem;white-space:nowrap;'
        f'transition:color 0.15s;"'
        f' onmouseover="this.style.color=\'var(--fk-accent)\'"'
        f' onmouseout="this.style.color=\'var(--fk-text-muted)\'"'
        f'>{label}</a>'
        for key, label in _section_labels
    )
    st.markdown(
        f'<div style="background:var(--fk-card-alt);border-radius:8px;'
        f'display:flex;flex-wrap:wrap;justify-content:center;'
        f'padding:0.3em 0;margin-bottom:1.5rem;">'
        f'{_nav_links}</div>',
        unsafe_allow_html=True,
    )

    # ── Render ALL sections as one scrollable page ─────────────────────
    _section_renderers = [
        ("profile", t("profile"), _render_profile),
        ("appearance", t("appearance"), _render_appearance),
        ("notifications_title", t("notifications_title"), _render_notifications),
        ("modules", t("modules"), _render_modules),
        ("data_privacy", t("data_privacy"), _render_data_privacy),
        ("authentication", t("authentication"), _render_authentication),
        ("household", t("household"), _render_household),
        ("email_smtp", t("email_smtp"), _render_email_smtp),
        ("invoice_freelance", t("invoice_freelance"), _render_invoice_freelance),
        ("sharing", t("sharing"), _render_sharing),
        ("cloud_sync", t("cloud_sync"), _render_cloud_sync),
        ("legal_privacy", t("legal_privacy"), _render_legal_privacy),
        ("about", t("about"), _render_about),
    ]

    for key, label, renderer in _section_renderers:
        # Section anchor + collapsible header
        st.markdown(f'<div id="{key}"></div>', unsafe_allow_html=True)
        with st.expander(label, expanded=True):
            renderer(settings)
