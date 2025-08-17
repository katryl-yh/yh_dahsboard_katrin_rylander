import logging
import pandas as pd
from taipy.gui import Gui
import taipy.gui.builder as tgb

from backend.data_processing import (
    load_base_df,
    get_statistics,
    compute_national_stats,
    summarize_providers,
)

from frontend.maps import build_sweden_map
from frontend.charts import (
    education_area_chart, 
    provider_education_area_chart,
    credits_histogram    
)

from frontend.viewmodels import (
    compute_provider_view, 
    compute_county_view
)

logging.basicConfig(level=logging.WARNING)

# Centralize chart font settings so both initial and reactive renders match
CHART_XTICK_SIZE = 11
CHART_YTICK_SIZE = 12
CHART_TITLE_SIZE = 18
CHART_LEGEND_SIZE = 12
CHART_LABEL_SIZE = 11
CHART_FONT_FAMILY = "Arial"

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

# Build providers table from enriched df (df is already enriched by load_base_df)
df_providers = summarize_providers(df)

# EXPLICITLY expose national KPIs as module-level vars
national_total_courses = nat.get("national_total_courses", 0)
national_approved_courses = nat.get("national_approved_courses", 0)
national_approval_rate_str = nat.get("national_approval_rate_str", "0%")
national_requested_places = nat.get("national_requested_places", 0)
national_approved_places = nat.get("national_approved_places", 0)

# Initial county state (compute via view-model)
all_counties = sorted(df["Län"].dropna().unique().tolist())
selected_county = all_counties[0] if all_counties else ""
county_vm = compute_county_view(
    df,
    selected_county,
    xtick_size=CHART_XTICK_SIZE,
    ytick_size=CHART_YTICK_SIZE,
    title_size=CHART_TITLE_SIZE,
    legend_font_size=CHART_LEGEND_SIZE,
    label_font_size=CHART_LABEL_SIZE,
    font_family=CHART_FONT_FAMILY,
)
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
    xtick_size=CHART_XTICK_SIZE,
    ytick_size=CHART_YTICK_SIZE,
    title_size=CHART_TITLE_SIZE,
    legend_font_size=CHART_LEGEND_SIZE,
    label_font_size=CHART_LABEL_SIZE,
    font_family=CHART_FONT_FAMILY,
)

# --- National histogram (reuse credits_histogram with county=None) ---
sweden_histogram = credits_histogram(
    df,
    county=None,
    nbinsx=20,
    xtick_size=CHART_XTICK_SIZE,
    ytick_size=CHART_YTICK_SIZE,
    title_size=CHART_TITLE_SIZE,
    legend_font_size=CHART_LEGEND_SIZE,
    font_family=CHART_FONT_FAMILY,
)

# initial chart for selected county
county_chart = education_area_chart(
    summary,
    selected_county,
    xtick_size=CHART_XTICK_SIZE,
    ytick_size=CHART_YTICK_SIZE,
    title_size=CHART_TITLE_SIZE,
    legend_font_size=CHART_LEGEND_SIZE,
    label_font_size=CHART_LABEL_SIZE,
    font_family=CHART_FONT_FAMILY,
)

# Initial histogram for selected county (reuse same function)
county_histogram = credits_histogram(
    df,
    selected_county,
    nbinsx=20,
    xtick_size=CHART_XTICK_SIZE,
    ytick_size=CHART_YTICK_SIZE,
    title_size=CHART_TITLE_SIZE,
    legend_font_size=CHART_LEGEND_SIZE,
    font_family=CHART_FONT_FAMILY,
)

# ---------- Provider state (initial) ----------
all_providers = sorted(df["Anordnare namn"].dropna().astype(str).str.strip().unique().tolist())
selected_provider = all_providers[0] if all_providers else ""
provider_vm = compute_provider_view(
    df,
    df_providers,
    selected_provider,
    xtick_size=CHART_XTICK_SIZE,
    ytick_size=CHART_YTICK_SIZE,
    title_size=CHART_TITLE_SIZE,
    legend_font_size=CHART_LEGEND_SIZE,
    label_font_size=CHART_LABEL_SIZE,
    font_family=CHART_FONT_FAMILY,
)
provider_rank_places = provider_vm["provider_rank_places"]
provider_rank_places_summary_str = provider_vm["provider_rank_places_summary_str"]
provider_places_summary_str = provider_vm["provider_places_summary_str"]
provider_places_approval_rate_str = provider_vm["provider_places_approval_rate_str"]
provider_courses_summary_str = provider_vm["provider_courses_summary_str"]
provider_courses_approval_rate_str = provider_vm["provider_courses_approval_rate_str"]
provider_chart = provider_vm["provider_chart"]

def on_provider_change(state, var_name=None, var_value=None):
    if var_name != "selected_provider":
        return
    selected = (str(var_value).strip() if var_value is not None else "").strip()
    if not selected or selected not in state.all_providers:
        return
    state.selected_provider = selected
    try:
        vm = compute_provider_view(
            state.df,
            state.df_providers if hasattr(state, "df_providers") else df_providers,
            selected,
            xtick_size=CHART_XTICK_SIZE,
            ytick_size=CHART_YTICK_SIZE,
            title_size=CHART_TITLE_SIZE,
            legend_font_size=CHART_LEGEND_SIZE,
            label_font_size=CHART_LABEL_SIZE,
            font_family=CHART_FONT_FAMILY,
        )
        state.provider_rank_places = vm["provider_rank_places"]
        state.provider_rank_places_summary_str = vm["provider_rank_places_summary_str"]
        state.provider_places_summary_str = vm["provider_places_summary_str"]
        state.provider_places_approval_rate_str = vm["provider_places_approval_rate_str"]
        state.provider_courses_summary_str = vm["provider_courses_summary_str"]
        state.provider_courses_approval_rate_str = vm["provider_courses_approval_rate_str"]
        state.provider_chart = vm["provider_chart"]
    except Exception as e:
        logging.warning("on_provider_change failed for '%s': %s", selected, e)
    _safe_refresh(
        state,
        "selected_provider",
        "provider_rank_places",
        "provider_rank_places_summary_str",
        "provider_places_summary_str",
        "provider_places_approval_rate_str",
        "provider_courses_summary_str",
        "provider_courses_approval_rate_str",
        "provider_chart",
    )

# -----------------------------

def on_county_change(state, var_name=None, var_value=None):
    if var_name != "selected_county":
        return
    selected = (str(var_value).strip() if var_value is not None else "").strip()
    if not selected or selected not in state.all_counties:
        return
    state.selected_county = selected
    try:
        vm = compute_county_view(
            state.df,
            state.selected_county,
            xtick_size=CHART_XTICK_SIZE,
            ytick_size=CHART_YTICK_SIZE,
            title_size=CHART_TITLE_SIZE,
            legend_font_size=CHART_LEGEND_SIZE,
            label_font_size=CHART_LABEL_SIZE,
            font_family=CHART_FONT_FAMILY,
        )
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
            tgb.text("#### Beviljade kurser", mode="md")
            tgb.text("**{national_approved_courses}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Ansökta kurser", mode="md")
            tgb.text("**{national_total_courses}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljandegrad", mode="md")
            tgb.text("**{national_approval_rate_str}**", mode="md")
   
    with tgb.layout(columns="1 1 1"):
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljade platser", mode="md")
            tgb.text("**{national_approved_places}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Ansökta platser", mode="md")
            tgb.text("**{national_requested_places}**", mode="md")

    tgb.text(
        "Kartan visar antal beviljade kurser i respektive län där mörkare färg indikerar på fler beviljade kurser.  \n"
        "Vi ser tydligt att de större länen Stockholm, Västra götaland och Skåne har flest kurser beviljade.  \n"
        "Ta muspekaren över respektive län för att se exakta antalet beviljade kurser per län.",
        mode="md")
    with tgb.layout(columns="1"):
        tgb.chart(figure="{sweden_map}", type="plotly")
    
    tgb.text(
        "Stapeldiagrammet är uppdelat i respektive utbildningsområde och visar på antalet  \n"
        "beviljade utbildningar i blått och antalet avslag i grått.  \n",
        mode="md")
    with tgb.layout(columns="1"):
        tgb.chart(figure="{sweden_bar_chart}", type="plotly")

    with tgb.layout(columns="1"):
        tgb.chart(figure="{sweden_histogram}", type="plotly")
    with tgb.part(class_name="table-card"):
        tgb.text("### Utbildningsanordnare statistik", mode="md")
        tgb.text(
        "Tabellen är sorterad efter beviljade antal platser totalt, vilket innebär att vissa  \n"
        "anordnare fått högre värde på andra kolumner, men lägre plats i tabellen.   \n",
        mode="md")
        # Simple paginated table; adjust page_size/height as needed
        tgb.table("{df_providers}", page_size=15, height="520px")
    
    tgb.selector("{selected_provider}", lov=all_providers, dropdown=True, on_change=on_provider_change)

    with tgb.layout(columns="1 1 1 1 1"):
        with tgb.part(class_name="stat-card"):
            tgb.text("##### Ranking beviljade platser", mode="md")
            tgb.text("**{provider_rank_places_summary_str}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("##### Platser: beviljade av sökta", mode="md")
            tgb.text("**{provider_places_summary_str}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("##### Beviljandegrad (platser)", mode="md")
            tgb.text("**{provider_places_approval_rate_str}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("##### Kurser: beviljade av sökta", mode="md")
            tgb.text("**{provider_courses_summary_str}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("##### Beviljandegrad (kurser)", mode="md")
            tgb.text("**{provider_courses_approval_rate_str}**", mode="md")

    with tgb.layout(columns="1"):
        tgb.chart(figure="{provider_chart}", type="plotly")

    # County section
    tgb.text("## Ansökningsomgång per Län", mode="md")
    tgb.selector("{selected_county}", lov=all_counties, dropdown=True, on_change=on_county_change)

    with tgb.layout(columns="1 1 1"):
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljade", mode="md")
            tgb.text("**{approved_courses}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Ansökta kurser", mode="md")
            tgb.text("**{total_courses}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljandegrad", mode="md")
            tgb.text("**{approval_rate_str}**", mode="md")

    with tgb.layout(columns="1 1 1"):
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljade platser", mode="md")
            tgb.text("**{approved_places}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Ansökta platser", mode="md")
            tgb.text("**{requested_places}**", mode="md")


    with tgb.layout(columns="1"):
        tgb.chart(figure="{county_chart}", type="plotly")

    tgb.text("Valt län: {selected_county}", mode="md")
    tgb.table("{df_selected_county}")

    with tgb.layout(columns="1"):
        tgb.chart(figure="{county_histogram}", type="plotly")

Gui(page).run(
    port=8080,
    dark_mode=False,
    use_reloader=False,
    data={
        "df": df,
        "df_providers": df_providers,
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
        # national (static) — pass explicitly instead of **nat
        "sweden_map": sweden_map, 
        "sweden_bar_chart": sweden_bar_chart, 
        "sweden_histogram": sweden_histogram,
        "national_total_courses": national_total_courses,
        "national_approved_courses": national_approved_courses,
        "national_approval_rate_str": national_approval_rate_str,
        "national_requested_places": national_requested_places,
        "national_approved_places": national_approved_places,
        # Provider bindings
        "all_providers": all_providers,
        "selected_provider": selected_provider,
        "provider_rank_places": provider_rank_places,
        "provider_places_summary_str": provider_places_summary_str,
        "provider_places_approval_rate_str": provider_places_approval_rate_str,
        "provider_courses_summary_str": provider_courses_summary_str,
        "provider_courses_approval_rate_str": provider_courses_approval_rate_str,
        "provider_chart": provider_chart,
    },
)