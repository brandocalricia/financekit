import streamlit as st
import pandas as pd
import io
import uuid
from datetime import datetime, timedelta, date
from utils.data_persistence import load_json, save_json
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout, CHART_COLORS, _theme_colors, _chart_font
from utils.formatting import format_currency, format_currency_int, get_currency_symbol
from utils.notifications import create_notification
from utils.i18n import t

DATA_FILE = "freelance_data.json"
OLD_DATA_FILE = "job_applications.json"
STATUSES = ["In Progress", "Completed", "Invoiced", "Paid", "On Hold", "Cancelled"]
CLIENT_STATUSES = ["Active", "Inactive", "Lead", "Archived"]
EXPENSE_CATEGORIES = [
    "Software", "Hardware", "Travel", "Office Supplies",
    "Marketing", "Professional Services", "Meals", "Other",
]


def _load():
    import os
    from utils.data_persistence import _path
    old_path = _path(OLD_DATA_FILE)
    new_path = _path(DATA_FILE)
    if os.path.exists(old_path) and not os.path.exists(new_path):
        import shutil
        shutil.copy2(old_path, new_path)
    data = load_json(DATA_FILE, default={"clients": [], "invoices": []})
    return _migrate(data)


def _save(data):
    save_json(DATA_FILE, data)


def _migrate(data):
    """Ensure all expected keys exist."""
    if isinstance(data, list):
        return {"clients": [], "invoices": [], "time_entries": [],
                "recurring_invoices": [], "expenses": []}
    for key in ("clients", "invoices", "time_entries", "recurring_invoices", "expenses"):
        if key not in data:
            data[key] = []
    return data


def _calc_due_date(invoice_date_str, terms):
    """Calculate due date from invoice date and payment terms."""
    try:
        d = datetime.strptime(invoice_date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        d = datetime.now()
    days = {"Net 15": 15, "Net 30": 30, "Net 60": 60, "Due on Receipt": 0}
    return (d + timedelta(days=days.get(terms, 30))).strftime("%Y-%m-%d")


def _payment_reliability(client_name, invoices):
    """Calculate average days to payment for a client."""
    client_invs = [inv for inv in invoices
                   if inv.get("client") == client_name and inv.get("paid") and inv.get("paid_date")]
    if not client_invs:
        return None, "No data"
    delays = []
    for inv in client_invs:
        try:
            due = datetime.strptime(inv.get("due_date", inv["date"]), "%Y-%m-%d")
            paid = datetime.strptime(inv["paid_date"], "%Y-%m-%d")
            delays.append((paid - due).days)
        except (ValueError, TypeError):
            pass
    if not delays:
        return None, "No data"
    avg = sum(delays) / len(delays)
    if avg <= 0:
        return avg, "On time"
    elif avg <= 14:
        return avg, "Sometimes late"
    else:
        return avg, "Often late"


def _check_recurring_invoices(data):
    """Auto-generate any due recurring invoices."""
    from utils.invoice_templates import generate_invoice_number
    today = datetime.now().date()
    generated = []

    for ri in data.get("recurring_invoices", []):
        if ri.get("status") != "Active":
            continue
        # Check end date
        if ri.get("end_date"):
            try:
                end = datetime.strptime(ri["end_date"], "%Y-%m-%d").date()
                if today > end:
                    ri["status"] = "Ended"
                    continue
            except (ValueError, TypeError):
                pass
        # Check if next due
        try:
            next_due = datetime.strptime(ri["next_due"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        if today >= next_due:
            # Generate invoice
            inv_number = generate_invoice_number(data.get("invoices", []))
            new_inv = {
                "id": str(uuid.uuid4())[:8],
                "number": inv_number,
                "client": ri["client"],
                "date": today.strftime("%Y-%m-%d"),
                "due_date": _calc_due_date(today.strftime("%Y-%m-%d"), ri.get("payment_terms", "Net 30")),
                "amount": ri["amount"],
                "line_items": ri.get("line_items", []),
                "notes": t("jt_auto_generated_note"),
                "payment_terms": ri.get("payment_terms", "Net 30"),
                "paid": False,
                "tax_rate": ri.get("tax_rate", 0),
                "discount": ri.get("discount", 0),
                "recurring_id": ri.get("id", ""),
            }
            data["invoices"].append(new_inv)
            generated.append(new_inv)

            # Advance next due
            freq_days = {"Weekly": 7, "Bi-weekly": 14, "Monthly": 30, "Quarterly": 90}
            advance = freq_days.get(ri.get("frequency", "Monthly"), 30)
            ri["next_due"] = (next_due + timedelta(days=advance)).strftime("%Y-%m-%d")

            create_notification(
                "info", "freelance",
                t("jt_notif_auto_invoice", number=inv_number),
                t("jt_notif_recurring_for", client=ri['client'], amount=format_currency(ri['amount'])),
                action_module="job_tracker",
            )

    if generated:
        _save(data)
    return generated


def render():
    render_module_header("", t("jt_title"),
                         t("jt_subtitle"))

    if "freelance_data" not in st.session_state:
        st.session_state.freelance_data = _load()

    data = st.session_state.freelance_data
    clients = data.get("clients", [])
    invoices = data.get("invoices", [])
    time_entries = data.get("time_entries", [])
    expenses = data.get("expenses", [])

    # Check recurring invoices on load
    if "recurring_checked" not in st.session_state:
        generated = _check_recurring_invoices(data)
        st.session_state.recurring_checked = True
        if generated:
            st.toast(t("jt_auto_generated_invoices", count=len(generated)))

    settings = load_json("settings.json", default={})
    tax_rate = settings.get("invoice", {}).get("tax_rate", 0)

    tab_overview, tab_clients, tab_time, tab_invoices, tab_recurring, tab_expenses = st.tabs([
        t("jt_overview"), t("jt_clients"), t("jt_time"), t("jt_invoices"), t("jt_recurring"), t("jt_expenses")
    ])

    # ═══════════════════════════════════════════════════════════════════
    #  TAB: Overview
    # ═══════════════════════════════════════════════════════════════════
    with tab_overview:
        _render_overview(data, settings, tax_rate)

    # ═══════════════════════════════════════════════════════════════════
    #  TAB: Clients
    # ═══════════════════════════════════════════════════════════════════
    with tab_clients:
        _render_clients(data)

    # ═══════════════════════════════════════════════════════════════════
    #  TAB: Time Tracking
    # ═══════════════════════════════════════════════════════════════════
    with tab_time:
        _render_time_tracking(data)

    # ═══════════════════════════════════════════════════════════════════
    #  TAB: Invoices
    # ═══════════════════════════════════════════════════════════════════
    with tab_invoices:
        _render_invoices(data, settings, tax_rate)

    # ═══════════════════════════════════════════════════════════════════
    #  TAB: Recurring
    # ═══════════════════════════════════════════════════════════════════
    with tab_recurring:
        _render_recurring(data)

    # ═══════════════════════════════════════════════════════════════════
    #  TAB: Expenses
    # ═══════════════════════════════════════════════════════════════════
    with tab_expenses:
        _render_expenses(data, invoices)


# ═══════════════════════════════════════════════════════════════════════
#  Overview Tab
# ═══════════════════════════════════════════════════════════════════════

def _render_overview(data, settings, tax_rate):
    invoices = data.get("invoices", [])
    clients = data.get("clients", [])
    expenses = data.get("expenses", [])
    sym = get_currency_symbol()
    now = datetime.now()

    total_invoiced = sum(inv.get("amount", 0) for inv in invoices)
    total_paid = sum(inv.get("amount", 0) for inv in invoices if inv.get("paid"))
    total_outstanding = total_invoiced - total_paid

    # Revenue by period
    paid_invoices = [inv for inv in invoices if inv.get("paid")]

    def _sum_period(invs, start):
        return sum(inv.get("amount", 0) for inv in invs
                   if _parse_date(inv.get("date")) and _parse_date(inv["date"]) >= start)

    this_month_start = now.replace(day=1)
    this_quarter_start = now.replace(month=((now.month - 1) // 3) * 3 + 1, day=1)
    this_year_start = now.replace(month=1, day=1)

    rev_month = _sum_period(paid_invoices, this_month_start)
    rev_quarter = _sum_period(paid_invoices, this_quarter_start)
    rev_year = _sum_period(paid_invoices, this_year_start)

    # Revenue metrics
    st.markdown(f"### {t('jt_revenue')}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(t("jt_this_month"), format_currency(rev_month))
    m2.metric(t("jt_this_quarter"), format_currency(rev_quarter))
    m3.metric(t("jt_this_year"), format_currency(rev_year))
    m4.metric(t("jt_all_time"), format_currency(total_paid))

    # Secondary metrics
    m5, m6, m7, m8 = st.columns(4)
    avg_invoice = total_paid / len(paid_invoices) if paid_invoices else 0
    m5.metric(t("jt_avg_invoice"), format_currency(avg_invoice))

    # Average days to payment
    pay_delays = []
    for inv in paid_invoices:
        if inv.get("paid_date"):
            try:
                inv_d = datetime.strptime(inv["date"], "%Y-%m-%d")
                paid_d = datetime.strptime(inv["paid_date"], "%Y-%m-%d")
                pay_delays.append((paid_d - inv_d).days)
            except (ValueError, TypeError):
                pass
    avg_days = sum(pay_delays) / len(pay_delays) if pay_delays else 0
    m6.metric(t("jt_avg_days_to_payment"), f"{avg_days:.0f}")

    # Top client
    client_totals = {}
    for inv in paid_invoices:
        c = inv.get("client", "Unknown")
        client_totals[c] = client_totals.get(c, 0) + inv.get("amount", 0)
    if client_totals:
        top = max(client_totals, key=client_totals.get)
        top_pct = client_totals[top] / total_paid * 100 if total_paid > 0 else 0
        m7.metric(t("jt_top_client"), f"{top} ({top_pct:.0f}%)")
    else:
        m7.metric(t("jt_top_client"), t("jt_na"))

    m8.metric(t("jt_outstanding"), format_currency(total_outstanding),
              delta=f"-{format_currency(total_outstanding)}" if total_outstanding > 0 else None,
              delta_color="inverse")

    # Outstanding invoices list
    unpaid = [inv for inv in invoices if not inv.get("paid")]
    if unpaid:
        st.warning(t("jt_unpaid_warning", count=len(unpaid), total=format_currency(total_outstanding)))
        _check_overdue_alerts(unpaid)

    # Tax estimate
    if tax_rate > 0:
        st.markdown("---")
        st.markdown(f"### {t('jt_tax_estimate')}")
        tax_liability = rev_year * (tax_rate / 100)
        quarterly_tax = tax_liability / 4
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric(t("jt_estimated_tax_liability"), format_currency(tax_liability))
        tc2.metric(t("jt_quarterly_set_aside"), format_currency(quarterly_tax))
        tc3.metric(t("jt_tax_rate"), f"{tax_rate}%")
        st.caption(t("jt_tax_caption", income=format_currency(rev_year), rate=tax_rate))

    # Revenue trend chart
    if paid_invoices:
        st.markdown("---")
        st.markdown(f"### {t('jt_revenue_trend')}")
        import plotly.graph_objects as go
        tc = _theme_colors()

        inv_df = pd.DataFrame(paid_invoices)
        inv_df["date"] = pd.to_datetime(inv_df["date"], errors="coerce")
        inv_df = inv_df.dropna(subset=["date"])
        if not inv_df.empty:
            inv_df["month"] = inv_df["date"].dt.to_period("M").astype(str)
            monthly = inv_df.groupby("month")["amount"].sum().reset_index()
            monthly.columns = ["Month", "Revenue"]
            monthly = monthly.tail(12)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=monthly["Month"], y=monthly["Revenue"],
                marker_color=CHART_COLORS[3], text=[f"{sym}{v:,.0f}" for v in monthly["Revenue"]],
                textposition="outside", name=t("jt_revenue"),
            ))
            apply_layout(fig, height=300, title=t("jt_monthly_revenue"),
                         margin=dict(t=30, b=10))
            st.plotly_chart(fig, width='stretch')

    # Client revenue breakdown
    if client_totals:
        st.markdown("---")
        st.markdown(f"### {t('jt_client_revenue_breakdown')}")
        import plotly.graph_objects as go
        tc = _theme_colors()

        sorted_clients = sorted(client_totals.items(), key=lambda x: x[1], reverse=True)
        fig = go.Figure(go.Bar(
            x=[v for _, v in sorted_clients],
            y=[k for k, _ in sorted_clients],
            orientation="h",
            marker_color=CHART_COLORS[0],
            text=[f"{sym}{v:,.0f}" for _, v in sorted_clients],
            textposition="outside",
        ))
        apply_layout(fig, height=max(200, len(sorted_clients) * 40),
                     margin=dict(t=10, b=10, l=10, r=60), showlegend=False)
        st.plotly_chart(fig, width='stretch')

    # Invoice status pie
    if invoices:
        st.markdown("---")
        st.markdown(f"### {t('jt_invoice_status')}")
        import plotly.graph_objects as go

        now_date = datetime.now()
        paid_count = len([i for i in invoices if i.get("paid")])
        overdue_count = 0
        unpaid_count = 0
        for inv in invoices:
            if not inv.get("paid"):
                try:
                    due = datetime.strptime(inv.get("due_date", inv["date"]), "%Y-%m-%d")
                    if now_date > due:
                        overdue_count += 1
                    else:
                        unpaid_count += 1
                except (ValueError, TypeError):
                    unpaid_count += 1

        fig = go.Figure(go.Pie(
            labels=[t("jt_paid"), t("jt_unpaid"), t("jt_overdue")],
            values=[paid_count, unpaid_count, overdue_count],
            marker=dict(colors=[CHART_COLORS[3], CHART_COLORS[4], CHART_COLORS[5]]),
            hole=0.4,
            textinfo="label+value",
        ))
        apply_layout(fig, height=300, title=t("jt_invoice_status"))
        st.plotly_chart(fig, width='stretch')


# ═══════════════════════════════════════════════════════════════════════
#  Clients Tab
# ═══════════════════════════════════════════════════════════════════════

def _render_clients(data):
    clients = data.get("clients", [])
    invoices = data.get("invoices", [])

    with st.expander(t("jt_add_client"), expanded=not clients):
        with st.form("add_client", clear_on_submit=True):
            fc1, fc2 = st.columns(2)
            with fc1:
                client_name = st.text_input(t("jt_client_name") + " *")
                project = st.text_input(t("jt_project_description") + " *")
                date_started = st.date_input(t("jt_date_started"), value=date.today())
                client_email = st.text_input(t("jt_contact_email"))
            with fc2:
                status = st.selectbox(t("jt_status"), STATUSES)
                client_status = st.selectbox(t("jt_client_status"), CLIENT_STATUSES)
                _rate_type_map = {"Hourly": t("jt_hourly"), "Flat Rate": t("jt_flat_rate")}
                rate_type = st.selectbox(t("jt_rate_type"), list(_rate_type_map.keys()), format_func=lambda x: _rate_type_map[x])
                rate = st.number_input(t("jt_hourly_rate"), min_value=0.0, step=10.0, format="%.2f")
            fc3, fc4 = st.columns(2)
            with fc3:
                client_phone = st.text_input(t("jt_phone"))
                client_address = st.text_input(t("jt_address"))
            with fc4:
                notes = st.text_area(t("jt_notes"), height=80)

            if st.form_submit_button(t("jt_add_client"), type="primary", width='stretch'):
                if not client_name or not project:
                    st.error(t("jt_err_client_project_required"))
                else:
                    clients.append({
                        "id": str(uuid.uuid4())[:8],
                        "client": client_name,
                        "project": project,
                        "date_started": str(date_started),
                        "status": status,
                        "client_status": client_status,
                        "rate_type": rate_type,
                        "rate": rate,
                        "email": client_email,
                        "phone": client_phone,
                        "address": client_address,
                        "notes": notes,
                    })
                    data["clients"] = clients
                    _save(data)
                    st.toast(t("jt_client_added", name=client_name))
                    st.rerun()

    if not clients:
        from utils.ui_helpers import render_empty_state
        render_empty_state("", t("jt_no_clients"),
                           t("jt_no_clients_hint"))
        return

    # Filters
    fc1, fc2 = st.columns(2)
    with fc1:
        filter_status = st.multiselect(t("jt_filter_job_status"), STATUSES, default=STATUSES, key="client_filter")
    with fc2:
        filter_client_status = st.multiselect(t("jt_filter_client_status"), CLIENT_STATUSES, default=CLIENT_STATUSES, key="cl_status_filter")
    filtered = [c for c in clients
                if c.get("status") in filter_status
                and c.get("client_status", "Active") in filter_client_status]

    # Pipeline chart
    if filtered:
        import plotly.express as px
        status_counts = {}
        for c in clients:
            s = c.get("status", "In Progress")
            status_counts[s] = status_counts.get(s, 0) + 1
        pipe_df = pd.DataFrame({"Status": list(status_counts.keys()), "Count": list(status_counts.values())})
        colors = [CHART_COLORS[0], CHART_COLORS[3], CHART_COLORS[4], CHART_COLORS[8], CHART_COLORS[11], CHART_COLORS[5]]
        fig = px.bar(pipe_df, x="Status", y="Count", color="Status",
                     color_discrete_sequence=colors, text="Count")
        apply_layout(fig, height=220, margin=dict(t=10, b=10), showlegend=False)
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, width='stretch')

    for c in filtered:
        status_icons = {
            "In Progress": "[IP]", "Completed": "[Done]", "Invoiced": "[Inv]",
            "Paid": "[Paid]", "On Hold": "[Hold]", "Cancelled": "[X]",
        }
        icon = status_icons.get(c.get("status"), "[-]")
        rate_str = f"{format_currency(c['rate'])}/{('hr' if c.get('rate_type') == 'Hourly' else 'flat')}" if c.get("rate") else ""

        # Payment reliability badge
        avg_delay, reliability = _payment_reliability(c["client"], invoices)
        _rel_map = {"On time": t("jt_on_time"), "Sometimes late": t("jt_sometimes_late"), "Often late": t("jt_often_late")}
        rel_badge = ""
        if reliability in _rel_map:
            rel_badge = f" [{_rel_map[reliability]}]"

        cs_badge = f"[{c.get('client_status', 'Active')}]"
        label = f"{icon} **{c['client']}** — {c['project']} ({c.get('status')}) {rate_str}{rel_badge} `{cs_badge}`"

        with st.expander(label):
            # Client detail view
            dc1, dc2 = st.columns(2)
            with dc1:
                st.write(f"**{t('jt_started')}:** {c.get('date_started', t('jt_na'))}")
                st.write(f"**{t('jt_rate')}:** {rate_str or t('jt_not_set')}")
                st.write(f"**{t('jt_client_status')}:** {c.get('client_status', 'Active')}")
                if c.get("email"):
                    st.write(f"**{t('jt_contact_email')}:** {c['email']}")
                    st.markdown(
                        f"<a href='mailto:{c['email']}?subject=Re:%20{c.get('project', '')}' "
                        f"style='font-size:0.85rem;color:var(--text-color);'>{t('jt_send_email')}</a>",
                        unsafe_allow_html=True,
                    )
                if c.get("phone"):
                    st.write(f"**{t('jt_phone')}:** {c['phone']}")
            with dc2:
                # Revenue summary for this client
                client_invs = [inv for inv in invoices if inv.get("client") == c["client"]]
                client_paid = sum(inv.get("amount", 0) for inv in client_invs if inv.get("paid"))
                client_total = sum(inv.get("amount", 0) for inv in client_invs)
                st.write(f"**{t('jt_total_invoiced')}:** {format_currency(client_total)}")
                st.write(f"**{t('jt_total_paid')}:** {format_currency(client_paid)}")
                st.write(f"**{t('jt_invoices')}:** {len(client_invs)}")
                if reliability != "No data":
                    color = CHART_COLORS[3] if reliability == "On time" else CHART_COLORS[4] if reliability == "Sometimes late" else CHART_COLORS[5]
                    _avg_label = t('jt_avg')
                    _days_label = t('jt_days')
                    _delay_str = f' ({_avg_label} {avg_delay:.0f} {_days_label})' if avg_delay is not None else ''
                    st.markdown(
                        f"**{t('jt_payment')}:** <span style='color:{color};font-weight:600;'>{_rel_map.get(reliability, reliability)}</span>"
                        f"{_delay_str}",
                        unsafe_allow_html=True,
                    )
                if c.get("notes"):
                    st.write(f"**{t('jt_notes')}:** {c['notes']}")

            # Edit controls
            ec1, ec2, ec3 = st.columns([2, 1, 1])
            with ec1:
                new_status = st.selectbox(
                    t("jt_job_status"), STATUSES,
                    index=STATUSES.index(c["status"]) if c["status"] in STATUSES else 0,
                    key=f"cs_{c['id']}",
                )
            with ec2:
                new_client_status = st.selectbox(
                    t("jt_client_status"), CLIENT_STATUSES,
                    index=CLIENT_STATUSES.index(c.get("client_status", "Active")) if c.get("client_status", "Active") in CLIENT_STATUSES else 0,
                    key=f"ccs_{c['id']}",
                )
            with ec3:
                new_notes = st.text_input(t("jt_notes"), value=c.get("notes", ""), key=f"cn_{c['id']}")

            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button(t("jt_save"), key=f"csave_{c['id']}"):
                    for item in data["clients"]:
                        if item["id"] == c["id"]:
                            item["status"] = new_status
                            item["client_status"] = new_client_status
                            item["notes"] = new_notes
                            break
                    _save(data)
                    st.toast(t("jt_updated"))
                    st.rerun()
            with bc2:
                if st.button(t("jt_delete"), key=f"cdel_{c['id']}"):
                    data["clients"] = [x for x in data["clients"] if x["id"] != c["id"]]
                    _save(data)
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════
#  Time Tracking Tab
# ═══════════════════════════════════════════════════════════════════════

def _render_time_tracking(data):
    clients = data.get("clients", [])
    time_entries = data.get("time_entries", [])
    client_names = sorted(set(c["client"] for c in clients)) if clients else []

    if not client_names:
        st.info(t("jt_add_client_first_time"))
        return

    st.markdown(f"### {t('jt_log_time')}")

    # Simple timer
    with st.expander(t("jt_timer")):
        st.caption(t("jt_timer_hint"))
        if "timer_running" not in st.session_state:
            st.session_state.timer_running = False
            st.session_state.timer_start = None

        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            timer_client = st.selectbox(t("jt_client"), client_names, key="timer_client")
        with tc2:
            timer_project = st.text_input(t("jt_project"), key="timer_project", placeholder=t("jt_what_working_on"))
        with tc3:
            timer_notes = st.text_input(t("jt_notes"), key="timer_notes", placeholder=t("jt_optional_notes"))

        if not st.session_state.timer_running:
            if st.button(t("jt_start_timer"), type="primary", width='stretch'):
                st.session_state.timer_running = True
                st.session_state.timer_start = datetime.now().isoformat()
                st.toast(t("jt_timer_started"))
                st.rerun()
        else:
            start_time = datetime.fromisoformat(st.session_state.timer_start)
            elapsed = datetime.now() - start_time
            hours = elapsed.total_seconds() / 3600
            st.info(t("jt_timer_running", start=start_time.strftime('%H:%M:%S'), hours=f"{hours:.2f}"))
            if st.button(t("jt_stop_and_log"), type="primary", width='stretch'):
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds() / 3600
                entry = {
                    "id": str(uuid.uuid4())[:8],
                    "date": start_time.strftime("%Y-%m-%d"),
                    "start_time": start_time.strftime("%H:%M"),
                    "end_time": end_time.strftime("%H:%M"),
                    "hours": round(duration, 2),
                    "client": timer_client,
                    "project": timer_project,
                    "notes": timer_notes,
                }
                data["time_entries"].append(entry)
                _save(data)
                st.session_state.timer_running = False
                st.session_state.timer_start = None
                st.toast(t("jt_time_logged_hours", hours=f"{duration:.2f}"))
                st.rerun()

    # Manual time entry
    with st.expander(t("jt_manual_time_entry")):
        with st.form("manual_time", clear_on_submit=True):
            mt1, mt2 = st.columns(2)
            with mt1:
                mt_date = st.date_input(t("jt_date"), value=date.today(), key="mt_date")
                mt_hours = st.number_input(t("jt_hours"), min_value=0.1, step=0.5, format="%.2f", key="mt_hours")
                mt_client = st.selectbox(t("jt_client"), client_names, key="mt_client")
            with mt2:
                mt_project = st.text_input(t("jt_project"), key="mt_project")
                mt_notes = st.text_input(t("jt_notes"), key="mt_notes")

            if st.form_submit_button(t("jt_add_time_entry"), type="primary", width='stretch'):
                entry = {
                    "id": str(uuid.uuid4())[:8],
                    "date": str(mt_date),
                    "hours": mt_hours,
                    "client": mt_client,
                    "project": mt_project,
                    "notes": mt_notes,
                }
                data["time_entries"].append(entry)
                _save(data)
                st.toast(t("jt_time_logged_hours", hours=mt_hours))
                st.rerun()

    # Time log
    if not time_entries:
        st.info(t("jt_no_time_entries"))
        return

    st.markdown("---")
    st.markdown(f"### {t('jt_time_log')}")

    # Filters
    fl1, fl2 = st.columns(2)
    with fl1:
        time_filter_client = st.selectbox(t("jt_filter_by_client"), [t("jt_all")] + client_names, key="time_filter_client")
    with fl2:
        time_filter_range = st.selectbox(t("jt_date_range"), [t("jt_all_time"), t("jt_this_week"), t("jt_this_month")], key="time_filter_range")

    filtered_entries = time_entries[:]
    if time_filter_client != t("jt_all"):
        filtered_entries = [e for e in filtered_entries if e.get("client") == time_filter_client]
    if time_filter_range == t("jt_this_week"):
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        filtered_entries = [e for e in filtered_entries if e.get("date", "") >= week_start]
    elif time_filter_range == t("jt_this_month"):
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        filtered_entries = [e for e in filtered_entries if e.get("date", "") >= month_start]

    if filtered_entries:
        te_df = pd.DataFrame(filtered_entries)
        display_cols = [c for c in ["date", "hours", "client", "project", "notes"] if c in te_df.columns]
        st.dataframe(te_df[display_cols], width='stretch', hide_index=True)

        total_hours = sum(e.get("hours", 0) for e in filtered_entries)
        st.metric(t("jt_total_hours"), f"{total_hours:.1f}")

        # Weekly summary
        st.markdown(f"### {t('jt_weekly_summary')}")
        te_df["date"] = pd.to_datetime(te_df["date"], errors="coerce")
        te_df = te_df.dropna(subset=["date"])
        if not te_df.empty:
            te_df["week"] = te_df["date"].dt.isocalendar().week.astype(str)
            weekly = te_df.groupby(["week", "client"])["hours"].sum().reset_index()
            weekly.columns = ["Week", "Client", "Hours"]
            st.dataframe(weekly, width='stretch', hide_index=True)

        # Generate invoice from time
        st.markdown("---")
        st.markdown(f"### {t('jt_generate_invoice_from_time')}")
        gi1, gi2, gi3 = st.columns(3)
        with gi1:
            gi_client = st.selectbox(t("jt_client"), client_names, key="gi_client")
        with gi2:
            gi_start = st.date_input(t("jt_from"), value=date.today() - timedelta(days=30), key="gi_start")
        with gi3:
            gi_end = st.date_input(t("jt_to"), value=date.today(), key="gi_end")

        # Get rate for client
        client_record = next((c for c in data["clients"] if c["client"] == gi_client), None)
        gi_rate = client_record.get("rate", 0) if client_record else 0
        gi_rate = st.number_input(t("jt_hourly_rate"), value=gi_rate, step=5.0, format="%.2f", key="gi_rate")

        matching = [e for e in time_entries
                    if e.get("client") == gi_client
                    and str(gi_start) <= e.get("date", "") <= str(gi_end)]

        if matching:
            st.caption(t("jt_time_entries_summary", count=len(matching), hours=f"{sum(e.get('hours', 0) for e in matching):.1f}"))
            if st.button(t("jt_generate_invoice_from_time"), type="primary"):
                from utils.invoice_templates import generate_invoice_number
                line_items = []
                for e in matching:
                    hrs = e.get("hours", 0)
                    desc = f"{e.get('project', 'Work')} — {e.get('date', '')} ({hrs:.1f} hrs)"
                    line_items.append({"description": desc, "quantity": hrs, "rate": gi_rate})

                total = sum(item["quantity"] * item["rate"] for item in line_items)
                inv_number = generate_invoice_number(data.get("invoices", []))
                new_inv = {
                    "id": str(uuid.uuid4())[:8],
                    "number": inv_number,
                    "client": gi_client,
                    "date": str(date.today()),
                    "due_date": _calc_due_date(str(date.today()), "Net 30"),
                    "amount": round(total, 2),
                    "line_items": line_items,
                    "notes": t("jt_time_entries_range", start=gi_start, end=gi_end),
                    "payment_terms": "Net 30",
                    "paid": False,
                    "tax_rate": 0,
                    "discount": 0,
                }
                data["invoices"].append(new_inv)
                _save(data)
                st.toast(t("jt_invoice_created_amount", number=inv_number, amount=format_currency(total)))
                st.rerun()
        else:
            st.info(t("jt_no_matching_time_entries"))
    else:
        st.info(t("jt_no_matching_time_entries"))

    # Delete time entries
    with st.expander(t("jt_manage_time_entries")):
        for i, e in enumerate(reversed(time_entries)):
            idx = len(time_entries) - 1 - i
            tc1, tc2 = st.columns([4, 1])
            tc1.markdown(f"{e.get('date', '')} — {e.get('client', '')} — {e.get('hours', 0):.1f}h — {e.get('project', '')}")
            if tc2.button(t("jt_delete"), key=f"del_time_{idx}"):
                data["time_entries"].pop(idx)
                _save(data)
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════
#  Invoices Tab
# ═══════════════════════════════════════════════════════════════════════

def _render_invoices(data, settings, tax_rate):
    invoices = data.get("invoices", [])
    clients = data.get("clients", [])
    client_names = list({c["client"] for c in clients}) if clients else []

    st.markdown(f"### {t('jt_create_invoice')}")

    if not client_names:
        st.info(t("jt_add_client_first"))
    else:
        with st.form("create_invoice", clear_on_submit=True):
            ic1, ic2 = st.columns(2)
            with ic1:
                inv_client = st.selectbox(t("jt_client"), client_names)
                inv_date = st.date_input(t("jt_invoice_date"), value=date.today())
                _terms_map = {"Net 30": t("jt_net_30"), "Net 15": t("jt_net_15"), "Net 60": t("jt_net_60"), "Due on Receipt": t("jt_due_on_receipt")}
                payment_terms = st.selectbox(t("jt_payment_terms"), list(_terms_map.keys()), format_func=lambda x: _terms_map[x])
            with ic2:
                inv_tax = st.number_input(t("jt_tax_rate_pct"), min_value=0.0, max_value=50.0,
                                           value=float(tax_rate), step=0.5, format="%.1f")
                inv_discount = st.number_input(t("jt_discount"), min_value=0.0, step=5.0, format="%.2f")
                inv_notes = st.text_input(t("jt_notes_optional"))

            # Template selection
            from utils.invoice_templates import TEMPLATES
            template_names = list(TEMPLATES.keys())
            default_template = settings.get("invoice", {}).get("default_template", "Professional")
            template_idx = template_names.index(default_template) if default_template in template_names else 1
            inv_template = st.selectbox(t("jt_invoice_template"), template_names, index=template_idx)

            st.markdown(f"**{t('jt_line_items')}**")
            st.caption(t("jt_line_items_hint"))

            line_items = []
            for li in range(8):
                lc1, lc2, lc3 = st.columns([3, 1, 1])
                with lc1:
                    desc = st.text_input(t("jt_description"), key=f"li_desc_{li}",
                                         placeholder=t("jt_description_placeholder") if li == 0 else "")
                with lc2:
                    qty = st.number_input(t("jt_qty_hours"), min_value=0.0, step=1.0, key=f"li_qty_{li}", format="%.1f")
                with lc3:
                    li_rate = st.number_input(t("jt_rate"), min_value=0.0, step=10.0, key=f"li_rate_{li}", format="%.2f")

                if desc.strip():
                    line_items.append({"description": desc, "quantity": qty, "rate": li_rate})

            if st.form_submit_button(t("jt_create_invoice"), type="primary", width='stretch'):
                if not line_items:
                    st.error(t("jt_err_no_line_items"))
                else:
                    from utils.invoice_templates import generate_invoice_number, _calc_totals
                    subtotal, tax_amount, total = _calc_totals(line_items, inv_tax, inv_discount)
                    inv_number = generate_invoice_number(invoices)
                    due_date = _calc_due_date(str(inv_date), payment_terms)

                    # Get client info
                    client_record = next((c for c in clients if c["client"] == inv_client), {})
                    client_info = {
                        "name": inv_client,
                        "email": client_record.get("email", ""),
                        "address": client_record.get("address", ""),
                        "phone": client_record.get("phone", ""),
                    }

                    new_invoice = {
                        "id": str(uuid.uuid4())[:8],
                        "number": inv_number,
                        "client": inv_client,
                        "client_info": client_info,
                        "date": str(inv_date),
                        "due_date": due_date,
                        "amount": round(total, 2),
                        "line_items": line_items,
                        "notes": inv_notes,
                        "payment_terms": payment_terms,
                        "paid": False,
                        "tax_rate": inv_tax,
                        "discount": inv_discount,
                        "template": inv_template,
                    }
                    invoices.append(new_invoice)
                    data["invoices"] = invoices
                    _save(data)
                    st.toast(t("jt_invoice_created_amount", number=inv_number, amount=format_currency(total)))
                    st.rerun()

    # Invoice list
    if not invoices:
        return

    st.markdown("---")
    st.markdown(f"### {t('jt_all_invoices')}")

    unpaid = [inv for inv in invoices if not inv.get("paid")]
    paid = [inv for inv in invoices if inv.get("paid")]
    ic1, ic2 = st.columns(2)
    ic1.metric(t("jt_unpaid"), f"{len(unpaid)} ({format_currency(sum(i['amount'] for i in unpaid))})")
    ic2.metric(t("jt_paid"), f"{len(paid)} ({format_currency(sum(i['amount'] for i in paid))})")

    for inv in sorted(invoices, key=lambda x: x.get("date", ""), reverse=True):
        paid_icon = f"[{t('jt_paid')}]" if inv.get("paid") else f"[{t('jt_pending')}]"
        inv_num = inv.get("number", inv.get("id", "").upper())
        label = f"{paid_icon} #{inv_num} — {inv['client']} — {format_currency(inv['amount'])} ({inv.get('date', '')})"

        with st.expander(label):
            # Line items table
            if inv.get("line_items"):
                li_data = []
                for item in inv["line_items"]:
                    li_data.append({
                        t("jt_description"): item["description"],
                        t("jt_qty_hours"): item.get("quantity", 0),
                        t("jt_rate"): format_currency(item.get("rate", 0)),
                        t("jt_amount"): format_currency(item.get("quantity", 0) * item.get("rate", 0)),
                    })
                st.dataframe(pd.DataFrame(li_data), width='stretch', hide_index=True)

            # Invoice details
            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown(f"**{t('jt_total')}: {format_currency(inv['amount'])}**")
                if inv.get("tax_rate"):
                    st.caption(f"{t('jt_tax')}: {inv['tax_rate']}%")
                if inv.get("discount"):
                    st.caption(f"{t('jt_discount')}: {format_currency(inv['discount'])}")
            with dc2:
                st.caption(f"{t('jt_terms')}: {inv.get('payment_terms', t('jt_na'))}")
                st.caption(f"{t('jt_due_date')}: {inv.get('due_date', t('jt_na'))}")
                if inv.get("notes"):
                    st.caption(f"{t('jt_notes')}: {inv['notes']}")

            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                if inv.get("paid"):
                    if st.button(t("jt_mark_unpaid"), key=f"unpay_{inv['id']}"):
                        for item in data["invoices"]:
                            if item["id"] == inv["id"]:
                                item["paid"] = False
                                item.pop("paid_date", None)
                                break
                        _save(data)
                        st.rerun()
                else:
                    if st.button(t("jt_mark_paid"), key=f"pay_{inv['id']}", type="primary"):
                        for item in data["invoices"]:
                            if item["id"] == inv["id"]:
                                item["paid"] = True
                                item["paid_date"] = datetime.now().strftime("%Y-%m-%d")
                                break
                        _save(data)
                        create_notification(
                            "success", "freelance",
                            t("jt_notif_payment_received", amount=format_currency(inv['amount'])),
                            t("jt_notif_payment_from", client=inv.get('client', 'Unknown'), number=inv_num),
                            action_module="job_tracker",
                            dedup_hours=1,
                        )
                        st.toast(t("jt_invoice_marked_paid"))
                        st.rerun()
            with bc2:
                try:
                    from utils.invoice_templates import render_invoice_pdf
                    template = inv.get("template", "Professional")
                    pdf_bytes = render_invoice_pdf(inv, settings, template)
                    st.download_button(
                        f"PDF ({template})",
                        data=pdf_bytes,
                        file_name=f"invoice_{inv_num}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{inv['id']}",
                    )
                except Exception as e:
                    st.error(f"{t('jt_pdf_error')}: {e}")
            with bc3:
                if st.button(t("jt_delete"), key=f"idel_{inv['id']}"):
                    data["invoices"] = [x for x in data["invoices"] if x["id"] != inv["id"]]
                    _save(data)
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════
#  Recurring Invoices Tab
# ═══════════════════════════════════════════════════════════════════════

def _render_recurring(data):
    clients = data.get("clients", [])
    client_names = list({c["client"] for c in clients}) if clients else []
    recurring = data.get("recurring_invoices", [])

    st.markdown(f"### {t('jt_recurring_invoices')}")
    st.caption(t("jt_recurring_hint"))

    if not client_names:
        st.info(t("jt_add_client_first_recurring"))
        return

    with st.expander(t("jt_create_recurring_invoice")):
        with st.form("add_recurring", clear_on_submit=True):
            rc1, rc2 = st.columns(2)
            with rc1:
                ri_client = st.selectbox(t("jt_client"), client_names, key="ri_client")
                _freq_options = ["Weekly", "Bi-weekly", "Monthly", "Quarterly"]
                _freq_labels = {"Weekly": t("jt_weekly"), "Bi-weekly": t("jt_biweekly"), "Monthly": t("jt_monthly"), "Quarterly": t("jt_quarterly")}
                ri_frequency = st.selectbox(t("jt_frequency"), _freq_options, format_func=lambda x: _freq_labels.get(x, x))
                ri_start = st.date_input(t("jt_start_date"), value=date.today(), key="ri_start")
                _ri_terms_map = {"Net 30": t("jt_net_30"), "Net 15": t("jt_net_15"), "Net 60": t("jt_net_60"), "Due on Receipt": t("jt_due_on_receipt")}
                ri_terms = st.selectbox(t("jt_payment_terms"), list(_ri_terms_map.keys()), format_func=lambda x: _ri_terms_map[x], key="ri_terms")
            with rc2:
                ri_end = st.date_input(t("jt_end_date_optional"), value=None, key="ri_end")
                ri_tax = st.number_input(t("jt_tax_rate_pct"), min_value=0.0, max_value=50.0, value=0.0, step=0.5, key="ri_tax")
                ri_notes = st.text_input(t("jt_notes"), key="ri_notes")

            st.markdown(f"**{t('jt_line_items')}**")
            ri_items = []
            for li in range(5):
                lc1, lc2, lc3 = st.columns([3, 1, 1])
                with lc1:
                    desc = st.text_input(t("jt_description"), key=f"ri_desc_{li}")
                with lc2:
                    qty = st.number_input(t("jt_qty"), min_value=0.0, step=1.0, key=f"ri_qty_{li}", format="%.1f")
                with lc3:
                    rate = st.number_input(t("jt_rate"), min_value=0.0, step=10.0, key=f"ri_rate_{li}", format="%.2f")
                if desc.strip():
                    ri_items.append({"description": desc, "quantity": qty, "rate": rate})

            if st.form_submit_button(t("jt_create_recurring_invoice"), type="primary", width='stretch'):
                if not ri_items:
                    st.error(t("jt_err_no_line_items"))
                else:
                    total = sum(item["quantity"] * item["rate"] for item in ri_items)
                    new_ri = {
                        "id": str(uuid.uuid4())[:8],
                        "client": ri_client,
                        "frequency": ri_frequency,
                        "next_due": str(ri_start),
                        "end_date": str(ri_end) if ri_end else "",
                        "amount": round(total, 2),
                        "line_items": ri_items,
                        "payment_terms": ri_terms,
                        "tax_rate": ri_tax,
                        "discount": 0,
                        "notes": ri_notes,
                        "status": "Active",
                        "created": datetime.now().strftime("%Y-%m-%d"),
                    }
                    data["recurring_invoices"].append(new_ri)
                    _save(data)
                    st.toast(t("jt_recurring_added"))
                    st.rerun()

    if not recurring:
        st.info(t("jt_no_recurring"))
        return

    st.markdown("---")
    for ri in recurring:
        status_icon = f"[{t('jt_active')}]" if ri["status"] == "Active" else f"[{t('jt_paused')}]" if ri["status"] == "Paused" else f"[{t('jt_ended')}]"
        label = (f"{status_icon} {ri['client']} — {format_currency(ri['amount'])} "
                 f"{ri['frequency']} — {t('jt_next')}: {ri.get('next_due', t('jt_na'))}")

        with st.expander(label):
            st.caption(f"{t('jt_created')}: {ri.get('created', t('jt_na'))} · {t('jt_terms')}: {ri.get('payment_terms', t('jt_na'))}")
            if ri.get("end_date"):
                st.caption(f"{t('jt_ends')}: {ri['end_date']}")

            # Show generated invoices
            generated = [inv for inv in data.get("invoices", [])
                         if inv.get("recurring_id") == ri.get("id")]
            if generated:
                st.caption(t("jt_generated_count", count=len(generated)))

            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                if ri["status"] == "Active":
                    if st.button(t("jt_pause"), key=f"pause_{ri['id']}"):
                        ri["status"] = "Paused"
                        _save(data)
                        st.rerun()
                elif ri["status"] == "Paused":
                    if st.button(t("jt_resume"), key=f"resume_{ri['id']}"):
                        ri["status"] = "Active"
                        _save(data)
                        st.rerun()
            with bc2:
                if ri["status"] != "Ended":
                    if st.button(t("jt_end"), key=f"end_{ri['id']}"):
                        ri["status"] = "Ended"
                        _save(data)
                        st.rerun()
            with bc3:
                if st.button(t("jt_delete"), key=f"del_ri_{ri['id']}"):
                    data["recurring_invoices"] = [x for x in data["recurring_invoices"] if x["id"] != ri["id"]]
                    _save(data)
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════
#  Expenses Tab
# ═══════════════════════════════════════════════════════════════════════

def _render_expenses(data, invoices):
    expenses = data.get("expenses", [])
    clients = data.get("clients", [])
    client_names = [t("jt_none")] + sorted(set(c["client"] for c in clients))
    sym = get_currency_symbol()

    st.markdown(f"### {t('jt_expenses')}")

    with st.expander(t("jt_add_expense"), expanded=not expenses):
        with st.form("add_expense", clear_on_submit=True):
            ec1, ec2 = st.columns(2)
            with ec1:
                ex_date = st.date_input(t("jt_date"), value=date.today(), key="ex_date")
                ex_desc = st.text_input(t("jt_description") + " *", key="ex_desc")
                ex_amount = st.number_input(t("jt_amount"), min_value=0.01, step=10.0, format="%.2f", key="ex_amount")
            with ec2:
                ex_category = st.selectbox(t("jt_category"), EXPENSE_CATEGORIES, key="ex_cat")
                ex_client = st.selectbox(t("jt_client_optional_billable"), client_names, key="ex_client")
                ex_receipt = st.text_input(t("jt_receipt_link"), key="ex_receipt")

            if st.form_submit_button(t("jt_add_expense"), type="primary", width='stretch'):
                if not ex_desc.strip():
                    st.error(t("jt_err_description_required"))
                else:
                    expense = {
                        "id": str(uuid.uuid4())[:8],
                        "date": str(ex_date),
                        "description": ex_desc.strip(),
                        "amount": ex_amount,
                        "category": ex_category,
                        "client": ex_client if ex_client != t("jt_none") else "",
                        "receipt": ex_receipt.strip(),
                    }
                    data["expenses"].append(expense)
                    _save(data)
                    st.toast(t("jt_expense_added", amount=format_currency(ex_amount)))
                    st.rerun()

    if not expenses:
        st.info(t("jt_no_expenses"))
        return

    # Filters
    ef1, ef2 = st.columns(2)
    with ef1:
        ex_filter_cat = st.selectbox(t("jt_filter_by_category"), [t("jt_all")] + EXPENSE_CATEGORIES, key="ex_filter_cat")
    with ef2:
        ex_filter_range = st.selectbox(t("jt_date_range"), [t("jt_all_time"), t("jt_this_month"), t("jt_this_year")], key="ex_filter_range")

    filtered = expenses[:]
    if ex_filter_cat != t("jt_all"):
        filtered = [e for e in filtered if e.get("category") == ex_filter_cat]
    if ex_filter_range == t("jt_this_month"):
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        filtered = [e for e in filtered if e.get("date", "") >= month_start]
    elif ex_filter_range == t("jt_this_year"):
        year_start = datetime.now().replace(month=1, day=1).strftime("%Y-%m-%d")
        filtered = [e for e in filtered if e.get("date", "") >= year_start]

    total_expenses = sum(e.get("amount", 0) for e in filtered)
    st.metric(t("jt_total_expenses"), format_currency(total_expenses))

    # Expense table
    if filtered:
        ex_df = pd.DataFrame(filtered)
        display_cols = [c for c in ["date", "description", "amount", "category", "client"] if c in ex_df.columns]
        st.dataframe(ex_df[display_cols], width='stretch', hide_index=True)

    # Monthly expense chart
    if len(filtered) > 1:
        import plotly.graph_objects as go
        ex_df = pd.DataFrame(filtered)
        ex_df["date"] = pd.to_datetime(ex_df["date"], errors="coerce")
        ex_df = ex_df.dropna(subset=["date"])
        if not ex_df.empty:
            ex_df["month"] = ex_df["date"].dt.to_period("M").astype(str)
            monthly_exp = ex_df.groupby("month")["amount"].sum().reset_index()
            monthly_exp.columns = ["Month", "Expenses"]

            fig = go.Figure(go.Bar(
                x=monthly_exp["Month"], y=monthly_exp["Expenses"],
                marker_color=CHART_COLORS[5],
                text=[f"{sym}{v:,.0f}" for v in monthly_exp["Expenses"]],
                textposition="outside",
            ))
            apply_layout(fig, height=280, title=t("jt_monthly_expenses"), margin=dict(t=30, b=10))
            st.plotly_chart(fig, width='stretch')

    # ── Profit & Loss ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### {t('jt_profit_and_loss')}")

    paid_invoices = [inv for inv in invoices if inv.get("paid")]
    all_expenses = expenses

    if not paid_invoices and not all_expenses:
        st.info(t("jt_need_data_for_pl"))
        return

    # Build monthly P&L
    months_set = set()
    for inv in paid_invoices:
        d = _parse_date(inv.get("date"))
        if d:
            months_set.add(d.strftime("%Y-%m"))
    for exp in all_expenses:
        d = _parse_date(exp.get("date"))
        if d:
            months_set.add(d.strftime("%Y-%m"))

    if not months_set:
        return

    months_sorted = sorted(months_set)[-12:]  # Last 12 months

    pl_data = []
    for month in months_sorted:
        rev = sum(inv.get("amount", 0) for inv in paid_invoices
                  if inv.get("date", "")[:7] == month)
        exp_total = sum(e.get("amount", 0) for e in all_expenses
                        if e.get("date", "")[:7] == month)
        net = rev - exp_total
        margin = (net / rev * 100) if rev > 0 else 0
        pl_data.append({
            "Month": month,
            "Revenue": rev,
            "Expenses": exp_total,
            "Net Profit": net,
            "Margin": f"{margin:.0f}%",
        })

    pl_df = pd.DataFrame(pl_data)

    # Summary metrics
    total_rev = pl_df["Revenue"].sum()
    total_exp = pl_df["Expenses"].sum()
    total_net = total_rev - total_exp
    total_margin = (total_net / total_rev * 100) if total_rev > 0 else 0

    pm1, pm2, pm3, pm4 = st.columns(4)
    pm1.metric(t("jt_total_revenue"), format_currency(total_rev))
    pm2.metric(t("jt_total_expenses"), format_currency(total_exp))
    pm3.metric(t("jt_net_profit"), format_currency(total_net))
    pm4.metric(t("jt_profit_margin"), f"{total_margin:.0f}%")

    # P&L table
    display_pl = pl_df.copy()
    for col in ["Revenue", "Expenses", "Net Profit"]:
        display_pl[col] = display_pl[col].apply(lambda v: format_currency(v))
    st.dataframe(display_pl, width='stretch', hide_index=True)

    # P&L chart
    import plotly.graph_objects as go
    tc = _theme_colors()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pl_df["Month"], y=pl_df["Revenue"],
        name=t("jt_revenue"), marker_color=CHART_COLORS[3],
    ))
    fig.add_trace(go.Bar(
        x=pl_df["Month"], y=pl_df["Expenses"],
        name=t("jt_expenses"), marker_color=CHART_COLORS[5],
    ))
    fig.add_trace(go.Scatter(
        x=pl_df["Month"], y=pl_df["Net Profit"],
        name=t("jt_net_profit"), line=dict(color=CHART_COLORS[0], width=3),
        mode="lines+markers",
    ))
    apply_layout(fig, height=350, title=t("jt_profit_and_loss"),
                 margin=dict(t=30, b=10))
    fig.update_layout(barmode="group")
    st.plotly_chart(fig, width='stretch')

    # Export P&L as PDF
    if st.button(t("jt_export_pl_pdf")):
        try:
            from utils.report_builder import ReportPDF
            settings = load_json("settings.json", default={})
            user_name = settings.get("user_name", "")
            pdf = ReportPDF(t("jt_pl_report"), user_name)
            pdf.add_title_page()
            pdf.add_page()
            pdf.add_section_header(t("jt_pl_summary"))
            pdf.add_summary_box({
                t("jt_total_revenue"): format_currency(total_rev),
                t("jt_total_expenses"): format_currency(total_exp),
                t("jt_net_profit"): format_currency(total_net),
                t("jt_profit_margin"): f"{total_margin:.0f}%",
            })
            pdf.add_section_header(t("jt_monthly_breakdown"))
            headers = ["Month", "Revenue", "Expenses", "Net Profit", "Margin"]
            rows = []
            for _, row in pl_df.iterrows():
                rows.append([
                    row["Month"],
                    format_currency(row["Revenue"]),
                    format_currency(row["Expenses"]),
                    format_currency(row["Net Profit"]),
                    row["Margin"],
                ])
            pdf.add_table(headers, rows, col_widths=[35, 35, 35, 35, 25])
            pdf_bytes = pdf.get_bytes()
            st.download_button(
                t("jt_download_pl_pdf"),
                data=pdf_bytes,
                file_name=f"pl_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"{t('jt_pdf_error')}: {e}")

    # Delete expenses
    with st.expander(t("jt_manage_expenses")):
        for i, e in enumerate(reversed(expenses)):
            idx = len(expenses) - 1 - i
            ec1, ec2 = st.columns([4, 1])
            ec1.markdown(f"{e.get('date', '')} — {e.get('description', '')} — {format_currency(e.get('amount', 0))}")
            if ec2.button(t("jt_delete"), key=f"del_exp_{idx}"):
                data["expenses"].pop(idx)
                _save(data)
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════

def _parse_date(date_str):
    """Parse a date string, returning datetime or None."""
    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _check_overdue_alerts(unpaid_invoices):
    """Fire notifications for overdue invoices."""
    _prefs = load_json("settings.json", default={}).get("notifications", {})
    _overdue_days = _prefs.get("invoice_overdue_days", 30)
    for inv in unpaid_invoices:
        try:
            inv_date = datetime.strptime(inv.get("date", ""), "%Y-%m-%d")
            days_old = (datetime.now() - inv_date).days
            inv_num = inv.get("number", inv.get("id", "?"))
            inv_client = inv.get("client", "Unknown")
            inv_amt = inv.get("amount", 0)
            if days_old > 60:
                create_notification(
                    "alert", "freelance",
                    t("jt_notif_overdue", number=inv_num, days=days_old),
                    t("jt_notif_outstanding", client=inv_client, amount=format_currency(inv_amt)),
                    action_module="job_tracker",
                )
            elif days_old > _overdue_days:
                create_notification(
                    "warning", "freelance",
                    t("jt_notif_overdue", number=inv_num, days=days_old),
                    t("jt_notif_outstanding", client=inv_client, amount=format_currency(inv_amt)),
                    action_module="job_tracker",
                )
        except (ValueError, TypeError):
            pass
