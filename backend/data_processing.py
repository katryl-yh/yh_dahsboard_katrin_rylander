import pandas as pd
from utils.constants import DATA_DIRECTORY

# Load data
df = pd.read_excel(
    DATA_DIRECTORY / "resultat-2025-for-kurser-inom-yh.xlsx",
    sheet_name="Lista ansökningar",
)

def get_county_data(df, county="Stockholm"):
    """
    Creates a summary of county data including:
    1. DataFrame with education area statistics
    2. Dictionary with overall county statistics
    
    Parameters:
        df: DataFrame with course data
        county: Name of county to analyze (default: "Stockholm")
    
    Returns:
        tuple: (DataFrame, dict) where:
        - DataFrame contains: Utbildningsområde, Ansökta utbildningar, 
          Beviljade utbildningar, Beviljandegrad
        - dict contains: county name, total courses, approved, rejected, approval rate
    """
    # Filter for county
    county_df = df.query("Län == @county")
    
    # Calculate overall statistics
    total_courses = int(len(county_df))
    approved_courses = int((county_df['Beslut'] == 'Beviljad').sum())
    rejected_courses = int((county_df['Beslut'] == 'Avslag').sum())
    approval_rate = round((approved_courses / total_courses) * 100, 2) if total_courses > 0 else 0.0

    stats_dict = {
        'Län': county,
        'Ansökta Kurser': total_courses,
        'Beviljade': approved_courses,
        'Avslag': rejected_courses,
        'Beviljandegrad (%)': approval_rate
    }
    
    # Get education area breakdown
    total_df = (
        county_df["Utbildningsområde"]
        .value_counts()
        .reset_index()
        .rename({"count": "Ansökta utbildningar"}, axis=1)
    )
    
    approved_df = (
        county_df[county_df["Beslut"] == 'Beviljad']["Utbildningsområde"]
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
    
    # Calculate approval rate per education area
    result_df["Beviljandegrad"] = (
        (result_df["Beviljade utbildningar"] / result_df["Ansökta utbildningar"] * 100)
        .round(1)
    )
    
    # Sort by total applications
    result_df = result_df.sort_values("Ansökta utbildningar", ascending=True)
    
    return result_df, stats_dict