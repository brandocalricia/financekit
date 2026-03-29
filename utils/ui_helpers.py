"""Shared UI helper functions for consistent styling across all modules."""
import streamlit as st


def render_module_header(icon: str, title: str, description: str):
    """Render a standardized module header with icon, title, description, and gradient underline."""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:0.5rem;">
        <span style="font-size:2rem;">{icon}</span>
        <div>
            <div class="fk-module-title">{title}</div>
            <div class="fk-module-desc">{description}</div>
        </div>
    </div>
    <div class="fk-module-line"></div>
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


def render_empty_state(icon: str, title: str, description: str):
    """Render a friendly empty state with icon and message."""
    st.markdown(
        f'<div class="fk-empty">'
        f'<div class="icon">{icon}</div>'
        f'<div class="title">{title}</div>'
        f'<div>{description}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
