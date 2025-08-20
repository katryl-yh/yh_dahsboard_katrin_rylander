import os
import logging
import sys
from pathlib import Path
from typing import Tuple, Iterable
import json
import numpy as np
import pandas as pd
from difflib import get_close_matches
import duckdb

from utils.constants import (
    DATA_DIRECTORY,
    EXCEL_RESULTS_FILE,
    EXCEL_RESULTS_SHEET,
    EXCEL_APPS_FILE,
    EXCEL_APPS_SHEET,
    COL_LAN, 
    COL_BESLUT, 
    COL_ANORDNARE, 
    COL_EDUCATION_AREA,
    BESLUT_BEVILJAD, 
    BESLUT_AVSLAG,
    COL_TOTAL_SOKTA, 
    COL_TOTAL_BEVILJADE_PLATSER,
    REQUIRED_COLUMNS,
    KEY_COL,
    SOKT_PREFIX,
    COL_TOTAL_SOKTA,
    COL_TOTAL_BEVILJADE_PLATSER,
)

logging.basicConfig(level=logging.WARNING)

def _validate_df(df: pd.DataFrame, where: str = "dataframe"):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {where}: {sorted(missing)}")

def _read_data_or_exit(path: Path, sheet: str) -> pd.DataFrame:
    try:
        df_ = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    except FileNotFoundError:
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"Error: {e}. Try: pip install openpyxl", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e} (sheet='{sheet}')", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error reading Excel: {e}", file=sys.stderr)
        sys.exit(1)
    return df_

def enrich_base_data(
    df_base: pd.DataFrame,
    apps_filename: str = EXCEL_APPS_FILE,
    sheet: str = EXCEL_APPS_SHEET,
    key_col: str = KEY_COL,
    prefix: str = SOKT_PREFIX,
    suffix: str = "",
) -> pd.DataFrame:
    """
    Enrich df_base with columns starting with `prefix` from the applications Excel.
    Reuses _read_data_or_exit and left-joins on `key_col`. Adds COL_TOTAL_SOKTA as a row-wise sum.
    """
    if df_base is None or df_base.empty:
        return df_base

    try:
        apps = _read_data_or_exit(DATA_DIRECTORY / apps_filename, sheet=sheet)
    except SystemExit:
        return df_base

    if key_col not in df_base.columns:
        logging.warning("Base df missing key column '%s'; enrichment skipped.", key_col)
        return df_base
    if key_col not in apps.columns:
        logging.warning("Applications sheet missing key column '%s'; enrichment skipped.", key_col)
        return df_base

    base = df_base.copy()
    base[key_col] = base[key_col].astype(str).str.strip()

    apps = apps.copy()
    apps[key_col] = apps[key_col].astype(str).str.strip()

    wanted = [key_col] + [
        c for c in apps.columns
        if c != key_col and c.strip().casefold().startswith(prefix.casefold())
    ]
    if len(wanted) == 1:
        logging.warning("No columns starting with '%s' found in '%s' (%s).", prefix, apps_filename, sheet)
        return df_base

    apps_sel = apps[wanted].copy()

    # Try full-column numeric conversion (avoid deprecated errors='ignore')
    for c in wanted:
        if c == key_col:
            continue
        try:
            apps_sel[c] = pd.to_numeric(apps_sel[c])
        except (ValueError, TypeError):
            pass

    # Sum all sökta-antal columns into COL_TOTAL_SOKTA
    sum_source_cols = [c for c in apps_sel.columns if c != key_col]
    numeric_block = apps_sel[sum_source_cols].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    apps_sel[COL_TOTAL_SOKTA] = numeric_block.sum(axis=1, min_count=1).fillna(0).astype(int)

    # Deduplicate by key (keep last)
    apps_sel = apps_sel.drop_duplicates(subset=[key_col], keep="last")

    # Optional suffix for name collisions
    incoming_cols = [c for c in apps_sel.columns if c != key_col]
    if suffix:
        rename_map = {c: f"{c}{suffix}" for c in incoming_cols if c in base.columns}
        if rename_map:
            apps_sel = apps_sel.rename(columns=rename_map)
    else:
        collisions = [c for c in incoming_cols if c in base.columns]
        if collisions:
            logging.warning("Incoming columns collide with base: %s. Pandas may suffix duplicate names.", collisions)

    try:
        merged = base.merge(apps_sel, on=key_col, how="left", validate="m:1")
    except Exception as e:
        logging.warning("Validated merge failed: %s. Falling back to plain left join.", e)
        merged = base.merge(apps_sel, on=key_col, how="left")

    return merged

def load_base_df(suffix_for_apps: str = " (ansökningar)") -> pd.DataFrame:
    """Load, normalize, validate, and enrich the base dataset."""
    df = _read_data_or_exit(DATA_DIRECTORY / EXCEL_RESULTS_FILE, sheet=EXCEL_RESULTS_SHEET)
    df["Län"] = df["Län"].astype(str).str.strip()
    _validate_df(df, "input Excel")
    df = enrich_base_data(df, suffix=suffix_for_apps)
    return df

def _sum_col_numeric(d: pd.DataFrame, col: str) -> int:
    if col in d.columns:
        return int(pd.to_numeric(d[col], errors="coerce").sum(skipna=True))
    return 0

def get_statistics(df_or_filtered: pd.DataFrame, county: str | None = None, label: str | None = None) -> Tuple[pd.DataFrame, dict]:
    """
    Return (summary_df, stats_dict).
    - If county is provided: filter df_or_filtered by Län == county (normalized).
    - If county is None: df_or_filtered is assumed pre-filtered (e.g., df_selected_county).
      'label' lets you name the scope (e.g., selected county or 'Sverige').
    """
    _validate_df(df_or_filtered, "get_statistics() input")

    if county is not None:
        sel = str(county).strip()
        scope_df = df_or_filtered[df_or_filtered[COL_LAN].astype(str).str.strip() == sel].copy()
        scope_label = label or sel
    else:
        scope_df = df_or_filtered.copy()
        uniq = scope_df[COL_LAN].dropna().unique().tolist()
        scope_label = label or (uniq[0] if len(uniq) == 1 else "Sverige")

    total_courses = int(len(scope_df))
    approved_courses = int((scope_df[COL_BESLUT] == BESLUT_BEVILJAD).sum())
    rejected_courses = int((scope_df[COL_BESLUT] == BESLUT_AVSLAG).sum())
    approval_rate = round((approved_courses / total_courses) * 100, 1) if total_courses else 0.0

    stats = {
        "Län": scope_label,
        "Ansökta Kurser": total_courses,
        "Beviljade": approved_courses,
        "Avslag": rejected_courses,
        "Beviljandegrad (%)": approval_rate,
        "Ansökta platser": _sum_col_numeric(scope_df, COL_TOTAL_SOKTA),
        "Beviljade platser": _sum_col_numeric(scope_df, COL_TOTAL_BEVILJADE_PLATSER),
    }

    if scope_df.empty:
        summary = pd.DataFrame(columns=[
            "Utbildningsområde", "Ansökta utbildningar", "Beviljade utbildningar", "Beviljandegrad"
        ])
        return summary, stats

    total_series = (
        total_series := (scope_df.groupby(COL_EDUCATION_AREA).size().rename("Ansökta utbildningar"))
    )
    approved_series = (scope_df[scope_df[COL_BESLUT] == BESLUT_BEVILJAD]
                       .groupby(COL_EDUCATION_AREA)
                       .size()
                       .rename("Beviljade utbildningar")
                       )

    summary = (
        pd.concat([total_series, approved_series], axis=1)
        .fillna(0)
        .reset_index()
    )
    summary["Ansökta utbildningar"] = summary["Ansökta utbildningar"].astype(int)
    summary["Beviljade utbildningar"] = summary["Beviljade utbildningar"].astype(int)
    summary["Beviljandegrad"] = (
        (summary["Beviljade utbildningar"] / summary["Ansökta utbildningar"] * 100).fillna(0).round(1)
    )
    summary = summary.sort_values("Ansökta utbildningar", ascending=True)
    return summary, stats

def compute_national_stats(df: pd.DataFrame) -> dict:
    decisions = df[COL_BESLUT].value_counts()
    total = int(len(df))
    approved = int(decisions.get(BESLUT_BEVILJAD, 0))
    rate = f"{(approved / total * 100):.1f}%" if total else "0%"

    requested_places = _sum_col_numeric(df, COL_TOTAL_SOKTA)
    approved_places = _sum_col_numeric(df, COL_TOTAL_BEVILJADE_PLATSER)
    
    # Calculate the places approval rate
    places_rate = (approved_places / requested_places * 100) if requested_places > 0 else 0
    places_rate_str = f"{places_rate:.1f}%"

    return {
        "national_total_courses": total,
        "national_approved_courses": approved,
        "national_approval_rate_str": rate,
        "national_requested_places": requested_places,
        "national_approved_places": approved_places,
        "national_places_approval_rate_str": places_rate_str, 
    }

def aggregate_approved_by_county(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with columns ['Län','Beviljade'] sorted by Beviljade desc, Län asc.
    """
    return (
        df.loc[df[COL_LAN] != "Flera kommuner"]
        .groupby(COL_LAN)[COL_BESLUT]
        .apply(lambda s: (s == BESLUT_BEVILJAD).sum())
        .astype("int64")
        .reset_index(name="Beviljade")
        .sort_values(["Beviljade", COL_LAN], ascending=[False, True])
        .reset_index(drop=True)
)

def load_region_geojson(geojson_path: str | Path) -> dict:
    geojson_path = Path(geojson_path)
    with open(geojson_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_region_code_map(geojson: dict) -> dict[str, str]:
    """
    Maps region 'name' -> länskod from the GeoJSON features.
    """
    features = geojson.get("features", []) or []
    props = [feat.get("properties", {}) for feat in features]
    return {p.get("name"): p.get("ref:se:länskod") for p in props if p.get("name")}

def match_region_codes(
    regions: Iterable[str], code_map: dict[str, str]
) -> list[str | None]:
    """
    Fuzzy-match region names to länskod using difflib.get_close_matches.
    """
    matched: list[str | None] = []
    keys = list(code_map.keys())
    for region in regions:
        hit = get_close_matches(region, keys, n=1)
        matched.append(code_map[hit[0]] if hit else None)
    return matched

def summarize_providers(df: pd.DataFrame, provider_col: str = "Anordnare namn") -> pd.DataFrame:
    """
    Summarize per provider (from enriched df) with rankings:
      - Ranking beviljade platser (primary: Beviljade platser DESC, tiebreak: Beviljandegrad (platser) % DESC)
      - Anordnare namn
      - Beviljade platser
      - Sökta platser
      - Beviljandegrad (platser) %
      - Beviljade kurser
      - Sökta kurser
      - Beviljandegrad (kurser) %
      - Ranking beviljade kurser (primary: Beviljade kurser DESC, tiebreak: Beviljandegrad (kurser) % DESC)
    """
    if provider_col not in df.columns:
        raise ValueError(f"summarize_providers(): missing column '{provider_col}' in df")
    if COL_BESLUT not in df.columns:
        raise ValueError(f"summarize_providers(): missing column '{COL_BESLUT}' in df")

    # Resolve granted-places column
    granted_candidates = [
        "Totalt antal beviljade platser",
        "Beviljade platser totalt",  # in case enrichment already named it like this
        COL_TOTAL_BEVILJADE_PLATSER,  # prefer constant if present
    ]
    granted_col = next((c for c in granted_candidates if c in df.columns), None)
    if not granted_col:
        raise ValueError(
            "summarize_providers(): could not find granted places column. "
            f"Tried: {granted_candidates}"
        )

    # Resolve applied-places expression (prefer enriched total)
    if COL_TOTAL_SOKTA in df.columns:
        applied_expr = f'"{COL_TOTAL_SOKTA}"'
    elif "Sökta platser totalt" in df.columns:
        applied_expr = '"Sökta platser totalt"'
    else:
        year_cols = [c for c in df.columns if c.startswith("Sökt antal platser ")]
        if not year_cols:
            applied_expr = "0"
        else:
            applied_expr = " + ".join([f'COALESCE("{c}", 0)' for c in year_cols])

    q = f"""--sql
    WITH agg AS (
        SELECT
            TRIM("{provider_col}") AS provider,
            SUM(COALESCE("{granted_col}", 0)) AS beviljade_platser,
            SUM({applied_expr}) AS sokta_platser,
            COALESCE(
                ROUND(100.0 * SUM(COALESCE("{granted_col}", 0)) / NULLIF(SUM({applied_expr}), 0), 1),
                0.0
            ) AS beviljandegrad_platser_pct,
            SUM(CASE WHEN "Beslut" = 'Beviljad' THEN 1 ELSE 0 END) AS beviljade_kurser,
            COUNT(*) AS sokta_kurser,
            COALESCE(
                ROUND(100.0 * SUM(CASE WHEN "Beslut" = 'Beviljad' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1),
                0.0
            ) AS beviljandegrad_kurser_pct
        FROM df
        GROUP BY TRIM("{provider_col}")
    )
    SELECT
        DENSE_RANK() OVER (ORDER BY beviljade_platser DESC, beviljandegrad_platser_pct DESC) AS "Ranking beviljade platser",
        provider AS "Anordnare namn",
        beviljade_platser AS "Beviljade platser",
        sokta_platser AS "Sökta platser",
        beviljandegrad_platser_pct AS "Beviljandegrad (platser) %",
        beviljade_kurser AS "Beviljade kurser",
        sokta_kurser AS "Sökta kurser",
        beviljandegrad_kurser_pct AS "Beviljandegrad (kurser) %",
        DENSE_RANK() OVER (ORDER BY beviljade_kurser DESC, beviljandegrad_kurser_pct DESC) AS "Ranking beviljade kurser"
    FROM agg
    ORDER BY "Ranking beviljade platser" ASC, "Anordnare namn" ASC
    """

    con = duckdb.connect()
    try:
        con.register("df", df)
        out = con.execute(q).df()
    finally:
        con.close()

    return out

# --------- DATA LOADING FUNCTIONS STUDENT ---------

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

# --------- DATA PREPARATION FUNCTIONS STUDENTS ---------

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
    
def get_education_areas(df):
    """
    Gets unique education areas from the dataframe.
    
    Parameters:
        df: Student dataframe
        
    Returns:
        list: List of unique education areas
    """
    if df.empty:
        return []
    
    try:
        # Get unique values
        areas = df["utbildningsområde"].unique().tolist()
        # Filter out "totalt" and sort alphabetically
        areas = [area for area in areas if area.lower() != "totalt"]
        areas.sort()
        # Add "Alla områden" at the beginning
        return ["Alla områden"] + areas
    
    except Exception as e:
        logging.error(f"Error getting education areas: {str(e)}")
        return []

# Add this helper function for large ratios
def simplify_large_ratio(a, b, max_terms=10):
    """Simplify a large ratio to a small one with max_terms as the maximum allowed term."""
    if a == 0 or b == 0:
        return (0, 0)
        
    # Ensure a is the larger number
    if a < b:
        a, b = b, a
        swapped = True
    else:
        swapped = False
        
    # Try to find small integers that approximate the ratio
    ratio = a / b
    best_error = float('inf')
    best_pair = (1, 1)
    
    # Try different denominators
    for d in range(1, max_terms + 1):
        n = round(ratio * d)
        if n > max_terms:
            continue
            
        error = abs(ratio - (n / d))
        if error < best_error:
            best_error = error
            best_pair = (n, d)
            
    if swapped:
        return best_pair[1], best_pair[0]
    else:
        return best_pair

def calculate_gender_distribution(df, year=None):
    """
    Calculate gender distribution statistics from student data.
    
    Parameters:
        df: Processed student dataframe
        year: Optional specific year to calculate for (if None, uses all years)
        
    Returns:
        dict: Dictionary with gender statistics
    """
    try:
        # Get yearly data
        yearly_data = prepare_yearly_gender_data(df)
        if yearly_data.empty:
            return {"women_pct": 0, "men_pct": 0, "ratio_simple": "0:0"}
            
        # Filter for specific year if provided
        if year is not None:
            year_str = str(year)
            yearly_data = yearly_data[yearly_data["år"] == year_str]
            
            # Return default values if no data for this year
            if yearly_data.empty:
                return {"women_pct": 0, "men_pct": 0, "ratio_simple": "0:0"}
            
        # Sum across filtered data
        women_total = yearly_data[yearly_data["kön"].str.lower() == "kvinnor"]["antal"].sum()
        men_total = yearly_data[yearly_data["kön"].str.lower() == "män"]["antal"].sum()
        all_students = women_total + men_total
        
        # Calculate percentages
        if all_students > 0:
            women_pct = round((women_total / all_students) * 100, 1)
            men_pct = round((men_total / all_students) * 100, 1)
        else:
            women_pct = men_pct = 0
            
        # Calculate simplified ratio (e.g., 1:3)
        if women_total > 0 and men_total > 0:
            # Method 1: Use percentages to calculate a simple ratio
            # For example, if women:men is 59%:41%, we want to get 3:2
            # Start with the percentages
            if all_students > 0:
                women_pct_value = women_total / all_students
                men_pct_value = men_total / all_students
                
                # Find the simplest representation by testing small integers
                best_ratio = "1:1"  # Default
                best_error = float('inf')
                
                # Try ratios with denominators from 1 to 10
                for denominator in range(1, 11):
                    # Calculate numerators
                    women_numerator = round(women_pct_value * denominator)
                    men_numerator = round(men_pct_value * denominator)
                    
                    # Skip if either is zero
                    if women_numerator == 0 or men_numerator == 0:
                        continue
                        
                    # Calculate error from the actual percentages
                    test_women_pct = women_numerator / (women_numerator + men_numerator)
                    test_men_pct = men_numerator / (women_numerator + men_numerator)
                    
                    error = abs(test_women_pct - women_pct_value) + abs(test_men_pct - men_pct_value)
                    
                    # Keep if this is the best approximation so far
                    if error < best_error:
                        best_error = error
                        best_ratio = f"{women_numerator}:{men_numerator}"
                        
                        # If we get a perfect match, stop searching
                        if error < 0.01:
                            break
                
                ratio_simple = best_ratio
            else:
                # Fallback to original GCD method if we can't calculate percentages
                import math
                gcd = math.gcd(int(women_total), int(men_total))
                ratio_women = int(women_total / gcd)
                ratio_men = int(men_total / gcd)
                
                # If the ratio is still too complex, approximate it
                if ratio_women > 10 or ratio_men > 10:
                    ratio_women, ratio_men = simplify_large_ratio(women_total, men_total)
                    
                ratio_simple = f"{ratio_women}:{ratio_men}"
        else:
            ratio_simple = "0:0"
            
        return {
            "women_pct": women_pct,
            "men_pct": men_pct,
            "women_count": int(women_total),
            "men_count": int(men_total),
            "ratio_simple": ratio_simple
        }
        
    except Exception as e:
        logging.error(f"Error calculating gender distribution: {str(e)}")
        return {"women_pct": 0, "men_pct": 0, "ratio_simple": "0:0"}
    
def calculate_year_growth(df, current_year):
    """
    Calculate year-over-year growth in student numbers and return formatted strings.
    
    Parameters:
        df: Processed student dataframe
        current_year: The year to calculate growth for
        
    Returns:
        dict: Growth statistics with pre-formatted display strings
    """
    try:
        # Convert year to string for consistency
        current_year_str = str(current_year)
        
        # Get available years
        available_years = get_available_years(df)
        if len(available_years) < 2:
            return {
                "growth_pct": 0, 
                "growth_count": 0, 
                "is_increase": False, 
                "is_first_year": True,
                "growth_pct_display": "**Basår**",
                "growth_count_display": "Första året i datasetet",
                "growth_class": "neutral-value"
            }
            
        # Find index of current year
        if current_year_str not in available_years:
            return {
                "growth_pct": 0, 
                "growth_count": 0, 
                "is_increase": False, 
                "is_first_year": False,
                "growth_pct_display": "**0%**",
                "growth_count_display": "0 studenter",
                "growth_class": "neutral-value"
            }
            
        year_idx = available_years.index(current_year_str)
        
        # Check if it's the first year
        if year_idx == 0:
            return {
                "growth_pct": 0, 
                "growth_count": 0, 
                "is_increase": False, 
                "is_first_year": True,
                "growth_pct_display": "**0% (basår)**",
                "growth_count_display": "Första året i datasetet",
                "growth_class": "neutral-value"
            }
            
        # Get previous year
        previous_year_str = available_years[year_idx - 1]
            
        # Get total student counts for both years
        yearly_data = prepare_yearly_gender_data(df)
        if yearly_data.empty:
            return {
                "growth_pct": 0, 
                "growth_count": 0, 
                "is_increase": False, 
                "is_first_year": False,
                "growth_pct_display": "**0%**",
                "growth_count_display": "0 studenter",
                "growth_class": "neutral-value"
            }
            
        # Get total for current year
        current_year_data = yearly_data[yearly_data["år"] == current_year_str]
        current_total = current_year_data[current_year_data["kön"].str.lower() == "totalt"]["antal"].sum()
        
        # Get total for previous year
        previous_year_data = yearly_data[yearly_data["år"] == previous_year_str]
        previous_total = previous_year_data[previous_year_data["kön"].str.lower() == "totalt"]["antal"].sum()
        
        # Calculate growth
        if previous_total > 0:
            growth_count = current_total - previous_total
            growth_pct = (growth_count / previous_total) * 100
            is_increase = growth_count > 0
            
            # Format display strings with proper sign
            sign = "+" if is_increase else ""
            growth_pct_display = f"**{sign}{round(growth_pct, 1)}%**"
            growth_count_display = f"{sign}{int(growth_count)} studenter"
            growth_class = "positive-value" if is_increase else "negative-value"
        else:
            growth_count = 0
            growth_pct = 0
            is_increase = False
            growth_pct_display = "**0%**"
            growth_count_display = "0 studenter"
            growth_class = "neutral-value"
            
        return {
            "growth_pct": round(growth_pct, 1),
            "growth_count": int(growth_count),
            "is_increase": is_increase,
            "is_first_year": False,
            "previous_year": previous_year_str,
            "previous_total": int(previous_total),
            "current_total": int(current_total),
            "growth_pct_display": growth_pct_display,
            "growth_count_display": growth_count_display,
            "growth_class": growth_class
        }
        
    except Exception as e:
        logging.error(f"Error calculating year growth: {str(e)}")
        return {
            "growth_pct": 0, 
            "growth_count": 0, 
            "is_increase": False, 
            "is_first_year": False,
            "growth_pct_display": "**0%**",
            "growth_count_display": "0 studenter",
            "growth_class": "neutral-value"
        }