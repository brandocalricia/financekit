"""Shared Plotly chart configuration for consistent styling across all modules."""
import streamlit as st

CHART_COLORS = ["#6366f1", "#a78bfa", "#8b5cf6", "#22c55e", "#f59e0b", "#ef4444"]

CHART_FONT = dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")


def _is_light():
    return st.session_state.get("fk_theme", "dark") == "light"


def _theme_colors():
    """Return chart-relevant colors for the current theme."""
    if _is_light():
        return {
            "font_color": "#1e293b",
            "grid": "#e2e8f0",
            "plot_bg": "rgba(0,0,0,0)",
            "paper_bg": "rgba(0,0,0,0)",
        }
    return {
        "font_color": "#e2e8f0",
        "grid": "#2a2a40",
        "plot_bg": "rgba(0,0,0,0)",
        "paper_bg": "rgba(0,0,0,0)",
    }


def _chart_font():
    tc = _theme_colors()
    return {**CHART_FONT, "color": tc["font_color"]}


def _chart_layout():
    tc = _theme_colors()
    return dict(
        plot_bgcolor=tc["plot_bg"],
        paper_bgcolor=tc["paper_bg"],
        font=_chart_font(),
        xaxis=dict(gridcolor=tc["grid"]),
        yaxis=dict(gridcolor=tc["grid"]),
    )


# Legacy constants for backwards compatibility
CHART_LAYOUT = _chart_layout()


def apply_layout(fig, height=350, margin=None, **overrides):
    """Apply consistent chart styling to a Plotly figure."""
    layout = {**_chart_layout(), "height": height}
    if margin:
        layout["margin"] = margin
    else:
        layout["margin"] = dict(t=40, b=10)
    layout.update(overrides)
    fig.update_layout(**layout)
    return fig


def donut_layout(fig, height=260):
    """Apply layout for donut/pie charts."""
    fig.update_layout(
        height=height,
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        font=_chart_font(),
    )
    return fig
