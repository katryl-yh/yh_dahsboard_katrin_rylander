import pandas as pd
from taipy.gui import Gui
import taipy.gui.builder as tgb
from pathlib import Path
import sys
import logging

logging.basicConfig(level=logging.WARNING)

REQUIRED_COLUMNS = {"Län", "Beslut", "Utbildningsområde"}

DATA_DIRECTORY = Path(__file__).parent / "data" / "resultat_kurser"

def _safe_refresh(state, *var_names):
    # Taipy 4.x: one var per call; guard for API changes
    if hasattr(state, "refresh"):
        for v in var_names:
            try:
                state.refresh(v)
            except Exception:
                logging.warning("refresh(%s) failed: %s", v, e)

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
    except ValueError as e:
        print(f"Error: {e} (sheet='{sheet}')", file=sys.stderr)
        sys.exit(1)
    return df_

# Load data (with error handling)
df = _read_data_or_exit(
    DATA_DIRECTORY / "resultat-2025-for-kurser-inom-yh.xlsx",
    sheet="Lista ansökningar",
)
# Normalize and validate
df["Län"] = df["Län"].astype(str).str.strip()
_validate_df(df, "input Excel")

def get_statistics(df_or_filtered: pd.DataFrame, county: str | None = None, label: str | None = None):
    """
    Return (summary_df, stats_dict).
    - If county is provided: filter df_or_filtered by Län == county (normalized).
    - If county is None: df_or_filtered is assumed pre-filtered (e.g., df_selected_county).
      'label' lets you name the scope (e.g., selected county or 'Sverige').
    """
    _validate_df(df_or_filtered, "get_statistics() input")

    if county is not None:
        sel = str(county).strip()
        scope_df = df_or_filtered[df_or_filtered["Län"].astype(str).str.strip() == sel].copy()
        scope_label = label or sel
    else:
        scope_df = df_or_filtered.copy()
        uniq = scope_df["Län"].dropna().unique().tolist()
        scope_label = label or (uniq[0] if len(uniq) == 1 else "Sverige")

    total_courses = int(len(scope_df))
    approved_courses = int((scope_df["Beslut"] == "Beviljad").sum())
    rejected_courses = int((scope_df["Beslut"] == "Avslag").sum())
    approval_rate = round((approved_courses / total_courses) * 100, 1) if total_courses else 0.0

    stats = {
        "Län": scope_label,
        "Ansökta Kurser": total_courses,
        "Beviljade": approved_courses,
        "Avslag": rejected_courses,
        "Beviljandegrad (%)": approval_rate,
    }

    if scope_df.empty:
        summary = pd.DataFrame(columns=[
            "Utbildningsområde", "Ansökta utbildningar", "Beviljade utbildningar", "Beviljandegrad"
        ])
        return summary, stats

    total_series = (
        scope_df.groupby("Utbildningsområde")
        .size()
        .rename("Ansökta utbildningar")
    )
    approved_series = (
        scope_df[scope_df["Beslut"] == "Beviljad"]
        .groupby("Utbildningsområde")
        .size()
        .rename("Beviljade utbildningar")
    )

    summary = (
        pd.concat([total_series, approved_series], axis=1)
        .fillna(0)
        .reset_index()  # -> ['Utbildningsområde', 'Ansökta utbildningar', 'Beviljade utbildningar']
    )
    summary["Ansökta utbildningar"] = summary["Ansökta utbildningar"].astype(int)
    summary["Beviljade utbildningar"] = summary["Beviljade utbildningar"].astype(int)
    summary["Beviljandegrad"] = (
        (summary["Beviljade utbildningar"] / summary["Ansökta utbildningar"] * 100)
        .fillna(0)
        .round(1)
    )
    summary = summary.sort_values("Ansökta utbildningar", ascending=True)
    return summary, stats

# Normalize county names
df["Län"] = df["Län"].astype(str).str.strip()

# ----- National statistics (static) -----
decisions = df["Beslut"].value_counts()
national_total_courses = int(len(df))
national_approved_courses = int(decisions.get("Beviljad", 0))
national_approval_rate_str = f"{(national_approved_courses / national_total_courses * 100):.1f}%" if national_total_courses else "0%"

# ----- Initial county state (reactive) -----
all_counties = sorted(df["Län"].dropna().unique().tolist())
selected_county = "Stockholm"
df_selected_county = df[df["Län"] == selected_county].copy()
summary, stats = get_statistics(df_selected_county, county=None, label=selected_county)

# Simple, bindable KPI variables (reactive)
total_courses = int(stats["Ansökta Kurser"])
approved_courses = int(stats["Beviljade"])
approval_rate_str = f"{stats['Beviljandegrad (%)']:.1f}%"

def on_county_change(state, var_name=None, var_value=None):
    # Update and validate selection
    if var_name == "selected_county" and var_value is not None:
        state.selected_county = str(var_value).strip()

    county = (state.selected_county or "").strip()
    if not county or county not in state.all_counties:
        # Ignore invalid or no-op selection
        return
    
    try:
        # Filter and compute stats on pre-filtered df; set label explicitly
        state.df_selected_county = state.df[state.df["Län"].astype(str).str.strip() == county].copy()
        state.summary, state.stats = get_statistics(state.df_selected_county, county=None, label=county)
        state.total_courses = int(state.stats["Ansökta Kurser"])
        state.approved_courses = int(state.stats["Beviljade"])
        state.approval_rate_str = f"{state.stats['Beviljandegrad (%)']:.1f}%"
    except Exception as e:
        logging.warning("on_county_change failed for '%s': %s", county, e)
        state.df_selected_county = pd.DataFrame()
        state.summary = pd.DataFrame()
        state.stats = {"Län": county, "Ansökta Kurser": 0, "Beviljade": 0, "Avslag": 0, "Beviljandegrad (%)": 0.0}
        state.total_courses = 0
        state.approved_courses = 0
        state.approval_rate_str = "0.0%"

    # Refresh only reactive vars (national KPIs are static and not refreshed)
    _safe_refresh(
        state,
        "df_selected_county",
        "summary",
        "stats",
        "total_courses",
        "approved_courses",
        "approval_rate_str",
        "selected_county",
    )

# Builder page
with tgb.Page() as page:
    # National stats (static)
    tgb.text("## Statistik för Sverige", mode="md")
    with tgb.layout(columns="1 1 1"):
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Ansökta kurser", mode="md")
            tgb.text("**{national_total_courses}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljade", mode="md")
            tgb.text("**{national_approved_courses}**", mode="md")
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljandegrad", mode="md")
            tgb.text("**{national_approval_rate_str}**", mode="md")

    tgb.text("# Course Applications by County", mode="md")
    tgb.selector(
        "{selected_county}", # Bind with braces
        lov=all_counties,
        dropdown=True,
        on_change=on_county_change,
    )

    # Statistics cards
    with tgb.layout(columns="1 1 1"):
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Ansökta kurser", mode="md")
            tgb.text("**{total_courses}**", mode="md")
            
        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljade", mode="md")
            tgb.text("**{approved_courses}**", mode="md")

        with tgb.part(class_name="stat-card"):
            tgb.text("#### Beviljandegrad", mode="md")
            tgb.text("**{approval_rate_str}**", mode="md")

    # Show current selection
    tgb.text("Valt län: {selected_county}", mode="md")
    tgb.table("{df_selected_county}")

Gui(page).run(
    port=8080,
    dark_mode=False,
    use_reloader=False,
    data={
        "df": df,
        "all_counties": all_counties,
        "selected_county": selected_county,
        "df_selected_county": df_selected_county,
        "summary": summary,
        "stats": stats,
        "total_courses": total_courses,
        "approved_courses": approved_courses,
        "approval_rate_str": approval_rate_str,
        # national (static)
        "national_total_courses": national_total_courses,
        "national_approved_courses": national_approved_courses,
        "national_approval_rate_str": national_approval_rate_str,
    },
)