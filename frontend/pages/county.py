import taipy.gui.builder as tgb
from frontend.viewmodels import compute_county_view
from utils.chart_style import CHART_STYLE

def on_county_change(state, var_name=None, var_value=None):
    # Copy the on_county_change function from main.py
    # ...

def build_county_page(county_data):
    with tgb.Page(title="YH Dashboard - Län") as page:
        tgb.text("# Ansökningsomgång per Län", mode="md")
        
        # County selector
        tgb.selector("{selected_county}", lov=county_data["all_counties"], 
                     dropdown=True, on_change=on_county_change)
        
        # County statistics
        with tgb.layout(columns="1 1 1"):
            # Copy the county stats section from main.py
            # ...
        
        # County charts
        with tgb.layout(columns="1"):
            tgb.chart(figure="{county_chart}", type="plotly")
        
        with tgb.layout(columns="1"):
            tgb.chart(figure="{county_histogram}", type="plotly")
        
        # County data table
        tgb.text("Valt län: {selected_county}", mode="md")
        tgb.table("{df_selected_county}")
        
        # Navigation
        with tgb.part(class_name="navigation"):
            tgb.navigate_to("Nationell statistik", to="home", class_name="nav-button")
            tgb.navigate_to("Utbildningsanordnare", to="providers", class_name="nav-button")
    
    return page

# Will be initialized in main.py
county_page = None
county_data = None

def initialize_county_page(df, **kwargs):
    global county_page, county_data
    
    # Prepare data
    all_counties = sorted(df["Län"].dropna().unique().tolist())
    selected_county = all_counties[0] if all_counties else ""
    
    county_vm = compute_county_view(df, selected_county, **CHART_STYLE)
    
    county_data = {
        "df": df,
        "all_counties": all_counties,
        "selected_county": selected_county,
        **county_vm  # Unpack all county view model data
    }
    
    county_page = build_county_page(county_data)
    return county_page