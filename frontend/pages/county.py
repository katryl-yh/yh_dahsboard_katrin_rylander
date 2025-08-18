import logging
import pandas as pd
from taipy.gui import Gui
import taipy.gui.builder as tgb

from backend.data_processing import (
    load_base_df,
    compute_national_stats
)

from frontend.maps import build_sweden_map
from frontend.charts import (
    education_area_chart, 
    credits_histogram    
)

from frontend.viewmodels import compute_county_view
from utils.chart_style import CHART_STYLE

logging.basicConfig(level=logging.WARNING)

def _safe_refresh(state, *var_names):
    if hasattr(state, "refresh"):
        for v in var_names:
            try:
                state.refresh(v)
            except Exception as e:
                logging.warning("refresh(%s) failed: %s", v, e)

# Load & prepare data
df = load_base_df()
nat = compute_national_stats(df)

# Initial county state (compute via view-model)
all_counties = sorted(df["Län"].dropna().unique().tolist())
selected_county = all_counties[0] if all_counties else ""
county_vm = compute_county_view(df, selected_county, **CHART_STYLE)
df_selected_county = county_vm["df_selected_county"]
summary = county_vm["summary"]
stats = county_vm["stats"]
total_courses = county_vm["total_courses"]
approved_courses = county_vm["approved_courses"]
approval_rate_str = county_vm["approval_rate_str"]
requested_places = county_vm["requested_places"]
approved_places = county_vm["approved_places"]
county_chart = county_vm["county_chart"]
county_histogram = county_vm["county_histogram"]

def on_county_change(state, var_name=None, var_value=None):
    if var_name != "selected_county":
        return
    selected = (str(var_value).strip() if var_value is not None else "").strip()
    if not selected or selected not in state.all_counties:
        return
    state.selected_county = selected
    try:
        vm = compute_county_view(df, state.selected_county, **CHART_STYLE)
        state.df_selected_county = vm["df_selected_county"]
        state.summary = vm["summary"]
        state.stats = vm["stats"]
        state.total_courses = vm["total_courses"]
        state.approved_courses = vm["approved_courses"]
        state.approval_rate_str = vm["approval_rate_str"]
        state.requested_places = vm["requested_places"]
        state.approved_places = vm["approved_places"]
        state.county_chart = vm["county_chart"]
        state.county_histogram = vm["county_histogram"]
    except Exception as e:
        logging.warning("on_county_change failed for '%s': %s", selected, e)
    _safe_refresh(
        state,
        "selected_county",
        "df_selected_county",
        "summary",
        "stats",
        "total_courses",
        "approved_courses",
        "approval_rate_str",
        "requested_places",
        "approved_places",
        "county_chart",
        "county_histogram",
    )

# UI
with tgb.Page() as county_page:
    with tgb.part(class_name="page-container"):
        with tgb.part(class_name="dashboard-content card stack-large"):
            tgb.navbar()

            with tgb.part(class_name="card"):
                tgb.text("## Statistik per Län", mode="md")
                tgb.text(
                    "Välj ett Län för att se statistik och KPIer.", 
                    mode="md")

                tgb.selector("{selected_county}", lov=all_counties, dropdown=True, on_change=on_county_change)

                with tgb.layout(columns="1 1 1"):
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Beviljade kurser", mode="md")
                        tgb.text("**{approved_courses}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Ansökta kurser", mode="md")
                        tgb.text("**{total_courses}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Beviljandegrad (kurser)", mode="md")
                        tgb.text("**{approval_rate_str}**", mode="md")

                with tgb.layout(columns="1 1 1"):
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Beviljade platser", mode="md")
                        tgb.text("**{approved_places}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Ansökta platser", mode="md")
                        tgb.text("**{requested_places}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("#### Beviljandegrad (platser)", mode="md")
                        #tgb.text("**{}**", mode="md")
                
                tgb.text("### Fördelning av beviljade och avslagna kursansökningar per utbildningsområde i {selected_county}", mode="md")
                tgb.text(
                        "Stapeldiagrammet är uppdelat i respektive utbildningsområde och visar på antalet beviljade kurser i blått och antalet avslag i grått.  \n",
                        mode="md")
                tgb.chart(figure="{county_chart}", type="plotly")
                tgb.text("### Histogram över YH-poäng för beviljade och avslagna kurser i {selected_county}", mode="md")
                tgb.chart(figure="{county_histogram}", type="plotly")

                with tgb.layout(columns="1"):
                    with tgb.part(class_name="table-container"):
                        tgb.text("### Rå data för {selected_county}", mode="md")
                        tgb.table("{df_selected_county}", width="100%")


""" Gui(county_page).run(
    port=8080,
    dark_mode=False,
    use_reloader=False,
    data={
        "df": df,
        "all_counties": all_counties,
        "selected_county": selected_county,
        "df_selected_county": df_selected_county,
        "summary": summary,
        "stats": stats,
        "total_courses": total_courses,
        "approved_courses": approved_courses,
        "approval_rate_str": approval_rate_str,
        "requested_places": requested_places,
        "approved_places": approved_places,
        "county_chart": county_chart,
        "county_histogram": county_histogram,
    },
) """