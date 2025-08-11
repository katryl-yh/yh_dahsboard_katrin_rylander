import pandas as pd
from utils.constants import DATA_DIRECTORY

# Load data
df = pd.read_excel(
    DATA_DIRECTORY / "resultat-2025-for-kurser-inom-yh.xlsx",
    sheet_name="Lista ansökningar",
)

def filter_per_county(df, county="Stockholm"):
    """
    Creates a summary DataFrame for a specific county showing education areas,
    total applications, approved applications, and approval rate.
    
    Parameters:
        df: DataFrame with course data
        county: Name of county to analyze (default: "Stockholm")
    
    Returns:
        DataFrame with columns: Utbildningsområde, Ansökta utbildningar, 
        Beviljade utbildningar, Beviljandegrad
    """
    # Get total applications per education area
    total_df = (
        df.query("Län == @county")["Utbildningsområde"]
        .value_counts()
        .reset_index()
        .rename({"count": "Ansökta utbildningar"}, axis=1)
    )
    
    # Get approved applications per education area
    approved_df = (
        df.query("Län == @county and Beslut == 'Beviljad'")["Utbildningsområde"]
        .value_counts()
        .reset_index()
        .rename({"count": "Beviljade utbildningar"}, axis=1)
    )
    
    # Merge total and approved
    result_df = pd.merge(
        total_df, 
        approved_df, 
        on="Utbildningsområde", 
        how="left"
    ).fillna(0)
    
    # Calculate approval rate
    result_df["Beviljandegrad"] = (
        (result_df["Beviljade utbildningar"] / result_df["Ansökta utbildningar"] * 100)
        .round(1)
    )
    
    # Sort by total applications
    result_df = result_df.sort_values("Ansökta utbildningar", ascending=True)
    
    return result_df
