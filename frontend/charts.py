from __future__ import annotations
import plotly.graph_objects as go
from utils.constants import BLUE_1, GRAY_1, GRAY_12
import pandas as pd

def education_area_chart(
    df_summary,
    county: str,
    height: int = 500,
    title: str | None = None,
    show_title: bool = True,  # Added parameter
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
      
    Parameters:
        df_summary: DataFrame with Utbildningsområde, Ansökta utbildningar, and Beviljade utbildningar
        county: County name to show in the title
        height: Chart height in pixels
        title: Custom title (overrides default if provided)
        show_title: Whether to display the title (default: True)
        xtick_size: Font size for x-axis ticks
        ytick_size: Font size for y-axis ticks
        title_size: Font size for title
        legend_font_size: Font size for legend
        label_font_size: Font size for approval rate labels
        font_family: Font family for all text
    """
    fig = go.Figure()

    required = {"Utbildningsområde", "Ansökta utbildningar", "Beviljade utbildningar"}
    if df_summary is None or len(df_summary) == 0 or not required.issubset(df_summary.columns):
        layout_args = {
            "height": height,
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "margin": dict(l=120, r=30, t=80 if show_title else 20, b=40),
            "xaxis": dict(
                tickfont=dict(size=xtick_size, family=font_family, color=GRAY_12)
            ),
            "yaxis": dict(
                tickfont=dict(size=ytick_size, family=font_family, color=GRAY_12)
            ),
            "legend": dict(font=dict(size=legend_font_size, family=font_family)),
            **options
        }
        
        # Only add title if show_title is True
        if show_title:
            layout_args["title"] = dict(
                text=title or f"Ansökningar per utbildningsområde – {county}",
                font=dict(size=title_size, family=font_family)
            )
            
        fig.update_layout(**layout_args)
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

    # Create layout arguments dictionary
    layout_args = {
        "barmode": "stack",
        "bargap": 0.25,
        "margin": dict(l=120, r=30, t=80 if show_title else 20, b=40),
        "height": height,
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "showlegend": True,
        "legend": dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=legend_font_size, family=font_family),
            traceorder="normal"  # legendrank controls order
        ),
        "yaxis": dict(
            showline=True, linecolor=GRAY_12,
            tickfont=dict(color=GRAY_12, size=ytick_size, family=font_family),
            categoryorder="array", categoryarray=categories,
            automargin=True
        ),
        "xaxis": dict(
            showline=True, linecolor=GRAY_12,
            tickfont=dict(color=GRAY_12, size=xtick_size, family=font_family),
            rangemode="tozero",
            automargin=True
        ),
        "annotations": annotations,
        **options
    }
    
    # Only add title if show_title is True
    if show_title:
        layout_args["title"] = dict(
            text=title or f"Ansökningar per utbildningsområde – {county}",
            font=dict(size=title_size, family=font_family)
        )
    
    fig.update_layout(**layout_args)
    return fig

def provider_education_area_chart(
    df: pd.DataFrame,
    provider: str,
    *,
    show_title: bool = True,
    custom_title: str | None = None,  # Added this parameter
    xtick_size: int = 11,
    ytick_size: int = 12,
    title_size: int = 18,
    legend_font_size: int = 12,
    label_font_size: int = 11,
    font_family: str = "Arial",
):
    """
    Horizontal stacked bar chart per educational area for a specific provider.
    Shows approved (blue) and rejected (gray) applications.
    
    Parameters:
        df: DataFrame with the data
        provider: Provider name to filter on
        show_title: Whether to display a title (default: True)
        custom_title: Optional custom title text (overrides default if provided)
        xtick_size: Font size for x-axis ticks
        ytick_size: Font size for y-axis ticks
        title_size: Font size for chart title
        legend_font_size: Font size for legend
        label_font_size: Font size for labels
        font_family: Font family for all text
    """
    d = df[df["Anordnare namn"].astype(str).str.strip() == str(provider).strip()].copy()
    if d.empty:
        # Return empty figure with proper layout
        fig = go.Figure()
        layout_args = {
            "barmode": "stack",
            "bargap": 0.25,
            "height": 500,
            "margin": dict(l=120, r=30, t=80 if show_title else 20, b=40),
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "showlegend": True,
            "legend": dict(
                orientation="h",
                yanchor="bottom", y=1.02,
                xanchor="right", x=1,
                font=dict(size=legend_font_size, family=font_family),
                traceorder="normal",
            ),
            "font": dict(family=font_family),
            "xaxis": dict(
                showline=True, linecolor=GRAY_12,
                tickfont=dict(size=xtick_size, color=GRAY_12, family=font_family),
                zeroline=False,
                automargin=True,
            ),
            "yaxis": dict(
                showline=True, linecolor=GRAY_12,
                tickfont=dict(size=ytick_size, color=GRAY_12, family=font_family),
                zeroline=False,
                automargin=True,
            ),
        }
        
        # Only add title if requested
        if show_title:
            layout_args["title"] = dict(
                text=custom_title or f"Ansökningar per utbildningsområde – {provider} (inga data)",
                font=dict(size=title_size, family=font_family),
            )
            
        fig.update_layout(**layout_args)
        return fig

    total = d.groupby("Utbildningsområde").size()
    approved = d[d["Beslut"] == "Beviljad"].groupby("Utbildningsområde").size()
    summary = (
        pd.DataFrame({"Total": total, "Approved": approved})
        .fillna(0)
        .astype(int)
        .sort_values("Total", ascending=True)
    )
    summary["Rejected"] = (summary["Total"] - summary["Approved"]).clip(lower=0)

    categories = summary.index.tolist()
    fig = go.Figure()
    # Beviljade (near axis)
    fig.add_trace(go.Bar(
        y=categories,
        x=summary["Approved"],
        name="Beviljade",
        orientation="h",
        marker_color=BLUE_1,
        hovertemplate="Utbildningsområde: %{y}<br>Beviljade: %{x}<extra></extra>",
        legendrank=1,
    ))
    # Avslag (to the right)
    fig.add_trace(go.Bar(
        y=categories,
        x=summary["Rejected"],
        name="Avslag",
        orientation="h",
        marker_color=GRAY_1,
        hovertemplate="Utbildningsområde: %{y}<br>Avslag: %{x}<extra></extra>",
        legendrank=2,
    ))

    # Create layout arguments dictionary
    layout_args = {
        "barmode": "stack",
        "bargap": 0.25,
        "height": 500,
        "margin": dict(l=120, r=30, t=80 if show_title else 20, b=40),
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "showlegend": True,
        "legend": dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=legend_font_size, family=font_family),
            traceorder="normal",
        ),
        "font": dict(family=font_family),
    }
    
    # Only add title if requested
    if show_title:
        layout_args["title"] = dict(
            text=custom_title or f"Ansökningar per utbildningsområde – {provider}",
            font=dict(size=title_size, family=font_family),
        )
    
    fig.update_layout(**layout_args)
    
    fig.update_yaxes(
        showline=True,
        linecolor=GRAY_12,
        tickfont=dict(size=ytick_size, color=GRAY_12, family=font_family),
        categoryorder="array",
        categoryarray=categories,
        automargin=True,
    )
    fig.update_xaxes(
        showline=True,
        linecolor=GRAY_12,
        tickfont=dict(size=xtick_size, color=GRAY_12, family=font_family),
        rangemode="tozero",
        automargin=True,
    )
    return fig

def credits_histogram(
    df: pd.DataFrame,
    county: str | None = None,
    *,
    nbinsx: int = 20,
    xtick_size: int = 11,
    ytick_size: int = 12,
    title_size: int = 18,
    legend_font_size: int = 12,
    label_font_size: int = 11,
    font_family: str = "Arial",
    show_title: bool = True,      # Add this parameter
    custom_title: str | None = None,  # Add this parameter
) -> go.Figure:
    """
    Stacked histogram of YH credits for approved (blue) and rejected (gray).
    If county is None => national (Sverige), else filters to the specified county.
    
    Parameters:
        df: DataFrame with the data
        county: County to filter on, None for national data (Sverige)
        nbinsx: Number of bins for histogram
        xtick_size, ytick_size: Font sizes for axis ticks
        title_size: Font size for chart title
        legend_font_size: Font size for legend
        label_font_size: Font size for labels
        font_family: Font family for all text
        show_title: Whether to display a title (set to False to hide)
        custom_title: Optional custom title text (overrides default if provided)
    """
    fig = go.Figure()
    if df is None or df.empty:
        layout_args = {
            "barmode": "stack",
            "bargap": 0.25,
            "height": 500,
            "margin": dict(l=120, r=30, t=80 if show_title else 20, b=40),
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "showlegend": True,
            "legend": dict(
                orientation="h",
                yanchor="bottom", y=1.02,
                xanchor="right", x=1.0,
                font=dict(size=legend_font_size, family=font_family),
                traceorder="normal",
            ),
            "xaxis": dict(
                showline=True, linecolor=GRAY_12,
                tickfont=dict(size=xtick_size, color=GRAY_12, family=font_family),
                zeroline=False,
                automargin=True,
                showgrid=False,  # Remove horizontal grid lines
            ),
            "yaxis": dict(
                showline=True, linecolor=GRAY_12,
                tickfont=dict(size=ytick_size, color=GRAY_12, family=font_family),
                zeroline=False,
                automargin=True,
                showgrid=False,  # Remove vertical grid lines
            ),
        }
        
        # Only add title if requested
        if show_title:
            layout_args["title"] = dict(
                text=custom_title or "Fördelning av YH-poäng",
                font=dict(size=title_size, family=font_family),
            )
            
        fig.update_layout(**layout_args)
        return fig

    d = df.copy()
    scope_label = "Sverige" if county in (None, "", "None") else str(county).strip()
    if county not in (None, "", "None"):
        d["Län"] = d["Län"].astype(str).str.strip()
        d = d[d["Län"] == scope_label]

    if d.empty:
        layout_args = {
            "barmode": "stack",
            "bargap": 0.25,
            "height": 500,
            "margin": dict(l=120, r=30, t=80 if show_title else 20, b=40),
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "showlegend": True,
            "legend": dict(
                orientation="h",
                yanchor="bottom", y=1.02,
                xanchor="right", x=1.0,
                font=dict(size=legend_font_size, family=font_family),
                traceorder="normal",
            ),
            "xaxis": dict(
                showline=True, linecolor=GRAY_12,
                tickfont=dict(size=xtick_size, color=GRAY_12, family=font_family),
                zeroline=False,
                automargin=True,
                showgrid=False,  # Remove horizontal grid lines
            ),
            "yaxis": dict(
                showline=True, linecolor=GRAY_12,
                tickfont=dict(size=ytick_size, color=GRAY_12, family=font_family),
                zeroline=False,
                automargin=True,
                showgrid=False,  # Remove vertical grid lines
            ),
        }
        
        # Only add title if requested
        if show_title:
            layout_args["title"] = dict(
                text=custom_title or f"Fördelning av YH-poäng i {scope_label}",
                font=dict(size=title_size, family=font_family),
            )
            
        fig.update_layout(**layout_args)
        return fig

    credits_col = "YH-poäng" if "YH-poäng" in d.columns else ("Poäng" if "Poäng" in d.columns else None)
    if credits_col is None:
        layout_args = {
            "barmode": "stack",
            "bargap": 0.25,
            "height": 500,
            "margin": dict(l=120, r=30, t=80 if show_title else 20, b=40),
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "showlegend": False,
            "xaxis": dict(
                showline=True, linecolor=GRAY_12,
                tickfont=dict(size=xtick_size, color=GRAY_12, family=font_family),
                zeroline=False,
                automargin=True,
                showgrid=False,  # Remove horizontal grid lines
            ),
            "yaxis": dict(
                showline=True, linecolor=GRAY_12,
                tickfont=dict(size=ytick_size, color=GRAY_12, family=font_family),
                zeroline=False,
                automargin=True,
                showgrid=False,  # Remove vertical grid lines
            ),
        }
        
        # Only add title if requested
        if show_title:
            layout_args["title"] = dict(
                text=custom_title or f"Fördelning av YH-poäng i {scope_label} (saknar kolumn för poäng)",
                font=dict(size=title_size, family=font_family),
            )
            
        fig.update_layout(**layout_args)
        return fig

    approved = d[d["Beslut"] == "Beviljad"][credits_col].dropna()
    rejected = d[d["Beslut"] == "Avslag"][credits_col].dropna()

    total_courses = len(d)
    approved_count = int(approved.shape[0])
    approval_rate = (approved_count / total_courses * 100.0) if total_courses > 0 else 0.0

    fig.add_trace(go.Histogram(
        x=approved,
        name="Beviljade",
        nbinsx=nbinsx,
        marker_color=BLUE_1,
        opacity=1.0,
        hovertemplate="YH-poäng: %{x}<br>Antal: %{y}<extra></extra>",
        legendrank=1,
    ))
    fig.add_trace(go.Histogram(
        x=rejected,
        name="Avslag",
        nbinsx=nbinsx,
        marker_color=GRAY_1,
        opacity=1.0,
        hovertemplate="YH-poäng: %{x}<br>Antal: %{y}<extra></extra>",
        legendrank=2,
    ))

    # Create layout arguments dictionary
    layout_args = {
        "barmode": "stack",
        "bargap": 0.25,
        "height": 500,
        "margin": dict(l=120, r=30, t=80 if show_title else 20, b=40),
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "showlegend": True,
        "legend": dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1.0,
            font=dict(size=legend_font_size, family=font_family),
            traceorder="normal",
        ),
        "xaxis_title": "YH-poäng",
        "yaxis_title": "Antal kurser",
        "font": dict(family=font_family),
        "xaxis": dict(
            showline=True, linecolor=GRAY_12,
            tickfont=dict(size=xtick_size, color=GRAY_12, family=font_family),
            zeroline=False,
            automargin=True,
            showgrid=False,  # Remove horizontal grid lines
        ),
        "yaxis": dict(
            showline=True, linecolor=GRAY_12,
            tickfont=dict(size=ytick_size, color=GRAY_12, family=font_family),
            zeroline=False,
            showgrid=False,  # Remove vertical grid lines
            automargin=True,
        ),
    }
    
    # Only add title if requested
    if show_title:
        title_text = custom_title
        if title_text is None:
            title_text = f"Fördelning av YH-poäng i {scope_label}"
            title_text += f"<br><sup>Beviljandegrad: {approval_rate:.1f}% ({approved_count} av {total_courses} kurser)</sup>"
            
        layout_args["title"] = dict(
            text=title_text,
            font=dict(size=title_size, family=font_family),
        )
    
    fig.update_layout(**layout_args)
    return fig

# --------- VISUALIZATION FUNCTIONS ---------

def create_education_gender_chart(
    pivot_df: pd.DataFrame, 
    year: str,
    *,
    show_title: bool = True,
    custom_title: str | None = None,
    xtick_size: int = 11,
    ytick_size: int = 12,
    title_size: int = 18,
    legend_font_size: int = 12,
    label_font_size: int = 11,
    font_family: str = "Arial",
) -> go.Figure:
    """
    Creates a horizontal stacked bar chart for gender distribution by education area.
    
    Parameters:
        pivot_df: Pivot table with utbildningsområde and gender data
        year: Year being displayed
        show_title: Whether to display a title
        custom_title: Optional custom title text
        xtick_size: Font size for x-axis ticks
        ytick_size: Font size for y-axis ticks
        title_size: Font size for chart title
        legend_font_size: Font size for legend
        label_font_size: Font size for labels
        font_family: Font family for all text
        
    Returns:
        Plotly figure object
    """
    # Define the base layout configuration once
    base_layout = {
        "height": 500 if pivot_df.empty else 550,
        "margin": dict(l=120, r=30, t=80 if show_title else 20, b=40),
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "showlegend": False if pivot_df.empty else True,
        "barmode": "stack",  # Add this line to ensure bars are stacked
        "bargap": 0.25,      # Add consistent bargap for spacing
        "xaxis": dict(
            showline=True, 
            linecolor=GRAY_12,
            tickfont=dict(size=xtick_size, color=GRAY_12, family=font_family),
            zeroline=True,            # Show zero line
            zerolinecolor=GRAY_12,    # Same color as axis
            zerolinewidth=1,          # Width of zero line
            automargin=True,
            showgrid=False,           # Remove horizontal grid lines
            rangemode="tozero",       # Ensure range starts at zero
            constrain="domain",       # Constrain to exact domain
            anchor="y",               # Anchor to y-axis
            position=0,               # Position at 0
        ),
        "yaxis": dict(
            showline=True, 
            linecolor=GRAY_12,
            tickfont=dict(size=ytick_size, color=GRAY_12, family=font_family),
            zeroline=False,
            automargin=True,
            showgrid=False,
            ticklabelposition="outside left",
            ticksuffix="  ",
            # Remove y-axis title
        ),
        # Add custom annotations for axis titles
        "annotations": [
            # X-axis title annotation
            dict(
                text="<b>ANTAL STUDENTER</b>",
                font=dict(size=label_font_size+2, family=font_family),
                xref="paper", yref="paper",
                x=0.0,  # Left edge of plot
                y=-0.05,  # Below the x-axis
                showarrow=False,
                xanchor="left",  # Left-aligned
                yanchor="top",   # Top-aligned to specified position
            ),
            # Y-axis title annotation
            dict(
                text="<b>UTBILDNINGSOMRÅDE</b>",
                font=dict(size=label_font_size+2, family=font_family),
                xref="paper", yref="paper",
                x=-0.0,  # Left of y-axis
                y=1.0,    # Top of plot
                showarrow=False,
                xanchor="right",  # Right-aligned
                yanchor="bottom", # Bottom-aligned to specified position
                textangle=0,      # Horizontal text
            ),
        ],
        "font": dict(family=font_family),
    }
    
    # Create figure
    fig = go.Figure()
    
    # Handle empty dataframe case
    if pivot_df.empty:
        # Only add title if requested
        if show_title:
            base_layout["title"] = dict(
                text="Ingen data tillgänglig",
                font=dict(size=title_size, family=font_family),
            )
        
        fig.update_layout(**base_layout)
        return fig
    
    try:
        # Add stacked bars
        fig.add_trace(go.Bar(
            x=pivot_df["Kvinnor"],
            y=pivot_df["utbildningsområde"],
            name="Kvinnor",
            orientation="h",
            marker_color="#f59e0b",  # Orange
            hovertemplate="Utbildningsområde: %{y}<br>Kvinnor: %{x}<extra></extra>",
            legendrank=1,
        ))
        
        fig.add_trace(go.Bar(
            x=pivot_df["Män"],
            y=pivot_df["utbildningsområde"],
            name="Män",
            orientation="h",
            marker_color="#0284c7",  # Blue
            hovertemplate="Utbildningsområde: %{y}<br>Män: %{x}<extra></extra>",
            legendrank=2,
        ))
        
        # Add total markers
        fig.add_trace(go.Scatter(
            x=pivot_df["Totalt"],
            y=pivot_df["utbildningsområde"],
            mode="markers",
            name="Totalt",
            marker=dict(color="#4A606C", size=10, symbol="circle"),
            hovertemplate="Utbildningsområde: %{y}<br>Totalt: %{x}<extra></extra>",
            showlegend=True,
            legendrank=3,
        ))
        
        # Add additional layout configuration for non-empty data
        layout_args = base_layout.copy()
        
        # Add legend settings for non-empty case
        layout_args["legend"] = dict(
            orientation="h",
            yanchor="bottom", 
            y=1.02,
            xanchor="center", 
            x=0.5,
            font=dict(size=legend_font_size, family=font_family),
            traceorder="normal",
        )
        
        # Add categoryorder for y-axis
        if "yaxis" in layout_args:
            layout_args["yaxis"]["categoryorder"] = "array"
            layout_args["yaxis"]["categoryarray"] = pivot_df["utbildningsområde"].tolist()
        
        # Only add title if requested
        if show_title:
            title_text = custom_title
            if title_text is None:
                title_text = f"Antal antagna per utbildningsområde ({year})"
                
            layout_args["title"] = dict(
                text=title_text,
                font=dict(size=title_size, family=font_family),
            )
        
        fig.update_layout(**layout_args)
        return fig
        
    except Exception as e:
        import logging
        logging.error(f"Error creating chart: {str(e)}")
        
        # Use base layout for error case
        if show_title:
            base_layout["title"] = dict(
                text=f"Fel vid skapande av diagram: {str(e)}",
                font=dict(size=title_size, family=font_family),
            )
            
        fig.update_layout(**base_layout)
        return fig