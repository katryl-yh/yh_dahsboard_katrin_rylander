from __future__ import annotations
import plotly.graph_objects as go
from utils.constants import BLUE_1, GRAY_1, GRAY_12
import pandas as pd

def education_area_chart(
    df_summary,
    county: str,
    height: int = 500,
    title: str | None = None,
    # font controls (override from main.py)
    xtick_size: int = 12,
    ytick_size: int = 13,
    title_size: int = 16,
    legend_font_size: int = 12,
    label_font_size: int = 12,      # approval-rate annotation font size
    font_family: str = "Arial",
    **options
):
    """
    Horizontal stacked bar chart per 'Utbildningsområde':
      - Beviljade (closest to the y-axis) + Avslag (stacked to the right) = Ansökta utbildningar.
      - 'Beviljandegrad' shown as a label next to the total length.
    """
    fig = go.Figure()

    required = {"Utbildningsområde", "Ansökta utbildningar", "Beviljade utbildningar"}
    if df_summary is None or len(df_summary) == 0 or not required.issubset(df_summary.columns):
        fig.update_layout(
            height=height,
            plot_bgcolor="white",
            paper_bgcolor="white",
            title=dict(text=title or f"Ansökningar per utbildningsområde – {county}",
                       font=dict(size=title_size, family=font_family)),
            xaxis=dict(
                tickfont=dict(size=xtick_size, family=font_family, color=GRAY_12)
            ),
            yaxis=dict(
                tickfont=dict(size=ytick_size, family=font_family, color=GRAY_12)
            ),
            legend=dict(font=dict(size=legend_font_size, family=font_family)),
            **options
        )
        return fig

    # Sort by total so the last row is the largest bar
    df_plot = df_summary.sort_values("Ansökta utbildningar", ascending=True).copy()
    categories = df_plot["Utbildningsområde"].tolist()

    total = df_plot["Ansökta utbildningar"].astype(float)
    approved = df_plot["Beviljade utbildningar"].astype(float).clip(lower=0, upper=total)
    rejected = (total - approved).clip(lower=0)

    # Stacked bars: Beviljade (near axis) + Avslag (to the right)
    fig.add_trace(go.Bar(
        y=categories,
        x=approved,
        name="Beviljade",
        orientation="h",
        marker_color=BLUE_1,
        hovertemplate="Utbildningsområde: %{y}<br>Beviljade: %{x}<extra></extra>",
        legendrank=1, 
    ))
    fig.add_trace(go.Bar(
        y=categories,
        x=rejected,
        name="Avslag",
        orientation="h",
        marker_color=GRAY_1,  
        hovertemplate="Utbildningsområde: %{y}<br>Avslag: %{x}<extra></extra>",
        legendrank=2,  
    ))

    # Beviljandegrad labels placed just to the right of the total bar length
    max_total = float(total.max()) if len(df_plot) else 0.0
    annotations = []
    if "Beviljandegrad" in df_plot.columns:
        offset = 0.02 * (max_total or 1.0)
        clamp = 1.05 * (max_total or 1.0)  # headroom to avoid clipping
        for _, row in df_plot.iterrows():
            x_pos = float(row["Ansökta utbildningar"]) + offset
            x_pos = min(x_pos, clamp)
            annotations.append(dict(
                x=x_pos,
                y=row["Utbildningsområde"],
                text=f"{float(row['Beviljandegrad']):.1f}%",
                showarrow=False,
                font=dict(color=GRAY_12, size=label_font_size, family=font_family),
                xanchor="left",
                yanchor="middle"
            ))

    fig.update_layout(
        barmode="stack",
        bargap=0.25,
        margin=dict(l=120, r=30, t=80, b=40),
        height=height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=legend_font_size, family=font_family),
            traceorder="normal"  # legendrank controls order
        ),
        title=dict(
            text=title or f"Ansökningar per utbildningsområde – {county}",
            font=dict(size=title_size, family=font_family)
        ),
        yaxis=dict(
            showline=True, linecolor=GRAY_12,
            tickfont=dict(color=GRAY_12, size=ytick_size, family=font_family),
            categoryorder="array", categoryarray=categories,
            automargin=True
        ),
        xaxis=dict(
            showline=True, linecolor=GRAY_12,
            tickfont=dict(color=GRAY_12, size=xtick_size, family=font_family),
            rangemode="tozero",
            automargin=True
        ),
        annotations=annotations,
        **options
    )
    return fig

def provider_education_area_chart(
    df: pd.DataFrame,
    provider: str,
    *,
    xtick_size: int = 11,
    ytick_size: int = 12,
    title_size: int = 18,
    legend_font_size: int = 12,
    label_font_size: int = 11,
    font_family: str = "Arial",
    gray_total: str = "#d1d5db",
    blue_approved: str = "#0284c7",
    gray_axis: str = "#989898",
):
    d = df[df["Anordnare namn"].astype(str).str.strip() == str(provider).strip()].copy()
    if d.empty:
        return go.Figure()

    total = d.groupby("Utbildningsområde").size()
    approved = d[d["Beslut"] == "Beviljad"].groupby("Utbildningsområde").size()
    summary = (
        pd.DataFrame({"Total": total, "Approved": approved})
        .fillna(0)
        .astype(int)
        .sort_values("Total")
    )

    categories = summary.index.tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=categories,
        x=summary["Total"],
        name="Totalt",
        orientation="h",
        marker_color=gray_total,
    ))
    fig.add_trace(go.Bar(
        y=categories,
        x=summary["Approved"],
        name="Beviljad",
        orientation="h",
        marker_color=blue_approved,
    ))

    fig.update_layout(
        barmode="overlay",
        height=500,
        margin=dict(l=100, r=20, t=60, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=True,
        legend=dict(font=dict(size=legend_font_size, family=font_family)),
        title=dict(
            text=f"Utbildningsområden för {provider}",
            x=0.0,
            font=dict(size=title_size, family=font_family),
        ),
        font=dict(family=font_family),
    )
    fig.update_yaxes(
        showline=True, linecolor=gray_axis, tickfont=dict(size=ytick_size, color=gray_axis)
    )
    fig.update_xaxes(
        showline=True, linecolor=gray_axis, tickfont=dict(size=xtick_size, color=gray_axis)
    )
    return fig