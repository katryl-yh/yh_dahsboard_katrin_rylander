import logging
import pandas as pd
from taipy.gui import Gui
import taipy.gui.builder as tgb
import os

# Get the absolute path to the data directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
file_path = os.path.join(project_root, "data", "scb", "Antal antagna som påbörjat studier.csv")

# Print the path to help with debugging
print(f"Looking for file at: {file_path}")

# Load data safely
try:
    # Check if file exists
    if not os.path.isfile(file_path):
        logging.error(f"File not found: {file_path}")
        df = pd.DataFrame()
        file_not_found = True
    else:
        # Use the exact same loading approach that worked in your notebook
        df = pd.read_csv(file_path, encoding="latin1")
        file_not_found = False
        
        # Clean column names as in your notebook
        df.columns = df.columns.str.strip()
        logging.info(f"Successfully loaded data with {len(df)} rows")
        
        # Rename columns for consistency (optional)
        if len(df.columns) >= 7:  # Check if we have the expected columns
            df.columns = ["kön", "utbildningsområde", "ålder", "2020", "2021", "2022", "2023", "2024"]
            
            # Ensure year columns are int
            for col in ["2020", "2021", "2022", "2023", "2024"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            
except Exception as e:
    logging.error(f"Error reading CSV: {str(e)}")
    df = pd.DataFrame()
    file_not_found = True

# UI
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
                tgb.text("## SCB Studentdata", mode="md")
                
                # Show warning if file not found
                if file_not_found:
                    with tgb.part(class_name="warning-box"):
                        tgb.text("⚠️ **CSV-filen kunde inte hittas.**", mode="md")
                        tgb.text(f"Sökte efter filen på: {file_path}", mode="md")
                else:
                    tgb.text(f"Visar data för {len(df)} rader med antal antagna som påbörjat studier.", mode="md")
            
            # Data table - only show if we have data
            with tgb.part(class_name="card"):
                if df.empty:
                    tgb.text("Ingen data tillgänglig.", mode="md")
                else:
                    # Basic stats
                    with tgb.layout(columns="1 1 1"):
                        with tgb.part(class_name="stat-card"):
                            tgb.text("#### Antal rader", mode="md")
                            tgb.text(f"**{len(df):,}**", mode="md")
                        with tgb.part(class_name="stat-card"):
                            tgb.text("#### Utbildningsområden", mode="md")
                            tgb.text(f"**{df['utbildningsområde'].nunique():,}**", mode="md")
                        with tgb.part(class_name="stat-card"):
                            tgb.text("#### Åldersgrupper", mode="md")
                            tgb.text(f"**{df['ålder'].nunique():,}**", mode="md")
                    
                    # Add visualization (optional)
                    with tgb.part(class_name="table-container"):
                        tgb.table("{df}", width="100%")