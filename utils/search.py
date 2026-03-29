"""Global search utility — searches across all data files."""
import os
from utils.data_persistence import load_json


def search_all(query: str, limit: int = 20) -> list[dict]:
    """Search across all data files for matching items.

    Returns a list of dicts: {"module": str, "icon": str, "title": str, "detail": str, "nav": str}
    """
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip().lower()
    results = []

    # Receipts
    receipts = load_json("receipts.json", default=[])
    for r in receipts:
        vendor = str(r.get("vendor", ""))
        total = str(r.get("total", ""))
        date_str = str(r.get("date", ""))
        searchable = f"{vendor} {total} {date_str}".lower()
        if q in searchable:
            results.append({
                "module": "Receipt Scanner",
                "icon": "🧾",
                "title": vendor[:50] or "Unknown vendor",
                "detail": f"{date_str} · {total}" if total else date_str,
                "nav": "🧾 Receipt Scanner",
            })

    # Portfolio holdings
    portfolio = load_json("portfolio.json", default={"holdings": [], "watchlist": []})
    for h in portfolio.get("holdings", []):
        ticker = str(h.get("ticker", ""))
        if q in ticker.lower() or q in h.get("type", "").lower():
            results.append({
                "module": "Portfolio Tracker",
                "icon": "📈",
                "title": f"{ticker} ({h.get('type', '')})",
                "detail": f"Qty: {h.get('quantity', 0)}",
                "nav": "📈 Portfolio Tracker",
            })
    for w in portfolio.get("watchlist", []):
        ticker = str(w.get("ticker", ""))
        if q in ticker.lower():
            results.append({
                "module": "Portfolio Tracker",
                "icon": "👁️",
                "title": f"{ticker} (Watchlist)",
                "detail": w.get("type", ""),
                "nav": "📈 Portfolio Tracker",
            })

    # Goals
    goals_data = load_json("goals.json", default={"goals": []})
    for g in goals_data.get("goals", []):
        name = str(g.get("name", ""))
        if q in name.lower():
            results.append({
                "module": "Goal Tracker",
                "icon": "🎯",
                "title": name,
                "detail": f"${g.get('current', 0):,.0f} / ${g.get('target', 0):,.0f}",
                "nav": "🎯 Goal Tracker",
            })

    # Freelance clients & invoices
    freelance = load_json("freelance_data.json", default={"clients": [], "invoices": []})
    for c in freelance.get("clients", []):
        client = str(c.get("client", ""))
        project = str(c.get("project", ""))
        if q in client.lower() or q in project.lower():
            results.append({
                "module": "Freelance Dashboard",
                "icon": "💼",
                "title": client,
                "detail": project[:40],
                "nav": "💼 Freelance Dashboard",
            })
    for inv in freelance.get("invoices", []):
        inv_id = str(inv.get("id", ""))
        inv_client = str(inv.get("client", ""))
        if q in inv_id.lower() or q in inv_client.lower():
            status = "Paid" if inv.get("paid") else "Unpaid"
            results.append({
                "module": "Freelance Dashboard",
                "icon": "📄",
                "title": f"Invoice #{inv_id.upper()} — {inv_client}",
                "detail": f"${inv.get('amount', 0):,.2f} · {status}",
                "nav": "💼 Freelance Dashboard",
            })

    # Transactions (report generator)
    transactions = load_json("transactions.json", default=[])
    for t in transactions:
        desc = str(t.get("description", ""))
        cat = str(t.get("category", ""))
        if q in desc.lower() or q in cat.lower():
            results.append({
                "module": "Report Generator",
                "icon": "📊",
                "title": desc[:50],
                "detail": cat,
                "nav": "📊 Report Generator",
            })
            if len(results) >= limit:
                break

    # Budget transactions
    budget_txns = load_json("budget_transactions.json", default=[])
    for t in budget_txns:
        desc = str(t.get("description", ""))
        cat = str(t.get("category", ""))
        if q in desc.lower() or q in cat.lower():
            results.append({
                "module": "Budget Tracker",
                "icon": "💰",
                "title": desc[:50],
                "detail": cat,
                "nav": "💰 Budget Tracker",
            })
            if len(results) >= limit:
                break

    # Subscriptions (from statement transactions - detected subs)
    sub_decisions = load_json("sub_decisions.json", default={})
    for name, decision in sub_decisions.items():
        if q in name.lower():
            results.append({
                "module": "Subscription Auditor",
                "icon": "🔄",
                "title": name[:50],
                "detail": f"Decision: {decision}",
                "nav": "🔄 Subscription Auditor",
            })

    return results[:limit]
