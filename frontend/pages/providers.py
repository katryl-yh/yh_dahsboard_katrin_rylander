import logging
import pandas as pd
from taipy.gui import Gui
import taipy.gui.builder as tgb

from backend.data_processing import (
    load_base_df,
    summarize_providers,
)

from frontend.charts import ( 
    provider_education_area_chart,
    credits_histogram    
)

from frontend.viewmodels import compute_provider_view
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

# Build providers table from enriched df (df is already enriched by load_base_df)
df_providers = summarize_providers(df)

# ---------- Provider state (initial) ----------
all_providers = sorted(df["Anordnare namn"].dropna().astype(str).str.strip().unique().tolist())
selected_provider = all_providers[0] if all_providers else ""
provider_vm = compute_provider_view(
    df,
    df_providers,
    selected_provider,
    **CHART_STYLE,
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
            **CHART_STYLE,
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


# UI
with tgb.Page() as providers_page:
    with tgb.part(class_name="page-container"):
        with tgb.part(class_name="dashboard-content card stack-large"):
            tgb.navbar()

            with tgb.part(class_name="card"):
                tgb.text("## Statistik per Utbildningsanordnare.", mode="md")
                tgb.text(
                    "Välj en utbildningsanordnare för att se statistik och KPIer.",
                    mode="md")
                tgb.selector("{selected_provider}", lov=all_providers, dropdown=True, on_change=on_provider_change)
            
                with tgb.layout(columns="1 1 1"):
                    with tgb.part(class_name="stat-card"):
                        tgb.text("##### Ranking beviljade platser", mode="md")
                        tgb.text("**{provider_rank_places_summary_str}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("##### Platser: beviljade av sökta", mode="md")
                        tgb.text("**{provider_places_summary_str}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("##### Beviljandegrad (platser)", mode="md")
                        tgb.text("**{provider_places_approval_rate_str}**", mode="md")
                with tgb.layout(columns="1 1 1"):
                    with tgb.part(class_name="stat-card"):
                        tgb.text("##### Ranking beviljade kurser", mode="md")
                        #tgb.text("**{provider_rank_courses_summary_str}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("##### Kurser: beviljade av sökta", mode="md")
                        tgb.text("**{provider_courses_summary_str}**", mode="md")
                    with tgb.part(class_name="stat-card"):
                        tgb.text("##### Beviljandegrad (kurser)", mode="md")
                        tgb.text("**{provider_courses_approval_rate_str}**", mode="md")

                tgb.text("### Fördelning av beviljade och avslagna kursansökningar per utbildningsområde för {selected_provider}", mode="md")
                tgb.text(
                        "Stapeldiagrammet är uppdelat i respektive utbildningsområde och visar på antalet beviljade kurser i blått och antalet avslag i grått.  \n",
                        mode="md")
                tgb.chart(figure="{provider_chart}", type="plotly")
                #tgb.text("### Histogram över YH-poäng för beviljade och avslagna kurser för {selected_provider}", mode="md")
                #tgb.chart(figure="{county_histogram}", type="plotly")
                
                tgb.text("### Tabell över utbildningsanordnare", mode="md")
                tgb.text(
                    "Tabellen är sorterad efter beviljade antal platser totalt, vilket innebär att vissa "
                    "anordnare fått högre värde på andra kolumner, men lägre plats i tabellen. ",
                    mode="md")
                tgb.table("{df_providers}", width="100%")
        
    

""" Gui(providers_page).run(
    port=8080,
    dark_mode=False,
    use_reloader=False,
    data={
        "df": df,
        "df_providers": df_providers,
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
) """