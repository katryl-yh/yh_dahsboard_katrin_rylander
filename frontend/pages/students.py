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
from frontend.charts import create_education_gender_chart

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
        state.student_chart = create_education_gender_chart(pivot_data, state.selected_year)
    
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
    student_chart = create_education_gender_chart(pivot_data, selected_year)

# --------- UI DEFINITION ---------

with tgb.Page() as students_page:
    with tgb.part(class_name="page-container"):
        with tgb.part(class_name="dashboard-content card stack-large"):
            # Navigation bar
            tgb.navbar([
                ("Home", "/"),
                ("Counties", "/county"),
                ("Providers", "/providers"),
                ("Students", "/students", True)
            ])
            
            # Page title
            with tgb.part(class_name="card"):
                tgb.text("## Antal antagna som påbörjat studier", mode="md")
                
                # Show warning if file not found
                if file_not_found:
                    with tgb.part(class_name="warning-box"):
                        tgb.text("⚠️ **CSV-filen kunde inte hittas.**", mode="md")
                        tgb.text(f"Sökte efter filen på: {file_path}", mode="md")
                        if error_message:
                            tgb.text(f"Felmeddelande: {error_message}", mode="md")
                else:
                    tgb.text(f"Visar data för antagna studenter per utbildningsområde uppdelat på kön.", mode="md")
            
            # Year selector (if data loaded)
            if not file_not_found and available_years:
                with tgb.part(class_name="card"):
                    with tgb.layout(columns="1fr 3fr"):
                        tgb.text("### Välj år:", mode="md")
                        tgb.selector(
                            value="{selected_year}", 
                            lov=available_years,
                            on_change=on_year_change
                        )
            
            # Chart - only show if we have data
            if not file_not_found:
                with tgb.part(class_name="card"):
                    tgb.text("### Fördelning av antagna studenter per utbildningsområde", mode="md")
                    tgb.text(
                        "Diagrammet visar antal kvinnor (orange) och män (blå) som påbörjat studier i varje utbildningsområde. "
                        "Den gråa cirkeln representerar det totala antalet studenter.", 
                        mode="md"
                    )
                    tgb.chart(figure="{student_chart}", type="plotly")
            
            # Data table - only show if we have data
            if not file_not_found:
                with tgb.part(class_name="card"):
                    tgb.text("### Rådata", mode="md")
                    with tgb.part(class_name="table-container"):
                        tgb.table("{df}", width="100%")