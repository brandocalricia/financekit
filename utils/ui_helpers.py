"""Shared UI helper functions for consistent styling across all modules."""
import streamlit as st


def render_module_header(icon: str, title: str, description: str):
    """Render a standardized module header with icon, title, description, and gradient underline."""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:0.5rem;">
        <span style="font-size:2rem;">{icon}</span>
        <div>
            <div style="font-size:1.6rem;font-weight:700;color:#e2e8f0;">{title}</div>
            <div style="color:#94a3b8;font-size:0.95rem;">{description}</div>
        </div>
    </div>
    <div style="height:2px;background:linear-gradient(90deg,#6366f1,transparent);margin-bottom:1rem;"></div>
    """, unsafe_allow_html=True)


def styled_metric_card(title: str, value: str, subtitle: str = "", icon: str = ""):
    """Render a styled metric card matching the dashboard widget style."""
    icon_html = f'<span style="margin-right:4px;">{icon}</span>' if icon else ""
    sub_html = f'<div class="widget-sub">{subtitle}</div>' if subtitle else ""
    return (
        f'<div class="dash-widget">'
        f'<div class="widget-title">{icon_html}{title}</div>'
        f'<div class="widget-value">{value}</div>'
        f'{sub_html}</div>'
    )
