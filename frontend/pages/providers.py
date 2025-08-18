import taipy.gui.builder as tgb
from frontend.viewmodels import compute_provider_view
from utils.chart_style import CHART_STYLE

def on_provider_change(state, var_name=None, var_value=None):
    # Copy the on_provider_change function from main.py
    # ...

def build_providers_page(providers_data):
    with tgb.Page(title="YH Dashboard - Utbildningsanordnare") as page:
        tgb.text("# Utbildningsanordnare", mode="md")
        
        # Provider selector and statistics
        tgb.selector("{selected_provider}", lov=providers_data["all_providers"], 
                    dropdown=True, on_change=on_provider_change)
        
        # Provider statistics
        with tgb.layout(columns="1 1 1 1 1"):
            # Copy the provider stats section from main.py
            # ...
        
        # Provider chart
        with tgb.layout(columns="1"):
            tgb.chart(figure="{provider_chart}", type="plotly")
        
        # Provider table
        with tgb.part(class_name="table-card"):
            tgb.text("### Utbildningsanordnare statistik", mode="md")
            tgb.table("{df_providers}", page_size=15, height="520px")
        
        # Navigation
        with tgb.part(class_name="navigation"):
            tgb.navigate_to("Nationell statistik", to="home", class_name="nav-button")
            tgb.navigate_to("Län statistik", to="county", class_name="nav-button")
        
    return page

# Will be initialized in main.py
providers_page = None
providers_data = None

def initialize_providers_page(df, df_providers, **kwargs):
    global providers_page, providers_data
    
    # Prepare data
    all_providers = sorted(df["Anordnare namn"].dropna().astype(str).str.strip().unique().tolist())
    selected_provider = all_providers[0] if all_providers else ""
    
    provider_vm = compute_provider_view(df, df_providers, selected_provider, **CHART_STYLE)
    
    providers_data = {
        "df": df,
        "df_providers": df_providers,
        "all_providers": all_providers,
        "selected_provider": selected_provider,
        **provider_vm  # Unpack all provider view model data
    }
    
    providers_page = build_providers_page(providers_data)
    return providers_page