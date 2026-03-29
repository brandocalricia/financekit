"""Shared Plotly chart configuration for consistent styling across all modules."""

CHART_COLORS = ["#6366f1", "#a78bfa", "#8b5cf6", "#22c55e", "#f59e0b", "#ef4444"]

CHART_FONT = dict(color="#e2e8f0", family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")

CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=CHART_FONT,
    xaxis=dict(gridcolor="#2a2a40"),
    yaxis=dict(gridcolor="#2a2a40"),
)


def apply_layout(fig, height=350, margin=None, **overrides):
    """Apply consistent chart styling to a Plotly figure."""
    layout = {**CHART_LAYOUT, "height": height}
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
        font=CHART_FONT,
    )
    return fig
