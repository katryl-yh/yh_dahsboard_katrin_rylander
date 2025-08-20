import logging
import pandas as pd
from taipy.gui import Gui, notify
import taipy.gui.builder as tgb
from pathlib import Path

from utils.constants import PROJECT_ROOT, BLUE_1, GRAY_1, ORANGE_1
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
df_providers = summarize_providers(df)

# ---------- Provider state (initial) ----------
provider_names = sorted(df["Anordnare namn"].dropna().astype(str).str.strip().unique().tolist())
primary_provider = ""
comparison_provider = ""

def on_primary_provider_change(state):
    """Handle primary provider selection."""
    # Clear comparison provider if it's the same as the primary
    if state.primary_provider == state.comparison_provider:
        state.comparison_provider = ""
    return state

def on_comparison_provider_change(state):
    """Handle comparison provider selection."""
    # Clear if it's the same as the primary
    if state.comparison_provider == state.primary_provider:
        state.comparison_provider = ""
        notify(state, "Kan inte jämföra samma anordnare", "warning")
    return state

# UI definition
with tgb.Page() as providers_comp_page:
    with tgb.part(class_name="page-container"):
        with tgb.part(class_name="dashboard-content card stack-large"):
            tgb.navbar()
            
            with tgb.part(class_name="card"):
                tgb.text("## Jämför Utbildningsanordnare", mode="md")
                tgb.text("Välj två utbildningsanordnare för att jämföra deras statistik.", mode="md")
                
                # Two selector layout
                with tgb.layout(columns="1 1"):
                    # Primary provider selector
                    tgb.text("### Välj anordnare:", mode="md")
                    tgb.selector(
                        value="{primary_provider}",
                        lov=provider_names,
                        dropdown=True,
                        on_change=on_primary_provider_change,
                        class_name="provider-selector"
                    )
                    
                    # Comparison provider selector
                    tgb.text("### Jämför med (valfritt):", mode="md")
                    tgb.selector(
                        value="{comparison_provider}",
                        lov=provider_names,
                        dropdown=True,
                        on_change=on_comparison_provider_change,
                        class_name="provider-selector"
                    )

            # Conditional parts based on selections
            with tgb.part(render="{len(primary_provider) == 0}", class_name="card"):
                tgb.text("### Välj en anordnare för att se statistik", mode="md")

            # Primary provider display (when no comparison is selected)
            with tgb.part(render="{len(primary_provider) > 0 and len(comparison_provider) == 0}", class_name="card"):
                tgb.text(f"### Statistik för {{primary_provider}}", mode="md")
                
                with tgb.layout(columns="1 1 1"):
                    with tgb.part():
                        tgb.text("#### Beviljade platser", mode="md")
                        tgb.text(lambda state: compute_provider_view(
                            state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                        )["provider_places_summary_str"], mode="md")
                        tgb.text(lambda state: f"Beviljandegrad: {compute_provider_view(
                            state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                        )['provider_places_approval_rate_str']}", mode="md")
                    
                    with tgb.part():
                        tgb.text("#### Beviljade kurser", mode="md")
                        tgb.text(lambda state: compute_provider_view(
                            state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                        )["provider_courses_summary_str"], mode="md")
                        tgb.text(lambda state: f"Beviljandegrad: {compute_provider_view(
                            state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                        )['provider_courses_approval_rate_str']}", mode="md")
                    
                    with tgb.part():
                        tgb.text("#### Ranking bland anordnare", mode="md")
                        tgb.text(lambda state: compute_provider_view(
                            state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                        )["provider_rank_places_summary_str"], mode="md")
                        tgb.text("(baserat på antal beviljade platser)", mode="md")
                
                tgb.text("### Utbildningsområden", mode="md")
                tgb.chart(
                    figure=lambda state: compute_provider_view(
                        state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                    )["provider_chart"], 
                    type="plotly"
                )
                
                tgb.text("### YH-poäng", mode="md")
                tgb.chart(
                    figure=lambda state: compute_provider_view(
                        state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                    )["provider_histogram"], 
                    type="plotly"
                )

            # Comparison display (when both providers are selected)
            with tgb.part(render="{len(primary_provider) > 0 and len(comparison_provider) > 0}", class_name="card"):
                tgb.text("### Jämförelse av nyckeltal", mode="md")
                tgb.table(
                    value=lambda state: pd.DataFrame([
                        {
                            "Nyckeltal": "Anordnare",
                            "Anordnare 1": state.primary_provider,
                            "Anordnare 2": state.comparison_provider
                        },
                        {
                            "Nyckeltal": "Beviljandegrad platser",
                            "Anordnare 1": compute_provider_view(
                                state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                            )["provider_places_approval_rate_str"],
                            "Anordnare 2": compute_provider_view(
                                state.df, state.df_providers, state.comparison_provider, **CHART_STYLE
                            )["provider_places_approval_rate_str"]
                        },
                        {
                            "Nyckeltal": "Beviljade platser",
                            "Anordnare 1": compute_provider_view(
                                state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                            )["provider_places_summary_str"],
                            "Anordnare 2": compute_provider_view(
                                state.df, state.df_providers, state.comparison_provider, **CHART_STYLE
                            )["provider_places_summary_str"]
                        },
                        {
                            "Nyckeltal": "Beviljandegrad kurser",
                            "Anordnare 1": compute_provider_view(
                                state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                            )["provider_courses_approval_rate_str"],
                            "Anordnare 2": compute_provider_view(
                                state.df, state.df_providers, state.comparison_provider, **CHART_STYLE
                            )["provider_courses_approval_rate_str"]
                        },
                        {
                            "Nyckeltal": "Beviljade kurser",
                            "Anordnare 1": compute_provider_view(
                                state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                            )["provider_courses_summary_str"],
                            "Anordnare 2": compute_provider_view(
                                state.df, state.df_providers, state.comparison_provider, **CHART_STYLE
                            )["provider_courses_summary_str"]
                        },
                        {
                            "Nyckeltal": "Ranking (platser)",
                            "Anordnare 1": compute_provider_view(
                                state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                            )["provider_rank_places_summary_str"],
                            "Anordnare 2": compute_provider_view(
                                state.df, state.df_providers, state.comparison_provider, **CHART_STYLE
                            )["provider_rank_places_summary_str"]
                        }
                    ]),
                    class_name="comparison-table"
                )

            # Comparison charts (when both providers are selected)
            with tgb.part(render="{len(primary_provider) > 0 and len(comparison_provider) > 0}", class_name="card"):
                tgb.text("### Utbildningsområden", mode="md")
                
                with tgb.layout(columns="1 1"):
                    with tgb.part(class_name="chart-container"):
                        tgb.text("#### {primary_provider}", mode="md")
                        tgb.chart(
                            figure=lambda state: compute_provider_view(
                                state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                            )["provider_chart"], 
                            type="plotly"
                        )
                    
                    with tgb.part(class_name="chart-container"):
                        tgb.text("#### {comparison_provider}", mode="md")
                        tgb.chart(
                            figure=lambda state: compute_provider_view(
                                state.df, state.df_providers, state.comparison_provider, **CHART_STYLE
                            )["provider_chart"], 
                            type="plotly"
                        )

            # YH-poäng charts (when both providers are selected)
            with tgb.part(render="{len(primary_provider) > 0 and len(comparison_provider) > 0}", class_name="card"):
                tgb.text("### YH-poäng", mode="md")
                
                with tgb.layout(columns="1 1"):
                    with tgb.part(class_name="chart-container"):
                        tgb.text("#### {primary_provider}", mode="md")
                        tgb.chart(
                            figure=lambda state: compute_provider_view(
                                state.df, state.df_providers, state.primary_provider, **CHART_STYLE
                            )["provider_histogram"], 
                            type="plotly"
                        )
                    
                    with tgb.part(class_name="chart-container"):
                        tgb.text("#### {comparison_provider}", mode="md")
                        tgb.chart(
                            figure=lambda state: compute_provider_view(
                                state.df, state.df_providers, state.comparison_provider, **CHART_STYLE
                            )["provider_histogram"], 
                            type="plotly"
                        )