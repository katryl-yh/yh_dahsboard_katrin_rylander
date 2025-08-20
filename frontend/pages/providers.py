import logging
import pandas as pd
from taipy.gui import Gui
import taipy.gui.builder as tgb

from backend.data_processing import (
    load_base_df,
    summarize_providers,
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

# Build providers table from enriched df
df_providers = summarize_providers(df)

# ---------- Provider state (initial) ----------
all_providers = sorted(df["Anordnare namn"].dropna().astype(str).str.strip().unique().tolist())

# Set a custom default provider
all_providers = sorted(df["Anordnare namn"].dropna().astype(str).str.strip().unique().tolist())

# Get the exact name as it appears in the data
default_provider_name = "Stiftelsen Stockholms Tekniska Institut"
providers_lower = {p.lower(): p for p in all_providers}
default_provider_lower = default_provider_name.lower()

if default_provider_lower in providers_lower:
    # Use the correct case version from the data
    selected_provider = providers_lower[default_provider_lower]
else:
    # Fallback
    selected_provider = all_providers[0] if all_providers else ""

print(f"Selected provider: {selected_provider}")

# Calculate initial view model
provider_vm = compute_provider_view(
    df,
    df_providers,
    selected_provider,
    **CHART_STYLE,
)
provider_rank_places = provider_vm["provider_rank_places"]
provider_rank_places_summary_str = provider_vm["provider_rank_places_summary_str"]
provider_rank_courses = provider_vm["provider_rank_courses"]                    
provider_rank_courses_summary_str = provider_vm["provider_rank_courses_summary_str"]  
provider_places_summary_str = provider_vm["provider_places_summary_str"]
provider_places_approval_rate_str = provider_vm["provider_places_approval_rate_str"]
provider_courses_summary_str = provider_vm["provider_courses_summary_str"]
provider_courses_approval_rate_str = provider_vm["provider_courses_approval_rate_str"]
provider_chart = provider_vm["provider_chart"]
provider_histogram = provider_vm["provider_histogram"]

def on_provider_change(state, var_name=None, var_value=None):
    if var_name != "selected_provider":
        return
        
    selected = (str(var_value).strip() if var_value is not None else "").strip()
    if not selected or selected not in state.all_providers:
        return
        
    state.selected_provider = selected
    
    try:
        # Get all provider data in one call
        vm = compute_provider_view(
            state.df,
            state.df_providers if hasattr(state, "df_providers") else df_providers,
            selected,
            **CHART_STYLE,
        )
        
        # Update all state variables at once
        for key, value in vm.items():
            if hasattr(state, key):
                setattr(state, key, value)
                
    except Exception as e:
        logging.warning("on_provider_change failed for '%s': %s", selected, e)
        
    # Refresh all state variables
    _safe_refresh(
        state,
        "selected_provider",
        "provider_rank_places",
        "provider_places_summary_str",
        "provider_rank_courses", 
        "provider_rank_places_summary_str",         
        "provider_rank_courses_summary_str", 
        "provider_places_approval_rate_str",
        "provider_courses_summary_str",
        "provider_courses_approval_rate_str",
        "provider_chart",
        "provider_histogram",
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
                tgb.selector("{selected_provider}", lov=all_providers, dropdown=True, on_change=on_provider_change,class_name="wide-selector")
            
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
                        tgb.text("**{provider_rank_courses_summary_str}**", mode="md")
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
                tgb.text("### Histogram över YH-poäng för beviljade och avslagna kurser för {selected_provider}", mode="md")
                tgb.chart(figure="{provider_histogram}", type="plotly")
                tgb.text("### Tabell över utbildningsanordnare", mode="md")
                tgb.text(
                    "Tabellen är sorterad efter beviljade antal platser totalt, vilket innebär att vissa "
                    "anordnare fått högre värde på andra kolumner, men lägre plats i tabellen. ",
                    mode="md")
                tgb.table("{df_providers}", width="100%", page_size=10)