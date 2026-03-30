import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import uuid
from utils.data_persistence import load_json, save_json
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout, _theme_colors, _chart_font
from utils.formatting import format_currency, format_currency_int, get_currency_symbol
from utils.notifications import create_notification

DATA_FILE = "goals.json"


def _load():
    return load_json(DATA_FILE, default={"goals": []})


def _save(data):
    save_json(DATA_FILE, data)


def _project_date(current: float, target: float, monthly: float) -> str:
    if monthly <= 0:
        return "Never (set a monthly contribution)"
    remaining = target - current
    if remaining <= 0:
        return "Already reached!"
    months_needed = remaining / monthly
    today = date.today()
    total_months = int(months_needed)
    proj_year = today.year + (today.month - 1 + total_months) // 12
    proj_month = (today.month - 1 + total_months) % 12 + 1
    proj_day = min(today.day, 28)
    return f"{date(proj_year, proj_month, proj_day).strftime('%B %d, %Y')}"


def render():
    render_module_header("🎯", "Savings Goal Tracker",
                         "Set goals, track progress, and hit milestones. Your reason to open the app every day.")

    if "goals_data" not in st.session_state:
        st.session_state.goals_data = _load()

    data = st.session_state.goals_data
    goals = data.get("goals", [])

    # ── Add New Goal ──────────────────────────────────────────────────────
    with st.expander("➕ Add a New Goal", expanded=not goals):
        with st.form("add_goal_form", clear_on_submit=True):
            gc1, gc2 = st.columns(2)
            with gc1:
                goal_name = st.text_input("Goal Name *", placeholder="Emergency Fund, Vacation, New Car...")
                target_amount = st.number_input("Target Amount ($)", min_value=1.0, value=1000.0, step=100.0)
                current_amount = st.number_input("Already Saved ($)", min_value=0.0, value=0.0, step=50.0)
            with gc2:
                default_deadline = date(date.today().year + 1, date.today().month, 1)
                deadline = st.date_input("Target Date", value=default_deadline)
                monthly_contribution = st.number_input("Monthly Contribution ($)", min_value=0.0, value=100.0, step=25.0)
                notes = st.text_input("Notes (optional)", placeholder="Why this goal matters...")

            # Shared goal toggle (only if household mode is enabled)
            from utils.household import is_household_enabled, get_member_names
            _hh_on = is_household_enabled()
            shared_goal = False
            if _hh_on:
                shared_goal = st.checkbox("🏠 Shared household goal",
                                           help="All household members can contribute to this goal")

            if st.form_submit_button("🎯 Add Goal", type="primary", width='stretch'):
                if not goal_name:
                    st.error("Please enter a goal name.")
                elif current_amount > target_amount:
                    st.error("Current amount cannot exceed target.")
                else:
                    _member_names = get_member_names() if _hh_on else []
                    _contributions = {}
                    if shared_goal and _member_names:
                        _contributions = {name: 0.0 for name in _member_names}
                        if _member_names:
                            _contributions[_member_names[0]] = float(current_amount)

                    new_goal = {
                        "id": str(uuid.uuid4())[:8],
                        "name": goal_name,
                        "target": float(target_amount),
                        "current": float(current_amount),
                        "deadline": str(deadline),
                        "monthly": float(monthly_contribution),
                        "notes": notes,
                        "created": str(date.today()),
                        "history": [{"date": str(date.today()), "amount": float(current_amount)}],
                        "milestones_celebrated": [],
                        "shared": shared_goal,
                        "contributions": _contributions,
                    }
                    goals.append(new_goal)
                    data["goals"] = goals
                    _save(data)
                    st.toast(f"Goal '{goal_name}' added!", icon="🎯")
                    st.rerun()

    if not goals:
        from utils.ui_helpers import render_empty_state
        render_empty_state("🎯", "No savings goals yet",
                           "Add your first goal above to start tracking your progress!")
        return

    # ── Goals Summary Cards (v4.8) ──────────────────────────────────────
    total_target = sum(g["target"] for g in goals)
    total_saved = sum(g["current"] for g in goals)
    total_remaining = total_target - total_saved
    completed_count = sum(1 for g in goals if g["current"] >= g["target"])
    _overall_pct = int(total_saved / total_target * 100) if total_target > 0 else 0

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">🎯 Active Goals</div>'
            f'<div class="widget-value">{len(goals)}</div>'
            f'<div class="widget-sub">{completed_count} completed</div></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">💰 Total Saved</div>'
            f'<div class="widget-value">{format_currency_int(total_saved)}</div>'
            f'<div class="widget-sub">{_overall_pct}% of target</div></div>',
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">📊 Remaining</div>'
            f'<div class="widget-value">{format_currency_int(total_remaining)}</div>'
            f'<div class="widget-sub">across {len(goals) - completed_count} goal{"s" if len(goals) - completed_count != 1 else ""}</div></div>',
            unsafe_allow_html=True,
        )
    with s4:
        # Progress ring SVG
        _ring_pct = min(_overall_pct, 100)
        _ring_dash = _ring_pct * 2.51327  # circumference = 251.327 for r=40
        _ring_color = "#22c55e" if _ring_pct >= 75 else "#6366f1" if _ring_pct >= 50 else "#a78bfa"
        st.markdown(
            f'<div style="text-align:center;">'
            f'<svg width="80" height="80" viewBox="0 0 100 100" style="margin:auto;">'
            f'<circle cx="50" cy="50" r="40" fill="none" stroke="var(--fk-progress-bg)" stroke-width="8"/>'
            f'<circle cx="50" cy="50" r="40" fill="none" stroke="{_ring_color}" stroke-width="8" '
            f'stroke-dasharray="{_ring_dash:.1f} 251.327" stroke-linecap="round" '
            f'transform="rotate(-90 50 50)" style="transition:stroke-dasharray 0.5s;"/>'
            f'<text x="50" y="54" text-anchor="middle" fill="var(--fk-text)" font-size="18" font-weight="700">'
            f'{_ring_pct}%</text></svg>'
            f'<div style="font-size:0.72rem;color:var(--fk-text-muted);margin-top:2px;">Overall</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Your Goals")

    for goal in goals:
        pct = (goal["current"] / goal["target"] * 100) if goal["target"] > 0 else 0
        pct_capped = min(pct, 100.0)
        is_complete = goal["current"] >= goal["target"]

        # Milestone celebration check
        milestones_celebrated = goal.get("milestones_celebrated", [])
        for milestone in [25, 50, 75]:
            if pct >= milestone and milestone not in milestones_celebrated:
                milestones_celebrated.append(milestone)
                goal["milestones_celebrated"] = milestones_celebrated
                _save(data)
                st.balloons()
                st.toast(f"🎉 {milestone}% milestone reached for '{goal['name']}'!", icon="🎉")
                create_notification(
                    "success", "goals",
                    f"{goal['name']} is {milestone}% funded",
                    f"{goal['name']} is {milestone}% funded — {'halfway there!' if milestone == 50 else 'keep going!'}",
                    action_module="goal_tracker",
                )
                break

        if is_complete and 100 not in milestones_celebrated:
            milestones_celebrated.append(100)
            goal["milestones_celebrated"] = milestones_celebrated
            _save(data)
            st.snow()
            st.toast(f"🏆 Goal '{goal['name']}' COMPLETED! Incredible work!", icon="🏆")
            create_notification(
                "success", "goals",
                f"{goal['name']} fully funded!",
                f"Congratulations! You've fully funded your {goal['name']}!",
                action_module="goal_tracker",
            )

        # Status icon
        if is_complete:
            bar_color, status_icon = "#22c55e", "🏆"
        elif pct >= 75:
            bar_color, status_icon = "#6366f1", "🔥"
        elif pct >= 50:
            bar_color, status_icon = "#8b5cf6", "💪"
        elif pct >= 25:
            bar_color, status_icon = "#a78bfa", "📈"
        else:
            bar_color, status_icon = "#64748b", "🎯"

        expander_label = (
            f"{status_icon} **{goal['name']}** — "
            f"{format_currency_int(goal['current'])} / {format_currency_int(goal['target'])} ({pct:.0f}%)"
        )

        with st.expander(expander_label, expanded=True):
            # Goal card with progress ring + stats (v4.8)
            _g_ring_dash = pct_capped * 2.51327
            _ring_col, _stats_col = st.columns([1, 3])
            with _ring_col:
                st.markdown(
                    f'<div style="text-align:center;padding:0.5rem 0;">'
                    f'<svg width="90" height="90" viewBox="0 0 100 100">'
                    f'<circle cx="50" cy="50" r="40" fill="none" stroke="var(--fk-progress-bg)" stroke-width="8"/>'
                    f'<circle cx="50" cy="50" r="40" fill="none" stroke="{bar_color}" stroke-width="8" '
                    f'stroke-dasharray="{_g_ring_dash:.1f} 251.327" stroke-linecap="round" '
                    f'transform="rotate(-90 50 50)" style="transition:stroke-dasharray 0.5s;"/>'
                    f'<text x="50" y="46" text-anchor="middle" fill="var(--fk-text)" font-size="20" font-weight="700">'
                    f'{pct_capped:.0f}%</text>'
                    f'<text x="50" y="62" text-anchor="middle" fill="var(--fk-text-muted)" font-size="10">saved</text>'
                    f'</svg></div>',
                    unsafe_allow_html=True,
                )
            with _stats_col:
                sm1, sm2, sm3, sm4 = st.columns(4)
                sm1.metric("Saved", format_currency_int(goal['current']))
                sm2.metric("Target", format_currency_int(goal['target']))
                sm3.metric("Remaining", format_currency_int(max(0, goal['target'] - goal['current'])))
                sm4.metric("Monthly", f"{format_currency_int(goal['monthly'])}/mo")

            # Progress bar (thin version)
            st.markdown(
                f'<div style="background:var(--fk-progress-bg);border-radius:6px;height:8px;overflow:hidden;margin:4px 0 8px;">'
                f'<div style="background:{bar_color};width:{pct_capped:.1f}%;height:100%;border-radius:6px;'
                f'transition:width 0.5s;"></div></div>',
                unsafe_allow_html=True,
            )

            # Shared goal contributions
            if goal.get("shared") and goal.get("contributions"):
                contrib = goal["contributions"]
                parts = [f"{name}: {format_currency_int(amt)}" for name, amt in contrib.items()]
                st.caption("🏠 Shared: " + " · ".join(parts))

            # Projection & deadline
            if not is_complete:
                projected = _project_date(goal["current"], goal["target"], goal["monthly"])
                try:
                    dl_date = datetime.strptime(goal["deadline"], "%Y-%m-%d").date()
                    days_left = (dl_date - date.today()).days
                    deadline_str = f"Deadline: **{goal['deadline']}** ({days_left} days away)"
                except Exception:
                    deadline_str = f"Deadline: {goal['deadline']}"

                if goal["monthly"] > 0:
                    # Check if on track
                    try:
                        proj_d = datetime.strptime(
                            _project_date(goal["current"], goal["target"], goal["monthly"]),
                            "%B %d, %Y"
                        ).date() if "Never" not in projected and "Already" not in projected else None
                        dl_d = datetime.strptime(goal["deadline"], "%Y-%m-%d").date()
                        if proj_d and proj_d <= dl_d:
                            st.success(f"✅ On track! At {format_currency_int(goal['monthly'])}/mo → **{projected}**. {deadline_str}")
                        else:
                            st.warning(f"⚠️ At {format_currency_int(goal['monthly'])}/mo → **{projected}** — may miss deadline. {deadline_str}")
                            # Behind schedule notification
                            remaining_amt = goal["target"] - goal["current"]
                            if proj_d and dl_d:
                                months_left = max(1, (dl_d.year - date.today().year) * 12 + dl_d.month - date.today().month)
                                needed_monthly = remaining_amt / months_left
                                create_notification(
                                    "warning", "goals",
                                    f"{goal['name']} behind schedule",
                                    f"{goal['name']} is behind schedule — increase monthly contribution to {get_currency_symbol()}{needed_monthly:,.0f} to stay on track",
                                    action_module="goal_tracker",
                                )
                    except Exception:
                        st.info(f"📅 At {format_currency_int(goal['monthly'])}/mo → **{projected}**. {deadline_str}")
                else:
                    st.info(f"📅 {deadline_str} — set a monthly contribution to see your projection.")

                # Deadline approaching + behind notification
                try:
                    _dl = datetime.strptime(goal["deadline"], "%Y-%m-%d").date()
                    _days_left = (_dl - date.today()).days
                    if 0 < _days_left <= 30 and pct < 90:
                        create_notification(
                            "alert", "goals",
                            f"{goal['name']} deadline in {_days_left} days",
                            f"{goal['name']} deadline is in {_days_left} days but you're only at {pct:.0f}%",
                            action_module="goal_tracker",
                        )
                except Exception:
                    pass
            else:
                st.success("🏆 **Goal completed!** Congratulations!")

            if goal.get("notes"):
                st.caption(f"💬 {goal['notes']}")

            # History chart
            history = goal.get("history", [])
            if len(history) > 1:
                hist_df = pd.DataFrame(history)
                hist_df["date"] = pd.to_datetime(hist_df["date"])
                hist_df = hist_df.sort_values("date")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hist_df["date"], y=hist_df["amount"],
                    mode="lines+markers",
                    line=dict(color=bar_color, width=3),
                    fill="tozeroy",
                    fillcolor="rgba(99,102,241,0.1)",
                    name="Saved",
                    hovertemplate=f"{get_currency_symbol()}%{{y:,.0f}}<extra></extra>",
                ))
                fig.add_hline(
                    y=goal["target"], line_dash="dash", line_color="#22c55e",
                    annotation_text=f"Goal: ${goal['target']:,.0f}",
                    annotation_position="top left",
                )
                _tc = _theme_colors()
                fig.update_layout(
                    height=180, margin=dict(t=10, b=10, l=40, r=10),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font={**_chart_font(), "size": 11},
                    xaxis=dict(gridcolor=_tc["grid"], showgrid=True),
                    yaxis=dict(gridcolor=_tc["grid"], showgrid=True, tickprefix="$"),
                    showlegend=False,
                )
                st.plotly_chart(fig, width='stretch')

            # Milestone timeline (v4.8)
            celebrated = goal.get("milestones_celebrated", [])
            _milestones_all = [25, 50, 75, 100]
            _ms_html = '<div style="display:flex;gap:4px;align-items:center;margin:6px 0;">'
            for _ms in _milestones_all:
                if _ms in celebrated:
                    _ms_icon = "🏆" if _ms == 100 else "🎉"
                    _ms_html += (
                        f'<div style="flex:1;text-align:center;padding:4px;border-radius:6px;'
                        f'background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);">'
                        f'<div style="font-size:0.9rem;">{_ms_icon}</div>'
                        f'<div style="font-size:0.65rem;color:var(--fk-accent);font-weight:600;">{_ms}%</div></div>'
                    )
                else:
                    _ms_html += (
                        f'<div style="flex:1;text-align:center;padding:4px;border-radius:6px;'
                        f'background:var(--fk-card-alt);border:1px solid var(--fk-border);opacity:0.5;">'
                        f'<div style="font-size:0.9rem;">⭕</div>'
                        f'<div style="font-size:0.65rem;color:var(--fk-text-muted);">{_ms}%</div></div>'
                    )
            _ms_html += '</div>'
            st.markdown(_ms_html, unsafe_allow_html=True)

            # Quick-add funds buttons
            st.markdown("**Add Funds**")
            _is_shared = goal.get("shared", False)
            _contributor = None
            if _is_shared and goal.get("contributions"):
                _contributor = st.selectbox(
                    "Contributing as", list(goal["contributions"].keys()),
                    key=f"contrib_{goal['id']}", label_visibility="collapsed",
                )
            qa1, qa2, qa3, qa4 = st.columns(4)
            for col, amt in zip([qa1, qa2, qa3, qa4], [50, 100, 250, 500]):
                with col:
                    if st.button(f"+${amt}", key=f"qa_{goal['id']}_{amt}", width='stretch'):
                        for g in data["goals"]:
                            if g["id"] == goal["id"]:
                                g["current"] = float(goal["current"]) + amt
                                if _is_shared and _contributor and "contributions" in g:
                                    g["contributions"][_contributor] = g["contributions"].get(_contributor, 0) + amt
                                if "history" not in g:
                                    g["history"] = []
                                g["history"].append({
                                    "date": str(date.today()),
                                    "amount": g["current"],
                                })
                                break
                        _save(data)
                        st.session_state.goals_data = data
                        st.toast(f"Added ${amt} to '{goal['name']}'!", icon="💰")
                        st.rerun()

            # Update + Delete
            st.markdown("**Custom Update**")
            uc1, uc2, uc3 = st.columns([3, 1, 1])
            with uc1:
                new_amount = st.number_input(
                    "Current amount saved ($)",
                    min_value=0.0,
                    value=float(goal["current"]),
                    step=50.0,
                    key=f"update_{goal['id']}",
                    label_visibility="collapsed",
                )
            with uc2:
                if st.button("💾 Update", key=f"save_{goal['id']}", width='stretch'):
                    for g in data["goals"]:
                        if g["id"] == goal["id"]:
                            g["current"] = float(new_amount)
                            if "history" not in g:
                                g["history"] = []
                            if not g["history"] or g["history"][-1]["amount"] != float(new_amount):
                                g["history"].append({
                                    "date": str(date.today()),
                                    "amount": float(new_amount),
                                })
                            break
                    _save(data)
                    st.session_state.goals_data = data
                    st.toast(f"'{goal['name']}' updated!", icon="✅")
                    st.rerun()
            with uc3:
                if st.button("🗑️ Delete", key=f"del_{goal['id']}", width='stretch'):
                    data["goals"] = [g for g in data["goals"] if g["id"] != goal["id"]]
                    _save(data)
                    st.session_state.goals_data = data
                    st.rerun()
