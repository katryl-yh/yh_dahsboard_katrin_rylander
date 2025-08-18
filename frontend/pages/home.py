import logging
import pandas as pd
from taipy.gui import Gui
import taipy.gui.builder as tgb

from backend.data_processing import (
    load_base_df,
    get_statistics,
    compute_national_stats,
)

from frontend.maps import build_sweden_map
from frontend.charts import (
    education_area_chart, 
    credits_histogram    
)

from utils.chart_style import CHART_STYLE
from utils.constants import BLUE_1

logging.basicConfig(level=logging.WARNING)

# Load & prepare data
df = load_base_df()
nat = compute_national_stats(df)

# EXPLICITLY expose national KPIs as module-level vars
national_total_courses = nat.get("national_total_courses", 0)
national_approved_courses = nat.get("national_approved_courses", 0)
national_approval_rate_str = nat.get("national_approval_rate_str", "0%")
national_requested_places = nat.get("national_requested_places", 0)
national_approved_places = nat.get("national_approved_places", 0)
national_places_approval_rate_str = nat.get("national_places_approval_rate_str", "0.0%")

# --- National map with approved courses per county ---
sweden_map = build_sweden_map(
    df,
    tick_mode="log_equal",   # or "percentiles"
    n_ticks=6,
    colorbar_side="left",
)

# --- National bar chart (education_area_chart for whole Sweden) ---
summary_sweden, _stats_sweden = get_statistics(df, county=None, label="Sverige")
sweden_bar_chart = education_area_chart(
    summary_sweden,
    "Sverige",
    show_title=False,
    **CHART_STYLE,
)

# --- National histogram (reuses credits_histogram with county=None) ---
sweden_histogram = credits_histogram(
    df,
    county=None,
    nbinsx=20,
    show_title=False,
    **CHART_STYLE,
)

# UI
with tgb.Page() as home_page:
    with tgb.part(class_name="page-container"):
        with tgb.part(class_name="dashboard-content card stack-large"):
            tgb.navbar()

            with tgb.part(class_name="card"):
                tgb.text("# YH dashboard 2025 - ansökningsomgång för kurser", mode="md")
                tgb.text(
                    "Denna dashboard syftar till att vara ett verktyg för intressenter inom yrkeshögskola att läsa av KPIer för olika utbildningsanordnare.  \n"
                    "För utbildningsanordnare skulle man exempelvis kunna se vad konkurrenterna ansökt och ta inspiration från dem.  \n" 
                    "Dessutom kan det vara ett verktyg för utbildningsledarna att få en övergripande bild över ansökningsprocessen. ",
                    mode="md",
                )
                tgb.text("## Statistik för Sverige", mode="md")
                tgb.text(
                    "Nedan presenteras KPIer och information för hela ansökningsomgången för hela Sverige."
                    "Detta innebär samtliga län, utbildningsområden och utbildningsanordnare i landet.", 
                    mode="md")
                
                with tgb.layout(columns="1 1 1"):
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Beviljade kurser", mode="md")
                        tgb.text("**{national_approved_courses}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Ansökta kurser", mode="md")
                        tgb.text("**{national_total_courses}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Beviljandegrad (kurser)", mode="md")
                        tgb.text("**{national_approval_rate_str}**", mode="md")
        
                with tgb.layout(columns="1 1 1"):
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Beviljade platser", mode="md")
                        tgb.text("**{national_approved_places}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Ansökta platser", mode="md")
                        tgb.text("**{national_requested_places}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Beviljandegrad (platser)", mode="md")
                        tgb.text("**{national_places_approval_rate_str}**", mode="md")

                tgb.text("### Beviljade kurser i respektive län", mode="md")
                with tgb.layout(columns="1 2"):
                    with tgb.part(class_name="stat-card"):
                        tgb.text(
                            "Kartan visar antal beviljade kurser i respektive län där mörkare färg indikerar på fler beviljade kurser.  \n  \n"
                            "Vi ser tydligt att de större länen:  \n Stockholm, Västra götaland och Skåne   \n har flest kurser beviljade.  \n  \n"
                            "Ta muspekaren över respektive län för att se exakta antalet beviljade kurser per län.",
                            mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.chart(figure="{sweden_map}", type="plotly")

                tgb.text("### Fördelning av beviljade och avslagna kurser ansökningar per utbildningsområde", mode="md")
                tgb.text(
                        "Stapeldiagrammet är uppdelat i respektive utbildningsområde och visar på antalet beviljade kurser i blått och antalet avslag i grått.",
                        mode="md")
                tgb.chart(figure="{sweden_bar_chart}", type="plotly")
                tgb.text("### Historgram över YH-poäng för beviljade och avslagna kurser", mode="md")
                tgb.chart(figure="{sweden_histogram}", type="plotly")   

""" Gui(home_page).run(
    port=8080,
    dark_mode=False,
    use_reloader=False,
    data={
        "df": df,
        "sweden_map": sweden_map, 
        "sweden_bar_chart": sweden_bar_chart, 
        "sweden_histogram": sweden_histogram,
        "national_total_courses": national_total_courses,
        "national_approved_courses": national_approved_courses,
        "national_approval_rate_str": national_approval_rate_str,
        "national_requested_places": national_requested_places,
        "national_approved_places": national_approved_places,
    },
) """