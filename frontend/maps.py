from __future__ import annotations

from pathlib import Path
import numpy as np
import plotly.graph_objects as go

from backend.data_processing import (
    aggregate_approved_by_county,
    load_region_geojson,
    build_region_code_map,
    match_region_codes,
)

def _ticks_log_equal(vals: np.ndarray, n: int):
    pos = vals[vals > 0]
    if len(pos) == 0:
        return np.array([0.0]), ["0"]
    lo = np.log1p(pos.min())
    hi = np.log1p(pos.max())
    ticks_log = np.linspace(lo, hi, n)
    labels = np.expm1(ticks_log)
    labels = np.round(labels).astype(int)
    uniq = np.unique(labels)
    return ticks_log[: len(uniq)], [str(v) for v in uniq]

def _ticks_percentiles(vals: np.ndarray, n: int):
    if len(vals) == 0:
        return np.array([0.0]), ["0"]
    qs = np.linspace(0, 100, n)
    qv = np.percentile(vals, qs)
    qv = np.round(qv).astype(int)
    qv = qv[qv > 0]
    qv = np.unique(qv)
    if len(qv) == 0:
        return np.array([0.0]), ["0"]
    ticks_log = np.log1p(qv)
    return ticks_log, [str(v) for v in qv]

def build_sweden_map(
    df,
    geojson_path: str | Path | None = None,
    tick_mode: str = "log_equal",  # "log_equal" | "percentiles"
    n_ticks: int = 6,
    colorbar_side: str = "left",  # "left" | "right"
) -> go.Figure:
    """
    Build a static choropleth map of approved courses per county (län).
    """
    df_regions = aggregate_approved_by_county(df)

    if geojson_path is None:
        geojson_path = Path(__file__).resolve().parents[1] / "assets" / "swedish_regions.geojson"
    geojson = load_region_geojson(geojson_path)
    code_map = build_region_code_map(geojson)
    codes = match_region_codes(df_regions["Län"].tolist(), code_map)

    beviljade = df_regions["Beviljade"].values
    zvals = np.log1p(beviljade)

    if tick_mode == "percentiles":
        tickvals_log, ticktext = _ticks_percentiles(beviljade, n_ticks)
    else:
        tickvals_log, ticktext = _ticks_log_equal(beviljade, n_ticks)

    # Colorbar position
    if colorbar_side == "left":
        cb = dict(x=0.0, xanchor="left", y=0.5, yanchor="middle")
        margins = dict(l=70, r=0, t=50, b=0)
    else:
        cb = dict(x=1.0, xanchor="right", y=0.5, yanchor="middle")
        margins = dict(l=0, r=30, t=50, b=0)

    fig = go.Figure(
        go.Choroplethmap(
            geojson=geojson,
            locations=codes,
            z=zvals,
            featureidkey="properties.ref:se:länskod",
            colorscale="Blues",
            showscale=True,
            colorbar=dict(
                title="Beviljade <br>kurser",
                tickvals=tickvals_log,
                ticktext=ticktext,
                thickness=20,
                len=0.8,
                **cb,
            ),
            customdata=df_regions["Beviljade"],
            text=df_regions["Län"],
            hovertemplate="<b>%{text}</b><br>Beviljade utbildningar: %{customdata}<extra></extra>",
            marker_line_width=0.3,
        )
    )
    fig.update_layout(
        map=dict(style="white-bg", zoom=3.2, center=dict(lat=62.6952, lon=13.9149)),
        width=470,
        height=500,
        margin=margins,
    )
    return fig
