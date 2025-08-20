from __future__ import annotations
import plotly.graph_objects as go
from utils.constants import BLUE_1, GRAY_1, GRAY_12, GRAY_2, ORANGE_1
from utils.chart_style import CHART_STYLE
import pandas as pd

def get_chart_params(params=None):
    """
    Returns standardized chart parameters with defaults.
    
    Parameters:
        params: Optional dictionary of parameters to override defaults
        
    Returns:
        dict: Chart parameters with defaults
    """
    defaults = {
        "show_title": CHART_STYLE["show_title"],
        "title": None,  # Changed from custom_title to title
        "height": CHART_STYLE["height"],
        "xtick_size": CHART_STYLE["xtick_size"],
        "ytick_size": CHART_STYLE["ytick_size"],
        "title_size": CHART_STYLE["title_size"],
        "legend_font_size": CHART_STYLE["legend_font_size"],
        "label_font_size": CHART_STYLE["label_font_size"],
        "font_family": CHART_STYLE["font_family"],
    }
    
    if params:
        defaults.update(params)
        
    return defaults

def education_area_chart(
    df_summary,
    county: str,
    height: int = CHART_STYLE["height"],  # Use from CHART_STYLE
    title: str | None = None,  # Changed from custom_title to title
    show_title: bool = CHART_STYLE["show_title"],
    # font controls
    xtick_size: int = CHART_STYLE["xtick_size"],
    ytick_size: int = CHART_STYLE["ytick_size"],
    title_size: int = CHART_STYLE["title_size"],
    legend_font_size: int = CHART_STYLE["legend_font_size"],
    label_font_size: int = CHART_STYLE["label_font_size"],
    font_family: str = CHART_STYLE["font_family"],
    **options
):
    """
    Horizontal stacked bar chart per 'Utbildningsområde':
      - Beviljade (closest to the y-axis) + Avslag (stacked to the right) = Ansökta utbildningar.
      - 'Beviljandegrad' shown as a label next to the total length.
      
    Parameters:
        df_summary: DataFrame with Utbildningsområde, Ansökta utbildningar, and Beviljade utbildningar
        county: County name to show in the title
        height: Chart height in pixels (default: 450)
        title: Optional title text (overrides default if provided)
        show_title: Whether to display the title (default: False)
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
    height: int = CHART_STYLE["height"],
    show_title: bool = CHART_STYLE["show_title"],
    title: str | None = None,  
    xtick_size: int = CHART_STYLE["xtick_size"],
    ytick_size: int = CHART_STYLE["ytick_size"],
    title_size: int = CHART_STYLE["title_size"],
    legend_font_size: int = CHART_STYLE["legend_font_size"],
    label_font_size: int = CHART_STYLE["label_font_size"],
    font_family: str = CHART_STYLE["font_family"],
):
    """
    Horizontal stacked bar chart per educational area for a specific provider.
    Shows approved (blue) and rejected (gray) applications.
    
    Parameters:
        df: DataFrame with the data
        provider: Provider name to filter on
        height: Chart height in pixels (default: 450)
        show_title: Whether to display a title (default: False)
        title: Optional title text (overrides default if provided)
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
                text=title or f"Ansökningar per utbildningsområde – {provider}",
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
            text=title or f"Ansökningar per utbildningsområde – {provider}",
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
    height: int = CHART_STYLE["height"],
    nbinsx: int = 20,
    xtick_size: int = CHART_STYLE["xtick_size"],
    ytick_size: int = CHART_STYLE["ytick_size"],
    title_size: int = CHART_STYLE["title_size"],
    legend_font_size: int = CHART_STYLE["legend_font_size"],
    label_font_size: int = CHART_STYLE["label_font_size"],
    font_family: str = CHART_STYLE["font_family"],
    show_title: bool = CHART_STYLE["show_title"],
    title: str | None = None,  # Changed from custom_title
) -> go.Figure:
    """
    Stacked histogram of YH credits for approved (blue) and rejected (gray).
    If county is None => national (Sverige), else filters to the specified county.
    
    Parameters:
        df: DataFrame with the data
        county: County to filter on, None for national data (Sverige)
        height: Chart height in pixels (default: 450)
        nbinsx: Number of bins for histogram
        xtick_size, ytick_size: Font sizes for axis ticks
        title_size: Font size for chart title
        legend_font_size: Font size for legend
        label_font_size: Font size for labels
        font_family: Font family for all text
        show_title: Whether to display a title (default: False)
        title: Optional title text (overrides default if provided)
    """
    # Define common base layout used in all cases
    base_layout = {
        "barmode": "stack",
        "bargap": 0.25,
        "height": height,
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
        # Add annotations for axis titles
        "annotations": [
            # X-axis title annotation
            dict(
                text="<b>YH-POÄNG</b>",
                font=dict(
                    size=label_font_size+2, 
                    color=GRAY_12,
                    family=font_family
                ),
                xref="paper", yref="paper",
                x=0.0,  # Left edge of plot
                y=-0.05,  # Below the x-axis (increased distance)
                showarrow=False,
                xanchor="left",  # Left-aligned
                yanchor="top",   # Top-aligned
            ),
            # Y-axis title annotation
            dict(
                text="<b>ANTAL KURSER</b>",
                font=dict(
                    size=label_font_size+2,
                    color=GRAY_12,
                    family=font_family
                ),
                xref="paper", yref="paper",
                x=-0.06,  # Left of y-axis
                y=1.0,    # Top of plot
                showarrow=False,
                xanchor="right",  # Right-aligned
                yanchor="top",    # Top-aligned
                textangle=270,    # Vertical text (rotated 270 degrees)
            ),
        ],
        "font": dict(family=font_family),
    }
    
    # Create figure
    fig = go.Figure()
    
    # Handle empty or invalid dataframe
    if df is None or df.empty:
        # Handle title for empty data
        if show_title:
            base_layout["title"] = dict(
                text=title or "Fördelning av YH-poäng",
                font=dict(size=title_size, family=font_family),
            )
        fig.update_layout(**base_layout)
        return fig

    # Apply county filter if specified
    scope_label = "Sverige" if county in (None, "", "None") else str(county).strip()
    if county not in (None, "", "None"):
        d = df.copy()
        d["Län"] = d["Län"].astype(str).str.strip()
        d = d[d["Län"] == scope_label]
    else:
        d = df.copy()

    # Handle empty filtered dataframe
    if d.empty:
        # Handle title for empty filtered data
        if show_title:
            base_layout["title"] = dict(
                text=title or f"Fördelning av YH-poäng i {scope_label}",
                font=dict(size=title_size, family=font_family),
            )
        fig.update_layout(**base_layout)
        return fig

    # Check for credits column
    credits_col = "YH-poäng" if "YH-poäng" in d.columns else ("Poäng" if "Poäng" in d.columns else None)
    
    # Handle missing credits column
    if credits_col is None:
        base_layout["showlegend"] = False
        if show_title:
            base_layout["title"] = dict(
                text=title or f"Fördelning av YH-poäng i {scope_label} (saknar kolumn för poäng)",
                font=dict(size=title_size, family=font_family),
            )
        fig.update_layout(**base_layout)
        return fig

    # Extract data for approved and rejected
    approved = d[d["Beslut"] == "Beviljad"][credits_col].dropna()
    rejected = d[d["Beslut"] == "Avslag"][credits_col].dropna()

    # Calculate statistics for title
    total_courses = len(d)
    approved_count = int(approved.shape[0])
    approval_rate = (approved_count / total_courses * 100.0) if total_courses > 0 else 0.0

    # Add histogram traces
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
    
    # Add chart title if requested
    if show_title:
        title_text = title
        if title_text is None:
            title_text = f"Fördelning av YH-poäng i {scope_label}"
            title_text += f"<br><sup>Beviljandegrad: {approval_rate:.1f}% ({approved_count} av {total_courses} kurser)</sup>"
            
        base_layout["title"] = dict(
            text=title_text,
            font=dict(size=title_size, family=font_family),
        )
    
    fig.update_layout(**base_layout)
    return fig

# --------- VISUALIZATION FUNCTIONS STUDENTS ---------

def create_education_gender_chart(
    pivot_df: pd.DataFrame, 
    year: str,
    *,
    height: int = CHART_STYLE["height"],
    show_title: bool = CHART_STYLE["show_title"],
    title: str | None = None,  # Changed from custom_title
    xtick_size: int = CHART_STYLE["xtick_size"],
    ytick_size: int = CHART_STYLE["ytick_size"],
    title_size: int = CHART_STYLE["title_size"],
    legend_font_size: int = CHART_STYLE["legend_font_size"],
    label_font_size: int = CHART_STYLE["label_font_size"],
    font_family: str = CHART_STYLE["font_family"],
) -> go.Figure:
    """
    Creates a horizontal stacked bar chart for gender distribution by education area.
    
    Parameters:
        pivot_df: Pivot table with utbildningsområde and gender data
        year: Year being displayed
        height: Chart height in pixels (default: 450)
        show_title: Whether to display a title (default: False)
        title: Optional title text (overrides default if provided)
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
        "height": height if pivot_df.empty else height+50,
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
                font=dict(
                    size=label_font_size, 
                    color=GRAY_12,
                    family=font_family
                    ),
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
                font=dict(
                    size=label_font_size,
                    color=GRAY_12,
                    family=font_family
                    ),
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
            marker_color=ORANGE_1,  # Orange
            hovertemplate="Utbildningsområde: %{y}<br>Kvinnor: %{x}<extra></extra>",
            legendrank=1,
        ))
        
        fig.add_trace(go.Bar(
            x=pivot_df["Män"],
            y=pivot_df["utbildningsområde"],
            name="Män",
            orientation="h",
            marker_color=BLUE_1,  # Blue
            hovertemplate="Utbildningsområde: %{y}<br>Män: %{x}<extra></extra>",
            legendrank=2,
        ))
        
        # Add total markers
        fig.add_trace(go.Scatter(
            x=pivot_df["Totalt"],
            y=pivot_df["utbildningsområde"],
            mode="markers",
            name="Totalt",
            marker=dict(color=GRAY_12, size=10, symbol="circle"),
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
            title_text = title
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
    

def create_yearly_gender_chart(
    df: pd.DataFrame, 
    *,
    height: int = CHART_STYLE["height"],
    show_title: bool = CHART_STYLE["show_title"],
    title: str | None = None,  # Changed from custom_title
    xtick_size: int = CHART_STYLE["xtick_size"],
    ytick_size: int = CHART_STYLE["ytick_size"],
    title_size: int = CHART_STYLE["title_size"],
    legend_font_size: int = CHART_STYLE["legend_font_size"],
    label_font_size: int = CHART_STYLE["label_font_size"],
    font_family: str = CHART_STYLE["font_family"],
) -> go.Figure:
    """
    Creates a vertical stacked bar chart showing gender distribution across years.
    
    Parameters:
        df: DataFrame with yearly gender data
        height: Chart height in pixels (default: 450)
        show_title: Whether to display a title (default: False)
        title: Optional title text (overrides default if provided)
        xtick_size: Font size for x-axis ticks
        ytick_size: Font size for y-axis ticks
        title_size: Font size for chart title
        legend_font_size: Font size for legend
        label_font_size: Font size for labels
        font_family: Font family for all text
        
    Returns:
        Plotly figure object
    """
    # Define the base layout configuration
    base_layout = {
        "height": height,
        "margin": dict(l=80, r=30, t=80 if show_title else 20, b=60),
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "showlegend": True,
        "barmode": "stack",  # Ensure bars are stacked
        "bargap": 0.3,       # Spacing between bars
        "xaxis": dict(
            showline=True, 
            linecolor=GRAY_12,
            tickfont=dict(size=xtick_size, color=GRAY_12, family=font_family),
            zeroline=False,
            automargin=True,
            showgrid=False,
            type="category",  # Treat x-axis as categorical
        ),
        "yaxis": dict(
            showline=True, 
            linecolor=GRAY_12,
            tickfont=dict(size=ytick_size, color=GRAY_12, family=font_family),
            zeroline=True,            
            zerolinecolor=GRAY_12,    
            zerolinewidth=1,          
            automargin=True,
            showgrid=False,
            rangemode="tozero",
        ),
        # Add custom annotations for axis titles
        "annotations": [
            # X-axis title annotation - NONE
            # Y-axis title annotation
            dict(
                text="<b>ANTAL STUDENTER</b>",
                font=dict(
                    size=label_font_size, 
                    color=GRAY_12,
                    family=font_family,
                ),
                xref="paper", yref="paper",
                x=-0.08,  # Left of y-axis
                y=1.0,    # Middle of plot
                showarrow=False,
                xanchor="right",
                yanchor="top",
                textangle=270,  # Vertical text
            ),
        ],
        "font": dict(family=font_family),
        "legend": dict(
            orientation="h",
            yanchor="bottom", 
            y=1.02,
            xanchor="center", 
            x=0.5,
            font=dict(size=legend_font_size, family=font_family),
            traceorder="normal",
        ),
    }
    
    # Create figure
    fig = go.Figure()
    
    # Handle empty dataframe case
    if df.empty:
        if show_title:
            base_layout["title"] = dict(
                text="Ingen data tillgänglig",
                font=dict(size=title_size, family=font_family),
            )
        
        fig.update_layout(**base_layout)
        return fig
    
    try:
        # Transform data to have years as columns if needed
        if "år" in df.columns and "kön" in df.columns and "antal" in df.columns:
            # Data is in long format, need to pivot
            pivot_df = df.pivot_table(
                index="år",
                columns="kön",
                values="antal",
                aggfunc="sum"
            ).fillna(0).reset_index()
            
            # Rename columns for consistency
            pivot_df.columns.name = None
            pivot_df.rename(columns={
                "kvinnor": "Kvinnor",
                "män": "Män",
                "totalt": "Totalt"
            }, inplace=True)
            
            # Ensure columns are present
            for col in ["Kvinnor", "Män", "Totalt"]:
                if col not in pivot_df.columns:
                    pivot_df[col] = 0
                    
            # Sort by year
            pivot_df = pivot_df.sort_values("år")
            
            years = pivot_df["år"].tolist()
            women_values = pivot_df["Kvinnor"].tolist()
            men_values = pivot_df["Män"].tolist()
            total_values = pivot_df["Totalt"].tolist()
        else:
            # Assume data is already in correct format
            # Expecting columns: Year (or similar), Kvinnor, Män, Totalt
            # First column is assumed to be years
            years = df.iloc[:, 0].tolist()
            women_values = df["Kvinnor"].tolist() if "Kvinnor" in df.columns else [0] * len(years)
            men_values = df["Män"].tolist() if "Män" in df.columns else [0] * len(years)
            total_values = df["Totalt"].tolist() if "Totalt" in df.columns else [0] * len(years)
        
        # Add stacked bars
        fig.add_trace(go.Bar(
            x=years,
            y=women_values,
            name="Kvinnor",
            marker_color=ORANGE_1,  # Use ORANGE_1 instead of hardcoded value
            hovertemplate="År: %{x}<br>Kvinnor: %{y}<extra></extra>",
            legendrank=1,
        ))
        
        fig.add_trace(go.Bar(
            x=years,
            y=men_values,
            name="Män",
            marker_color=BLUE_1,  # Use BLUE_1 instead of BLUE_2
            hovertemplate="År: %{x}<br>Män: %{y}<extra></extra>",
            legendrank=2,
        ))
        
        # Add total markers
        fig.add_trace(go.Scatter(
            x=years,
            y=total_values,
            mode="markers",
            name="Totalt",
            marker=dict(color=GRAY_12, size=10, symbol="circle"),  # Use GRAY_12 instead of GRAY_DARK
            hovertemplate="År: %{x}<br>Totalt: %{y}<extra></extra>",
            showlegend=True,
            legendrank=3,
        ))
        
        # Only add title if requested
        if show_title:
            title_text = title
            if title_text is None:
                title_text = "Antal antagna studenter per år"
                
            base_layout["title"] = dict(
                text=title_text,
                font=dict(size=title_size, family=font_family),
            )
        
        fig.update_layout(**base_layout)
        return fig
        
    except Exception as e:
        import logging
        logging.error(f"Error creating yearly gender chart: {str(e)}")
        
        # Use base layout for error case
        if show_title:
            base_layout["title"] = dict(
                text=f"Fel vid skapande av diagram: {str(e)}",
                font=dict(size=title_size, family=font_family),
            )
            
        fig.update_layout(**base_layout)
        return fig
    
def create_age_gender_chart(
    df: pd.DataFrame,
    year: str,
    education_area: str = "Alla områden",
    *,
    height: int = CHART_STYLE["height"],
    show_title: bool = CHART_STYLE["show_title"],
    title: str | None = None,  # Changed from custom_title
    xtick_size: int = CHART_STYLE["xtick_size"],
    ytick_size: int = CHART_STYLE["ytick_size"],
    title_size: int = CHART_STYLE["title_size"],
    legend_font_size: int = CHART_STYLE["legend_font_size"],
    label_font_size: int = CHART_STYLE["label_font_size"],
    font_family: str = CHART_STYLE["font_family"],
) -> go.Figure:
    """
    Creates a grouped bar chart showing gender distribution across age groups.
    
    Parameters:
        df: DataFrame with age and gender data
        year: Year being displayed
        education_area: Selected education area to filter for
        height: Chart height in pixels (default: 450)
        show_title: Whether to display a title (default: False)
        title: Optional title text (overrides default if provided)
        xtick_size: Font size for x-axis ticks
        ytick_size: Font size for y-axis ticks
        title_size: Font size for chart title
        legend_font_size: Font size for legend
        label_font_size: Font size for labels
        font_family: Font family for all text
        
    Returns:
        Plotly figure object
    """
    # Define the base layout configuration
    base_layout = {
        "height": height,
        "margin": dict(l=80, r=30, t=80 if show_title else 20, b=60),
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "showlegend": True,
        "barmode": "group",  # Grouped bars instead of stacked
        "bargap": 0.3,       # Spacing between bar groups
        "bargroupgap": 0.1,  # Gap between bars in a group
        "xaxis": dict(
            showline=True, 
            linecolor=GRAY_12,
            tickfont=dict(size=xtick_size, color=GRAY_12, family=font_family),
            zeroline=False,
            automargin=True,
            showgrid=False,
            type="category",  # Treat x-axis as categorical
        ),
        "yaxis": dict(
            showline=True, 
            linecolor=GRAY_12,
            tickfont=dict(size=ytick_size, color=GRAY_12, family=font_family),
            zeroline=True,            
            zerolinecolor=GRAY_12,    
            zerolinewidth=1,          
            automargin=True,
            showgrid=False,
            rangemode="tozero",
        ),
        # Add custom annotations for axis titles
        "annotations": [
            # X-axis title annotation
            dict(
                text="<b>ÅLDERSGRUPP</b>",
                font=dict(
                    size=label_font_size, 
                    color=GRAY_12,
                    family=font_family
                    ),
                xref="paper", yref="paper",
                x=0.0,  # Center of plot
                y=-0.1,  # Below the x-axis
                showarrow=False,
                xanchor="left",  
                yanchor="top",
            ),
            # Y-axis title annotation
            dict(
                text="<b>ANTAL STUDENTER</b>",
                font=dict(
                    size=label_font_size,
                    color=GRAY_12, 
                    family=font_family
                    ),
                xref="paper", yref="paper",
                x=-0.06,  # Left of y-axis
                y=1.0,    # Middle of plot
                showarrow=False,
                xanchor="right",
                yanchor="top",
                textangle=270,  # Vertical text
            ),
        ],
        "font": dict(family=font_family),
        "legend": dict(
            orientation="h",
            yanchor="bottom", 
            y=1.02,
            xanchor="center", 
            x=0.5,
            font=dict(size=legend_font_size, family=font_family),
            traceorder="normal",
        ),
    }
    
    # Create figure
    fig = go.Figure()
    
    # Handle empty dataframe case
    if df.empty:
        if show_title:
            base_layout["title"] = dict(
                text="Ingen data tillgänglig",
                font=dict(size=title_size, family=font_family),
            )
        
        fig.update_layout(**base_layout)
        return fig
    
    try:
        # Filter data for the selected education area
        if education_area != "Alla områden":
            df_filtered = df[df["utbildningsområde"] == education_area]
        else:
            df_filtered = df.copy()
            
        # Ensure we have data after filtering
        if df_filtered.empty:
            if show_title:
                base_layout["title"] = dict(
                    text=f"Ingen data tillgänglig för {education_area}",
                    font=dict(size=title_size, family=font_family),
                )
            
            fig.update_layout(**base_layout)
            return fig
            
        # Extract unique age groups from the data
        age_groups = df_filtered["ålder"].unique().tolist()
        
        # Custom sorting function for age groups
        def age_group_sort_key(age):
            if age.lower() == "totalt":
                return 999  # Place "Totalt" at the end
            elif age == "-24 år":
                return 0    # Place youngest group first
            elif age == "45+ år":
                return 45   # Place middle aged group in correct position
            elif "+" in age:
                # Handle other plus ranges
                return int(age.split("+")[0])
            elif "-" in age:
                # Handle ranges like "25-29 år"
                return int(age.split("-")[0])
            else:
                # Default case
                return 999
        
        # Sort age groups logically
        age_groups.sort(key=age_group_sort_key)
        
        # Remove "Totalt" from visualization if present
        age_groups = [age for age in age_groups if age.lower() != "totalt"]


        # Pivot to have one row per ålder, columns for kvinnor and män
        pivot_age = df_filtered.pivot_table(
            index="ålder",
            columns="kön",
            values="antal",
            aggfunc="sum"
        ).fillna(0)
        
        # Reindex with our sorted age groups, excluding any not in the pivot index
        available_ages = [age for age in age_groups if age in pivot_age.index]
        pivot_age = pivot_age.reindex(available_ages)

        # You should also drop "Totalt" from the pivot_age index if it exists
        if "Totalt" in pivot_age.index:
            pivot_age = pivot_age.drop("Totalt")
        
        # Normalize column names
        if "kvinnor" in pivot_age.columns:
            pivot_age.rename(columns={"kvinnor": "Kvinnor"}, inplace=True)
        if "män" in pivot_age.columns:
            pivot_age.rename(columns={"män": "Män"}, inplace=True)
            
        # Add women bars
        if "Kvinnor" in pivot_age.columns:
            fig.add_trace(go.Bar(
                x=pivot_age.index,
                y=pivot_age["Kvinnor"],
                name="Kvinnor",
                marker_color=ORANGE_1,
                hovertemplate="Åldersgrupp: %{x}<br>Kvinnor: %{y}<extra></extra>",
                legendrank=1,
            ))
        
        # Add men bars
        if "Män" in pivot_age.columns:
            fig.add_trace(go.Bar(
                x=pivot_age.index,
                y=pivot_age["Män"],
                name="Män",
                marker_color=BLUE_1,
                hovertemplate="Åldersgrupp: %{x}<br>Män: %{y}<extra></extra>",
                legendrank=2,
            ))
        
        # Only add title if requested
        if show_title:
            title_text = title
            if title_text is None:
                area_text = f" - {education_area}" if education_area != "Alla områden" else ""
                title_text = f"Åldersfördelning bland studenter ({year}){area_text}"
                
            base_layout["title"] = dict(
                text=title_text,
                font=dict(size=title_size, family=font_family),
            )
        
        fig.update_layout(**base_layout)
        return fig
        
    except Exception as e:
        import logging
        logging.error(f"Error creating age gender chart: {str(e)}")
        
        # Use base layout for error case
        if show_title:
            base_layout["title"] = dict(
                text=f"Fel vid skapande av diagram: {str(e)}",
                font=dict(size=title_size, family=font_family),
            )
            
        fig.update_layout(**base_layout)
        return fig