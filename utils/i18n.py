"""Internationalization (i18n) groundwork for FinanceKit v5.8.

Provides a `t()` function for translatable strings. Currently English-only,
but infrastructure is ready for additional languages.
"""

import streamlit as st

_STRINGS = {
    "en": {
        # Navigation
        "dashboard": "Dashboard",
        "settings": "Settings",
        "budget_tracker": "Budget Tracker",
        "goal_tracker": "Goal Tracker",
        "receipt_scanner": "Receipt Scanner",
        "portfolio_tracker": "Portfolio Tracker",
        "report_generator": "Report Generator",
        "freelance_dashboard": "Freelance Dashboard",
        "subscription_auditor": "Subscription Auditor",

        # Auth
        "sign_in": "Sign In",
        "sign_out": "Sign Out",
        "sign_up": "Create Account",
        "email": "Email",
        "password": "Password",
        "remember_me": "Remember me (30 days)",
        "forgot_password": "Forgot password?",
        "welcome_back": "Welcome back",
        "sign_in_to_account": "Sign in to your account",
        "create_account": "Create Account",
        "start_managing": "Start managing your finances",
        "already_have_account": "Already have an account?",
        "dont_have_account": "Don't have an account?",

        # Common actions
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "edit": "Edit",
        "add": "Add",
        "close": "Close",
        "back": "Back",
        "next": "Next",
        "skip": "Skip",
        "confirm": "Confirm",
        "search": "Search...",
        "loading": "Loading...",
        "no_data": "No data yet",

        # Budget
        "add_expense": "Add Expense",
        "add_transaction": "Add Transaction",
        "category": "Category",
        "amount": "Amount",
        "description": "Description",
        "date": "Date",
        "monthly_budget": "Monthly Budget",

        # Goals
        "create_goal": "Create Goal",
        "goal_name": "Goal Name",
        "target_amount": "Target Amount",
        "current_progress": "Current Progress",
        "contribute": "Contribute",

        # Portfolio
        "add_holding": "Add Holding",
        "ticker": "Ticker",
        "quantity": "Quantity",
        "purchase_price": "Purchase Price",
        "current_price": "Current Price",
        "gain_loss": "Gain/Loss",

        # Dashboard
        "net_worth": "Net Worth",
        "monthly_spending": "Monthly Spending",
        "savings_progress": "Savings Progress",
        "quick_actions": "Quick Actions",
        "recent_activity": "Recent Activity",
        "financial_health": "Financial Health",

        # Settings
        "appearance": "Appearance",
        "profile": "Profile",
        "notifications_title": "Notifications",
        "data_privacy": "Data & Privacy",
        "about": "About",
        "cloud_sync": "Cloud Sync",
        "sharing": "Sharing",

        # Time
        "today": "Today",
        "yesterday": "Yesterday",
        "days_ago": "{n} days ago",
        "just_now": "Just now",
        "minutes_ago": "{n} min ago",
        "hours_ago": "{n}h ago",
    },
}

# Supported languages
AVAILABLE_LANGUAGES = {
    "English": "en",
}


def t(key: str, **kwargs) -> str:
    """Translate a key to the current language.

    Args:
        key: The string key to translate.
        **kwargs: Format variables (e.g., n=5 for "{n} days ago").

    Returns:
        Translated string, or the key itself if not found.
    """
    try:
        lang = st.session_state.get("language", "en")
    except Exception:
        lang = "en"

    strings = _STRINGS.get(lang, _STRINGS["en"])
    text = strings.get(key, key)

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return text


def get_current_language() -> str:
    """Get the current language code."""
    try:
        return st.session_state.get("language", "en")
    except Exception:
        return "en"


def set_language(lang_code: str):
    """Set the current language."""
    if lang_code in _STRINGS:
        st.session_state["language"] = lang_code
