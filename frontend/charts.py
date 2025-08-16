import plotly.express as px
import plotly.graph_objects as go

# Color constants
GRAY_1 = "#CCCCCC"
GRAY_2 = "#657072"
GRAY_3 = "#4A606C"
BLUE_1 = "#1f77b4"
BLUE_11 = "#0284c7"
GRAY_11 = "#d1d5db"
GRAY_12 = "#989898"
GRAY_13 = "#4A606C"

def education_area_chart(
    df_summary,
    county: str,
    show_arrows: bool = True,
    height: int = 500,
    title: str | None = None,
    **options
):
    """
    Horizontal bar chart for:
      - 'Ansökta utbildningar'
      - 'Beviljade utbildningar'
    per 'Utbildningsområde', with optional arrows pointing to the largest category.

    Expects df_summary columns:
      ['Utbildningsområde','Ansökta utbildningar','Beviljade utbildningar','Beviljandegrad']
    """
    fig = go.Figure()

    required = {"Utbildningsområde", "Ansökta utbildningar", "Beviljade utbildningar"}
    if df_summary is None or len(df_summary) == 0 or not required.issubset(df_summary.columns):
        fig.update_layout(
            height=height,
            plot_bgcolor="white",
            paper_bgcolor="white",
            title=title or f"Ansökningar per utbildningsområde – {county}",
            **options
        )
        return fig

    # Sort by total so the last row is the largest bar
    df_plot = df_summary.sort_values("Ansökta utbildningar", ascending=True).copy()

    categories = df_plot["Utbildningsområde"].tolist()

    # Bars
    fig.add_trace(go.Bar(
        y=categories,
        x=df_plot["Ansökta utbildningar"],
        name="Totalt",
        orientation="h",
        marker_color=GRAY_11
    ))
    fig.add_trace(go.Bar(
        y=categories,
        x=df_plot["Beviljade utbildningar"],
        name="Beviljad",
        orientation="h",
        marker_color=BLUE_11
    ))

    # Approval-rate labels (if present)
    max_total = float(df_plot["Ansökta utbildningar"].max()) if len(df_plot) else 0.0
    annotations = []
    if "Beviljandegrad" in df_plot.columns:
        for _, row in df_plot.iterrows():
            annotations.append(dict(
                x=float(row["Ansökta utbildningar"]) + 0.01 * max_total,
                y=row["Utbildningsområde"],
                text=f"{float(row['Beviljandegrad']):.1f}%",
                showarrow=False,
                font=dict(color=GRAY_12, size=12),
                xanchor="left",
                yanchor="middle"
            ))

    # Arrow annotations toward the largest bar
    if show_arrows and len(categories) > 0:
        top_cat = categories[-1]
        val_approved = float(df_plot["Beviljade utbildningar"].iloc[-1])
        val_total = float(df_plot["Ansökta utbildningar"].iloc[-1])

        plot_height = max(1, height - 120)  # margins (t=80, b=40)
        bar_height = plot_height / max(1, len(categories))
        standoff = bar_height / 2

        annotations += [
            dict(
                xref="x", yref="y",
                x=val_approved, y=top_cat,
                text="antal beviljade",
                showarrow=True, arrowhead=5,
                ax=-20, ay=-2.0 * standoff,
                font=dict(color=BLUE_11, size=13),
                arrowcolor=BLUE_11, arrowwidth=2,
                xanchor="auto", yanchor="top",
                standoff=standoff
            ),
            dict(
                xref="x", yref="y",
                x=val_total, y=top_cat,
                text="totalt antal",
                showarrow=True, arrowhead=5,
                ax=0, ay=-2.0 * standoff,
                font=dict(color=GRAY_12, size=13),
                arrowcolor=GRAY_12, arrowwidth=2,
                xanchor="auto", yanchor="top",
                standoff=standoff
            ),
        ]

    fig.update_layout(
        barmode="overlay",
        margin=dict(l=100, r=30, t=80, b=40),
        height=height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        title=title or f"Ansökningar per utbildningsområde – {county}",
        yaxis=dict(
            showline=True, linecolor=GRAY_12,
            tickfont=dict(color=GRAY_12, size=13, family="Arial")
        ),
        xaxis=dict(
            showline=True, linecolor=GRAY_12,
            tickfont=dict(color=GRAY_12, size=13, family="Arial")
        ),
        annotations=annotations,
        **options
    )
    return fig