from __future__ import annotations
from typing import Dict, Any

import pandas as pd

from backend.data_processing import get_statistics
from frontend.charts import (
    education_area_chart,
    provider_education_area_chart,
    credits_histogram,
)
from utils.chart_style import CHART_STYLE

def compute_provider_view(
    df: pd.DataFrame,
    df_providers: pd.DataFrame,
    provider: str,
    *,
    # Add all current CHART_STYLE parameters
    xtick_size: int = CHART_STYLE["xtick_size"],
    ytick_size: int = CHART_STYLE["ytick_size"],
    title_size: int = CHART_STYLE["title_size"],
    legend_font_size: int = CHART_STYLE["legend_font_size"],
    label_font_size: int = CHART_STYLE["label_font_size"],
    font_family: str = CHART_STYLE["font_family"],
    show_title: bool = CHART_STYLE["show_title"],  # Add this parameter
    height: int = CHART_STYLE["height"],           # Add this parameter
    **kwargs            
) -> Dict[str, Any]:
    row = pd.DataFrame()
    provider_norm = str(provider).strip()
    if provider_norm:
        row = df_providers[df_providers["Anordnare namn"].astype(str).str.strip() == provider_norm]

    total_providers = len(df_providers)
    if row.empty:
        return dict(
            provider_rank_places=0,
            provider_rank_places_summary_str=f"0 av {total_providers:,}",
            provider_places_summary_str="0 av 0",
            provider_places_approval_rate_str="0.0%",
            provider_courses_summary_str="0 av 0",
            provider_courses_approval_rate_str="0.0%",
            provider_chart=provider_education_area_chart(
                df,
                provider_norm,
                xtick_size=xtick_size,
                ytick_size=ytick_size,
                title_size=title_size,
                legend_font_size=legend_font_size,
                label_font_size=label_font_size,
                font_family=font_family,
                show_title=show_title,      
                height=height, 
            ),
            # Add provider histogram
            provider_histogram=credits_histogram(
                df,
                None,  # No county filter
                nbinsx=20,
                xtick_size=xtick_size,
                ytick_size=ytick_size,
                title_size=title_size,
                legend_font_size=legend_font_size,
                label_font_size=label_font_size,  
                font_family=font_family,
                show_title=show_title,            
                height=height,
            ),
        )

    # Filter df to only show this provider
    provider_df = df[df["Anordnare namn"].astype(str).str.strip() == provider_norm]

    r = row.iloc[0]
    places_appr = int(r.get("Beviljade platser", 0))
    places_applied = int(r.get("Sökta platser", 0))
    places_rate = float(r.get("Beviljandegrad (platser) %", 0.0))
    courses_appr = int(r.get("Beviljade kurser", 0))
    courses_total = int(r.get("Sökta kurser", 0))
    courses_rate = float(r.get("Beviljandegrad (kurser) %", 0.0))
    rank_places = int(r.get("Ranking beviljade platser", 0))
    rank_courses = int(r.get("Ranking beviljade kurser", 0))

    return dict(
        provider_rank_places=rank_places,
        provider_rank_places_summary_str=f"{rank_places} av {total_providers:,}",
        provider_rank_courses=rank_courses,                     
        provider_rank_courses_summary_str=f"{rank_courses} av {total_providers:,}", 
        provider_places_summary_str=f"{places_appr:,} av {places_applied:,}",
        provider_places_approval_rate_str=f"{places_rate:.1f}%",
        provider_courses_summary_str=f"{courses_appr:,} av {courses_total:,}",
        provider_courses_approval_rate_str=f"{courses_rate:.1f}%",
        provider_chart=provider_education_area_chart(
            df,
            provider_norm,
            xtick_size=xtick_size,
            ytick_size=ytick_size,
            title_size=title_size,
            legend_font_size=legend_font_size,
            label_font_size=label_font_size,
            font_family=font_family,
            show_title=show_title,      
            height=height,
        ),
        # Add provider histogram with filtered dataframe
        provider_histogram=credits_histogram(
            provider_df,  # Use filtered dataframe for this provider only
            None,  # No county filter
            nbinsx=20,
            xtick_size=xtick_size,
            ytick_size=ytick_size,
            title_size=title_size,
            legend_font_size=legend_font_size,
            label_font_size=label_font_size,  
            font_family=font_family,
            show_title=show_title,            
            height=height, 
        ),
    )

def compute_county_view(
    df: pd.DataFrame,
    county: str,
    *,
    # Use CHART_STYLE for all parameters
    xtick_size: int = CHART_STYLE["xtick_size"],
    ytick_size: int = CHART_STYLE["ytick_size"],
    title_size: int = CHART_STYLE["title_size"],
    legend_font_size: int = CHART_STYLE["legend_font_size"],
    label_font_size: int = CHART_STYLE["label_font_size"],
    font_family: str = CHART_STYLE["font_family"],
    show_title: bool = CHART_STYLE["show_title"],
    height: int = CHART_STYLE["height"],
    **kwargs
) -> Dict[str, Any]:
    county_norm = str(county).strip()
    df_selected = df[df["Län"].astype(str).str.strip() == county_norm].copy()

    summary, stats = get_statistics(df_selected, county=None, label=county_norm)

    total_courses = int(stats.get("Ansökta Kurser", 0))
    approved_courses = int(stats.get("Beviljade", 0))
    approval_rate_str = f"{float(stats.get('Beviljandegrad (%)', 0.0)):.1f}%"
    requested_places = int(stats.get("Ansökta platser", 0))
    approved_places = int(stats.get("Beviljade platser", 0))
    places_approval_rate = (approved_places / requested_places * 100) if requested_places > 0 else 0
    places_approval_rate_str = f"{places_approval_rate:.1f}%"

    county_chart = education_area_chart(
        summary,
        county_norm,
        xtick_size=xtick_size,
        ytick_size=ytick_size,
        title_size=title_size,
        legend_font_size=legend_font_size,
        label_font_size=label_font_size,
        font_family=font_family,
        show_title=show_title,      
        height=height, 
    )
    county_histogram = credits_histogram(
        df,
        county_norm,
        nbinsx=20,
        xtick_size=xtick_size,
        ytick_size=ytick_size,
        title_size=title_size,
        legend_font_size=legend_font_size,
        label_font_size=label_font_size,  
        font_family=font_family,
        show_title=show_title,            
        height=height,
    )

    return dict(
        df_selected_county=df_selected,
        summary=summary,
        stats=stats,
        total_courses=total_courses,
        approved_courses=approved_courses,
        approval_rate_str=approval_rate_str,
        requested_places=requested_places,
        approved_places=approved_places,
        places_approval_rate_str=places_approval_rate_str,
        county_chart=county_chart,
        county_histogram=county_histogram,
    )