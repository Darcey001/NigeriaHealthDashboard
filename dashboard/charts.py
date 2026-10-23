"""Plotly charts for the dashboard.

Style: Nigeria is highlighted in blue, comparison countries are grey and labelled
directly at the end of their lines, so colour is never the only way to tell them apart.
"""

import pandas as pd
import plotly.graph_objects as go

# One set of colours that reads well on both light and dark backgrounds.
# Text colour isn't set here, so labels follow Streamlit's light/dark theme.
COLORS = {
    "focus": "#3987e5",  # Nigeria
    "context": "#9b9a95",  # comparison countries
    "target": "rgba(128, 128, 128, 0.8)",
    "grid": "rgba(128, 128, 128, 0.18)",
    "muted_text": "rgba(128, 128, 128, 1)",
}


def _layout(fig: go.Figure, unit: str, height: int = 380) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=110, t=16, b=8),
        showlegend=False,
        hovermode="x unified",
        font=dict(size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, linecolor=COLORS["grid"], tickformat="d")
    fig.update_yaxes(
        title_text=unit,
        title_font=dict(size=12),
        gridcolor=COLORS["grid"],
        zeroline=False,
        rangemode="tozero",
    )
    return fig


def spread_labels(labels: list[dict], min_gap: float) -> list[dict]:
    """Moves end-of-line labels up or down just enough that none are closer than `min_gap`."""
    placed = sorted(labels, key=lambda lab: lab["y"])
    for i in range(1, len(placed)):
        if placed[i]["y"] - placed[i - 1]["y"] < min_gap:
            placed[i] = {**placed[i], "y": placed[i - 1]["y"] + min_gap}
    return placed


def trend_chart(
    df: pd.DataFrame,
    focus: str,
    unit: str,
    target: float | None = None,
    value_format: str = ",.0f",
) -> go.Figure:
    """Line chart over time. `df` has columns country, year, value."""
    fig = go.Figure()

    # Draw comparison countries first so Nigeria sits on top
    countries = sorted(df["country"].unique(), key=lambda c: c == focus)
    labels = []
    for country in countries:
        d = df[df["country"] == country].sort_values("year")
        if d.empty:
            continue
        is_focus = country == focus
        color = COLORS["focus"] if is_focus else COLORS["context"]
        fig.add_trace(
            go.Scatter(
                x=d["year"],
                y=d["value"],
                name=country,
                mode="lines",
                line=dict(color=color, width=3 if is_focus else 2),
                hovertemplate=f"{country}: %{{y:{value_format}}}<extra></extra>",
            )
        )
        last = d.iloc[-1]
        labels.append({"country": country, "x": last["year"], "y": last["value"], "focus": is_focus})

    # Direct labels at the end of each line, nudged apart so they never overlap
    y_max = max(df["value"].max(), target or 0)
    for label in spread_labels(labels, min_gap=y_max * 0.06):
        fig.add_annotation(
            x=label["x"],
            y=label["y"],
            text=f"<b>{label['country']}</b>" if label["focus"] else label["country"],
            showarrow=False,
            xanchor="left",
            xshift=6,
            font=dict(color=COLORS["focus"], size=12) if label["focus"] else dict(size=12),
        )

    fig.update_xaxes(range=[df["year"].min() - 0.5, df["year"].max() + 0.5])

    if target is not None:
        # The target is explained in the chart heading, so the line stays unlabelled here
        fig.add_hline(y=target, line=dict(color=COLORS["target"], width=1, dash="dot"))

    return _layout(fig, unit)


def ranking_chart(
    df: pd.DataFrame,
    focus: str,
    unit: str,
    better: str,
    value_format: str = ",.0f",
) -> go.Figure:
    """Horizontal bars of each country's latest value, best at the top."""
    d = df.sort_values("value", ascending=(better == "higher"))
    bar_colors = [COLORS["focus"] if c == focus else COLORS["context"] for c in d["country"]]
    fig = go.Figure(
        go.Bar(
            x=d["value"],
            y=d["country"],
            orientation="h",
            marker=dict(color=bar_colors, cornerradius=4),
            text=[format(v, value_format) for v in d["value"]],
            textposition="outside",
            cliponaxis=False,
            customdata=d["year"],
            hovertemplate="%{y}: %{x:" + value_format + "} (%{customdata})<extra></extra>",
        )
    )
    fig = _layout(fig, unit, height=40 + 34 * len(d))
    fig.update_layout(hovermode="closest", margin=dict(l=8, r=60, t=8, b=8), bargap=0.35)
    fig.update_xaxes(title_text=unit, showgrid=True, gridcolor=COLORS["grid"], tickformat="~s")
    fig.update_yaxes(title_text=None, gridcolor="rgba(0,0,0,0)")
    return fig
