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
)
from utils.constants import PROJECT_ROOT
from frontend.charts import (
    create_education_gender_chart,
    create_yearly_gender_chart,
)
# --------- DATA PREPARATION FUNCTIONS ---------

def prepare_yearly_gender_data(df):
    """
    Prepares data for yearly gender visualization.
    
    Parameters:
        df: Processed student dataframe
        
    Returns:
        DataFrame: Filtered dataframe in long format with year totals
    """
    if df.empty:
        return pd.DataFrame()
    
    try:
        # Melt to long format if not already
        if "år" not in df.columns:
            df_long = df.melt(
                id_vars=["kön", "utbildningsområde", "ålder"],
                var_name="år",
                value_name="antal"
            )
        else:
            df_long = df.copy()
        
        # Filter for total age group and education area
        df_filtered = df_long[
            (df_long["ålder"].str.lower() == "totalt") & 
            (df_long["utbildningsområde"].str.lower() == "totalt")
        ]
        
        return df_filtered
        
    except Exception as e:
        logging.error(f"Error preparing yearly gender data: {str(e)}")
        return pd.DataFrame()
    
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
    
    except Exception as e:
        logging.error(f"Error in year change callback: {str(e)}")
    
    return state

# --------- MAIN CODE ---------

# Get file path using project constants for consistency
file_path = PROJECT_ROOT / "data" / "scb" / "Antal antagna som påbörjat studier.csv"
print(f"Looking for file at: {file_path}")

# Load and process data
raw_df, file_not_found, error_message = load_student_data(file_path)
df = preprocess_student_data(raw_df)

# Get available years and initialize selections
available_years = get_available_years(df)
selected_year = available_years[-1] if available_years else "2024"


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
                        "- män (blå) som påbörjat studier för varje år.  \n"
                        "Den gråa cirkeln representerar det totala antalet studenter per år.", 
                        mode="md"
                    )
                    with tgb.part(class_name="card"):
                        tgb.chart(figure="{yearly_chart}", type="plotly")


                with tgb.layout(columns="2 3"):
                    tgb.text("### Välj år för att få fördjupad statistik:", mode="md")
                    tgb.selector(
                            value="{selected_year}", 
                            lov=available_years,
                            dropdown=True,
                            on_change=on_year_change
                            )
                    
                tgb.text("### Fördelning av antagna studenter per utbildningsområde i {selected_year}", mode="md")
                tgb.text(
                    "Diagrammet visar antal kvinnor (orange) och män (blå) som påbörjat studier i varje utbildningsområde.  \n "
                    "Den gråa cirkeln representerar det totala antalet studenter.", 
                    mode="md"
                    )
                with tgb.part(class_name="card"):
                    tgb.chart(figure="{student_chart}", type="plotly")
            
            # Data table 
            with tgb.part(class_name="card"):
                tgb.text("### Rådata", mode="md")
                with tgb.part(class_name="table-container"):
                    tgb.table("{df}", width="100%")