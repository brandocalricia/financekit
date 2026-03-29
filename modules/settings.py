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

SETTINGS_FILE = "settings.json"

CURRENCY_OPTIONS = {
    "USD ($)": {"code": "USD", "symbol": "$"},
    "EUR (\u20ac)": {"code": "EUR", "symbol": "\u20ac"},
    "GBP (\u00a3)": {"code": "GBP", "symbol": "\u00a3"},
    "CAD (C$)": {"code": "CAD", "symbol": "C$"},
    "AUD (A$)": {"code": "AUD", "symbol": "A$"},
    "JPY (\u00a5)": {"code": "JPY", "symbol": "\u00a5"},
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
    "version": "2.4",
}


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
        return "2.4"


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
                # Try to describe contents
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
                count = "—"
        except Exception:
            count = "invalid JSON"
        if size < 1024:
            size_str = f"{size} B"
        else:
            size_str = f"{size / 1024:.1f} KB"
        stats.append({"File": fn, "Size": size_str, "Contents": count})
    return stats


def render():
    render_module_header("\u2699\ufe0f", "Settings",
                         "Configure your profile, email, data management, and app preferences.")

    settings = _load_settings()

    tab_profile, tab_email, tab_auth, tab_data, tab_about = st.tabs([
        "\ud83d\udc64 Profile", "\ud83d\udce7 Email (SMTP)", "\ud83d\udd10 Authentication",
        "\ud83d\udcc1 Data Management", "\u2139\ufe0f About"
    ])

    # ── Profile Tab ──────────────────────────────────────────────────────
    with tab_profile:
        st.markdown("### Profile")

        with st.form("profile_form"):
            pc1, pc2 = st.columns(2)
            with pc1:
                user_name = st.text_input(
                    "Display Name",
                    value=settings.get("user_name", ""),
                    placeholder="Your name (used in reports & invoices)",
                )
                currency_labels = list(CURRENCY_OPTIONS.keys())
                current_code = settings.get("currency", {}).get("code", "USD")
                current_idx = next(
                    (i for i, k in enumerate(currency_labels)
                     if CURRENCY_OPTIONS[k]["code"] == current_code),
                    0,
                )
                currency_choice = st.selectbox("Currency", currency_labels, index=current_idx)
            with pc2:
                user_email = st.text_input(
                    "Email Address",
                    value=settings.get("user_email", ""),
                    placeholder="you@example.com",
                )
                current_date_fmt = settings.get("date_format", "MM/DD/YYYY")
                date_fmt_idx = DATE_FORMAT_OPTIONS.index(current_date_fmt) if current_date_fmt in DATE_FORMAT_OPTIONS else 0
                date_format = st.selectbox("Date Format", DATE_FORMAT_OPTIONS, index=date_fmt_idx)

            if st.form_submit_button("\ud83d\udcbe Save Profile", type="primary", use_container_width=True):
                settings["user_name"] = user_name
                settings["user_email"] = user_email
                settings["currency"] = CURRENCY_OPTIONS[currency_choice]
                settings["date_format"] = date_format
                _save_settings(settings)
                st.toast("Profile saved!", icon="\u2705")
                st.rerun()

        # Show current settings
        st.markdown("**Current Settings:**")
        sym = settings.get("currency", {}).get("symbol", "$")
        code = settings.get("currency", {}).get("code", "USD")
        st.markdown(
            f"- **Name:** {settings.get('user_name') or '(not set)'}\n"
            f"- **Email:** {settings.get('user_email') or '(not set)'}\n"
            f"- **Currency:** {sym} ({code})\n"
            f"- **Date Format:** {settings.get('date_format', 'MM/DD/YYYY')}"
        )

    # ── Email (SMTP) Tab ─────────────────────────────────────────────────
    with tab_email:
        st.markdown("### Email Configuration")
        st.caption(
            "Configure SMTP settings here once. Report Generator and Portfolio Tracker "
            "will use these settings automatically."
        )

        smtp = settings.get("email_smtp", DEFAULT_SETTINGS["email_smtp"])

        with st.form("smtp_form"):
            ec1, ec2 = st.columns(2)
            with ec1:
                smtp_server = st.text_input("SMTP Server", value=smtp.get("server", ""), placeholder="smtp.gmail.com")
                smtp_email = st.text_input("Email Address", value=smtp.get("email", ""), placeholder="you@gmail.com")
            with ec2:
                smtp_port = st.number_input("Port", value=int(smtp.get("port", 587)), step=1, min_value=1)
                smtp_password = st.text_input("App Password", value=smtp.get("password", ""), type="password")

            if st.form_submit_button("\ud83d\udcbe Save Email Settings", type="primary", use_container_width=True):
                settings["email_smtp"] = {
                    "server": smtp_server,
                    "port": smtp_port,
                    "email": smtp_email,
                    "password": smtp_password,
                }
                _save_settings(settings)
                st.toast("Email settings saved!", icon="\u2705")
                st.rerun()

        # Test email
        if st.button("\ud83d\udce8 Send Test Email"):
            smtp = settings.get("email_smtp", {})
            if not all([smtp.get("server"), smtp.get("email"), smtp.get("password")]):
                st.error("Please fill in and save all SMTP fields first.")
            else:
                try:
                    import smtplib
                    from email.mime.text import MIMEText
                    msg = MIMEText("This is a test email from FinanceKit. Your SMTP settings are working!")
                    msg["Subject"] = "FinanceKit — Test Email"
                    msg["From"] = smtp["email"]
                    msg["To"] = smtp["email"]
                    with smtplib.SMTP(smtp["server"], int(smtp["port"])) as server:
                        server.starttls()
                        server.login(smtp["email"], smtp["password"])
                        server.send_message(msg)
                    st.toast("Test email sent successfully!", icon="\u2705")
                except Exception as e:
                    st.error(f"Failed to send test email: {e}")

        with st.expander("\ud83d\udca1 How to get a Gmail App Password"):
            st.markdown("""
1. Go to [myaccount.google.com](https://myaccount.google.com/)
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", make sure **2-Step Verification** is turned ON
4. Go back to Security, then click **2-Step Verification**
5. Scroll to the bottom and click **App passwords**
6. Select **Mail** as the app and **Other** as the device (name it "FinanceKit")
7. Click **Generate** — Google will show a 16-character password
8. Copy that password and paste it into the **App Password** field above
9. Use `smtp.gmail.com` as the server and `587` as the port

**Note:** Regular Gmail passwords won't work — you must use an App Password.
            """)

    # ── Authentication Tab ───────────────────────────────────────────────
    with tab_auth:
        from utils.auth import (
            load_auth_config, save_auth_config, get_user_count,
            change_password, delete_user, register_user,
        )

        auth_cfg = load_auth_config()
        st.markdown("### Authentication")

        # Master toggle
        require_auth = st.toggle(
            "Require authentication",
            value=auth_cfg.get("require_auth", False),
            help="When enabled, users must sign in before accessing the app.",
        )

        if require_auth != auth_cfg.get("require_auth", False):
            # If enabling for first time and no users exist, prompt to create admin
            if require_auth and get_user_count() == 0:
                st.warning("No user accounts exist yet. Create the first (admin) account below.")
                with st.form("first_user_form"):
                    fu_name = st.text_input("Display Name")
                    fu_email = st.text_input("Email")
                    fu_pass = st.text_input("Password", type="password")
                    fu_confirm = st.text_input("Confirm Password", type="password")
                    if st.form_submit_button("Create Admin Account & Enable Auth", type="primary",
                                              use_container_width=True):
                        if fu_pass != fu_confirm:
                            st.error("Passwords don't match.")
                        elif not fu_email or "@" not in fu_email:
                            st.error("Please enter a valid email.")
                        else:
                            success, msg = register_user(fu_email, fu_pass, fu_name)
                            if success:
                                auth_cfg["require_auth"] = True
                                save_auth_config(auth_cfg)
                                st.toast("Admin account created! Auth enabled.", icon="✅")
                                st.rerun()
                            else:
                                st.error(msg)
            else:
                auth_cfg["require_auth"] = require_auth
                save_auth_config(auth_cfg)
                status = "enabled" if require_auth else "disabled"
                st.toast(f"Authentication {status}.", icon="✅")
                st.rerun()

        st.markdown(f"**Registered users:** {get_user_count()}")

        # Session expiry
        st.markdown("---")
        st.markdown("**Session Settings**")
        expiry = st.number_input(
            "Session expiry (hours)",
            min_value=1, max_value=720, value=int(auth_cfg.get("session_expiry_hours", 24)),
            step=1, help="How long before a user needs to sign in again. 'Remember me' extends to 30 days.",
        )
        if expiry != auth_cfg.get("session_expiry_hours", 24):
            auth_cfg["session_expiry_hours"] = expiry
            save_auth_config(auth_cfg)
            st.toast("Session expiry updated.", icon="✅")

        # OAuth configuration
        st.markdown("---")
        st.markdown("### OAuth Providers (Optional)")
        st.caption(
            "Configure Google and GitHub OAuth for social sign-in. "
            "These require creating OAuth apps on each provider's developer console."
        )

        # Google OAuth
        with st.expander("Google OAuth 2.0"):
            google_cfg = auth_cfg.get("google", {})
            g_status = "✅ Configured" if google_cfg.get("client_id") and google_cfg.get("client_secret") else "⚠️ Not configured"
            st.markdown(f"**Status:** {g_status}")
            with st.form("google_oauth_form"):
                g_id = st.text_input("Client ID", value=google_cfg.get("client_id", ""),
                                     placeholder="xxxx.apps.googleusercontent.com")
                g_secret = st.text_input("Client Secret", value=google_cfg.get("client_secret", ""),
                                          type="password")
                if st.form_submit_button("Save Google OAuth", use_container_width=True):
                    auth_cfg["google"] = {"client_id": g_id, "client_secret": g_secret}
                    save_auth_config(auth_cfg)
                    st.toast("Google OAuth saved!", icon="✅")
                    st.rerun()

            with st.expander("How to set up Google OAuth"):
                st.markdown("""
1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Go to **APIs & Services** → **OAuth consent screen**
4. Choose **External**, fill in app name and email
5. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
6. Select **Web application**
7. Add your FinanceKit URL to **Authorized redirect URIs** (e.g., `http://localhost:8501`)
8. Copy the **Client ID** and **Client Secret** and paste them above
                """)

        # GitHub OAuth
        with st.expander("GitHub OAuth"):
            github_cfg = auth_cfg.get("github", {})
            gh_status = "✅ Configured" if github_cfg.get("client_id") and github_cfg.get("client_secret") else "⚠️ Not configured"
            st.markdown(f"**Status:** {gh_status}")
            with st.form("github_oauth_form"):
                gh_id = st.text_input("Client ID", value=github_cfg.get("client_id", ""))
                gh_secret = st.text_input("Client Secret", value=github_cfg.get("client_secret", ""),
                                           type="password")
                if st.form_submit_button("Save GitHub OAuth", use_container_width=True):
                    auth_cfg["github"] = {"client_id": gh_id, "client_secret": gh_secret}
                    save_auth_config(auth_cfg)
                    st.toast("GitHub OAuth saved!", icon="✅")
                    st.rerun()

            with st.expander("How to set up GitHub OAuth"):
                st.markdown("""
1. Go to [github.com/settings/developers](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Set **Application name** to "FinanceKit"
4. Set **Homepage URL** to your FinanceKit URL (e.g., `http://localhost:8501`)
5. Set **Authorization callback URL** to `http://localhost:8501`
6. Click **Register application**
7. Copy the **Client ID** and generate a **Client Secret**, then paste both above
                """)

        st.markdown("---")
        st.warning(
            "⚠️ `auth_config.json` contains secrets (OAuth client secrets). "
            "Do not share this file or commit it to version control."
        )

        # Account management (for authenticated users)
        if st.session_state.get("authenticated"):
            st.markdown("---")
            st.markdown("### Account Management")
            _auth_method = st.session_state.get("auth_method", "local")

            if _auth_method != "local":
                st.info(f"Signed in via **{_auth_method.title()}**. Password management is handled by your OAuth provider.")
            else:
                with st.expander("🔑 Change Password"):
                    with st.form("change_pw_form"):
                        cur_pw = st.text_input("Current Password", type="password")
                        new_pw = st.text_input("New Password", type="password")
                        confirm_pw = st.text_input("Confirm New Password", type="password")
                        if st.form_submit_button("Change Password", use_container_width=True):
                            if new_pw != confirm_pw:
                                st.error("New passwords don't match.")
                            else:
                                success, msg = change_password(
                                    st.session_state.get("user_email", ""), cur_pw, new_pw
                                )
                                if success:
                                    st.toast(msg, icon="✅")
                                else:
                                    st.error(msg)

            # Delete account
            with st.expander("🗑️ Delete Account"):
                st.warning("This will permanently delete your account and all your data.")
                if "confirm_delete_account" not in st.session_state:
                    st.session_state.confirm_delete_account = False

                if not st.session_state.confirm_delete_account:
                    if st.button("Delete My Account", use_container_width=True):
                        st.session_state.confirm_delete_account = True
                        st.rerun()
                else:
                    dac1, dac2 = st.columns(2)
                    with dac1:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state.confirm_delete_account = False
                            st.rerun()
                    with dac2:
                        if st.button("⚠️ Confirm Delete", type="primary", use_container_width=True):
                            success, msg = delete_user(st.session_state.get("user_email", ""))
                            if success:
                                st.toast("Account deleted.", icon="🗑️")
                                st.session_state.confirm_delete_account = False
                                # Sign out
                                from utils.data_persistence import clear_user_context
                                clear_user_context()
                                for k in list(st.session_state.keys()):
                                    st.session_state.pop(k, None)
                                st.rerun()
                            else:
                                st.error(msg)

    # ── Data Management Tab ──────────────────────────────────────────────
    with tab_data:
        st.markdown("### Data Management")

        # Data file stats
        st.markdown("**Data Files:**")
        stats = _data_file_stats()
        if stats:
            import pandas as pd
            st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)
        else:
            st.info("No data files found.")

        st.markdown("---")

        # Export All Data
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.markdown("**Export All Data**")
            st.caption("Download a ZIP backup of all your data files.")
            if st.button("\ud83d\udce6 Export All Data", use_container_width=True):
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
                    "\u2b07\ufe0f Download ZIP",
                    data=st.session_state["export_zip"],
                    file_name=f"financekit_backup_{datetime.now().strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

        # Import Data
        with dc2:
            st.markdown("**Import Data**")
            st.caption("Restore from a previously exported ZIP file.")
            import_file = st.file_uploader("Upload ZIP", type=["zip"], key="import_zip", label_visibility="collapsed")
            if import_file and st.button("\ud83d\udce5 Import Data", use_container_width=True):
                try:
                    os.makedirs(DATA_DIR, exist_ok=True)
                    restored = []
                    with zipfile.ZipFile(io.BytesIO(import_file.read()), "r") as zf:
                        for name in zf.namelist():
                            if name.endswith(".json"):
                                zf.extract(name, DATA_DIR)
                                # Count records
                                fp = os.path.join(DATA_DIR, name)
                                try:
                                    with open(fp, "r", encoding="utf-8") as f:
                                        data = json.load(f)
                                    if isinstance(data, list):
                                        restored.append(f"{name} ({len(data)} records)")
                                    else:
                                        restored.append(f"{name} (restored)")
                                except Exception:
                                    restored.append(f"{name} (restored)")
                    st.toast(f"Imported {len(restored)} file(s)!", icon="\u2705")
                    if restored:
                        st.success("Restored: " + ", ".join(restored))
                except Exception as e:
                    st.error(f"Import failed: {e}")

        # Reset All Data
        with dc3:
            st.markdown("**Reset All Data**")
            st.caption("Delete all data files. Backups are preserved.")
            if "confirm_reset" not in st.session_state:
                st.session_state.confirm_reset = False

            if not st.session_state.confirm_reset:
                if st.button("\u26a0\ufe0f Reset All Data", use_container_width=True):
                    st.session_state.confirm_reset = True
                    st.rerun()
            else:
                st.warning("This will delete ALL data files. Backups will be kept.")
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("\u274c Cancel", use_container_width=True):
                        st.session_state.confirm_reset = False
                        st.rerun()
                with rc2:
                    if st.button("\ud83d\uddd1\ufe0f Confirm Delete", type="primary", use_container_width=True):
                        deleted = 0
                        for fn in os.listdir(DATA_DIR):
                            fp = os.path.join(DATA_DIR, fn)
                            if os.path.isfile(fp) and fn.endswith(".json"):
                                os.remove(fp)
                                deleted += 1
                        st.session_state.confirm_reset = False
                        st.toast(f"Deleted {deleted} data file(s).", icon="\ud83d\uddd1\ufe0f")
                        st.rerun()

    # ── About Tab ────────────────────────────────────────────────────────
    with tab_about:
        st.markdown("### About FinanceKit")

        version = _get_version()

        st.markdown(
            f"- **Version:** v{version}\n"
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

        # Check for Updates
        if st.button("\ud83d\udd04 Check for Updates"):
            try:
                import requests
                resp = requests.get(
                    "https://raw.githubusercontent.com/brandocalricia/financekit/main/version.txt",
                    timeout=5,
                )
                if resp.status_code == 200:
                    remote_version = resp.text.strip()
                    if remote_version == version:
                        st.success(f"\u2705 You're up to date! (v{version})")
                    else:
                        st.info(
                            f"\ud83c\udd95 Version **v{remote_version}** is available! "
                            f"You're on v{version}. Visit the Gumroad page to download the update."
                        )
                else:
                    st.warning("Could not check for updates. Try again later.")
            except Exception:
                st.warning("Could not connect to GitHub. Check your internet connection.")
