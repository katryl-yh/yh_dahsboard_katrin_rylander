import logging
import pandas as pd
from taipy.gui import Gui
import taipy.gui.builder as tgb

from backend.data_processing import (
    load_base_df,
    get_statistics,
    compute_national_stats,
)

from frontend.charts import education_area_chart

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

# EXPLICITLY expose national KPIs as module-level vars
national_total_courses = nat.get("national_total_courses", 0)
national_approved_courses = nat.get("national_approved_courses", 0)
national_approval_rate_str = nat.get("national_approval_rate_str", "0%")
national_requested_places = nat.get("national_requested_places", 0)
national_approved_places = nat.get("national_approved_places", 0)

# Initial county state
all_counties = sorted(df["Län"].dropna().unique().tolist())
selected_county = all_counties[0] if all_counties else ""
df_selected_county = df[df["Län"] == selected_county].copy()
summary, stats = get_statistics(df_selected_county, county=None, label=selected_county)

# Bindable KPI scalars (reactive)
total_courses = int(stats["Ansökta Kurser"])
approved_courses = int(stats["Beviljade"])
approval_rate_str = f"{stats['Beviljandegrad (%)']:.1f}%"
requested_places = int(stats.get("Ansökta platser", 0))
approved_places = int(stats.get("Beviljade platser", 0))
# initial chart for selected county
county_chart = education_area_chart(summary, selected_county)

def on_county_change(state, var_name=None, var_value=None):
    if var_name != "selected_county":
        return
    selected = (str(var_value).strip() if var_value is not None else "").strip()
    if not selected or selected not in state.all_counties:
        return

    state.selected_county = selected
    try:
        state.df_selected_county = state.df[state.df["Län"].astype(str).str.strip() == selected].copy()
        state.summary, state.stats = get_statistics(state.df_selected_county, county=None, label=selected)
        state.total_courses = int(state.stats["Ansökta Kurser"])
        state.approved_courses = int(state.stats["Beviljade"])
        state.approval_rate_str = f"{state.stats['Beviljandegrad (%)']:.1f}%"
        state.requested_places = int(state.stats.get("Ansökta platser", 0))
        state.approved_places = int(state.stats.get("Beviljade platser", 0))
        state.county_chart = education_area_chart(state.summary, state.selected_county)
    except Exception as e:
        logging.warning("on_county_change failed for '%s': %s", selected, e)
        state.df_selected_county = pd.DataFrame()
        state.summary = pd.DataFrame()
        state.stats = {"Län": selected, "Ansökta Kurser": 0, "Beviljade": 0, "Avslag": 0, "Beviljandegrad (%)": 0.0}
        state.total_courses = 0
        state.approved_courses = 0
        state.approval_rate_str = "0.0%"
        state.requested_places = 0
        state.approved_places = 0
        state.county_chart = education_area_chart(state.summary, state.selected_county)

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
    )

# UI
with tgb.Page() as page:
    tgb.text("# YH 2025 - ansökningsomgång för kurser", mode="md")
    tgb.text(
        "Denna dashboard syftar till att vara ett verktyg för intressenter inom yrkeshögskola att läsa av KPIer för olika utbildningsanordnare.  \n"
        "För utbildningsanordnare skulle man exempelvis kunna se vad konkurrenterna ansökt och ta inspiration från dem.",
        mode="md",
    )
    # National stats (static)
    tgb.text("## Statistik för Sverige", mode="md")
    tgb.text(
        "Nedan syns KPIer och information för hela ansökningsomgången för hela Sverige.  \n"
        "Detta innebär samtliga kommuner, utbildningsområden och utbildningsanordnare i landet.", 
        mode="md")
    with tgb.layout(columns="1 1 1"):
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Ansökta kurser", mode="md")
            tgb.text("**{national_total_courses}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljade", mode="md")
            tgb.text("**{national_approved_courses}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljandegrad", mode="md")
            tgb.text("**{national_approval_rate_str}**", mode="md")

    with tgb.layout(columns="1 1"):
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Ansökta platser (Sverige)", mode="md")
            tgb.text("**{national_requested_places}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljade platser (Sverige)", mode="md")
            tgb.text("**{national_approved_places}**", mode="md")

    # County section
    tgb.text("## Ansökningsomgång per Län", mode="md")
    tgb.selector("{selected_county}", lov=all_counties, dropdown=True, on_change=on_county_change)

    with tgb.layout(columns="1 1 1"):
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Ansökta kurser", mode="md")
            tgb.text("**{total_courses}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljade", mode="md")
            tgb.text("**{approved_courses}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljandegrad", mode="md")
            tgb.text("**{approval_rate_str}**", mode="md")

    with tgb.layout(columns="1 1"):
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Ansökta platser", mode="md")
            tgb.text("**{requested_places}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljade platser", mode="md")
            tgb.text("**{approved_places}**", mode="md")

    with tgb.layout(columns="1"):
        tgb.chart(figure="{county_chart}", type="plotly")

    tgb.text("Valt län: {selected_county}", mode="md")
    tgb.table("{df_selected_county}")

Gui(page).run(
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
        # national (static) — pass explicitly instead of **nat
        "national_total_courses": national_total_courses,
        "national_approved_courses": national_approved_courses,
        "national_approval_rate_str": national_approval_rate_str,
        "national_requested_places": national_requested_places,
        "national_approved_places": national_approved_places,
    },
)