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

def create_county_bar(df_summary, 
                     county: str,
                     show_arrows: bool = True,
                     height: int = 500,
                     **options):
    """
    Creates a horizontal bar chart showing total and approved applications per education area.
    
    Parameters:
        df_summary: DataFrame with columns [Utbildningsområde, Ansökta utbildningar, 
                   Beviljade utbildningar, Beviljandegrad]
        county: Name of county for title
        show_arrows: Whether to show annotation arrows (default: True)
        height: Height of the plot in pixels (default: 500)
        **options: Additional options for customization
        
    Returns:
        Plotly Figure object
    """
    # Create figure
    fig = go.Figure()
    
    # Get categories (education areas)
    categories = df_summary["Utbildningsområde"].tolist()
    
    # Add total applications bars
    fig.add_trace(go.Bar(
        y=categories,
        x=df_summary["Ansökta utbildningar"],
        name="Totalt",
        orientation="h",
        marker_color=GRAY_11
    ))
    
    # Add approved applications bars
    fig.add_trace(go.Bar(
        y=categories,
        x=df_summary["Beviljade utbildningar"],
        name="Beviljad",
        orientation="h",
        marker_color=BLUE_11
    ))
    
    # Prepare approval rate annotations
    approval_annotations = []
    for i, row in df_summary.iterrows():
        approval_annotations.append(dict(
            x=row["Ansökta utbildningar"] + max(df_summary["Ansökta utbildningar"]) * 0.01,
            y=row["Utbildningsområde"],
            text=f"{row['Beviljandegrad']}%",
            showarrow=False,
            font=dict(color=GRAY_12, size=12),
            xanchor="left",
            yanchor="middle"
        ))
    
    # Add arrow annotations if requested
    all_annotations = approval_annotations
    if show_arrows:
        # Get values for the top category
        first_category = categories[-1]
        first_value_approved = df_summary["Beviljade utbildningar"].iloc[-1]
        first_value_total = df_summary["Ansökta utbildningar"].iloc[-1]

        # Calculate dynamic standoff based on plot height and number of categories
        plot_height = height - 120  # Subtract margins (t=80, b=40)
        bar_height = plot_height / len(categories)
        dynamic_standoff = bar_height / 2
        
        arrow_annotations = [
            dict(
                xref="x", yref="y",
                x=first_value_approved,
                y=first_category,
                text="antal beviljade",
                showarrow=True,
                arrowhead=5,
                ax=-20, ay=-2.0*dynamic_standoff,
                font=dict(color=BLUE_11, size=13),
                arrowcolor=BLUE_11,
                arrowwidth=2,
                xanchor="auto",
                yanchor="top",
                standoff=dynamic_standoff
            ),
            dict(
                xref="x", yref="y",
                x=first_value_total,
                y=first_category,
                text="totalt antal",
                showarrow=True,
                arrowhead=5,
                ax=0, ay=-2.0*dynamic_standoff,
                font=dict(color=GRAY_12, size=13),
                arrowcolor=GRAY_12,
                arrowwidth=2,
                xanchor="auto",
                yanchor="top",
                standoff=dynamic_standoff
            )
        ]
        all_annotations.extend(arrow_annotations)
    
    # Layout customization
    fig.update_layout(
        barmode="overlay",
        margin=dict(l=100, r=30, t=80, b=40),
        height=height,
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        yaxis=dict(
            showline=True,
            linecolor=GRAY_12,
            tickfont=dict(
                color=GRAY_12,
                size=13,
                family="Arial"
            )
        ),
        xaxis=dict(
            showline=True,
            linecolor=GRAY_12,
            tickfont=dict(
                color=GRAY_12,
                size=13,
                family="Arial"
            )
        ),
        annotations=all_annotations,
        **options  # Allow additional layout customization
    )
    
    return fig