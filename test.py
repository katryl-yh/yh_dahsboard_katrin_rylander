import pandas as pd
from taipy.gui import Gui
import taipy.gui.builder as tgb
from pathlib import Path

DATA_DIRECTORY = Path(__file__).parent / "data" / "resultat_kurser"

# Load data
df = pd.read_excel(
    DATA_DIRECTORY / "resultat-2025-for-kurser-inom-yh.xlsx",
    sheet_name="Lista ansökningar",
    engine="openpyxl",
)

def get_statistics(df_or_filtered: pd.DataFrame, county: str | None = None):
    """
    Return (summary_df, stats_dict) for a county.
    If `county` is None, df_or_filtered is assumed to be pre-filtered (df_selected_county).

    summary_df columns:
      - 'Utbildningsområde', 'Ansökta utbildningar', 'Beviljade utbildningar', 'Beviljandegrad'
    stats_dict keys:
      - 'Län', 'Ansökta Kurser', 'Beviljade', 'Avslag', 'Beviljandegrad (%)'
    """
    if county is not None:
        county_df = df_or_filtered[df_or_filtered["Län"] == county].copy()
    else:
        county_df = df_or_filtered.copy()
        if not county_df.empty and "Län" in county_df.columns:
            county = str(county_df["Län"].mode().iat[0])
        else:
            county = "Okänd"

    total_courses = int(len(county_df))
    approved_courses = int((county_df["Beslut"] == "Beviljad").sum())
    rejected_courses = int((county_df["Beslut"] == "Avslag").sum())
    approval_rate = round((approved_courses / total_courses) * 100, 1) if total_courses else 0.0

    stats = {
        "Län": county,
        "Ansökta Kurser": total_courses,
        "Beviljade": approved_courses,
        "Avslag": rejected_courses,
        "Beviljandegrad (%)": approval_rate,
    }

    if county_df.empty:
        summary = pd.DataFrame(columns=[
            "Utbildningsområde", "Ansökta utbildningar", "Beviljade utbildningar", "Beviljandegrad"
        ])
        return summary, stats

    total_series = (
        county_df.groupby("Utbildningsområde")
        .size()
        .rename("Ansökta utbildningar")
    )
    approved_series = (
        county_df[county_df["Beslut"] == "Beviljad"]
        .groupby("Utbildningsområde")
        .size()
        .rename("Beviljade utbildningar")
    )

    summary = (
        pd.concat([total_series, approved_series], axis=1)
        .fillna(0)
        .reset_index()
        .rename(columns={"index": "Utbildningsområde"})
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
summary, stats = get_statistics(df_selected_county, selected_county)

# Simple, bindable KPI variables (reactive)
total_courses = int(stats["Ansökta Kurser"])
approved_courses = int(stats["Beviljade"])
approval_rate_str = f"{stats['Beviljandegrad (%)']:.1f}%"

def on_county_change(state, var_name=None, var_value=None):
    # Update selection
    if var_name == "selected_county" and var_value is not None:
        state.selected_county = str(var_value).strip()
    county = (state.selected_county or "").strip()

    # Recompute filtered df and KPIs (reactive)
    state.df_selected_county = state.df[state.df["Län"].astype(str).str.strip() == county].copy()
    state.summary, state.stats = get_statistics(state.df_selected_county, county)
    # Update bindable KPI scalars
    state.total_courses = int(state.stats["Ansökta Kurser"])
    state.approved_courses = int(state.stats["Beviljade"])
    state.approval_rate_str = f"{state.stats['Beviljandegrad (%)']:.1f}%"

    # Refresh only reactive vars (national KPIs are static and not refreshed)
    # Refresh one var per call 
    state.refresh("df_selected_county")
    state.refresh("total_courses")
    state.refresh("approved_courses")
    state.refresh("approval_rate_str")

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