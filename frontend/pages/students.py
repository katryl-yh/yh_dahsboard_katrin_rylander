import logging
import pandas as pd
import plotly.graph_objects as go
from taipy.gui import Gui
import taipy.gui.builder as tgb
from pathlib import Path
from backend.data_processing import (
    load_student_data, 
    preprocess_student_data,
    get_available_years,
    filter_data_by_year,
    prepare_education_gender_data,
    prepare_yearly_gender_data,  
    get_education_areas, 
    calculate_gender_distribution,   
    calculate_year_growth,     
)
from utils.constants import PROJECT_ROOT
from frontend.charts import (
    create_education_gender_chart,
    create_yearly_gender_chart,
    create_age_gender_chart
)

def _safe_refresh(state, *var_names):
    if hasattr(state, "refresh"):
        for v in var_names:
            try:
                state.refresh(v)
            except Exception as e:
                logging.warning("refresh(%s) failed: %s", v, e)
# --------- TAIPY CALLBACK FUNCTIONS ---------

def on_year_change(state):
    """
    Callback for when the year selection changes.
    
    Parameters:
        state: Taipy state object
    """
    try:
        # Filter data for selected year
        filtered_data = filter_data_by_year(state.df, state.selected_year)
        
        # Prepare data for visualization
        pivot_data = prepare_education_gender_data(filtered_data)
        
        # Create chart
        state.student_chart = create_education_gender_chart(
            pivot_data, 
            state.selected_year, 
            show_title=False
            )
        # Create age distribution chart with the selected education area
        state.age_chart = create_age_gender_chart(
            filtered_data,
            state.selected_year,
            state.selected_education_area,
            show_title=False
        )

        # Update gender stats for the selected year
        year_gender_stats = calculate_gender_distribution(state.df, state.selected_year)
        state.year_women_pct = year_gender_stats["women_pct"]
        state.year_men_pct = year_gender_stats["men_pct"]
        state.year_gender_ratio = year_gender_stats["ratio_simple"]
        state.year_women_count = year_gender_stats["women_count"]
        state.year_men_count = year_gender_stats["men_count"]

        # Update growth stats for the selected year
        growth_stats = calculate_year_growth(state.df, state.selected_year)
        state.growth_pct_display = growth_stats["growth_pct_display"]
        state.growth_count_display = growth_stats["growth_count_display"]
        state.growth_class = growth_stats["growth_class"]

        # Use _safe_refresh to refresh all the updated state variables
        _safe_refresh(
            state,
            "student_chart",
            "age_chart",
            "year_women_pct",
            "year_men_pct",
            "year_gender_ratio",
            "year_women_count",
            "year_men_count",
            "growth_pct_display",
            "growth_count_display",
            "growth_class"
        )
    
    
    except Exception as e:
        logging.error(f"Error in year change callback: {str(e)}")
    
    return state

def on_education_area_change(state):
    """
    Callback for when the education area selection changes.
    
    Parameters:
        state: Taipy state object
    """
    try:
        # Get current filtered data for the selected year
        filtered_data = filter_data_by_year(state.df, state.selected_year)
        
        # Update only the age chart with the new education area
        state.age_chart = create_age_gender_chart(
            filtered_data,
            state.selected_year,
            state.selected_education_area,
            show_title=False
        )
    
    except Exception as e:
        logging.error(f"Error in education area change callback: {str(e)}")
    
    return state

# --------- MAIN CODE ---------

# Get file path using project constants for consistency
file_path = PROJECT_ROOT / "data" / "scb" / "Antagna som påbörjat studier på yrkeshögskolans kurser.csv"


# Load and process data
raw_df, file_not_found, error_message = load_student_data(file_path)
df = preprocess_student_data(raw_df)

# Get available years and initialize selections
available_years = get_available_years(df)
selected_year = available_years[-1] if available_years else "2024"

# Get education areas for filtering
education_areas = get_education_areas(df)
selected_education_area = "Alla områden"

# Create initial chart if data is available
student_chart = None
if not file_not_found:
    filtered_data = filter_data_by_year(df, selected_year)
    pivot_data = prepare_education_gender_data(filtered_data)
    student_chart = create_education_gender_chart(
            pivot_data, 
            selected_year, 
            show_title=False
    )

    # Create yearly gender distribution chart
    yearly_data = prepare_yearly_gender_data(df)
    yearly_chart = create_yearly_gender_chart(
        yearly_data, 
        show_title=False
    )

    # Create age distribution chart
    age_chart = create_age_gender_chart(
        filtered_data,
        selected_year,
        selected_education_area,
        show_title=False
    )

# Get all-time gender stats
gender_stats = calculate_gender_distribution(df)
women_pct = gender_stats["women_pct"]
men_pct = gender_stats["men_pct"]
gender_ratio = gender_stats["ratio_simple"]
women_count = gender_stats["women_count"]
men_count = gender_stats["men_count"]

# Also calculate year-specific gender stats
year_gender_stats = calculate_gender_distribution(df, selected_year)
year_women_pct = year_gender_stats["women_pct"]
year_men_pct = year_gender_stats["men_pct"]
year_gender_ratio = year_gender_stats["ratio_simple"]
year_women_count = year_gender_stats["women_count"]
year_men_count = year_gender_stats["men_count"]

# Calculate growth stats for selected year
growth_stats = calculate_year_growth(df, selected_year)
growth_pct_display = growth_stats["growth_pct_display"]
growth_count_display = growth_stats["growth_count_display"]
growth_class = growth_stats["growth_class"]

# --------- UI DEFINITION ---------

with tgb.Page() as students_page:
    with tgb.part(class_name="page-container"):
        with tgb.part(class_name="dashboard-content card stack-large"):
            # Navigation bar
            tgb.navbar()
            
            # Page title
            with tgb.part(class_name="card"):
                tgb.text(f"## Statistik över antagna som påbörjat YH-studier", mode="md")
                tgb.text("Visar data för antagna som påbörjat YH-studier med möjlighet att analysera "
                            "fördelningen per utbildningsområde, kön och åldersgrupp över tid.", mode="md")
            
                tgb.text(f"### Utveckling av antagna studenter över tid", mode="md")
                with tgb.layout(columns="1 2"):
                # Year selector 

                    tgb.text(
                        "Diagrammet visar:  \n" \
                        "- antal kvinnor (orange) och   \n" \
                        "- män (blå) som påbörjat studier för varje år.  \n  \n"
                        "Den gråa cirkeln representerar det totala antalet studenter per år.", 
                        mode="md"
                    )
                    tgb.chart(figure="{yearly_chart}", type="plotly")
                    tgb.text("  \n", mode="md") 

                with tgb.part(class_name="card"):
                    with tgb.layout(columns="1 1"):
                        tgb.text("### Välj år för att få fördjupad statistik:", mode="md")
                        tgb.selector(
                                value="{selected_year}", 
                                lov=available_years,
                                dropdown=True,
                                on_change=on_year_change,
                                class_name="padded-selector"
                                )

                    tgb.text("#### Tillväxt i antagna från föregående år: {growth_pct_display} ", mode="md")
                   
                    tgb.text("#### Könsfördelning bland YH-studenter {selected_year}", mode="md")
    
                    with tgb.layout(columns="1 1 1"):
                        with tgb.part(class_name="stat-card"):
                            tgb.text("#### Andel kvinnor", mode="md")
                            tgb.text("**{year_women_pct}%**", mode="md")
                            tgb.text("{year_women_count:,} kvinnor".replace(",", " "), mode="md")
                        
                        with tgb.part(class_name="stat-card"):
                            tgb.text("#### Andel män", mode="md")
                            tgb.text("**{year_men_pct}%**", mode="md")
                            tgb.text("{year_men_count:,} män".replace(",", " "), mode="md")
                        
                        with tgb.part(class_name="stat-card"):
                            tgb.text("#### Könsfördelning", mode="md")
                            tgb.text("**{year_gender_ratio}**", mode="md")
                            tgb.text("( kvinnor : män )", mode="md")

                    tgb.text("#### Fördelning av antagna studenter per utbildningsområde i {selected_year}", mode="md")
                    tgb.text(
                        "Diagrammet visar antal kvinnor (orange) och män (blå) som påbörjat studier i varje utbildningsområde.  \n "
                        "Den gråa cirkeln representerar det totala antalet studenter.", 
                        mode="md"
                        )

                    tgb.chart(figure="{student_chart}", type="plotly")
            
                # Add age distribution chart
                    tgb.text(f"#### Åldersfördelning bland antagna studenter i {selected_year}", mode="md")
                    with tgb.layout(columns="1 2"):
                        tgb.text("##### Välj utbildningsområde:", mode="md")
                        tgb.selector(
                            value="{selected_education_area}",
                            lov=education_areas,
                            dropdown=True,
                            on_change=on_education_area_change,
                            class_name="padded-selector"
                        )
                    tgb.text(
                        "Diagrammet visar antal kvinnor (orange) och män (blå) fördelade på åldersgrupper.  \n "
                        "Filtrera per utbildningsområde för att se åldersfördelningen inom specifika områden.", 
                        mode="md"
                    )
                    tgb.chart(figure="{age_chart}", type="plotly")
            
            # Data table 
            #tgb.text("### Rådata över antalet antagna som påbörjat YH-studier", mode="md")
            #with tgb.part(class_name="table-container"):
            #    tgb.table("{df}", width="100%")