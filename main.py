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

# ---------------------------------------------- map -------------
import json
import numpy as np
import plotly.graph_objects as go
from difflib import get_close_matches
from pathlib import Path

def build_sweden_map(
    df: pd.DataFrame,
    geojson_path: str | Path | None = None,
    tick_mode: str = "log_equal",  # "log_equal" or "percentiles"
    n_ticks: int = 6,
) -> "go.Figure":
    """
    Build a static choropleth map of approved courses per county.

    tick_mode:
      - "log_equal": ticks evenly spaced in log1p space (labels are original counts)
      - "percentiles": ticks at data percentiles (labels are original counts)
    """
    # Aggregate approved courses per county (Län)
    df_regions = (
        df.loc[df["Län"] != "Flera kommuner"]
          .groupby("Län")["Beslut"]
          .apply(lambda s: (s == "Beviljad").sum())
          .astype("int64")
          .reset_index(name="Beviljade")
          .sort_values(["Beviljade", "Län"], ascending=[False, True])
    )

    # Resolve GeoJSON path relative to this file if not provided
    if geojson_path is None:
        geojson_path = Path(__file__).resolve().parent / "assets" / "swedish_regions.geojson"

    with open(geojson_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Map region names to län codes from GeoJSON
    properties = [feat.get("properties", {}) for feat in json_data.get("features", [])]
    region_codes = {p.get("name"): p.get("ref:se:länskod") for p in properties}

    region_codes_map: list[str | None] = []
    for region in df_regions["Län"]:
        matches = get_close_matches(region, list(region_codes.keys()), n=1)
        if matches:
            region_codes_map.append(region_codes[matches[0]])
        else:
            logging.warning("No GeoJSON match found for region: %s", region)
            region_codes_map.append(None)

    # Color scale on log scale to reduce skew
    beviljade = df_regions["Beviljade"].values
    log_approved = np.log1p(beviljade)

    # --- Tick strategies ---
    def ticks_log_equal(vals: np.ndarray, n: int):
        pos = vals[vals > 0]
        if len(pos) == 0:
            return np.array([0.0]), ["0"]
        lo = np.log1p(pos.min())
        hi = np.log1p(pos.max())
        ticks_log = np.linspace(lo, hi, n)
        labels = np.expm1(ticks_log)
        labels = np.round(labels).astype(int)
        # ensure uniqueness and >0
        uniq = np.unique(labels)
        return ticks_log[: len(uniq)], [str(v) for v in uniq]

    def ticks_percentiles(vals: np.ndarray, n: int):
        if len(vals) == 0:
            return np.array([0.0]), ["0"]
        qs = np.linspace(0, 100, n)
        qv = np.percentile(vals, qs)
        qv = np.round(qv).astype(int)
        qv = qv[qv > 0]
        qv = np.unique(qv)
        if len(qv) == 0:
            return np.array([0.0]), ["0"]
        ticks_log = np.log1p(qv)
        return ticks_log, [str(v) for v in qv]

    if tick_mode == "percentiles":
        tickvals_log, ticktext = ticks_percentiles(beviljade, n_ticks)
    else:
        tickvals_log, ticktext = ticks_log_equal(beviljade, n_ticks)

    fig = go.Figure(
        go.Choroplethmap(
            geojson=json_data,
            locations=region_codes_map,
            z=log_approved,
            featureidkey="properties.ref:se:länskod",
            colorscale="Blues",
            showscale=True,
            colorbar=dict(
                title="Beviljade <br>kurser",
                tickvals=tickvals_log,
                ticktext=ticktext,
                x=0.1,              # place at left side of plotting area
                xanchor="left",     # anchor colorbar's left edge to x
                y=0.5,              # vertically centered
                yanchor="middle",
                thickness=20,
                len=0.8,
            ),
            customdata=df_regions["Beviljade"],
            text=df_regions["Län"],
            hovertemplate="<b>%{text}</b><br>Beviljade utbildningar: %{customdata}<extra></extra>",
            marker_line_width=0.3,
        )
    )

    fig.update_layout(
        map=dict(style="white-bg", zoom=3.2, center=dict(lat=62.6952, lon=13.9149)),
        width=470,
        height=500,
        margin=dict(r=0, t=50, l=0, b=0),
    )
    return fig

# Build once (static)
sweden_map = build_sweden_map(df, tick_mode="log_equal", n_ticks=6)
# ----------------- end map


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

# Centralize chart font settings so both initial and reactive renders match
CHART_XTICK_SIZE = 11
CHART_YTICK_SIZE = 12
CHART_TITLE_SIZE = 18
CHART_LEGEND_SIZE = 12
CHART_LABEL_SIZE = 11
CHART_FONT_FAMILY = "Arial"

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
        state.county_chart = education_area_chart(
            state.summary,
            state.selected_county,
            xtick_size=CHART_XTICK_SIZE,
            ytick_size=CHART_YTICK_SIZE,
            title_size=CHART_TITLE_SIZE,
            legend_font_size=CHART_LEGEND_SIZE,
            label_font_size=CHART_LABEL_SIZE,
            font_family=CHART_FONT_FAMILY,
        )
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
        state.county_chart = education_area_chart(
            state.summary,
            state.selected_county,
            xtick_size=CHART_XTICK_SIZE,
            ytick_size=CHART_YTICK_SIZE,
            title_size=CHART_TITLE_SIZE,
            legend_font_size=CHART_LEGEND_SIZE,
            label_font_size=CHART_LABEL_SIZE,
            font_family=CHART_FONT_FAMILY,
        )
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
        "sweden_map": sweden_map, 
        "sweden_bar_chart": sweden_bar_chart, 
        "national_total_courses": national_total_courses,
        "national_approved_courses": national_approved_courses,
        "national_approval_rate_str": national_approval_rate_str,
        "national_requested_places": national_requested_places,
        "national_approved_places": national_approved_places,
    },
)