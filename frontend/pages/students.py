import logging
import pandas as pd
import plotly.graph_objects as go
from taipy.gui import Gui
import taipy.gui.builder as tgb
import os

# --------- DATA LOADING FUNCTIONS ---------

def load_student_data(file_path):
    """
    Loads student data from a CSV file.
    
    Parameters:
        file_path: Path to the CSV file
        
    Returns:
        tuple: (dataframe, error_status, error_message)
    """
    try:
        # Check if file exists
        if not os.path.isfile(file_path):
            return pd.DataFrame(), True, f"File not found: {file_path}"
        
        # Read CSV file
        df = pd.read_csv(file_path, encoding="latin1")
        
        # Clean column names
        df.columns = df.columns.str.strip()
        logging.info(f"Successfully loaded data with {len(df)} rows")
        
        return df, False, ""
        
    except Exception as e:
        error_msg = f"Error reading CSV: {str(e)}"
        logging.error(error_msg)
        return pd.DataFrame(), True, error_msg

def preprocess_student_data(df):
    """
    Preprocesses the student data for analysis.
    
    Parameters:
        df: Raw dataframe from CSV
        
    Returns:
        DataFrame: Processed dataframe
    """
    if df.empty:
        return df
        
    # Rename columns for consistency
    processed_df = df.copy()
    
    # Check if we have enough columns
    if len(processed_df.columns) >= 7:
        processed_df.columns = ["kön", "utbildningsområde", "ålder", "2020", "2021", "2022", "2023", "2024"]
        
        # Ensure year columns are int
        for col in ["2020", "2021", "2022", "2023", "2024"]:
            if col in processed_df.columns:
                processed_df[col] = pd.to_numeric(processed_df[col], errors="coerce").fillna(0).astype(int)
    
    return processed_df

def get_available_years(df):
    """
    Gets the available years in the dataframe.
    
    Parameters:
        df: Processed dataframe
        
    Returns:
        list: Available years
    """
    if df.empty or len(df.columns) < 4:
        return []
        
    return sorted([col for col in df.columns[3:] if str(col).isdigit()])

# --------- DATA FILTERING FUNCTIONS ---------

def filter_data_by_year(df, year):
    """
    Filters the data for a specific year.
    
    Parameters:
        df: Processed dataframe
        year: Year to filter for
        
    Returns:
        DataFrame: Filtered dataframe in long format with selected year
    """
    if df.empty:
        return pd.DataFrame()
    
    try:
        # Ensure we have a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Melt to long format
        df_long = df_copy.melt(
            id_vars=["kön", "utbildningsområde", "ålder"],
            var_name="år",
            value_name="antal"
        )
        
        # Ensure antal is int
        df_long["antal"] = pd.to_numeric(df_long["antal"], errors="coerce").fillna(0).astype(int)
        
        # Filter for the selected year
        year_str = str(year)
        return df_long[df_long["år"] == year_str]
        
    except Exception as e:
        logging.error(f"Error filtering data: {str(e)}")
        return pd.DataFrame()

def prepare_education_gender_data(df_year, exclude_total=True):
    """
    Prepares data for education area by gender visualization.
    
    Parameters:
        df_year: Filtered dataframe for specific year
        exclude_total: Whether to exclude "totalt" from utbildningsområde
        
    Returns:
        DataFrame: Pivot table with utbildningsområde and gender data
    """
    if df_year.empty:
        return pd.DataFrame()
    
    try:
        # Filter for total age group
        df_filtered = df_year[df_year["ålder"].str.lower() == "totalt"]
        
        # Exclude total education area if requested
        if exclude_total:
            df_filtered = df_filtered[df_filtered["utbildningsområde"].str.lower() != "totalt"]
        
        # Create pivot table
        pivot_df = df_filtered.pivot_table(
            index="utbildningsområde",
            columns="kön",
            values="antal",
            aggfunc="sum"
        ).fillna(0).reset_index()
        
        # Format column names
        pivot_df.columns.name = None
        pivot_df.rename(columns={
            "kvinnor": "Kvinnor",
            "män": "Män",
            "totalt": "Totalt"
        }, inplace=True)
        
        # Ensure columns are integers
        for col in ["Kvinnor", "Män", "Totalt"]:
            if col in pivot_df.columns:
                pivot_df[col] = pd.to_numeric(pivot_df[col], errors="coerce").fillna(0).astype(int)
        
        # Sort by total students
        return pivot_df.sort_values("Totalt")
        
    except Exception as e:
        logging.error(f"Error preparing education gender data: {str(e)}")
        return pd.DataFrame()

# --------- VISUALIZATION FUNCTIONS ---------

def create_education_gender_chart(pivot_df, year):
    """
    Creates a horizontal stacked bar chart for gender distribution by education area.
    
    Parameters:
        pivot_df: Pivot table with utbildningsområde and gender data
        year: Year being displayed
        
    Returns:
        Plotly figure object
    """
    if pivot_df.empty:
        # Return empty figure
        fig = go.Figure()
        fig.update_layout(
            title="Ingen data tillgänglig",
            height=500,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        return fig
    
    try:
        # Create visualization
        fig = go.Figure()
        
        # Add stacked bars
        fig.add_trace(go.Bar(
            x=pivot_df["Kvinnor"],
            y=pivot_df["utbildningsområde"],
            name="Kvinnor",
            orientation="h",
            marker_color="#f59e0b"  # Orange
        ))
        
        fig.add_trace(go.Bar(
            x=pivot_df["Män"],
            y=pivot_df["utbildningsområde"],
            name="Män",
            orientation="h",
            marker_color="#0284c7"  # Blue
        ))
        
        # Add total markers
        fig.add_trace(go.Scatter(
            x=pivot_df["Totalt"],
            y=pivot_df["utbildningsområde"],
            mode="markers",
            name="Totalt",
            marker=dict(color="#4A606C", size=10, symbol="circle"),
            showlegend=True
        ))
        
        # Layout configuration
        fig.update_layout(
            barmode="stack",
            title=f"Antal antagna per utbildningsområde ({year})",
            xaxis_title="Antal studenter",
            yaxis_title="Utbildningsområde",
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=550,
            margin=dict(l=10, r=10, t=50, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom", 
                y=1.02,
                xanchor="center", 
                x=0.5
            )
        )
        
        return fig
        
    except Exception as e:
        logging.error(f"Error creating chart: {str(e)}")
        # Return error figure
        fig = go.Figure()
        fig.update_layout(
            title=f"Fel vid skapande av diagram: {str(e)}",
            height=500,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        return fig

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

# Get file path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
file_path = os.path.join(project_root, "data", "scb", "Antal antagna som påbörjat studier.csv")
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