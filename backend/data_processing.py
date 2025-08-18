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
    return {
        "national_total_courses": total,
        "national_approved_courses": approved,
        "national_approval_rate_str": rate,
        "national_requested_places": _sum_col_numeric(df, COL_TOTAL_SOKTA),
        "national_approved_places": _sum_col_numeric(df, COL_TOTAL_BEVILJADE_PLATSER),
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
      - Ranking beviljade kursomgångar (primary: Beviljade kurser DESC, tiebreak: Beviljandegrad (kurser) % DESC)
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
        DENSE_RANK() OVER (ORDER BY beviljade_kurser DESC, beviljandegrad_kurser_pct DESC) AS "Ranking beviljade kursomgångar"
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
