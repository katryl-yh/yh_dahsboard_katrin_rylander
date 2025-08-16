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
            except Exception as e:
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

def enrich_base_data(
    df_base: pd.DataFrame,
    apps_filename: str = "inkomna-ansokningar-2025-for-kurser.xlsx",
    sheet: str = "Lista ansökningar",
    key_col: str = "Diarienummer",
    prefix: str = "Sökt antal platser",
    suffix: str = "",
) -> pd.DataFrame:
    """
    Enrich df_base with columns starting with `prefix` from the applications Excel.
    Reuses _read_data_or_exit to load the sheet and left-joins on `key_col`.
    Also adds 'Totalt antal sökta platser' as the row-wise sum of all 'Sökt antal platser*' columns.
    """
    if df_base is None or df_base.empty:
        return df_base

    # Read applications sheet (reuses existing robust reader)
    try:
        apps = _read_data_or_exit(DATA_DIRECTORY / apps_filename, sheet=sheet)
    except SystemExit:
        # _read_data_or_exit already logged the error and exited; keep base unchanged if caught
        return df_base

    if key_col not in df_base.columns:
        logging.warning("Base df missing key column '%s'; enrichment skipped.", key_col)
        return df_base
    if key_col not in apps.columns:
        logging.warning("Applications sheet missing key column '%s'; enrichment skipped.", key_col)
        return df_base

    # Normalize key on both sides
    base = df_base.copy()
    base[key_col] = base[key_col].astype(str).str.strip()

    apps = apps.copy()
    apps[key_col] = apps[key_col].astype(str).str.strip()

    # Select key + columns that start with the prefix (case-insensitive, trimmed)
    wanted = [key_col] + [
        c for c in apps.columns
        if c != key_col and c.strip().casefold().startswith(prefix.casefold())
    ]
    if len(wanted) == 1:
        logging.warning("No columns starting with '%s' found in '%s' (%s).", prefix, apps_filename, sheet)
        return df_base

    apps_sel = apps[wanted].copy()

    # Try full-column numeric conversion (no deprecated errors='ignore')
    for c in wanted:
        if c == key_col:
            continue
        try:
            apps_sel[c] = pd.to_numeric(apps_sel[c])
        except (ValueError, TypeError):
            # Leave as-is if non-numeric values present
            pass

    # Compute total sought places across all Sökt-antal columns
    sum_source_cols = [c for c in apps_sel.columns if c != key_col]
    numeric_block = apps_sel[sum_source_cols].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    apps_sel["Totalt antal sökta platser"] = (
        numeric_block.sum(axis=1, min_count=1).fillna(0).astype(int)
    )

    # Deduplicate by key (keep last)
    apps_sel = apps_sel.drop_duplicates(subset=[key_col], keep="last")

    # Avoid name collisions by optional suffix (applies to all incoming columns incl. total)
    incoming_cols = [c for c in apps_sel.columns if c != key_col]
    if suffix:
        rename_map = {c: f"{c}{suffix}" for c in incoming_cols if c in base.columns}
        if rename_map:
            apps_sel = apps_sel.rename(columns=rename_map)
    else:
        collisions = [c for c in incoming_cols if c in base.columns]
        if collisions:
            logging.warning(
                "Incoming columns collide with base: %s. Pandas will suffix duplicate names.",
                collisions,
            )

    # Merge (many-to-one validated)
    try:
        merged = base.merge(apps_sel, on=key_col, how="left", validate="m:1")
    except Exception as e:
        logging.warning("Validated merge failed: %s. Falling back to plain left join.", e)
        merged = base.merge(apps_sel, on=key_col, how="left")

    return merged

# Load data (with error handling)
df = _read_data_or_exit(
    DATA_DIRECTORY / "resultat-2025-for-kurser-inom-yh.xlsx",
    sheet="Lista ansökningar",
)
# Normalize and validate
df["Län"] = df["Län"].astype(str).str.strip()
_validate_df(df, "input Excel")

# Enrich base df with 'Sökt antal platser*' columns once at startup
df = enrich_base_data(df, suffix=" (ansökningar)")

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
    # Only handle the intended variable
    if var_name != "selected_county":
        return

    # Normalize selection; prefer event payload to avoid pre-update ambiguity
    selected = (str(var_value).strip() if var_value is not None else str(state.selected_county or "").strip())
    if not selected:
        return
    if hasattr(state, "all_counties") and selected not in state.all_counties:
        return

    # Persist selection (safe even if Taipy already updated it)
    state.selected_county = selected
    
    try:
        # Recompute filtered data and KPIs
        state.df_selected_county = state.df[state.df["Län"].astype(str).str.strip() == selected].copy()
        state.summary, state.stats = get_statistics(state.df_selected_county, county=None, label=selected)
        state.total_courses = int(state.stats["Ansökta Kurser"])
        state.approved_courses = int(state.stats["Beviljade"])
        state.approval_rate_str = f"{state.stats['Beviljandegrad (%)']:.1f}%"
    except Exception as e:
        logging.warning("on_county_change failed for '%s': %s", selected, e)
        state.df_selected_county = pd.DataFrame()
        state.summary = pd.DataFrame()
        state.stats = {"Län": selected, "Ansökta Kurser": 0, "Beviljade": 0, "Avslag": 0, "Beviljandegrad (%)": 0.0}
        state.total_courses = 0
        state.approved_courses = 0
        state.approval_rate_str = "0.0%"

    # Refresh reactive vars (one per call)
    _safe_refresh(
        state,
        "selected_county",
        "df_selected_county",
        "summary",
        "stats",
        "total_courses",
        "approved_courses",
        "approval_rate_str",
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