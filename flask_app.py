"""FinanceKit — Flask edition.

A reliable personal-finance dashboard built on Flask instead of Streamlit.
Reuses the existing utils/ layer (auth, data_persistence, formatting).
"""

import os
import sys
import json
import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_file,
)

# ── Ensure project root is on sys.path ──────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ── Patch i18n to work without Streamlit session state ──────────────────
# Must happen BEFORE any import that touches utils.i18n
import importlib, types

_fake_st = types.ModuleType("streamlit")
_fake_st.session_state = {"fk_language": "en"}
_fake_st.secrets = {}
def _noop(*a, **kw): pass
_fake_st.cache_data = lambda f=None, **kw: f if f else (lambda fn: fn)
_fake_st.cache_resource = _fake_st.cache_data
_fake_st.set_page_config = _noop
_fake_st.markdown = _noop
_fake_st.write = _noop
_fake_st.error = _noop
_fake_st.warning = _noop
_fake_st.info = _noop
_fake_st.success = _noop
_fake_st.toast = _noop
_fake_st.rerun = _noop
_fake_st.spinner = lambda msg="": __import__("contextlib").nullcontext()
_fake_st.query_params = {}
sys.modules["streamlit"] = _fake_st

from utils.auth import (
    register_user, login_user, login_oauth_user, create_session_token,
    validate_session_token, revoke_session_token,
    change_password, is_session_valid,
    get_google_credentials, get_github_credentials, get_google_redirect_uri,
    _load_users, _save_users, _hash_password,
)
from utils.data_persistence import set_user_context, load_json, save_json
from utils.formatting import (
    format_currency, format_currency_int, get_currency_symbol, format_date,
)

# ── App factory ─────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("FK_SECRET_KEY", secrets.token_hex(32))
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True

DATA_DIR = os.path.join(BASE_DIR, "data")

# ── Load OAuth credentials from .streamlit/secrets.toml into auth_config.json ──
def _sync_oauth_config():
    """Ensure auth_config.json exists with OAuth credentials from secrets.toml."""
    auth_cfg_path = os.path.join(DATA_DIR, "auth_config.json")
    secrets_path = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")
    if os.path.exists(auth_cfg_path) or not os.path.exists(secrets_path):
        return
    try:
        cfg = {}
        with open(secrets_path, encoding="utf-8") as f:
            section = None
            for line in f:
                line = line.strip()
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1]
                    cfg.setdefault(section, {})
                elif "=" in line and section:
                    key, val = line.split("=", 1)
                    cfg[section][key.strip()] = val.strip().strip('"')
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(auth_cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

_sync_oauth_config()
os.makedirs(DATA_DIR, exist_ok=True)


# ── Helpers ─────────────────────────────────────────────────────────────
def _read_version():
    try:
        with open(os.path.join(BASE_DIR, "version.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "9.1"

APP_VERSION = _read_version()


def login_required(f):
    """Decorator: redirect to /login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get("token")
        if not token:
            return redirect(url_for("login"))
        user = validate_session_token(token)
        if not user:
            session.clear()
            return redirect(url_for("login"))
        if not is_session_valid(user.get("login_time", ""), user.get("remember", False)):
            session.clear()
            flash("Session expired. Please sign in again.", "warning")
            return redirect(url_for("login"))
        # Set user context for data isolation
        set_user_context(user["user_id"])
        request.user = user
        return f(*args, **kwargs)
    return decorated


def _load_user_settings():
    return load_json("settings.json", default={
        "currency": {"code": "USD", "symbol": "$"},
        "date_format": "MM/DD/YYYY",
    })


def _fmt_currency(amount):
    """Format currency using user settings."""
    try:
        return format_currency_int(amount)
    except Exception:
        sym = get_currency_symbol()
        return f"{sym}{amount:,.0f}"


# ── Template context ────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return {
        "version": APP_VERSION,
        "fmt_currency": _fmt_currency,
        "format_date": format_date,
        "now": datetime.now(),
        "user": getattr(request, "user", None),
    }


# ── Auth routes ─────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("token") and validate_session_token(session["token"]):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        success, result = login_user(email, password)
        if success:
            token = create_session_token(
                result["id"], result["email"],
                result.get("name", ""), "local", remember,
            )
            session["token"] = token
            session.permanent = remember
            return redirect(url_for("dashboard"))
        # If OAuth account, redirect to set-password page
        err_msg = result if isinstance(result, str) else "Login failed."
        if "uses" in err_msg and "sign-in" in err_msg:
            session["oauth_email"] = email
            return redirect(url_for("set_password"))
        flash(err_msg, "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if password != confirm:
            flash("Passwords don't match.", "error")
            return render_template("register.html")

        success, msg = register_user(email, password, name)
        if success:
            # Auto-login
            ok, user = login_user(email, password)
            if ok:
                token = create_session_token(user["id"], user["email"], user.get("name", ""), "local", False)
                session["token"] = token
                return redirect(url_for("dashboard"))
            flash("Account created! Please sign in.", "success")
            return redirect(url_for("login"))
        flash(msg, "error")

    return render_template("register.html")


@app.route("/set-password", methods=["GET", "POST"])
def set_password():
    """Let OAuth users set a password so they can log in with email/password."""
    email = session.get("oauth_email")
    if not email:
        return redirect(url_for("login"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if password != confirm:
            flash("Passwords don't match.", "error")
            return render_template("set_password.html", email=email)
        # Find user and set password + switch to local auth
        from utils.security import password_meets_requirements
        if not password_meets_requirements(password):
            flash("Password must be 8+ chars with upper+lowercase, number, and special character.", "error")
            return render_template("set_password.html", email=email)
        users_data = _load_users()
        for u in users_data.get("users", []):
            if u["email"] == email.strip().lower():
                u["password_hash"] = _hash_password(password)
                u["auth_method"] = "local"
                _save_users(users_data)
                session.pop("oauth_email", None)
                flash("Password set! You can now sign in.", "success")
                return redirect(url_for("login"))
        flash("Account not found.", "error")

    return render_template("set_password.html", email=email)


# ── OAuth ───────────────────────────────────────────────────────────────
_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
_GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"
_GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


def _oauth_redirect_uri(provider):
    """Build the OAuth redirect URI for this Flask app."""
    return request.url_root.rstrip("/") + f"/auth/{provider}/callback"


@app.route("/auth/google")
def auth_google():
    cid, _ = get_google_credentials()
    if not cid:
        flash("Google sign-in is not configured.", "error")
        return redirect(url_for("login"))
    import urllib.parse
    params = urllib.parse.urlencode({
        "client_id": cid,
        "redirect_uri": _oauth_redirect_uri("google"),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    })
    return redirect(f"{_GOOGLE_AUTH_URL}?{params}")


@app.route("/auth/google/callback")
def auth_google_callback():
    code = request.args.get("code")
    if not code:
        flash("Google sign-in failed: no authorization code.", "error")
        return redirect(url_for("login"))

    cid, csecret = get_google_credentials()
    import requests as _req

    # Exchange code for token
    token_resp = _req.post(_GOOGLE_TOKEN_URL, data={
        "code": code,
        "client_id": cid,
        "client_secret": csecret,
        "redirect_uri": _oauth_redirect_uri("google"),
        "grant_type": "authorization_code",
    }, timeout=10)

    if token_resp.status_code != 200:
        flash("Google sign-in failed: could not get token.", "error")
        return redirect(url_for("login"))

    access_token = token_resp.json().get("access_token")
    if not access_token:
        flash("Google sign-in failed: no access token.", "error")
        return redirect(url_for("login"))

    # Get user profile
    profile_resp = _req.get(_GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
    if profile_resp.status_code != 200:
        flash("Could not fetch Google profile.", "error")
        return redirect(url_for("login"))

    profile = profile_resp.json()
    email = profile.get("email", "")
    name = profile.get("name", "")
    if not email:
        flash("Google account has no email.", "error")
        return redirect(url_for("login"))

    # Login or create user
    user = login_oauth_user(email, name, "google")
    token = create_session_token(user["id"], user["email"], user.get("name", ""), "google", True)
    session["token"] = token
    session.permanent = True
    return redirect(url_for("dashboard"))


@app.route("/auth/github")
def auth_github():
    cid, _ = get_github_credentials()
    if not cid:
        flash("GitHub sign-in is not configured.", "error")
        return redirect(url_for("login"))
    import urllib.parse
    params = urllib.parse.urlencode({
        "client_id": cid,
        "redirect_uri": _oauth_redirect_uri("github"),
        "scope": "user:email",
    })
    return redirect(f"{_GITHUB_AUTH_URL}?{params}")


@app.route("/auth/github/callback")
def auth_github_callback():
    code = request.args.get("code")
    if not code:
        flash("GitHub sign-in failed: no authorization code.", "error")
        return redirect(url_for("login"))

    cid, csecret = get_github_credentials()
    import requests as _req

    # Exchange code for token
    token_resp = _req.post(_GITHUB_TOKEN_URL, data={
        "code": code,
        "client_id": cid,
        "client_secret": csecret,
        "redirect_uri": _oauth_redirect_uri("github"),
    }, headers={"Accept": "application/json"}, timeout=10)

    if token_resp.status_code != 200:
        flash("GitHub sign-in failed.", "error")
        return redirect(url_for("login"))

    access_token = token_resp.json().get("access_token")
    if not access_token:
        flash("GitHub sign-in failed: no access token.", "error")
        return redirect(url_for("login"))

    # Get user profile
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    profile_resp = _req.get(_GITHUB_USER_URL, headers=headers, timeout=10)
    if profile_resp.status_code != 200:
        flash("Could not fetch GitHub profile.", "error")
        return redirect(url_for("login"))

    profile = profile_resp.json()
    name = profile.get("name") or profile.get("login", "")
    email = profile.get("email", "")

    # If no public email, fetch from emails API
    if not email:
        emails_resp = _req.get(_GITHUB_EMAILS_URL, headers=headers, timeout=10)
        if emails_resp.status_code == 200:
            for e in emails_resp.json():
                if e.get("primary") and e.get("verified"):
                    email = e["email"]
                    break
            if not email:
                for e in emails_resp.json():
                    if e.get("verified"):
                        email = e["email"]
                        break

    if not email:
        flash("GitHub account has no email. Add a public email to your GitHub profile.", "error")
        return redirect(url_for("login"))

    user = login_oauth_user(email, name, "github")
    token = create_session_token(user["id"], user["email"], user.get("name", ""), "github", True)
    session["token"] = token
    session.permanent = True
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    token = session.get("token")
    if token:
        revoke_session_token(token)
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ───────────────────────────────────────────────────────────
@app.route("/")
@login_required
def dashboard():
    settings = _load_user_settings()
    transactions = load_json("transactions.json", default=[])
    goals = load_json("goals.json", default=[])
    holdings = load_json("portfolio.json", default=[])
    receipts = load_json("receipts.json", default=[])
    subscriptions = load_json("subscriptions.json", default=[])

    # Calculate summary metrics
    now = datetime.now()
    month_key = now.strftime("%Y-%m")

    month_expenses = sum(
        float(t.get("amount", 0))
        for t in transactions
        if t.get("date", "").startswith(month_key) and float(t.get("amount", 0)) > 0
    )
    month_income = sum(
        abs(float(t.get("amount", 0)))
        for t in transactions
        if t.get("date", "").startswith(month_key) and float(t.get("amount", 0)) < 0
    )

    # Total savings across goals
    goals = [g for g in goals if isinstance(g, dict)]
    total_goal_saved = sum(float(g.get("current", 0)) for g in goals)
    total_goal_target = sum(float(g.get("target", 0)) for g in goals)

    # Portfolio value (simple: sum of quantity * last known price)
    holdings = [h for h in holdings if isinstance(h, dict)]
    portfolio_value = sum(
        float(h.get("quantity", 0)) * float(h.get("avg_price", 0))
        for h in holdings
    )

    # Monthly subscription cost
    subscriptions = [s for s in subscriptions if isinstance(s, dict)]
    monthly_sub_cost = sum(
        float(s.get("amount", 0))
        for s in subscriptions
        if s.get("active", True)
    )

    # Recent transactions (last 10)
    recent_txns = sorted(
        transactions, key=lambda x: x.get("date", ""), reverse=True
    )[:10]

    # Recent receipts (last 5)
    recent_receipts = sorted(
        receipts, key=lambda x: x.get("date", ""), reverse=True
    )[:5]

    # Spending by category (current month)
    cat_spending = {}
    for t in transactions:
        if t.get("date", "").startswith(month_key) and float(t.get("amount", 0)) > 0:
            cat = t.get("category", "Other")
            cat_spending[cat] = cat_spending.get(cat, 0) + float(t.get("amount", 0))

    return render_template("dashboard.html",
        month_expenses=month_expenses,
        month_income=month_income,
        total_goal_saved=total_goal_saved,
        total_goal_target=total_goal_target,
        portfolio_value=portfolio_value,
        monthly_sub_cost=monthly_sub_cost,
        recent_txns=recent_txns,
        recent_receipts=recent_receipts,
        goals=goals,
        cat_spending=cat_spending,
        settings=settings,
    )


# ── Budget Tracker ──────────────────────────────────────────────────────
@app.route("/budget")
@login_required
def budget():
    transactions = load_json("transactions.json", default=[])
    if isinstance(transactions, dict):
        transactions = transactions.get("transactions", [])
    budgets_data = load_json("budgets.json", default={})
    budgets = budgets_data.get("budgets", budgets_data) if isinstance(budgets_data, dict) else {}
    now = datetime.now()
    month_key = now.strftime("%Y-%m")

    # Monthly spending by category
    cat_spending = {}
    for t in transactions:
        if not isinstance(t, dict):
            continue
        if t.get("date", "").startswith(month_key) and float(t.get("amount", 0)) > 0:
            cat = t.get("category", "Other")
            cat_spending[cat] = cat_spending.get(cat, 0) + float(t.get("amount", 0))

    total_spent = sum(cat_spending.values())
    total_budget = sum(float(v) for v in budgets.values() if isinstance(v, (int, float, str))) if budgets else 0

    return render_template("budget.html",
        transactions=sorted(transactions, key=lambda x: x.get("date", ""), reverse=True)[:50],
        budgets=budgets,
        cat_spending=cat_spending,
        total_spent=total_spent,
        total_budget=total_budget,
        month_key=month_key,
    )


@app.route("/budget/add", methods=["POST"])
@login_required
def budget_add_transaction():
    transactions = load_json("transactions.json", default=[])
    txn = {
        "date": request.form.get("date", datetime.now().strftime("%Y-%m-%d")),
        "description": request.form.get("description", "").strip(),
        "amount": float(request.form.get("amount", 0)),
        "category": request.form.get("category", "Other"),
        "id": secrets.token_hex(8),
    }
    transactions.append(txn)
    save_json("transactions.json", transactions)
    flash("Transaction added.", "success")
    return redirect(url_for("budget"))


@app.route("/budget/delete/<txn_id>", methods=["POST"])
@login_required
def budget_delete_transaction(txn_id):
    transactions = load_json("transactions.json", default=[])
    transactions = [t for t in transactions if t.get("id") != txn_id]
    save_json("transactions.json", transactions)
    flash("Transaction deleted.", "success")
    return redirect(url_for("budget"))


# ── Goal Tracker ────────────────────────────────────────────────────────
@app.route("/goals")
@login_required
def goals():
    goals_data = load_json("goals.json", default=[])
    return render_template("goals.html", goals=goals_data)


@app.route("/goals/add", methods=["POST"])
@login_required
def goals_add():
    goals_data = load_json("goals.json", default=[])
    goal = {
        "id": secrets.token_hex(8),
        "name": request.form.get("name", "").strip(),
        "target": float(request.form.get("target", 0)),
        "current": float(request.form.get("current", 0)),
        "deadline": request.form.get("deadline", ""),
        "created": datetime.now().strftime("%Y-%m-%d"),
    }
    goals_data.append(goal)
    save_json("goals.json", goals_data)
    flash("Goal created.", "success")
    return redirect(url_for("goals"))


@app.route("/goals/update/<goal_id>", methods=["POST"])
@login_required
def goals_update(goal_id):
    goals_data = load_json("goals.json", default=[])
    for g in goals_data:
        if g.get("id") == goal_id:
            try:
                g["current"] = float(request.form.get("current", g["current"]))
            except (ValueError, TypeError):
                pass
            break
    save_json("goals.json", goals_data)
    flash("Goal updated.", "success")
    return redirect(url_for("goals"))


@app.route("/goals/delete/<goal_id>", methods=["POST"])
@login_required
def goals_delete(goal_id):
    goals_data = load_json("goals.json", default=[])
    goals_data = [g for g in goals_data if g.get("id") != goal_id]
    save_json("goals.json", goals_data)
    flash("Goal deleted.", "success")
    return redirect(url_for("goals"))


# ── Portfolio Tracker ───────────────────────────────────────────────────
@app.route("/portfolio")
@login_required
def portfolio():
    port_data = load_json("portfolio.json", default={"holdings": []})
    holdings = port_data.get("holdings", []) if isinstance(port_data, dict) else port_data
    holdings = [h for h in holdings if isinstance(h, dict)]
    total_value = sum(
        float(h.get("quantity", 0)) * float(h.get("avg_price", 0))
        for h in holdings
    )
    return render_template("portfolio.html", holdings=holdings, total_value=total_value)


@app.route("/portfolio/add", methods=["POST"])
@login_required
def portfolio_add():
    port_data = load_json("portfolio.json", default={"holdings": [], "alerts": []})
    if not isinstance(port_data, dict):
        port_data = {"holdings": port_data if isinstance(port_data, list) else [], "alerts": []}
    holdings = port_data.get("holdings", [])
    holding = {
        "id": secrets.token_hex(8),
        "ticker": request.form.get("ticker", "").strip().upper(),
        "type": request.form.get("type", "stock"),
        "quantity": float(request.form.get("quantity", 0)),
        "avg_price": float(request.form.get("avg_price", 0)),
        "added": datetime.now().strftime("%Y-%m-%d"),
    }
    holdings.append(holding)
    port_data["holdings"] = holdings
    save_json("portfolio.json", port_data)
    flash("Holding added.", "success")
    return redirect(url_for("portfolio"))


@app.route("/portfolio/delete/<holding_id>", methods=["POST"])
@login_required
def portfolio_delete(holding_id):
    port_data = load_json("portfolio.json", default={"holdings": [], "alerts": []})
    if not isinstance(port_data, dict):
        port_data = {"holdings": port_data if isinstance(port_data, list) else [], "alerts": []}
    port_data["holdings"] = [h for h in port_data.get("holdings", []) if isinstance(h, dict) and h.get("id") != holding_id]
    save_json("portfolio.json", port_data)
    flash("Holding removed.", "success")
    return redirect(url_for("portfolio"))


# ── Subscriptions ───────────────────────────────────────────────────────
@app.route("/subscriptions")
@login_required
def subscriptions():
    subs = load_json("subscriptions.json", default=[])
    total_monthly = sum(float(s.get("amount", 0)) for s in subs if s.get("active", True))
    total_yearly = total_monthly * 12
    return render_template("subscriptions.html",
        subscriptions=subs, total_monthly=total_monthly, total_yearly=total_yearly)


@app.route("/subscriptions/add", methods=["POST"])
@login_required
def subscriptions_add():
    subs = load_json("subscriptions.json", default=[])
    sub = {
        "id": secrets.token_hex(8),
        "name": request.form.get("name", "").strip(),
        "amount": float(request.form.get("amount", 0)),
        "frequency": request.form.get("frequency", "monthly"),
        "category": request.form.get("category", "Other"),
        "active": True,
        "added": datetime.now().strftime("%Y-%m-%d"),
    }
    subs.append(sub)
    save_json("subscriptions.json", subs)
    flash("Subscription added.", "success")
    return redirect(url_for("subscriptions"))


@app.route("/subscriptions/delete/<sub_id>", methods=["POST"])
@login_required
def subscriptions_delete(sub_id):
    subs = load_json("subscriptions.json", default=[])
    subs = [s for s in subs if s.get("id") != sub_id]
    save_json("subscriptions.json", subs)
    flash("Subscription removed.", "success")
    return redirect(url_for("subscriptions"))


# ── Settings ────────────────────────────────────────────────────────────
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings_page():
    settings = _load_user_settings()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "profile":
            settings["user_name"] = request.form.get("user_name", "").strip()
            settings["currency"] = {
                "code": request.form.get("currency_code", "USD"),
                "symbol": request.form.get("currency_symbol", "$"),
            }
            settings["date_format"] = request.form.get("date_format", "MM/DD/YYYY")
            save_json("settings.json", settings)
            flash("Settings saved.", "success")

        elif action == "password":
            current = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            if new_pw != confirm:
                flash("Passwords don't match.", "error")
            else:
                email = request.user.get("email", "")
                ok, msg = change_password(email, current, new_pw)
                flash(msg, "success" if ok else "error")

        elif action == "export":
            return redirect(url_for("export_data"))

        return redirect(url_for("settings_page"))

    currency_options = [
        ("USD", "$"), ("EUR", "\u20ac"), ("GBP", "\u00a3"),
        ("CAD", "C$"), ("AUD", "A$"), ("JPY", "\u00a5"),
        ("INR", "\u20b9"), ("BRL", "R$"),
    ]
    date_options = ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"]

    return render_template("settings.html",
        settings=settings,
        currency_options=currency_options,
        date_options=date_options,
    )


@app.route("/export")
@login_required
def export_data():
    """Export all user data as JSON."""
    import io, zipfile
    buf = io.BytesIO()
    files = ["transactions.json", "goals.json", "portfolio.json",
             "receipts.json", "subscriptions.json", "budgets.json", "settings.json"]
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fn in files:
            data = load_json(fn, default=[])
            zf.writestr(fn, json.dumps(data, indent=2))
    buf.seek(0)
    return send_file(buf, download_name="financekit_export.zip",
                     as_attachment=True, mimetype="application/zip")


# ── API endpoints (for AJAX) ───────────────────────────────────────────
@app.route("/api/transactions", methods=["GET"])
@login_required
def api_transactions():
    return jsonify(load_json("transactions.json", default=[]))


@app.route("/api/goals", methods=["GET"])
@login_required
def api_goals():
    return jsonify(load_json("goals.json", default=[]))


@app.route("/api/portfolio", methods=["GET"])
@login_required
def api_portfolio():
    return jsonify(load_json("portfolio.json", default=[]))


# ── Error handlers ──────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Something went wrong"), 500


# ── Run ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
