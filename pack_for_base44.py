"""Pack all Flask app source files into a single text file for Base44 prompt."""
import os

FILES = [
    "flask_app.py",
    "templates/base.html",
    "templates/nav_links.html",
    "templates/login.html",
    "templates/register.html",
    "templates/set_password.html",
    "templates/dashboard.html",
    "templates/budget.html",
    "templates/goals.html",
    "templates/portfolio.html",
    "templates/subscriptions.html",
    "templates/settings.html",
    "templates/error.html",
    "utils/auth.py",
    "utils/data_persistence.py",
    "utils/formatting.py",
    "utils/security.py",
    "requirements-flask.txt",
    "version.txt",
]

OUTPUT = "FinanceKit_Base44_Prompt.txt"

with open(OUTPUT, "w", encoding="utf-8") as out:
    out.write("# FinanceKit - Personal Finance Dashboard\n")
    out.write("# Full source code for Base44 Pro deployment\n")
    out.write("# Stack: Flask + Jinja2 HTML templates, dark mode only, JSON file storage\n")
    out.write("# Auth: email/password (bcrypt), Google OAuth, GitHub OAuth\n")
    out.write("# Pages: Dashboard, Budget Tracker, Goal Tracker, Portfolio Tracker, Subscriptions, Settings\n")
    out.write("# Features: session persistence, data export, responsive sidebar nav, mobile support\n")
    out.write("#" + "=" * 80 + "\n\n")

    for fp in FILES:
        if not os.path.exists(fp):
            print(f"  SKIP (not found): {fp}")
            continue
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        lines = len(content.splitlines())
        out.write(f"### FILE: {fp}\n")
        out.write(f"### Lines: {lines}\n")
        out.write("```\n")
        out.write(content)
        if not content.endswith("\n"):
            out.write("\n")
        out.write("```\n\n")
        print(f"  Added: {fp} ({lines} lines)")

size_kb = os.path.getsize(OUTPUT) / 1024
print(f"\nCreated {OUTPUT}: {size_kb:.0f} KB")
