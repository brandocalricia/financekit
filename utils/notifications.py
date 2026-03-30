"""Centralized notification system for FinanceKit v5.4.

Features: in-app notifications, browser push, email digest,
smart grouping, priority levels, quiet hours.
"""
import uuid
import smtplib
import html as _html
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.data_persistence import load_json, save_json

NOTIFICATIONS_FILE = "notifications.json"

# Priority levels
PRIORITY_NORMAL = "normal"    # in-app only
PRIORITY_IMPORTANT = "important"  # in-app + browser push
PRIORITY_URGENT = "urgent"    # in-app + browser push + email

# Module icons for rich notifications
MODULE_ICONS = {
    "budget_tracker": "💰",
    "budget": "💰",
    "goal_tracker": "🎯",
    "goals": "🎯",
    "portfolio_tracker": "📈",
    "portfolio": "📈",
    "subscription_auditor": "🔄",
    "subscriptions": "🔄",
    "job_tracker": "💼",
    "freelance": "💼",
    "receipt_scanner": "🧾",
    "receipts": "🧾",
    "report_generator": "📊",
    "reports": "📊",
    "system": "⚙️",
}


def _load_notifications() -> list:
    return load_json(NOTIFICATIONS_FILE, default=[])


def _save_notifications(notifications: list):
    save_json(NOTIFICATIONS_FILE, notifications)


def _load_notification_prefs() -> dict:
    settings = load_json("settings.json", default={})
    return settings.get("notifications", {})


def _is_module_enabled(module: str) -> bool:
    """Check if notifications are enabled for a specific module."""
    prefs = _load_notification_prefs()
    if not prefs.get("enabled", True):
        return False
    module_toggles = prefs.get("modules", {})
    return module_toggles.get(module, True)


def _dedup_key(notification: dict) -> str:
    """Generate a dedup key from type + module + title (prevents spam)."""
    return f"{notification.get('type', '')}|{notification.get('module', '')}|{notification.get('title', '')}"


def _is_quiet_hours() -> bool:
    """Check if current time is within quiet hours."""
    prefs = _load_notification_prefs()
    quiet = prefs.get("quiet_hours", {})
    if not quiet.get("enabled"):
        return False
    try:
        now = datetime.now().hour
        start = int(quiet.get("start", 22))
        end = int(quiet.get("end", 7))
        if start <= end:
            return start <= now < end
        else:  # wraps midnight
            return now >= start or now < end
    except Exception:
        return False


def create_notification(
    ntype: str,
    module: str,
    title: str,
    message: str,
    action_module: str | None = None,
    dedup_hours: int = 24,
    priority: str = PRIORITY_NORMAL,
) -> dict | None:
    """Create a notification and save it.

    Args:
        ntype: One of 'info', 'warning', 'success', 'alert'
        module: Source module name (budget, portfolio, goals, etc.)
        title: Short notification title
        message: Detailed message with context
        action_module: Nav target module name for click-to-navigate
        dedup_hours: Suppress duplicate (same type+module+title) within this window.
                     Set to 0 to skip dedup.
        priority: 'normal' (in-app), 'important' (+ browser), 'urgent' (+ email)

    Returns:
        The created notification dict, or None if suppressed by dedup or prefs.
    """
    if not _is_module_enabled(module):
        return None

    # Respect quiet hours for non-urgent notifications
    if priority != PRIORITY_URGENT and _is_quiet_hours():
        return None

    notifications = _load_notifications()

    # Dedup: skip if same type+module+title exists within dedup_hours
    if dedup_hours > 0:
        cutoff = (datetime.now() - timedelta(hours=dedup_hours)).isoformat()
        key = _dedup_key({"type": ntype, "module": module, "title": title})
        for n in notifications:
            if _dedup_key(n) == key and n.get("timestamp", "") > cutoff:
                return None

    # Rate limiting: max 1 notification per module per hour
    one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
    module_recent = sum(
        1 for n in notifications
        if n.get("module") == module and n.get("timestamp", "") > one_hour_ago
    )
    if module_recent >= 5 and priority == PRIORITY_NORMAL:
        return None

    notification = {
        "id": str(uuid.uuid4())[:8],
        "type": ntype,
        "module": module,
        "title": _html.escape(title),
        "message": _html.escape(message),
        "timestamp": datetime.now().isoformat(),
        "read": False,
        "action_module": action_module,
        "priority": priority,
        "icon": MODULE_ICONS.get(module, "🔔"),
    }

    notifications.append(notification)
    _save_notifications(notifications)
    return notification


def get_grouped_summary() -> list:
    """Group similar unread notifications into summary messages.

    E.g., "3 bills due this week" instead of 3 separate notifications.
    """
    unread = get_notifications(unread_only=True)
    if not unread:
        return []

    # Group by module
    by_module = {}
    for n in unread:
        mod = n.get("module", "system")
        by_module.setdefault(mod, []).append(n)

    summaries = []
    for mod, items in by_module.items():
        if len(items) >= 3:
            icon = MODULE_ICONS.get(mod, "🔔")
            mod_name = mod.replace("_", " ").title()
            summaries.append({
                "icon": icon,
                "title": f"{len(items)} {mod_name} notifications",
                "count": len(items),
                "module": mod,
            })
        else:
            for item in items:
                summaries.append(item)

    return summaries


def get_browser_push_js(notification: dict) -> str:
    """Generate JavaScript to trigger a browser push notification."""
    if not notification:
        return ""
    title = notification.get("title", "FinanceKit")
    body = notification.get("message", "")
    return f"""
    <script>
    (function() {{
        if ('Notification' in window && Notification.permission === 'granted') {{
            new Notification("{title}", {{
                body: "{body}",
                icon: '/app/static/icons/icon-192.png',
                badge: '/app/static/icons/icon-192.png',
                tag: 'fk-{notification.get("id", "")}',
            }});
        }}
    }})();
    </script>
    """


def request_push_permission_js() -> str:
    """Generate JavaScript to request browser notification permission."""
    return """
    <script>
    (function() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    })();
    </script>
    """


def get_notifications(unread_only: bool = False, limit: int = 50) -> list:
    """Return notifications sorted newest-first."""
    notifications = _load_notifications()
    if unread_only:
        notifications = [n for n in notifications if not n.get("read", False)]
    notifications.sort(key=lambda n: n.get("timestamp", ""), reverse=True)
    return notifications[:limit]


def get_unread_count() -> int:
    notifications = _load_notifications()
    return sum(1 for n in notifications if not n.get("read", False))


def mark_read(notification_id: str):
    notifications = _load_notifications()
    for n in notifications:
        if n.get("id") == notification_id:
            n["read"] = True
            break
    _save_notifications(notifications)


def mark_all_read():
    notifications = _load_notifications()
    for n in notifications:
        n["read"] = True
    _save_notifications(notifications)


def clear_all():
    _save_notifications([])


def clear_old(days: int = 30):
    """Remove notifications older than `days` days."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    notifications = _load_notifications()
    filtered = [n for n in notifications if n.get("timestamp", "") > cutoff]
    if len(filtered) != len(notifications):
        _save_notifications(filtered)


def relative_time(iso_str: str) -> str:
    """Convert ISO timestamp to human-readable relative time."""
    try:
        dt = datetime.fromisoformat(iso_str)
    except (ValueError, TypeError):
        return ""
    now = datetime.now()
    diff = now - dt

    if diff.total_seconds() < 60:
        return "Just now"
    if diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() / 60)
        return f"{mins} min{'s' if mins != 1 else ''} ago"
    if diff.total_seconds() < 86400:
        hrs = int(diff.total_seconds() / 3600)
        return f"{hrs} hour{'s' if hrs != 1 else ''} ago"
    if diff.days == 1:
        return "Yesterday"
    if diff.days < 7:
        return f"{diff.days} days ago"
    return dt.strftime("%b %d")


def group_notifications(notifications: list) -> dict:
    """Group notifications into Today / This Week / Earlier."""
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    groups = {"Today": [], "This Week": [], "Earlier": []}
    for n in notifications:
        try:
            dt = datetime.fromisoformat(n.get("timestamp", "")).date()
        except (ValueError, TypeError):
            groups["Earlier"].append(n)
            continue
        if dt == today:
            groups["Today"].append(n)
        elif dt > week_ago:
            groups["This Week"].append(n)
        else:
            groups["Earlier"].append(n)
    return groups


def notification_icon(ntype: str) -> str:
    """Return emoji icon for notification type."""
    return {
        "info": "\U0001f535",
        "warning": "\U0001f7e1",
        "success": "\U0001f7e2",
        "alert": "\U0001f534",
    }.get(ntype, "\U0001f535")


# ── Email Digest ─────────────────────────────────────────────────────────

def send_digest_email(settings: dict) -> tuple[bool, str]:
    """Send an email digest of unread notifications.

    Args:
        settings: Full settings dict (with email_smtp and notifications keys)

    Returns:
        (success, message) tuple
    """
    smtp_cfg = settings.get("email_smtp", {})
    if not all([smtp_cfg.get("server"), smtp_cfg.get("email"), smtp_cfg.get("password")]):
        return False, "SMTP not configured."

    unread = get_notifications(unread_only=True)
    last_sent = settings.get("notifications", {}).get("last_digest_sent", "")
    if last_sent:
        unread = [n for n in unread if n.get("timestamp", "") > last_sent]

    if not unread:
        return False, "No new notifications to send."

    # Build HTML email
    icon_colors = {
        "info": "#3b82f6", "warning": "#f59e0b",
        "success": "#22c55e", "alert": "#ef4444",
    }

    rows_html = ""
    for n in unread:
        color = icon_colors.get(n.get("type", "info"), "#3b82f6")
        ts = relative_time(n.get("timestamp", ""))
        rows_html += f"""
        <tr>
            <td style="padding:0 0 12px 0;">
                <div style="padding:12px 16px;border-left:3px solid {color};background:#f8fafc;border-radius:4px;">
                    <strong style="color:#1e293b;">{n.get('title','')}</strong>
                    <p style="color:#64748b;margin:4px 0 0;font-size:13px;">{n.get('message','')}</p>
                    <p style="color:#94a3b8;margin:4px 0 0;font-size:11px;">{n.get('module','').replace('_', ' ').title()} · {ts}</p>
                </div>
            </td>
        </tr>"""

    html_body = f"""
    <div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;background:#ffffff;padding:32px;">
        <div style="text-align:center;margin-bottom:24px;">
            <h1 style="color:#6366f1;font-size:24px;margin:0;">💰 FinanceKit</h1>
        </div>
        <h2 style="color:#1e293b;font-size:18px;margin:0 0 16px;">Your {'Daily' if notif_prefs.get('digest_frequency') == 'daily' else 'Weekly'} Digest</h2>
        <p style="color:#64748b;font-size:14px;margin:0 0 20px;">
            You have {len(unread)} new notification{'s' if len(unread) != 1 else ''}.
        </p>
        <table style="width:100%;border-collapse:collapse;">
            {rows_html}
        </table>
        <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
        <p style="color:#94a3b8;font-size:12px;text-align:center;">
            You received this because you enabled email digests in FinanceKit settings.<br>
            Your data stays private — stored locally on your device.
        </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"FinanceKit Digest — {len(unread)} new alert{'s' if len(unread)!=1 else ''}"
    msg["From"] = smtp_cfg["email"]
    msg["To"] = smtp_cfg["email"]
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_cfg["server"], int(smtp_cfg["port"])) as server:
            server.starttls()
            server.login(smtp_cfg["email"], smtp_cfg["password"])
            server.send_message(msg)
        return True, "Digest sent successfully."
    except Exception as e:
        return False, f"Failed to send digest: {e}"


def check_and_send_digest(settings: dict):
    """Check if a digest is due and send it automatically.

    Called on app startup. Respects frequency setting (daily/weekly).
    """
    notif_prefs = settings.get("notifications", {})
    if not notif_prefs.get("email_digest", False):
        return

    frequency = notif_prefs.get("digest_frequency", "daily")
    last_sent = notif_prefs.get("last_digest_sent", "")

    if last_sent:
        try:
            last_dt = datetime.fromisoformat(last_sent)
        except (ValueError, TypeError):
            last_dt = datetime.min
    else:
        last_dt = datetime.min

    now = datetime.now()
    if frequency == "daily" and (now - last_dt) < timedelta(hours=20):
        return
    if frequency == "weekly" and (now - last_dt) < timedelta(days=6):
        return

    success, _ = send_digest_email(settings)
    if success:
        # Update last_digest_sent
        notif_prefs["last_digest_sent"] = now.isoformat()
        settings["notifications"] = notif_prefs
        save_json("settings.json", settings)
