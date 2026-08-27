"""Streamlit presentation layer for Open Global Liquidity research."""

from __future__ import annotations

import os
from datetime import timedelta
from importlib import reload
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import dashboard_support as dashboard_support_module  # noqa: E402

reload(dashboard_support_module)
from dashboard_support import (  # noqa: E402
    COMPONENT_LABELS,
    DashboardDataError,
    assess_freshness,
    latest_boj_readings,
    latest_ecb_readings,
    latest_model_readings,
    latest_ogli_readings,
    latest_readings,
    load_bitcoin_contrast_summary,
    load_bitcoin_outcomes,
    load_bitcoin_regime_summary,
    load_bitcoin_revision_summary,
    load_boj_data,
    load_dashboard_data,
    load_ecb_data,
    load_liquidity_model_data,
    load_macro_context,
    load_market_comparisons,
    load_market_correlations,
    load_market_regime_statistics,
    load_market_subperiod_statistics,
    load_ogli_data,
    load_point_in_time_comparison,
    load_point_in_time_market_pairs,
    load_point_in_time_market_summary,
    load_snapshot_manifest,
    resolve_dashboard_data_path,
)

DATA_ROOT = Path(os.environ.get("OGLI_DATA_ROOT", PROJECT_ROOT / "data"))
PROCESSED_DATA_PATH = DATA_ROOT / "processed" / "us_fred_series.parquet"
SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "us_fred_series_snapshot.parquet"
ECB_DATA_PATH = DATA_ROOT / "processed" / "euro_area_ecb_series.parquet"
ECB_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "euro_area_ecb_series_snapshot.parquet"
BOJ_DATA_PATH = DATA_ROOT / "processed" / "japan_boj_series.parquet"
BOJ_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "japan_boj_series_snapshot.parquet"
MODEL_DATA_PATH = DATA_ROOT / "processed" / "us_liquidity_models.parquet"
MODEL_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "us_liquidity_models_snapshot.parquet"
OGLI_DATA_PATH = DATA_ROOT / "processed" / "us_ogli.parquet"
OGLI_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "us_ogli_snapshot.parquet"
MARKET_COMPARISONS_PATH = DATA_ROOT / "processed" / "us_liquidity_market_comparisons.parquet"
MARKET_COMPARISONS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_liquidity_market_comparisons_snapshot.parquet"
)
MARKET_CORRELATIONS_PATH = DATA_ROOT / "processed" / "us_liquidity_market_correlations.parquet"
MARKET_CORRELATIONS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_liquidity_market_correlations_snapshot.parquet"
)
MARKET_REGIMES_PATH = DATA_ROOT / "processed" / "us_liquidity_market_regimes.parquet"
MARKET_REGIMES_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_liquidity_market_regimes_snapshot.parquet"
)
MARKET_SUBPERIODS_PATH = DATA_ROOT / "processed" / "us_liquidity_market_subperiods.parquet"
MARKET_SUBPERIODS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_liquidity_market_subperiods_snapshot.parquet"
)
SNAPSHOT_MANIFEST_PATH = DATA_ROOT / "reference" / "dashboard_snapshot_manifest.json"
MACRO_CONTEXT_PATH = DATA_ROOT / "processed" / "us_macro_context_indicators.parquet"
MACRO_CONTEXT_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_macro_context_indicators_snapshot.parquet"
)
POINT_IN_TIME_COMPARISON_PATH = (
    DATA_ROOT / "vintages" / "fred" / "monthly_pilot" / "us_point_in_time_comparison.parquet"
)
POINT_IN_TIME_COMPARISON_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_point_in_time_comparison_snapshot.parquet"
)
POINT_IN_TIME_MARKET_PAIRS_PATH = (
    DATA_ROOT / "vintages" / "fred" / "monthly_pilot" / "us_point_in_time_market_pairs.parquet"
)
POINT_IN_TIME_MARKET_PAIRS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_point_in_time_market_pairs_snapshot.parquet"
)
POINT_IN_TIME_MARKET_SUMMARY_PATH = (
    DATA_ROOT / "vintages" / "fred" / "monthly_pilot" / "us_point_in_time_market_summary.parquet"
)
POINT_IN_TIME_MARKET_SUMMARY_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_point_in_time_market_summary_snapshot.parquet"
)
BITCOIN_OUTCOMES_PATH = (
    DATA_ROOT / "vintages" / "fred" / "monthly_pilot" / "us_point_in_time_bitcoin_outcomes.parquet"
)
BITCOIN_OUTCOMES_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_point_in_time_bitcoin_outcomes_snapshot.parquet"
)
BITCOIN_REGIMES_PATH = (
    DATA_ROOT / "vintages" / "fred" / "monthly_pilot" / "us_point_in_time_bitcoin_regimes.parquet"
)
BITCOIN_REGIMES_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_point_in_time_bitcoin_regimes_snapshot.parquet"
)
BITCOIN_REVISIONS_PATH = (
    DATA_ROOT / "vintages" / "fred" / "monthly_pilot" / "us_point_in_time_bitcoin_revisions.parquet"
)
BITCOIN_REVISIONS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_point_in_time_bitcoin_revisions_snapshot.parquet"
)
BITCOIN_CONTRASTS_PATH = (
    DATA_ROOT / "vintages" / "fred" / "monthly_pilot" / "us_point_in_time_bitcoin_contrasts.parquet"
)
BITCOIN_CONTRASTS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_point_in_time_bitcoin_contrasts_snapshot.parquet"
)
COMPONENT_ORDER = list(COMPONENT_LABELS)
WINDOW_DAYS = {"1 year": 365, "3 years": 3 * 365, "5 years": 5 * 365}
COLORS = {
    "Fed total assets": "#2563EB",
    "Treasury General Account": "#D97706",
    "ON reverse repo": "#7C3AED",
    "Reserve balances": "#059669",
}
MODEL_COLORS = {
    "Model A — Fed assets": "#2563EB",
    "Model B — Net Fed liquidity proxy": "#D97706",
    "Model C — Reserve-based liquidity": "#059669",
}
CONTRAST_STATUS_LABELS = {
    "insufficient_sample": "Insufficient sample",
    "inconclusive": "Inconclusive",
    "positive_interval": "Positive interval",
    "negative_interval": "Negative interval",
}

st.set_page_config(
    page_title="Open Global Liquidity",
    page_icon=":material/water_drop:",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def _load_data(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache processed data until its file modification timestamp changes."""
    del modified_ns
    return load_dashboard_data(Path(path))


@st.cache_data(show_spinner=False)
def _load_ecb(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache measured ECB data until its file modification timestamp changes."""
    del modified_ns
    return load_ecb_data(Path(path))


@st.cache_data(show_spinner=False)
def _load_boj(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache measured BOJ data until its file modification timestamp changes."""
    del modified_ns
    return load_boj_data(Path(path))


@st.cache_data(show_spinner=False)
def _load_models(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache model data until its file modification timestamp changes."""
    del modified_ns
    return load_liquidity_model_data(Path(path))


@st.cache_data(show_spinner=False)
def _load_ogli(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache calculated OGLI data until its file timestamp changes."""
    del modified_ns
    return load_ogli_data(Path(path))


@st.cache_data(show_spinner=False)
def _load_market_comparisons(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated market comparison pairs."""
    del modified_ns
    return load_market_comparisons(Path(path))


@st.cache_data(show_spinner=False)
def _load_market_correlations(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated market correlation summaries."""
    del modified_ns
    return load_market_correlations(Path(path))


@st.cache_data(show_spinner=False)
def _load_market_regimes(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated regime outcome summaries."""
    del modified_ns
    return load_market_regime_statistics(Path(path))


@st.cache_data(show_spinner=False)
def _load_market_subperiods(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated market subperiod diagnostics."""
    del modified_ns
    return load_market_subperiod_statistics(Path(path))


@st.cache_data(show_spinner=False)
def _load_snapshot_manifest(path: str, modified_ns: int) -> dict[str, object]:
    """Cache snapshot provenance until the manifest changes."""
    del modified_ns
    return load_snapshot_manifest(Path(path))


@st.cache_data(show_spinner=False)
def _load_macro_context(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated measured macro context."""
    del modified_ns
    return load_macro_context(Path(path))


@st.cache_data(show_spinner=False)
def _load_point_in_time_comparison(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated monthly vintage comparisons."""
    del modified_ns
    return load_point_in_time_comparison(Path(path))


@st.cache_data(show_spinner=False)
def _load_point_in_time_market_pairs(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated vintage signal/outcome pairs."""
    del modified_ns
    return load_point_in_time_market_pairs(Path(path))


@st.cache_data(show_spinner=False)
def _load_point_in_time_market_summary(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated vintage market summaries."""
    del modified_ns
    return load_point_in_time_market_summary(Path(path))


@st.cache_data(show_spinner=False)
def _load_bitcoin_outcomes(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated Bitcoin forward paths and vintage diagnostics."""
    del modified_ns
    return load_bitcoin_outcomes(Path(path))


@st.cache_data(show_spinner=False)
def _load_bitcoin_regimes(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated Bitcoin regime and transition summaries."""
    del modified_ns
    return load_bitcoin_regime_summary(Path(path))


@st.cache_data(show_spinner=False)
def _load_bitcoin_revisions(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated Bitcoin signal-revision summaries."""
    del modified_ns
    return load_bitcoin_revision_summary(Path(path))


@st.cache_data(show_spinner=False)
def _load_bitcoin_contrasts(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache package-calculated directional Bitcoin regime contrasts."""
    del modified_ns
    return load_bitcoin_contrast_summary(Path(path))


def _source_data() -> tuple[pd.DataFrame, Path, str]:
    data_path, data_origin = resolve_dashboard_data_path(PROCESSED_DATA_PATH, SNAPSHOT_DATA_PATH)
    return _load_data(str(data_path), data_path.stat().st_mtime_ns), data_path, data_origin


def _ecb_data() -> tuple[pd.DataFrame, Path, str]:
    path, origin = resolve_dashboard_data_path(ECB_DATA_PATH, ECB_SNAPSHOT_DATA_PATH)
    return _load_ecb(str(path), path.stat().st_mtime_ns), path, origin


def _boj_data() -> tuple[pd.DataFrame, Path, str]:
    path, origin = resolve_dashboard_data_path(BOJ_DATA_PATH, BOJ_SNAPSHOT_DATA_PATH)
    return _load_boj(str(path), path.stat().st_mtime_ns), path, origin


def _model_data() -> tuple[pd.DataFrame, str] | None:
    try:
        model_path, model_origin = resolve_dashboard_data_path(
            MODEL_DATA_PATH, MODEL_SNAPSHOT_DATA_PATH
        )
    except DashboardDataError:
        return None
    models = _load_models(str(model_path), model_path.stat().st_mtime_ns)
    return models, model_origin


def _ogli_data() -> tuple[pd.DataFrame, str]:
    ogli_path, ogli_origin = resolve_dashboard_data_path(OGLI_DATA_PATH, OGLI_SNAPSHOT_DATA_PATH)
    return _load_ogli(str(ogli_path), ogli_path.stat().st_mtime_ns), ogli_origin


def _market_data() -> tuple[pd.DataFrame | None, pd.DataFrame, str]:
    correlation_path, correlation_origin = resolve_dashboard_data_path(
        MARKET_CORRELATIONS_PATH, MARKET_CORRELATIONS_SNAPSHOT_PATH
    )
    correlations = _load_market_correlations(
        str(correlation_path), correlation_path.stat().st_mtime_ns
    )
    try:
        comparison_path, comparison_origin = resolve_dashboard_data_path(
            MARKET_COMPARISONS_PATH, MARKET_COMPARISONS_SNAPSHOT_PATH
        )
    except DashboardDataError:
        return None, correlations, correlation_origin
    comparisons = _load_market_comparisons(str(comparison_path), comparison_path.stat().st_mtime_ns)
    return comparisons, correlations, comparison_origin


def _market_regime_data() -> pd.DataFrame | None:
    try:
        path, _origin = resolve_dashboard_data_path(
            MARKET_REGIMES_PATH, MARKET_REGIMES_SNAPSHOT_PATH
        )
    except DashboardDataError:
        return None
    return _load_market_regimes(str(path), path.stat().st_mtime_ns)


def _market_subperiod_data() -> pd.DataFrame | None:
    try:
        path, _origin = resolve_dashboard_data_path(
            MARKET_SUBPERIODS_PATH, MARKET_SUBPERIODS_SNAPSHOT_PATH
        )
    except DashboardDataError:
        return None
    return _load_market_subperiods(str(path), path.stat().st_mtime_ns)


def _snapshot_provenance() -> dict[str, object] | None:
    if not SNAPSHOT_MANIFEST_PATH.is_file():
        return None
    try:
        return _load_snapshot_manifest(
            str(SNAPSHOT_MANIFEST_PATH), SNAPSHOT_MANIFEST_PATH.stat().st_mtime_ns
        )
    except DashboardDataError:
        return None


def _macro_context_data() -> pd.DataFrame | None:
    try:
        path, _origin = resolve_dashboard_data_path(MACRO_CONTEXT_PATH, MACRO_CONTEXT_SNAPSHOT_PATH)
    except DashboardDataError:
        return None
    return _load_macro_context(str(path), path.stat().st_mtime_ns)


def _point_in_time_data() -> tuple[pd.DataFrame, str] | None:
    try:
        path, origin = resolve_dashboard_data_path(
            POINT_IN_TIME_COMPARISON_PATH,
            POINT_IN_TIME_COMPARISON_SNAPSHOT_PATH,
        )
    except DashboardDataError:
        return None
    return _load_point_in_time_comparison(str(path), path.stat().st_mtime_ns), origin


def _point_in_time_market_data() -> tuple[pd.DataFrame, pd.DataFrame, str] | None:
    try:
        pairs_path, pairs_origin = resolve_dashboard_data_path(
            POINT_IN_TIME_MARKET_PAIRS_PATH,
            POINT_IN_TIME_MARKET_PAIRS_SNAPSHOT_PATH,
        )
        summary_path, _summary_origin = resolve_dashboard_data_path(
            POINT_IN_TIME_MARKET_SUMMARY_PATH,
            POINT_IN_TIME_MARKET_SUMMARY_SNAPSHOT_PATH,
        )
    except DashboardDataError:
        return None
    pairs = _load_point_in_time_market_pairs(str(pairs_path), pairs_path.stat().st_mtime_ns)
    summary = _load_point_in_time_market_summary(str(summary_path), summary_path.stat().st_mtime_ns)
    return pairs, summary, pairs_origin


def _bitcoin_research_data() -> (
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str] | None
):
    try:
        outcomes_path, origin = resolve_dashboard_data_path(
            BITCOIN_OUTCOMES_PATH,
            BITCOIN_OUTCOMES_SNAPSHOT_PATH,
        )
        regimes_path, _ = resolve_dashboard_data_path(
            BITCOIN_REGIMES_PATH,
            BITCOIN_REGIMES_SNAPSHOT_PATH,
        )
        revisions_path, _ = resolve_dashboard_data_path(
            BITCOIN_REVISIONS_PATH,
            BITCOIN_REVISIONS_SNAPSHOT_PATH,
        )
        contrasts_path, _ = resolve_dashboard_data_path(
            BITCOIN_CONTRASTS_PATH,
            BITCOIN_CONTRASTS_SNAPSHOT_PATH,
        )
    except DashboardDataError:
        return None
    outcomes = _load_bitcoin_outcomes(str(outcomes_path), outcomes_path.stat().st_mtime_ns)
    regimes = _load_bitcoin_regimes(str(regimes_path), regimes_path.stat().st_mtime_ns)
    revisions = _load_bitcoin_revisions(str(revisions_path), revisions_path.stat().st_mtime_ns)
    contrasts = _load_bitcoin_contrasts(str(contrasts_path), contrasts_path.stat().st_mtime_ns)
    return outcomes, regimes, revisions, contrasts, origin


def _show_freshness(frame: pd.DataFrame, label: str, *, max_age_days: int = 14) -> None:
    status = assess_freshness(frame, max_age_days=max_age_days)
    message = (
        f"{label} latest observation: {status.latest_date:%Y-%m-%d} ({status.age_days} days old)."
    )
    if status.is_stale:
        st.warning(
            message
            + f" Expected maximum age is {status.max_age_days} days; check the refresh workflow.",
            icon=":material/update_disabled:",
        )
    else:
        st.caption(message)


def _format_billions(value: float) -> str:
    return f"${value:,.1f}bn"


def _history_figure(frame: pd.DataFrame, title: str):
    figure = px.line(
        frame,
        x="date",
        y="value_usd_billions",
        color="label",
        color_discrete_map=COLORS,
        labels={"date": "", "value_usd_billions": "USD billions", "label": "Series"},
        title=title,
    )
    figure.update_traces(line={"width": 2})
    figure.update_layout(
        hovermode="x unified",
        legend_title_text="",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"gridcolor": "rgba(128,128,128,0.18)", "tickprefix": "$", "ticksuffix": "bn"},
    )
    return figure


def _model_figure(frame: pd.DataFrame, title: str):
    figure = px.line(
        frame,
        x="date",
        y="value_usd_billions",
        color="model_name",
        color_discrete_map=MODEL_COLORS,
        labels={"date": "", "value_usd_billions": "USD billions", "model_name": "Model"},
        title=title,
    )
    figure.update_traces(line={"width": 2})
    figure.update_layout(
        hovermode="x unified",
        legend_title_text="",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"gridcolor": "rgba(128,128,128,0.18)", "tickprefix": "$", "ticksuffix": "bn"},
    )
    return figure


def _ogli_figure(frame: pd.DataFrame, title: str):
    figure = px.line(
        frame,
        x="date",
        y="ogli",
        labels={"date": "", "ogli": "OGLI (0-100)"},
        title=title,
    )
    figure.update_traces(line={"width": 2.5, "color": "#2563EB"})
    for threshold in [10, 30, 45, 55, 70, 90]:
        figure.add_hline(
            y=threshold,
            line_width=1,
            line_dash="dot",
            line_color="rgba(128,128,128,0.3)",
        )
    figure.update_layout(
        hovermode="x unified",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"range": [0, 100], "gridcolor": "rgba(128,128,128,0.12)"},
        showlegend=False,
    )
    return figure


def _market_scatter_figure(frame: pd.DataFrame, title: str):
    figure = px.scatter(
        frame,
        x="liquidity_signal",
        y="market_return",
        hover_data={"date": "|%Y-%m-%d", "ogli": ":.1f"},
        labels={
            "liquidity_signal": "OGLI momentum score",
            "market_return": "Bitcoin return",
        },
        title=title,
    )
    figure.update_traces(marker={"size": 7, "opacity": 0.65, "color": "#2563EB"})
    figure.update_layout(
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"zeroline": True, "gridcolor": "rgba(128,128,128,0.15)"},
        yaxis={
            "zeroline": True,
            "gridcolor": "rgba(128,128,128,0.15)",
            "tickformat": ".0%",
        },
    )
    return figure


def _ogli_bitcoin_overlay_figure(frame: pd.DataFrame, title: str):
    """Plot package-calculated OGLI beside Bitcoin prices without altering either series."""
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["value"],
            name="Bitcoin price",
            line={"color": "#D97706", "width": 2.25},
            hovertemplate="$%{y:,.0f}<extra>Bitcoin</extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["ogli"],
            name="OGLI",
            line={"color": "#2563EB", "width": 2.25},
            hovertemplate="%{y:.1f}<extra>OGLI</extra>",
        ),
        secondary_y=True,
    )
    figure.update_layout(
        title=title,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
        margin={"l": 10, "r": 10, "t": 75, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
    )
    figure.update_yaxes(
        title_text="Bitcoin price (USD, log scale)",
        type="log",
        tickprefix="$",
        gridcolor="rgba(128,128,128,0.15)",
        secondary_y=False,
    )
    figure.update_yaxes(
        title_text="OGLI (0-100)",
        range=[0, 100],
        gridcolor="rgba(128,128,128,0.10)",
        secondary_y=True,
    )
    return figure


def _rolling_correlation_figure(frame: pd.DataFrame, title: str):
    figure = px.line(
        frame,
        x="date",
        y="rolling_correlation",
        labels={"date": "", "rolling_correlation": "Trailing correlation"},
        title=title,
    )
    figure.update_traces(line={"width": 2.25, "color": "#7C3AED"})
    figure.add_hline(y=0, line_width=1, line_color="rgba(128,128,128,0.5)")
    figure.update_layout(
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"range": [-1, 1], "gridcolor": "rgba(128,128,128,0.15)"},
        showlegend=False,
    )
    return figure


def _horizon_correlation_figure(frame: pd.DataFrame, title: str):
    chart = frame.copy()
    chart["horizon_label"] = chart["horizon_weeks"].map(
        lambda value: "0 (1w current)" if value == 0 else f"{value}w forward"
    )
    figure = go.Figure(
        go.Bar(
            x=chart["horizon_label"],
            y=chart["correlation"],
            text=chart["correlation"].map(lambda value: "—" if pd.isna(value) else f"{value:+.2f}"),
            textposition="outside",
            marker_color="#D97706",
            error_y={
                "type": "data",
                "symmetric": False,
                "array": chart["bootstrap_ci_upper"] - chart["correlation"],
                "arrayminus": chart["correlation"] - chart["bootstrap_ci_lower"],
            },
            hovertemplate="%{x}<br>Correlation: %{y:+.2f}<extra></extra>",
        )
    )
    figure.add_hline(y=0, line_width=1, line_color="rgba(128,128,128,0.5)")
    figure.update_layout(
        title=title,
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"range": [-1, 1], "gridcolor": "rgba(128,128,128,0.15)"},
    )
    return figure


def _subperiod_correlation_figure(frame: pd.DataFrame, title: str):
    figure = go.Figure(
        go.Bar(
            x=frame["period_label"],
            y=frame["correlation"],
            marker_color="#059669",
            text=frame["correlation"].map(lambda value: "—" if pd.isna(value) else f"{value:+.2f}"),
            textposition="outside",
            error_y={
                "type": "data",
                "symmetric": False,
                "array": frame["bootstrap_ci_upper"] - frame["correlation"],
                "arrayminus": frame["correlation"] - frame["bootstrap_ci_lower"],
            },
            customdata=frame[["observations", "period_start", "period_end"]],
            hovertemplate=(
                "%{x}<br>Correlation: %{y:+.2f}<br>Observations: %{customdata[0]:,}"
                "<br>Period: %{customdata[1]|%Y-%m-%d} to %{customdata[2]|%Y-%m-%d}<extra></extra>"
            ),
        )
    )
    figure.add_hline(y=0, line_width=1, line_color="rgba(128,128,128,0.5)")
    figure.update_layout(
        title=title,
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={
            "range": [-1, 1],
            "title": "Pearson correlation",
            "gridcolor": "rgba(128,128,128,0.15)",
        },
        xaxis={"title": "Predeclared research period"},
    )
    return figure


def _regime_return_figure(frame: pd.DataFrame, title: str):
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=frame["regime"],
            y=frame["median_return"],
            name="Median return",
            marker_color="#2563EB",
            hovertemplate="%{x}<br>Median: %{y:.1%}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["regime"],
            y=frame["mean_return"],
            mode="markers",
            name="Mean return",
            marker={"color": "#D97706", "size": 10},
            error_y={
                "type": "data",
                "symmetric": False,
                "array": frame["mean_ci_upper"] - frame["mean_return"],
                "arrayminus": frame["mean_return"] - frame["mean_ci_lower"],
            },
            hovertemplate="%{x}<br>Mean: %{y:.1%}<extra></extra>",
        )
    )
    figure.add_hline(y=0, line_width=1, line_color="rgba(128,128,128,0.5)")
    figure.update_layout(
        title=title,
        barmode="group",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"tickformat": ".0%", "title": "Bitcoin return"},
        xaxis={"title": "OGLI regime at signal observation"},
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    return figure


def _macro_context_figure(frame: pd.DataFrame, title: str):
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["treasury_yield_10y"],
            name="10-year yield",
            line={"color": "#2563EB", "width": 2},
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["treasury_yield_2y"],
            name="2-year yield",
            line={"color": "#7C3AED", "width": 2},
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=frame["date"],
            y=frame["broad_usd_index"],
            name="Broad USD index",
            line={"color": "#D97706", "width": 2},
        ),
        secondary_y=True,
    )
    figure.update_yaxes(title_text="Treasury yield (%)", secondary_y=False)
    figure.update_yaxes(title_text="Broad USD index (Jan 2006=100)", secondary_y=True)
    figure.update_layout(
        title=title,
        hovermode="x unified",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    return figure


def _load_or_explain() -> tuple[pd.DataFrame, Path, str] | None:
    try:
        return _source_data()
    except DashboardDataError as exc:
        st.error(str(exc), icon=":material/error:")
        st.code(
            "uv run python -m open_global_liquidity.pipeline --start 2020-01-01",
            language="zsh",
        )
        return None


def landing_page() -> None:
    st.badge("Independent public-data research · v0.2a pilot", icon=":material/science:")
    st.title("See the financial system through a liquidity lens")
    st.markdown(
        """
        **Global liquidity is the ease with which financing can be created, obtained, and moved
        through the financial system.** It reflects more than central-bank money: bank balance
        sheets, credit creation, collateral, funding markets, and cross-border finance all matter.

        Open Global Liquidity turns public data into transparent, reproducible indicators. The
        current OGLI remains deliberately **United States only**. A separate euro-area measured-
        data pilot begins the international expansion without currency conversion or aggregation.
        """
    )

    loaded = _load_or_explain()
    if loaded is not None:
        data, _data_path, data_origin = loaded
        latest = latest_readings(data).set_index("component")
        try:
            model_bundle = _model_data()
        except DashboardDataError:
            model_bundle = None
        models = model_bundle[0] if model_bundle is not None else None
        latest_models = (
            latest_model_readings(models).set_index("model_id") if models is not None else None
        )

        st.subheader("Latest US liquidity snapshot")
        with st.container(horizontal=True):
            if latest_models is not None and "model_b" in latest_models.index:
                row = latest_models.loc["model_b"]
                delta = row["change_usd_billions"]
                st.metric(
                    "Net Fed liquidity proxy",
                    _format_billions(float(row["value_usd_billions"])),
                    None if pd.isna(delta) else f"{delta:+,.1f}bn weekly",
                    border=True,
                    chart_data=models.loc[models["model_id"] == "model_b", "value_usd_billions"]
                    .tail(26)
                    .tolist(),
                )
            for component in ["fed_assets", "reserve_balances", "treasury_general_account"]:
                if component not in latest.index:
                    continue
                row = latest.loc[component]
                delta = row["change_usd_billions"]
                st.metric(
                    str(row["label"]),
                    _format_billions(float(row["value_usd_billions"])),
                    None if pd.isna(delta) else f"{delta:+,.1f}bn prior observation",
                    border=True,
                    chart_data=data.loc[data["component"] == component, "value_usd_billions"].tail(
                        26
                    ),
                )
        latest_date = data["date"].max()
        st.caption(
            f"Latest source date {latest_date:%Y-%m-%d} · {data_origin} · Nominal USD balances"
        )
        _show_freshness(data, "US liquidity data")
        provenance = _snapshot_provenance()
        if provenance is not None:
            generated_at = pd.to_datetime(provenance["generated_at"], utc=True)
            source_commit = str(provenance["source_commit"])
            source_label = source_commit[:8]
            if provenance["working_tree_dirty"] is True:
                source_label += " + local changes"
            st.caption(
                f"Public snapshot generated {generated_at:%Y-%m-%d %H:%M UTC} · "
                f"code source `{source_label}` · "
                f"{int(provenance['snapshot_count'])} files recorded with SHA-256 hashes"
            )

        try:
            comparisons, _correlations, market_origin = _market_data()
            ogli_data, _ogli_origin = _ogli_data()
        except DashboardDataError:
            comparisons = None
            ogli_data = pd.DataFrame()
            market_origin = "Unavailable"

        if comparisons is not None:
            current_btc = comparisons.loc[
                (comparisons["model_id"] == "model_b")
                & (comparisons["market_id"] == "bitcoin")
                & (comparisons["horizon_weeks"] == 0)
            ].dropna(subset=["market_return"])
            latest_ogli = ogli_data.loc[
                (ogli_data["model_id"] == "model_b") & ogli_data["ogli"].notna()
            ]
            if not current_btc.empty and not latest_ogli.empty:
                btc_row = current_btc.iloc[-1]
                ogli_row = latest_ogli.iloc[-1]
                st.subheader("Current Bitcoin and liquidity snapshot")
                with st.container(horizontal=True):
                    bitcoin_price = btc_row.get("value")
                    if pd.notna(bitcoin_price):
                        st.metric(
                            "Bitcoin price",
                            f"${float(bitcoin_price):,.0f}",
                            f"{btc_row['market_return']:+.1%} weekly",
                            border=True,
                        )
                    st.metric(
                        "OGLI · Model B",
                        f"{ogli_row['ogli']:.1f}",
                        str(ogli_row["regime"]),
                        border=True,
                    )
                    st.metric(
                        "Research status",
                        "Point-in-time",
                        "Primary specification predeclared",
                        border=True,
                    )
                st.caption(
                    f"Bitcoin data through {btc_row['date']:%Y-%m-%d} · {market_origin} · "
                    "Market outcomes are never inputs to OGLI."
                )

        try:
            bitcoin_research = _bitcoin_research_data()
        except DashboardDataError:
            bitcoin_research = None
        if bitcoin_research is not None:
            _outcomes, regime_summaries, _revisions, contrast_summaries, research_origin = (
                bitcoin_research
            )
            primary = regime_summaries.loc[
                (regime_summaries["specification_role"] == "primary")
                & (regime_summaries["analysis_dimension"] == "overall")
            ].sort_values("horizon_months")
            primary_contrasts = contrast_summaries.loc[
                contrast_summaries["specification_role"] == "primary"
            ].sort_values("horizon_months")
            if not primary.empty and not primary_contrasts.empty:
                st.subheader("Primary point-in-time Bitcoin study")
                st.badge(
                    "Model B · 1-week availability delay · non-overlapping outcomes",
                    icon=":material/check_circle:",
                    color="blue",
                )
                st.markdown("**OGLI directional contrast**")
                with st.container(horizontal=True):
                    for row in primary_contrasts.itertuples(index=False):
                        horizon_label = (
                            f"{row.horizon_months}-month" if row.horizon_months != 1 else "1-month"
                        )
                        interval = (
                            f"Welch 95% interval: {row.spread_ci_lower:.1%} to "
                            f"{row.spread_ci_upper:.1%}."
                            if pd.notna(row.spread_ci_lower)
                            else (
                                "Welch interval unavailable because a group has fewer than two "
                                "observations."
                            )
                        )
                        st.metric(
                            f"{horizon_label} return spread",
                            f"{row.mean_return_spread:+.1%}",
                            (
                                f"n={row.expansionary_observations} expansionary · "
                                f"n={row.contractionary_observations} contractionary"
                            ),
                            border=True,
                            help=(
                                "Expansionary-regime mean minus contractionary-regime mean. "
                                f"Expansionary: {row.expansionary_mean_return:.1%}; "
                                f"contractionary: {row.contractionary_mean_return:.1%}. {interval}"
                            ),
                        )
                st.caption(
                    "A positive spread means subsequent Bitcoin returns were higher on average "
                    "after expansionary point-in-time OGLI regimes than after contractionary "
                    "regimes. Neutral observations are excluded. This is descriptive association, "
                    "not evidence of causation or a forecast."
                )
                primary_statuses = set(primary_contrasts["interval_status"])
                if primary_statuses.issubset({"inconclusive", "insufficient_sample"}):
                    st.info(
                        "Current evidence status: inconclusive at every estimable horizon; "
                        "the 12-month contrast has insufficient group observations for an "
                        "interval.",
                        icon=":material/info:",
                    )
                with st.expander("Unconditional Bitcoin outcome baseline"):
                    st.caption(
                        "These figures describe all completed Bitcoin outcomes in the primary "
                        "sample, without conditioning on OGLI. They are context—not evidence that "
                        "the liquidity signal adds information."
                    )
                    with st.container(horizontal=True):
                        for row in primary.itertuples(index=False):
                            horizon_label = (
                                f"{row.horizon_months}-month"
                                if row.horizon_months != 1
                                else "1-month"
                            )
                            st.metric(
                                f"{horizon_label} BTC outcome",
                                f"{row.mean_return:.1%} mean",
                                f"{row.positive_share:.0%} positive · n={row.observations}",
                                border=True,
                            )
                st.caption(
                    f"Data mode: {research_origin}. The primary designation is a transparent "
                    "Open Global Liquidity model assumption, selected for interpretability—not "
                    "calibrated to maximize Bitcoin returns or correlation. Alternative models, "
                    "lags, and overlapping samples remain available as robustness checks."
                )
                smallest_group = primary_contrasts[
                    ["expansionary_observations", "contractionary_observations"]
                ].min(axis=1)
                if smallest_group.min() < 8:
                    sparse = primary_contrasts.loc[smallest_group.idxmin()]
                    sparse_group_size = int(
                        min(
                            sparse["expansionary_observations"],
                            sparse["contractionary_observations"],
                        )
                    )
                    observation_label = "observation" if sparse_group_size == 1 else "observations"
                    st.warning(
                        f"The {int(sparse['horizon_months'])}-month primary estimate currently "
                        "contains only "
                        f"{sparse_group_size} "
                        f"{observation_label} in its smaller directional group. "
                        "Treat its magnitude and sign as especially fragile.",
                        icon=":material/science:",
                    )
                st.page_link(
                    bitcoin_page,
                    label="Open the full Bitcoin research workspace",
                    icon=":material/currency_bitcoin:",
                )

    st.subheader("A practical way to think about global liquidity")
    concept_columns = st.columns(3)
    with concept_columns[0].container(border=True, height="stretch"):
        st.markdown("#### :material/account_balance: Monetary base")
        st.write(
            "Central-bank assets and reserve balances establish the official-money foundation "
            "on which financial institutions settle and expand balance sheets."
        )
    with concept_columns[1].container(border=True, height="stretch"):
        st.markdown("#### :material/credit_score: Credit capacity")
        st.write(
            "Banks and market-based lenders multiply financing through loans, securities, repo, "
            "and other forms of leverage."
        )
    with concept_columns[2].container(border=True, height="stretch"):
        st.markdown("#### :material/hub: Market transmission")
        st.write(
            "Collateral quality, volatility, funding costs, and cross-border channels influence "
            "how easily liquidity reaches markets and borrowers."
        )

    st.subheader("Why use a liquidity framework?")
    benefit_columns = st.columns(3)
    with benefit_columns[0]:
        st.markdown("**Track the direction of financing conditions**")
        st.caption(
            "Levels and momentum can provide context for whether balance-sheet capacity is "
            "expanding or contracting."
        )
    with benefit_columns[1]:
        st.markdown("**Compare competing definitions**")
        st.caption(
            "No single series captures liquidity. Showing alternatives makes model uncertainty "
            "visible instead of hiding it."
        )
    with benefit_columns[2]:
        st.markdown("**Audit every transformation**")
        st.caption(
            "Series IDs, units, alignment rules, source dates, and model weights remain explicit "
            "and reproducible."
        )

    st.warning(
        "Liquidity is not directly observable, and correlation with asset prices does not imply "
        "causation. This project is a research tool—not a market-timing signal or investment "
        "advice.",
        icon=":material/warning:",
    )
    with st.container(horizontal=True):
        st.page_link(data_page, label="Explore the data", icon=":material/monitoring:")
        st.page_link(guide_page, label="Read the research guide", icon=":material/menu_book:")


def data_dashboard_page() -> None:
    st.title("US liquidity dashboard")
    st.caption(
        "Measured balance-sheet data and three transparent model assumptions. This is not OGLI "
        "and does not reproduce CrossBorder Capital's proprietary GLI."
    )
    loaded = _load_or_explain()
    if loaded is None:
        return
    data, data_path, data_origin = loaded
    _show_freshness(data, "US liquidity data")
    try:
        model_bundle = _model_data()
        model_error = None
    except DashboardDataError as exc:
        model_bundle = None
        model_error = str(exc)
    if model_bundle is None:
        models = None
        model_origin = None
    else:
        models, model_origin = model_bundle

    latest = latest_readings(data).set_index("component")
    last_retrieved = pd.to_datetime(data["retrieved_at"].max(), utc=True)
    with st.sidebar:
        st.header("View controls")
        window = st.segmented_control(
            "History", ["1 year", "3 years", "5 years", "All"], default="5 years"
        )
        selected_label = st.selectbox(
            "Component explorer",
            [COMPONENT_LABELS[item] for item in COMPONENT_ORDER if item in set(data["component"])],
        )
        st.caption(f"Data mode: {data_origin}")
        st.caption(f"Retrieved {last_retrieved:%Y-%m-%d %H:%M UTC}")
        st.caption("Source: FRED and the named originating Federal Reserve releases.")

    max_date = data["date"].max()
    if window == "All":
        visible = data
    else:
        visible = data.loc[data["date"] >= max_date - timedelta(days=WINDOW_DAYS[str(window)])]

    overview_tab, models_tab, explorer_tab, data_tab = st.tabs(
        ["Measured data", "Liquidity models", "Component explorer", "Latest observations"]
    )
    with overview_tab:
        st.subheader("Latest measured balances")
        with st.container(horizontal=True):
            for component in COMPONENT_ORDER:
                if component not in latest.index:
                    st.metric(COMPONENT_LABELS[component], "Unavailable", border=True)
                    continue
                row = latest.loc[component]
                change = row["change_usd_billions"]
                st.metric(
                    str(row["label"]),
                    _format_billions(float(row["value_usd_billions"])),
                    None if pd.isna(change) else f"{change:+,.1f}bn vs prior observation",
                    border=True,
                )
        st.plotly_chart(
            _history_figure(visible, f"US liquidity-related balance-sheet series · {window}"),
            width="stretch",
            config={"displaylogo": False},
        )
        st.caption(
            "These charts show measured source series. USD-billions conversion is a display "
            "transformation, not an economic weighting."
        )

    with models_tab:
        st.subheader("Three competing US liquidity definitions")
        if model_error:
            st.error(model_error)
        elif models is None:
            st.info("Run the local pipeline to generate the liquidity-model dataset.")
            st.code(
                "uv run python -m open_global_liquidity.pipeline --start 2020-01-01",
                language="zsh",
            )
        else:
            latest_models = latest_model_readings(models).set_index("model_id")
            with st.container(horizontal=True):
                for model_id in ["model_a", "model_b", "model_c"]:
                    if model_id not in latest_models.index:
                        continue
                    row = latest_models.loc[model_id]
                    change = row["change_usd_billions"]
                    st.metric(
                        str(row["model_name"]),
                        _format_billions(float(row["value_usd_billions"])),
                        None if pd.isna(change) else f"{change:+,.1f}bn vs prior week",
                        border=True,
                    )
            model_max_date = models["date"].max()
            if window == "All":
                visible_models = models
            else:
                visible_models = models.loc[
                    models["date"] >= model_max_date - timedelta(days=WINDOW_DAYS[str(window)])
                ]
            st.plotly_chart(
                _model_figure(visible_models, f"US liquidity model levels · {window}"),
                width="stretch",
                config={"displaylogo": False},
            )
            st.warning(
                "These are configurable Open Global Liquidity assumptions. Model B is a common "
                "public-market proxy; none is CrossBorder Capital's proprietary formula."
            )
            st.caption(f"Model data mode: {model_origin}")

    with explorer_tab:
        selected_component = next(
            component for component, label in COMPONENT_LABELS.items() if label == selected_label
        )
        component_data = visible.loc[visible["component"] == selected_component]
        st.plotly_chart(
            _history_figure(component_data, selected_label),
            width="stretch",
            config={"displaylogo": False},
        )
        source_row = data.loc[data["component"] == selected_component].iloc[-1]
        source_columns = st.columns(2)
        source_columns[0].markdown(f"**FRED series:** `{source_row['series_id']}`")
        source_columns[0].markdown(f"**Source unit:** {source_row['unit']}")
        source_columns[1].markdown(f"**Frequency:** {source_row['frequency']}")
        source_columns[1].markdown(f"**Latest observation:** {source_row['date']:%Y-%m-%d}")

    with data_tab:
        st.subheader("Most recent source observations")
        table = (
            data.sort_values("date")
            .groupby("component", as_index=False)
            .tail(10)[["date", "label", "series_id", "value", "unit", "frequency"]]
            .sort_values(["label", "date"], ascending=[True, False])
        )
        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
            column_config={"date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")},
        )
        try:
            displayed_path = data_path.relative_to(PROJECT_ROOT)
        except ValueError:
            displayed_path = data_path
        st.caption(f"Displayed file: `{displayed_path}`")


def ogli_page() -> None:
    st.title("OGLI momentum index")
    st.caption(
        "Experimental 0-100 normalization of US liquidity momentum. Independent Open Global "
        "Liquidity methodology—not CrossBorder Capital's proprietary GLI."
    )
    try:
        data, data_origin = _ogli_data()
        latest_by_model = latest_ogli_readings(data)
    except DashboardDataError as exc:
        st.error(str(exc), icon=":material/error:")
        st.code(
            "uv run python -m open_global_liquidity.pipeline --start 2020-01-01",
            language="zsh",
        )
        return

    model_options = dict(
        latest_by_model[["model_name", "model_id"]].itertuples(index=False, name=None)
    )
    with st.sidebar:
        st.header("OGLI controls")
        selected_name = st.selectbox(
            "Liquidity definition",
            list(model_options),
            index=list(model_options).index("Model B — Net Fed liquidity proxy"),
        )
        history = st.segmented_control(
            "History", ["1 year", "3 years", "All"], default="3 years", key="ogli_history"
        )
        st.caption(f"Data mode: {data_origin}")

    model_id = model_options[selected_name]
    model_data = data.loc[(data["model_id"] == model_id) & data["ogli"].notna()].copy()
    latest = model_data.iloc[-1]
    if history == "All":
        visible = model_data
    else:
        visible = model_data.loc[
            model_data["date"]
            >= model_data["date"].max() - timedelta(days=WINDOW_DAYS[str(history)])
        ]

    with st.container(horizontal=True):
        st.metric(
            "Latest OGLI",
            f"{latest['ogli']:.1f}",
            border=True,
            chart_data=model_data["ogli"].tail(26).tolist(),
        )
        st.metric("Liquidity regime", str(latest["regime"]), border=True)
        st.metric(
            "Momentum score", f"{latest['momentum_score']:+.2f} standard deviations", border=True
        )
        st.metric(
            "3m annualized growth",
            f"{latest['growth_3m_annualized']:.1%}",
            border=True,
        )
        st.metric("12m YoY growth", f"{latest['growth_12m_yoy']:.1%}", border=True)

    st.plotly_chart(
        _ogli_figure(visible, f"{selected_name} · OGLI history"),
        width="stretch",
        config={"displaylogo": False},
    )
    st.caption(
        f"Latest reading {latest['date']:%Y-%m-%d} · "
        f"{latest['zscore_mode']} z-score · minimum {latest['zscore_min_periods']} observations"
    )

    with st.container(border=True):
        st.subheader("How to read OGLI")
        st.markdown(
            """
            OGLI measures how unusual current liquidity momentum is relative to historical
            observations. It uses z-score normalization and the standard normal cumulative
            distribution function. It is not normalized against the historical maximum, so new
            liquidity highs do not mechanically rescale the entire historical index.

            **Around 50 is statistically neutral.** Higher readings indicate momentum above its
            historical norm; lower readings indicate momentum below its historical norm. This is
            a relative momentum measure, not the dollar level of liquidity and not a forecast.
            """
        )

    with st.expander("Formula, weights, and regimes"):
        st.code(
            "Momentum = 0.60 * z(3m annualized growth) + 0.40 * z(12m YoY growth)\n"
            "OGLI = 100 * Phi(Momentum)",
            language=None,
        )
        st.write(
            "The 60/40 weights and regime thresholds are configurable Open Global Liquidity "
            "research assumptions. They are not calibrated parameters and are not Howell or "
            "CrossBorder Capital parameters."
        )
        st.dataframe(
            pd.DataFrame(
                {
                    "OGLI range": [
                        "0-10",
                        ">10-30",
                        ">30-45",
                        ">45-55",
                        ">55-70",
                        ">70-90",
                        ">90-100",
                    ],
                    "Regime": [
                        "Strong contraction",
                        "Contraction",
                        "Below normal",
                        "Neutral",
                        "Above normal",
                        "Expansion",
                        "Strong expansion",
                    ],
                }
            ),
            hide_index=True,
        )


def bitcoin_research_page() -> None:
    st.title("Bitcoin research")
    st.caption(
        "Point-in-time OGLI regimes, transitions, and subsequent Bitcoin paths. Outcomes are "
        "retrospective diagnostics—not forecasts, trading signals, or OGLI calibration targets."
    )
    try:
        loaded = _bitcoin_research_data()
    except DashboardDataError as exc:
        st.error(str(exc), icon=":material/error:")
        return
    if loaded is None:
        st.info(
            "Bitcoin research outputs have not been generated in this environment. The existing "
            "FRED key is sufficient and Coin Metrics Community Data requires no key.",
            icon=":material/currency_bitcoin:",
        )
        st.code("uv run ogli-point-in-time --publish-dashboard-snapshot", language="zsh")
        return
    outcomes, regime_summaries, revision_summaries, contrast_summaries, data_origin = loaded

    primary_rows = regime_summaries.loc[
        (regime_summaries["specification_role"] == "primary")
        & (regime_summaries["analysis_dimension"] == "overall")
    ]
    primary_model_id = str(primary_rows["model_id"].iloc[0])
    primary_lag = int(primary_rows["publication_lag_weeks"].iloc[0])
    primary_horizons = sorted(primary_rows["horizon_months"].unique())
    primary_sample_label = (
        "Non-overlapping"
        if primary_rows["sample_policy"].iloc[0] == "non_overlapping"
        else "Overlapping"
    )
    st.badge(
        "Primary: Model B · 1-week delay · non-overlapping · 1/3/6/12 months",
        icon=":material/check_circle:",
        color="blue",
    )
    st.caption(
        "This primary display policy is a predeclared model assumption. Change any control to "
        "inspect robustness alternatives; no Bitcoin outcome was used to calculate OGLI."
    )

    model_options = dict(
        outcomes[["model_name", "model_id"]].drop_duplicates().itertuples(index=False)
    )
    default_name = "Model B — Net Fed liquidity proxy"
    default_name = next(
        name
        for name, configured_model_id in model_options.items()
        if configured_model_id == primary_model_id
    )
    with st.sidebar:
        st.header("Bitcoin research controls")
        selected_name = st.selectbox(
            "Liquidity definition",
            list(model_options),
            index=list(model_options).index(default_name),
            key="bitcoin_model",
        )
        horizon = st.selectbox(
            "Forward horizon",
            sorted(outcomes["horizon_months"].unique()),
            index=sorted(outcomes["horizon_months"].unique()).index(
                3 if 3 in primary_horizons else primary_horizons[0]
            ),
            format_func=lambda value: f"{value} month{'s' if value != 1 else ''}",
            key="bitcoin_horizon",
        )
        publication_lag = st.selectbox(
            "Assumed availability delay",
            sorted(outcomes["publication_lag_weeks"].unique()),
            index=sorted(outcomes["publication_lag_weeks"].unique()).index(primary_lag),
            format_func=lambda value: f"{value} week{'s' if value != 1 else ''}",
            key="bitcoin_lag",
        )
        sample_policy = st.segmented_control(
            "Sample",
            ["Non-overlapping", "Overlapping"],
            default=primary_sample_label,
            key="bitcoin_sample",
        )
        st.caption(f"Data mode: {data_origin}")

    view = st.segmented_control(
        "Research view",
        [
            "Regime contrast",
            "Across horizons",
            "Regimes",
            "Transitions",
            "Path outcomes",
            "Signal revisions",
        ],
        default="Regime contrast",
        key="bitcoin_view",
    )
    model_id = model_options[selected_name]
    sample_key = "non_overlapping" if sample_policy == "Non-overlapping" else "overlapping"
    selected_is_primary = (
        model_id == primary_model_id
        and publication_lag == primary_lag
        and sample_key == str(primary_rows["sample_policy"].iloc[0])
        and horizon in primary_horizons
    )
    st.badge(
        "Selected controls: Primary specification"
        if selected_is_primary
        else "Selected controls: Robustness check",
        icon=":material/check_circle:" if selected_is_primary else ":material/science:",
        color="green" if selected_is_primary else "gray",
    )
    selected = outcomes.loc[
        (outcomes["model_id"] == model_id)
        & (outcomes["horizon_months"] == horizon)
        & (outcomes["publication_lag_weeks"] == publication_lag)
    ].copy()
    if sample_key == "non_overlapping":
        selected = selected.loc[selected["is_non_overlapping"]].copy()
    if selected.empty:
        st.warning("The selected Bitcoin research sample contains no complete outcomes.")
        return

    selected_contrast = contrast_summaries.loc[
        (contrast_summaries["model_id"] == model_id)
        & (contrast_summaries["horizon_months"] == horizon)
        & (contrast_summaries["publication_lag_weeks"] == publication_lag)
        & (contrast_summaries["sample_policy"] == sample_key)
    ]
    if view == "Regime contrast" and not selected_contrast.empty:
        contrast_row = selected_contrast.iloc[0]
        with st.container(horizontal=True):
            st.metric(
                "Expansionary minus contractionary",
                f"{contrast_row['mean_return_spread']:+.1%}",
                border=True,
            )
            st.metric(
                "Expansionary mean",
                f"{contrast_row['expansionary_mean_return']:.1%}",
                f"n={int(contrast_row['expansionary_observations'])}",
                border=True,
            )
            st.metric(
                "Contractionary mean",
                f"{contrast_row['contractionary_mean_return']:.1%}",
                f"n={int(contrast_row['contractionary_observations'])}",
                border=True,
            )
            interval_value = (
                f"{contrast_row['spread_ci_lower']:.1%} to {contrast_row['spread_ci_upper']:.1%}"
                if pd.notna(contrast_row["spread_ci_lower"])
                else "Unavailable"
            )
            st.metric("Welch 95% interval", interval_value, border=True)
            st.metric(
                "Interval reading",
                CONTRAST_STATUS_LABELS[str(contrast_row["interval_status"])],
                border=True,
            )
    else:
        with st.container(horizontal=True):
            st.metric("Observations", f"{len(selected):,}", border=True)
            st.metric("Mean forward return", f"{selected['market_return'].mean():.1%}", border=True)
            st.metric(
                "Positive outcomes", f"{selected['market_return'].gt(0).mean():.0%}", border=True
            )
            st.metric(
                "Average maximum drawdown",
                f"{selected['maximum_drawdown_from_peak'].mean():.1%}",
                border=True,
            )
            st.metric(
                "Average maximum upside",
                f"{selected['maximum_upside_from_start'].mean():.1%}",
                border=True,
            )

    if view == "Regime contrast":
        contrast_history = contrast_summaries.loc[
            (contrast_summaries["model_id"] == model_id)
            & (contrast_summaries["publication_lag_weeks"] == publication_lag)
            & (contrast_summaries["sample_policy"] == sample_key)
        ].copy()
        contrast_history["ci_error_plus"] = (
            contrast_history["spread_ci_upper"] - contrast_history["mean_return_spread"]
        )
        contrast_history["ci_error_minus"] = (
            contrast_history["mean_return_spread"] - contrast_history["spread_ci_lower"]
        )
        contrast_history["interval_reading"] = contrast_history["interval_status"].map(
            CONTRAST_STATUS_LABELS
        )
        contrast_figure = px.line(
            contrast_history,
            x="horizon_months",
            y="mean_return_spread",
            markers=True,
            error_y="ci_error_plus",
            error_y_minus="ci_error_minus",
            title="Expansionary minus contractionary Bitcoin return",
            labels={
                "horizon_months": "Forward horizon (months)",
                "mean_return_spread": "Mean Bitcoin return spread",
            },
        )
        contrast_figure.add_hline(y=0, line_color="#6B7280", line_width=1)
        contrast_figure.update_xaxes(dtick=1)
        contrast_figure.update_yaxes(tickformat=".0%")
        st.plotly_chart(contrast_figure, width="stretch", config={"displaylogo": False})
        st.dataframe(
            contrast_history[
                [
                    "horizon_months",
                    "expansionary_observations",
                    "contractionary_observations",
                    "expansionary_mean_return",
                    "contractionary_mean_return",
                    "mean_return_spread",
                    "spread_ci_lower",
                    "spread_ci_upper",
                    "interval_reading",
                ]
            ],
            width="stretch",
            hide_index=True,
            column_config={
                "horizon_months": st.column_config.NumberColumn("Horizon (months)", format="%d"),
                "expansionary_observations": st.column_config.NumberColumn(
                    "Expansionary n", format="%d"
                ),
                "contractionary_observations": st.column_config.NumberColumn(
                    "Contractionary n", format="%d"
                ),
                "expansionary_mean_return": st.column_config.NumberColumn(
                    "Expansionary mean", format="percent"
                ),
                "contractionary_mean_return": st.column_config.NumberColumn(
                    "Contractionary mean", format="percent"
                ),
                "mean_return_spread": st.column_config.NumberColumn(
                    "Mean spread", format="percent"
                ),
                "spread_ci_lower": st.column_config.NumberColumn("95% CI lower", format="percent"),
                "spread_ci_upper": st.column_config.NumberColumn("95% CI upper", format="percent"),
                "interval_reading": st.column_config.TextColumn("Interval reading"),
            },
        )
        st.caption(
            "Expansionary regimes are Above normal, Expansion, and Strong expansion. "
            "Contractionary regimes are Below normal, Contraction, and Strong contraction. "
            "Neutral observations are excluded. Error bars are classical Welch intervals and "
            "do not adjust for serial dependence, multiple comparisons, or data revisions."
        )

    elif view == "Across horizons":
        horizon_summary = regime_summaries.loc[
            (regime_summaries["model_id"] == model_id)
            & (regime_summaries["publication_lag_weeks"] == publication_lag)
            & (regime_summaries["sample_policy"] == sample_key)
            & (regime_summaries["analysis_dimension"] == "overall")
        ].copy()
        horizon_summary["ci_error_plus"] = (
            horizon_summary["mean_return_ci_upper"] - horizon_summary["mean_return"]
        )
        horizon_summary["ci_error_minus"] = (
            horizon_summary["mean_return"] - horizon_summary["mean_return_ci_lower"]
        )
        horizon_figure = px.line(
            horizon_summary,
            x="horizon_months",
            y="mean_return",
            markers=True,
            text="observations",
            error_y="ci_error_plus",
            error_y_minus="ci_error_minus",
            title="Bitcoin outcomes across forward horizons",
            labels={
                "horizon_months": "Forward horizon (months)",
                "mean_return": "Mean Bitcoin return",
                "observations": "Observations",
            },
        )
        horizon_figure.update_traces(
            texttemplate="n=%{text}",
            textposition="top center",
            hovertemplate=(
                "%{x} months<br>Mean return: %{y:.1%}<br>Observations: %{text}<extra></extra>"
            ),
        )
        horizon_figure.update_xaxes(dtick=1)
        horizon_figure.update_yaxes(tickformat=".0%", zeroline=True)
        st.plotly_chart(horizon_figure, width="stretch", config={"displaylogo": False})
        st.dataframe(
            horizon_summary[
                [
                    "horizon_months",
                    "observations",
                    "mean_return",
                    "median_return",
                    "positive_share",
                    "mean_return_ci_lower",
                    "mean_return_ci_upper",
                    "mean_maximum_drawdown",
                ]
            ],
            width="stretch",
            hide_index=True,
            column_config={
                "horizon_months": st.column_config.NumberColumn("Horizon (months)", format="%d"),
                "observations": st.column_config.NumberColumn("n", format="%d"),
                "mean_return": st.column_config.NumberColumn("Mean return", format="percent"),
                "median_return": st.column_config.NumberColumn("Median return", format="percent"),
                "positive_share": st.column_config.NumberColumn("Positive share", format="percent"),
                "mean_return_ci_lower": st.column_config.NumberColumn(
                    "95% CI lower", format="percent"
                ),
                "mean_return_ci_upper": st.column_config.NumberColumn(
                    "95% CI upper", format="percent"
                ),
                "mean_maximum_drawdown": st.column_config.NumberColumn(
                    "Avg. max drawdown", format="percent"
                ),
            },
        )
        st.caption(
            "Each point uses the same model, availability delay, and sample policy. Longer "
            "non-overlapping horizons naturally contain fewer independent observations. Error "
            "bars are descriptive Student-t intervals, not forecasts."
        )

    elif view in {"Regimes", "Transitions"}:
        dimension = "vintage_regime" if view == "Regimes" else "transition_direction"
        summary = regime_summaries.loc[
            (regime_summaries["model_id"] == model_id)
            & (regime_summaries["horizon_months"] == horizon)
            & (regime_summaries["publication_lag_weeks"] == publication_lag)
            & (regime_summaries["sample_policy"] == sample_key)
            & (regime_summaries["analysis_dimension"] == dimension)
        ].copy()
        minimum_display = 3
        summary = summary.loc[summary["observations"] >= minimum_display]
        if summary.empty:
            st.info(
                "No group has at least three observations under this selection. Choose the "
                "overlapping sample or a shorter horizon.",
                icon=":material/data_alert:",
            )
        else:
            chart_title = (
                "Bitcoin forward return by point-in-time OGLI regime"
                if view == "Regimes"
                else "Bitcoin forward return after OGLI regime transitions"
            )
            summary["ci_error_plus"] = summary["mean_return_ci_upper"] - summary["mean_return"]
            summary["ci_error_minus"] = summary["mean_return"] - summary["mean_return_ci_lower"]
            figure = px.bar(
                summary,
                x="group_label",
                y="mean_return",
                color="positive_share",
                text="observations",
                error_y="ci_error_plus",
                error_y_minus="ci_error_minus",
                color_continuous_scale="RdYlGn",
                range_color=[0, 1],
                title=chart_title,
                labels={
                    "group_label": "OGLI regime" if view == "Regimes" else "Transition",
                    "mean_return": f"Mean {horizon}-month Bitcoin return",
                    "positive_share": "Positive share",
                    "observations": "Observations",
                },
            )
            figure.update_traces(
                texttemplate="n=%{text}",
                hovertemplate=(
                    "%{x}<br>Mean return: %{y:.1%}<br>Observations: %{text}<extra></extra>"
                ),
            )
            figure.update_yaxes(tickformat=".0%", zeroline=True)
            st.plotly_chart(figure, width="stretch", config={"displaylogo": False})
            st.dataframe(
                summary[
                    [
                        "group_label",
                        "observations",
                        "mean_return",
                        "median_return",
                        "positive_share",
                        "mean_return_ci_lower",
                        "mean_return_ci_upper",
                        "mean_maximum_upside",
                        "mean_maximum_downside",
                        "mean_maximum_drawdown",
                    ]
                ],
                width="stretch",
                hide_index=True,
                column_config={
                    "group_label": st.column_config.TextColumn("Group", pinned=True),
                    "observations": st.column_config.NumberColumn("n", format="%d"),
                    "mean_return": st.column_config.NumberColumn("Mean return", format="percent"),
                    "median_return": st.column_config.NumberColumn(
                        "Median return", format="percent"
                    ),
                    "positive_share": st.column_config.NumberColumn(
                        "Positive share", format="percent"
                    ),
                    "mean_return_ci_lower": st.column_config.NumberColumn(
                        "95% CI lower", format="percent"
                    ),
                    "mean_return_ci_upper": st.column_config.NumberColumn(
                        "95% CI upper", format="percent"
                    ),
                    "mean_maximum_upside": st.column_config.NumberColumn(
                        "Avg. max upside", format="percent"
                    ),
                    "mean_maximum_downside": st.column_config.NumberColumn(
                        "Avg. downside", format="percent"
                    ),
                    "mean_maximum_drawdown": st.column_config.NumberColumn(
                        "Avg. max drawdown", format="percent"
                    ),
                },
            )
            st.caption(
                "Error bars are classical 95% Student-t intervals around the arithmetic mean. "
                "They are descriptive, not forecast intervals; overlapping outcomes can make "
                "them too narrow."
            )

    elif view == "Path outcomes":
        path_figure = px.scatter(
            selected,
            x="maximum_drawdown_from_peak",
            y="maximum_upside_from_start",
            color="vintage_regime",
            size="vintage_ogli",
            hover_data={
                "information_date": "|%Y-%m-%d",
                "market_return": ":.1%",
                "maximum_downside_from_start": ":.1%",
                "vintage_ogli": ":.1f",
            },
            title=(
                f"Bitcoin path outcomes over the next {horizon} month{'s' if horizon != 1 else ''}"
            ),
            labels={
                "maximum_drawdown_from_peak": "Maximum peak-to-trough drawdown",
                "maximum_upside_from_start": "Maximum upside from starting price",
                "vintage_regime": "Point-in-time OGLI regime",
                "vintage_ogli": "Point-in-time OGLI",
            },
        )
        path_figure.update_xaxes(tickformat=".0%")
        path_figure.update_yaxes(tickformat=".0%")
        st.plotly_chart(path_figure, width="stretch", config={"displaylogo": False})
        st.caption(
            "Maximum drawdown is the worst peak-to-trough loss inside the outcome window. "
            "Maximum downside is measured separately from the starting Bitcoin price."
        )

    else:
        revision = revision_summaries.loc[
            (revision_summaries["model_id"] == model_id)
            & (revision_summaries["horizon_months"] == horizon)
            & (revision_summaries["publication_lag_weeks"] == publication_lag)
            & (revision_summaries["sample_policy"] == sample_key)
        ]
        if revision.empty:
            st.info("No signal-revision summary is available for this selection.")
        else:
            row = revision.iloc[0]
            correlations = pd.DataFrame(
                {
                    "Signal version": ["As known then", "Recomputed today"],
                    "Correlation": [
                        row["vintage_signal_correlation"],
                        row["current_vintage_signal_correlation"],
                    ],
                }
            ).dropna()
            with st.container(horizontal=True):
                st.metric(
                    "Point-in-time correlation",
                    (
                        "Insufficient sample"
                        if pd.isna(row["vintage_signal_correlation"])
                        else f"{row['vintage_signal_correlation']:+.2f}"
                    ),
                    border=True,
                )
                st.metric(
                    "Recomputed correlation",
                    (
                        "Insufficient sample"
                        if pd.isna(row["current_vintage_signal_correlation"])
                        else f"{row['current_vintage_signal_correlation']:+.2f}"
                    ),
                    border=True,
                )
                st.metric("Regime agreement", f"{row['regime_agreement_share']:.0%}", border=True)
                st.metric(
                    "Mean absolute momentum revision",
                    f"{row['mean_absolute_momentum_revision']:.3f}",
                    border=True,
                )
            if not correlations.empty:
                revision_figure = px.bar(
                    correlations,
                    x="Signal version",
                    y="Correlation",
                    text_auto=".2f",
                    title="Same Bitcoin outcomes, different data-vintage signal",
                )
                revision_figure.add_hline(y=0, line_color="#6B7280", line_width=1)
                revision_figure.update_traces(marker_color=["#2563EB", "#D97706"])
                st.plotly_chart(
                    revision_figure,
                    width="stretch",
                    config={"displaylogo": False},
                )
            st.warning(
                "The recomputed-today signal uses revised data that was not available "
                "historically. It is a revision diagnostic, never the real-time backtest result.",
                icon=":material/history:",
            )

    download_columns = [
        "information_date",
        "signal_available_date",
        "model_name",
        "vintage_ogli",
        "vintage_momentum_score",
        "vintage_regime",
        "regime_transition",
        "transition_direction",
        "horizon_months",
        "publication_lag_weeks",
        "market_return",
        "maximum_upside_from_start",
        "maximum_downside_from_start",
        "maximum_drawdown_from_peak",
        "current_ogli",
        "current_momentum_score",
        "current_regime",
    ]
    st.download_button(
        "Download selected research sample",
        data=selected[download_columns].to_csv(index=False).encode("utf-8"),
        file_name=(f"ogli_bitcoin_{model_id}_{horizon}m_{publication_lag}w_{sample_key}.csv"),
        mime="text/csv",
        icon=":material/download:",
    )
    if len(selected) < 12:
        st.info(
            "This selection has fewer than 12 observations. Descriptive statistics remain "
            "visible, but their sign and magnitude are especially fragile.",
            icon=":material/science:",
        )
    st.warning(
        "Forward windows can overlap, regimes can proxy for broader macro conditions, and the "
        "sample is short. These results do not establish causation or an investable strategy.",
        icon=":material/warning:",
    )
    st.caption(
        "Source: Coin Metrics Community Data (CC BY-NC 4.0). OGLI inputs: ALFRED monthly "
        "information sets. All market outcomes occur after the stated assumed availability date."
    )


def vintage_pilot_page() -> None:
    st.title("Point-in-time OGLI pilot")
    st.caption(
        "Monthly reconstruction using ALFRED information sets available on each month end. "
        "This is a research pilot, not a revised production index."
    )
    try:
        loaded = _point_in_time_data()
    except DashboardDataError as exc:
        st.error(str(exc), icon=":material/error:")
        return
    if loaded is None:
        st.info(
            "The vintage pilot has not been published in this environment. Maintainers can "
            "generate it with the command below; the existing FRED key is sufficient.",
            icon=":material/history:",
        )
        st.code("uv run ogli-point-in-time --publish-dashboard-snapshot", language="zsh")
        return
    data, data_origin = loaded

    model_options = dict(data[["model_name", "model_id"]].drop_duplicates().itertuples(index=False))
    with st.sidebar:
        st.header("Vintage controls")
        default_name = "Model B — Net Fed liquidity proxy"
        selected_name = st.selectbox(
            "Liquidity definition",
            list(model_options),
            index=list(model_options).index(default_name),
            key="vintage_model",
        )
        st.caption("Information frequency: calendar month end")
        st.caption(f"Data mode: {data_origin}")

    selected = data.loc[data["model_id"] == model_options[selected_name]].copy()
    latest = selected.iloc[-1]
    absolute_revisions = selected["ogli_revision"].abs()
    with st.container(horizontal=True):
        st.metric("Latest vintage OGLI", f"{latest['vintage_ogli']:.1f}", border=True)
        st.metric("Current-vintage value", f"{latest['current_ogli']:.1f}", border=True)
        st.metric("Latest revision", f"{latest['ogli_revision']:+.3f}", border=True)
        st.metric("Largest absolute revision", f"{absolute_revisions.max():.3f}", border=True)
        st.metric("Month-end information sets", f"{len(selected):,}", border=True)

    levels = selected[["information_date", "vintage_ogli", "current_ogli"]].melt(
        id_vars="information_date",
        var_name="calculation",
        value_name="OGLI",
    )
    levels["calculation"] = levels["calculation"].map(
        {"vintage_ogli": "As known then", "current_ogli": "Recomputed today"}
    )
    level_figure = px.line(
        levels,
        x="information_date",
        y="OGLI",
        color="calculation",
        title=f"{selected_name} · vintage versus current-vintage OGLI",
        labels={"information_date": "Information date", "calculation": "Calculation"},
    )
    level_figure.update_yaxes(range=[0, 100])
    level_figure.update_layout(hovermode="x unified", legend_title_text="")
    st.plotly_chart(level_figure, width="stretch", config={"displaylogo": False})

    revision_figure = px.bar(
        selected,
        x="information_date",
        y="ogli_revision",
        title="Current-vintage OGLI minus the reading available at month end",
        labels={"information_date": "Information date", "ogli_revision": "OGLI revision"},
    )
    revision_figure.add_hline(y=0, line_color="#6B7280", line_width=1)
    st.plotly_chart(revision_figure, width="stretch", config={"displaylogo": False})

    st.info(
        "Small revisions here mean these specific FRED inputs have changed little at matched "
        "observation dates. The pilot still does not reconstruct intraday release timing, market "
        "availability, or every historical source revision.",
        icon=":material/science:",
    )
    st.dataframe(
        selected.tail(12)[
            [
                "information_date",
                "signal_observation_date",
                "vintage_ogli",
                "current_ogli",
                "ogli_revision",
                "vintage_regime",
            ]
        ].sort_values("information_date", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "information_date": st.column_config.DateColumn(
                "Information date", format="YYYY-MM-DD"
            ),
            "signal_observation_date": st.column_config.DateColumn(
                "Signal observation", format="YYYY-MM-DD"
            ),
            "vintage_ogli": st.column_config.NumberColumn("As known then", format="%.2f"),
            "current_ogli": st.column_config.NumberColumn("Recomputed today", format="%.2f"),
            "ogli_revision": st.column_config.NumberColumn("Revision", format="%+.3f"),
            "vintage_regime": st.column_config.TextColumn("Regime then"),
        },
    )
    st.caption(
        "Comparison policy: exact same weekly signal observation date. Expanding normalization "
        "is recomputed independently inside every ALFRED information set."
    )

    st.divider()
    st.header("Point-in-time OGLI vs subsequent markets")
    st.caption(
        "Market outcomes begin only after the selected assumed availability delay. Bitcoin is "
        "the primary comparison; gold and the broad dollar index are robustness context."
    )
    try:
        market_bundle = _point_in_time_market_data()
    except DashboardDataError as exc:
        st.error(str(exc), icon=":material/error:")
        market_bundle = None
    if market_bundle is None:
        st.info(
            "Point-in-time market outputs have not been generated in this environment. The "
            "existing FRED key is sufficient; Bitcoin, gold, and dollar data require no new key.",
            icon=":material/query_stats:",
        )
        st.code("uv run ogli-point-in-time --publish-dashboard-snapshot", language="zsh")
        return

    pairs, summaries, market_origin = market_bundle
    market_labels = {
        "bitcoin": "Bitcoin",
        "gold": "Gold (World Bank monthly average)",
        "broad_usd_index": "Broad U.S. dollar index",
    }
    available_markets = [item for item in market_labels if item in set(pairs["market_id"])]
    controls = st.columns(4)
    market_id = controls[0].selectbox(
        "Market outcome",
        available_markets,
        format_func=lambda value: market_labels[value],
        key="pit_market",
    )
    horizon = controls[1].selectbox(
        "Forward horizon",
        sorted(pairs["horizon_months"].unique()),
        index=1,
        format_func=lambda value: f"{value} month{'s' if value != 1 else ''}",
        key="pit_horizon",
    )
    sample_policy = controls[2].selectbox(
        "Sample",
        ["non_overlapping", "overlapping"],
        format_func=lambda value: value.replace("_", " ").title(),
        key="pit_sample",
    )
    lag = controls[3].selectbox(
        "Assumed availability delay",
        sorted(pairs["publication_lag_weeks"].unique()),
        index=1,
        format_func=lambda value: f"{value} week{'s' if value != 1 else ''}",
        key="pit_lag",
    )

    model_id = model_options[selected_name]
    summary_selection = summaries.loc[
        (summaries["model_id"] == model_id)
        & (summaries["market_id"] == market_id)
        & (summaries["horizon_months"] == horizon)
        & (summaries["sample_policy"] == sample_policy)
    ].copy()
    current_summary = summary_selection.loc[summary_selection["publication_lag_weeks"] == lag]
    if current_summary.empty:
        st.warning("The selected point-in-time market summary is unavailable.")
        return
    metric_row = current_summary.iloc[0]
    correlation = metric_row["correlation"]
    with st.container(horizontal=True):
        st.metric(
            "Pearson correlation",
            "Insufficient sample" if pd.isna(correlation) else f"{correlation:+.2f}",
            border=True,
        )
        st.metric("Paired observations", f"{int(metric_row['observations']):,}", border=True)
        st.metric("Mean forward return", f"{metric_row['mean_return']:.1%}", border=True)
        st.metric("Positive outcomes", f"{metric_row['positive_share']:.0%}", border=True)

    chart_summary = summary_selection.dropna(subset=["correlation"])
    chart_title = (
        f"{selected_name} vs {market_labels[market_id]} · {horizon}-month correlation sensitivity"
    )
    if chart_summary.empty:
        with st.container(border=True):
            st.subheader(chart_title)
            st.info(
                "No correlation is reported because every delay has fewer than the declared "
                "minimum observations. Select overlapping outcomes or a shorter horizon.",
                icon=":material/data_alert:",
            )
    else:
        lag_figure = px.bar(
            chart_summary,
            x="publication_lag_weeks",
            y="correlation",
            title=chart_title,
            labels={
                "publication_lag_weeks": "Assumed OGLI availability delay (weeks)",
                "correlation": "Pearson correlation",
            },
        )
        lag_figure.add_hline(y=0, line_color="#6B7280", line_width=1)
        lag_figure.update_traces(
            marker_color="#D97706",
            texttemplate="%{y:+.2f}",
            textposition="auto",
            hovertemplate=(
                "Availability delay: %{x} weeks<br>Correlation: %{y:+.2f}<extra></extra>"
            ),
        )
        lag_figure.update_yaxes(tickformat=".2f")
        st.plotly_chart(lag_figure, width="stretch", config={"displaylogo": False})

    if sample_policy == "non_overlapping" and 8 <= int(metric_row["observations"]) < 12:
        st.info(
            "This non-overlapping estimate clears the declared 8-observation display minimum "
            "but remains a small-sample result. Treat its sign and magnitude as fragile.",
            icon=":material/science:",
        )

    selected_pairs = pairs.loc[
        (pairs["model_id"] == model_id)
        & (pairs["market_id"] == market_id)
        & (pairs["horizon_months"] == horizon)
        & (pairs["publication_lag_weeks"] == lag)
    ].copy()
    if sample_policy == "non_overlapping":
        selected_pairs = selected_pairs.loc[selected_pairs["is_non_overlapping"]]
    market_name = market_labels[market_id]
    scatter = px.scatter(
        selected_pairs,
        x="vintage_momentum_score",
        y="market_return",
        hover_data={
            "information_date": "|%Y-%m-%d",
            "signal_available_date": "|%Y-%m-%d",
            "vintage_ogli": ":.1f",
        },
        title=f"Point-in-time OGLI momentum vs {horizon}-month {market_name} return",
        labels={
            "vintage_momentum_score": "Point-in-time OGLI momentum score",
            "market_return": f"{market_name} return",
        },
    )
    scatter.update_traces(marker={"size": 8, "opacity": 0.7, "color": "#2563EB"})
    scatter.update_yaxes(tickformat=".0%", zeroline=True)
    st.plotly_chart(scatter, width="stretch", config={"displaylogo": False})

    if market_id == "gold":
        st.info(
            "Gold is the World Bank Pink Sheet monthly average in USD per troy ounce. Monthly "
            "averages are coarser than Bitcoin/dollar closes, so week-level delay sensitivity "
            "changes only when the assumed start crosses a month end.",
            icon=":material/info:",
        )
    elif market_id == "broad_usd_index":
        st.info(
            "A positive return means the broad U.S. dollar index strengthened. Its sign is not "
            "inverted or optimized to improve the relationship with OGLI.",
            icon=":material/info:",
        )
    st.warning(
        "These are retrospective, univariate associations. Overlapping outcomes are dependent; "
        "non-overlapping samples are much smaller. Publication delays are sensitivity assumptions, "
        "not reconstructed trade timestamps, and correlation does not establish causation or an "
        "investable signal.",
        icon=":material/warning:",
    )
    st.caption(
        f"Data mode: {market_origin}. Bitcoin: Coin Metrics Community Data (CC BY-NC 4.0); "
        "gold: World Bank Pink Sheet monthly data; dollar: Federal Reserve H.10 via FRED."
    )


def markets_page() -> None:
    st.title("Liquidity vs markets")
    st.caption(
        "Retrospective comparison of OGLI momentum with Bitcoin returns. Correlation is not "
        "causation, a forecast, or parameter calibration."
    )
    try:
        comparisons, correlations, data_origin = _market_data()
    except DashboardDataError as exc:
        st.info(str(exc), icon=":material/info:")
        st.markdown(
            "Bitcoin comparison files are unavailable. Run the pipeline to refresh the public "
            "Coin Metrics market snapshot:"
        )
        st.code(
            "uv run python -m open_global_liquidity.pipeline --start 2020-01-01",
            language="zsh",
        )
        st.link_button(
            "Review Coin Metrics community data",
            "https://github.com/coinmetrics/data",
            icon=":material/open_in_new:",
        )
        return
    if comparisons is not None:
        _show_freshness(comparisons, "Bitcoin/OGLI comparison")

    model_options = dict(
        correlations[["model_name", "model_id"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    horizon_options = {
        "Current 1-week return": 0,
        "4 weeks forward": 4,
        "8 weeks forward": 8,
        "12 weeks forward": 12,
        "26 weeks forward": 26,
        "52 weeks forward": 52,
    }
    analysis_labels = {
        "Available-information (1-week release lag)": "available_information",
        "Observation-date exploratory": "observation_date",
    }
    available_analysis_modes = set(correlations["analysis_mode"])
    analysis_options = {
        label: value
        for label, value in analysis_labels.items()
        if value in available_analysis_modes
    }
    sample_labels = {
        "Non-overlapping windows": "non_overlapping",
        "All overlapping observations": "overlapping",
    }
    available_sample_policies = set(correlations["sample_policy"])
    sample_options = {
        label: value for label, value in sample_labels.items() if value in available_sample_policies
    }
    with st.sidebar:
        st.header("Market controls")
        selected_model = st.selectbox(
            "Liquidity definition",
            list(model_options),
            index=list(model_options).index("Model B — Net Fed liquidity proxy"),
            key="market_model",
        )
        selected_horizon_label = st.selectbox(
            "Return horizon",
            list(horizon_options),
            index=3,
            key="market_horizon",
        )
        selected_analysis_label = st.selectbox(
            "Signal timing",
            list(analysis_options),
            key="market_analysis_mode",
        )
        selected_sample_label = st.selectbox(
            "Statistical sample",
            list(sample_options),
            key="market_sample_policy",
        )
        timeline_history = st.segmented_control(
            "Timeline history",
            ["3 years", "5 years", "All"],
            default="5 years",
            key="market_timeline_history",
        )
        st.caption("Market: Bitcoin · Coin Metrics daily USD price")
        st.caption(f"Data mode: {data_origin}")

    model_id = model_options[selected_model]
    horizon = horizon_options[selected_horizon_label]
    analysis_mode = analysis_options[selected_analysis_label]
    sample_policy = sample_options[selected_sample_label]
    selected_summary = correlations.loc[
        (correlations["model_id"] == model_id)
        & (correlations["market_id"] == "bitcoin")
        & (correlations["horizon_weeks"] == horizon)
        & (correlations["analysis_mode"] == analysis_mode)
        & (correlations["sample_policy"] == sample_policy)
    ].iloc[0]
    model_correlations = correlations.loc[
        (correlations["model_id"] == model_id)
        & (correlations["market_id"] == "bitcoin")
        & (correlations["analysis_mode"] == analysis_mode)
        & (correlations["sample_policy"] == sample_policy)
    ]
    correlation = selected_summary["correlation"]

    if comparisons is None:
        with st.container(horizontal=True):
            st.metric(
                "Pearson correlation",
                "Insufficient history" if pd.isna(correlation) else f"{correlation:+.2f}",
                border=True,
            )
            st.metric(
                "Paired observations", f"{int(selected_summary['observations']):,}", border=True
            )
            st.metric("Selected horizon", selected_horizon_label, border=True)

        st.plotly_chart(
            _horizon_correlation_figure(
                model_correlations,
                f"{selected_model} · correlation by return horizon",
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        st.dataframe(
            model_correlations[
                [
                    "horizon_weeks",
                    "correlation",
                    "bootstrap_ci_lower",
                    "bootstrap_ci_upper",
                    "observations",
                ]
            ],
            width="stretch",
            hide_index=True,
            column_config={
                "horizon_weeks": st.column_config.NumberColumn("Forward horizon (weeks)"),
                "correlation": st.column_config.NumberColumn("Pearson correlation", format="%+.2f"),
                "bootstrap_ci_lower": st.column_config.NumberColumn(
                    "Block bootstrap CI lower", format="%+.2f"
                ),
                "bootstrap_ci_upper": st.column_config.NumberColumn(
                    "Block bootstrap CI upper", format="%+.2f"
                ),
                "observations": st.column_config.NumberColumn("Paired observations", format="%d"),
            },
        )
        st.info(
            "Only aggregate statistics are available in this data snapshot. Refresh the dashboard "
            "snapshots to publish the complete non-commercial Bitcoin research view.",
            icon=":material/info:",
        )
        st.warning(
            "These exploratory correlations do not establish causation or an investable signal. "
            "Refresh the full snapshots to compare observation-date and available-information "
            "timing policies.",
            icon=":material/warning:",
        )
        return

    selected_pairs = comparisons.loc[
        (comparisons["model_id"] == model_id)
        & (comparisons["market_id"] == "bitcoin")
        & (comparisons["horizon_weeks"] == horizon)
        & (comparisons["analysis_mode"] == analysis_mode)
    ].dropna(subset=["liquidity_signal", "market_return"])
    if sample_policy == "non_overlapping":
        selected_pairs = selected_pairs.loc[selected_pairs["is_non_overlapping"]]
    if selected_pairs.empty:
        st.info(
            "No completed Bitcoin outcome windows are available for this combination yet.",
            icon=":material/hourglass_empty:",
        )
        return
    latest_pair = selected_pairs.iloc[-1]
    bitcoin_price = latest_pair.get("value")

    with st.container(horizontal=True):
        st.metric(
            "Pearson correlation",
            "Insufficient history" if pd.isna(correlation) else f"{correlation:+.2f}",
            border=True,
        )
        st.metric("Paired observations", f"{int(selected_summary['observations']):,}", border=True)
        st.metric("Latest paired OGLI", f"{latest_pair['ogli']:.1f}", border=True)
        if pd.notna(bitcoin_price):
            st.metric("BTC at signal date", f"${float(bitcoin_price):,.0f}", border=True)
        st.metric("Latest paired BTC return", f"{latest_pair['market_return']:.1%}", border=True)
    if pd.notna(selected_summary["bootstrap_ci_lower"]):
        st.caption(
            f"95% circular moving-block bootstrap interval: "
            f"{selected_summary['bootstrap_ci_lower']:+.2f} to "
            f"{selected_summary['bootstrap_ci_upper']:+.2f} · "
            f"{int(selected_summary['bootstrap_valid_resamples']):,} valid resamples · "
            f"{int(selected_summary['bootstrap_block_length'])}-observation blocks"
        )

    (
        timeline_tab,
        scatter_tab,
        regimes_tab,
        rolling_tab,
        horizons_tab,
        subperiods_tab,
        macro_tab,
        data_tab,
    ) = st.tabs(
        [
            "Timeline",
            "Relationship",
            "Returns by regime",
            "Rolling correlation",
            "Across horizons",
            "Subperiod stability",
            "Macro context",
            "Paired data",
        ]
    )
    with timeline_tab:
        if "value" not in comparisons.columns:
            st.info(
                "Bitcoin price history will appear after the hosted data process finishes "
                "reloading the latest snapshot.",
                icon=":material/sync:",
            )
        else:
            timeline = comparisons.loc[
                (comparisons["model_id"] == model_id)
                & (comparisons["market_id"] == "bitcoin")
                & (comparisons["horizon_weeks"] == 0)
                & (comparisons["analysis_mode"] == analysis_mode)
            ].dropna(subset=["ogli", "value"])
            if timeline_history != "All":
                years = 3 if timeline_history == "3 years" else 5
                timeline = timeline.loc[
                    timeline["date"] >= timeline["date"].max() - timedelta(days=years * 365)
                ]
            st.plotly_chart(
                _ogli_bitcoin_overlay_figure(
                    timeline,
                    f"{selected_model} and Bitcoin · {timeline_history}",
                ),
                width="stretch",
                config={"displaylogo": False},
            )
            st.caption(
                "Bitcoin uses a logarithmic USD axis; OGLI uses its 0-100 scale. The lines share "
                "dates only—neither series is rescaled or fitted to the other."
            )
    with scatter_tab:
        st.plotly_chart(
            _market_scatter_figure(
                selected_pairs,
                f"{selected_model} vs Bitcoin · {selected_horizon_label}",
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        st.caption(
            "Each point anchors the expanding OGLI momentum score at t to the named market-return "
            "window. Forward outcomes are never inputs to OGLI."
        )
    with regimes_tab:
        regime_statistics = _market_regime_data()
        if regime_statistics is None:
            st.info(
                "Regime statistics will appear after the refreshed research snapshots are built.",
                icon=":material/sync:",
            )
        else:
            selected_regimes = regime_statistics.loc[
                (regime_statistics["model_id"] == model_id)
                & (regime_statistics["market_id"] == "bitcoin")
                & (regime_statistics["horizon_weeks"] == horizon)
                & (regime_statistics["analysis_mode"] == analysis_mode)
                & (regime_statistics["sample_policy"] == sample_policy)
            ]
            st.plotly_chart(
                _regime_return_figure(
                    selected_regimes,
                    f"Bitcoin outcomes by OGLI regime · {selected_horizon_label}",
                ),
                width="stretch",
                config={"displaylogo": False},
            )
            st.dataframe(
                selected_regimes[
                    [
                        "regime",
                        "observations",
                        "mean_return",
                        "median_return",
                        "positive_share",
                        "mean_ci_lower",
                        "mean_ci_upper",
                    ]
                ],
                hide_index=True,
                column_config={
                    "regime": "OGLI regime",
                    "observations": st.column_config.NumberColumn("Observations", format="%d"),
                    "mean_return": st.column_config.NumberColumn("Mean", format="percent"),
                    "median_return": st.column_config.NumberColumn("Median", format="percent"),
                    "positive_share": st.column_config.NumberColumn(
                        "Positive share", format="percent"
                    ),
                    "mean_ci_lower": st.column_config.NumberColumn(
                        "Mean CI lower", format="percent"
                    ),
                    "mean_ci_upper": st.column_config.NumberColumn(
                        "Mean CI upper", format="percent"
                    ),
                },
            )
            st.caption(
                "Error bars are classical 95% Student-t confidence intervals around the mean, "
                "not forecast intervals. Median and positive-share statistics are shown because "
                "Bitcoin returns are strongly skewed."
            )
    with rolling_tab:
        rolling = selected_pairs.dropna(subset=["rolling_correlation"])
        st.plotly_chart(
            _rolling_correlation_figure(
                rolling,
                f"52-week trailing correlation · {selected_horizon_label}",
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        st.caption("The rolling estimate requires at least 26 paired weekly observations.")
    with horizons_tab:
        st.plotly_chart(
            _horizon_correlation_figure(
                model_correlations,
                f"{selected_model} · correlation by return horizon",
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        st.caption(
            "All estimates use the same configured OGLI momentum signal. Horizon zero is the "
            "one-week return ending at t; positive horizons start at t."
        )
    with subperiods_tab:
        subperiod_statistics = _market_subperiod_data()
        if subperiod_statistics is None:
            st.info(
                "Subperiod diagnostics will appear after the next full pipeline run.",
                icon=":material/sync:",
            )
        else:
            selected_subperiods = subperiod_statistics.loc[
                (subperiod_statistics["model_id"] == model_id)
                & (subperiod_statistics["market_id"] == "bitcoin")
                & (subperiod_statistics["horizon_weeks"] == horizon)
                & (subperiod_statistics["analysis_mode"] == analysis_mode)
                & (subperiod_statistics["sample_policy"] == sample_policy)
            ]
            st.plotly_chart(
                _subperiod_correlation_figure(
                    selected_subperiods,
                    f"Bitcoin correlation across predeclared periods · {selected_horizon_label}",
                ),
                width="stretch",
                config={"displaylogo": False},
            )
            st.dataframe(
                selected_subperiods[
                    [
                        "period_label",
                        "period_start",
                        "period_end",
                        "correlation",
                        "bootstrap_ci_lower",
                        "bootstrap_ci_upper",
                        "observations",
                    ]
                ],
                width="stretch",
                hide_index=True,
                column_config={
                    "period_label": "Research period",
                    "period_start": st.column_config.DateColumn("Start", format="YYYY-MM-DD"),
                    "period_end": st.column_config.DateColumn("End", format="YYYY-MM-DD"),
                    "correlation": st.column_config.NumberColumn("Correlation", format="%+.2f"),
                    "bootstrap_ci_lower": st.column_config.NumberColumn(
                        "Block bootstrap CI lower", format="%+.2f"
                    ),
                    "bootstrap_ci_upper": st.column_config.NumberColumn(
                        "Block bootstrap CI upper", format="%+.2f"
                    ),
                    "observations": st.column_config.NumberColumn("Observations", format="%d"),
                },
            )
            st.caption(
                "Error bars are deterministic 95% circular moving-block bootstrap intervals. "
                "The periods—Pre-2020, 2020-2022, and 2023-present—were declared in configuration "
                "before calculating these results. They are model assumptions, not breakpoints "
                "optimized to improve Bitcoin correlation. Wide intervals and sign changes are "
                "evidence of relationship instability, not something to hide."
            )
    with macro_tab:
        macro_context = _macro_context_data()
        if macro_context is None:
            st.info(
                "Treasury-yield and dollar context will appear after the next full pipeline run.",
                icon=":material/sync:",
            )
        else:
            visible_macro = macro_context.loc[
                macro_context["date"] >= macro_context["date"].max() - timedelta(days=5 * 365)
            ]
            latest_macro = macro_context.dropna().iloc[-1]
            with st.container(horizontal=True):
                st.metric(
                    "10-year Treasury", f"{latest_macro['treasury_yield_10y']:.2f}%", border=True
                )
                st.metric(
                    "2-year Treasury", f"{latest_macro['treasury_yield_2y']:.2f}%", border=True
                )
                st.metric(
                    "10y-2y slope", f"{latest_macro['yield_curve_10y_2y']:+.2f}pp", border=True
                )
                st.metric("Broad USD index", f"{latest_macro['broad_usd_index']:.1f}", border=True)
            st.plotly_chart(
                _macro_context_figure(
                    visible_macro, "Treasury yields and broad U.S. dollar · 5 years"
                ),
                width="stretch",
                config={"displaylogo": False},
            )
            st.caption(
                "DGS10, DGS2, and DTWEXBGS are measured context series. The 10y-2y slope is a "
                "transparent subtraction. None is currently an OGLI input."
            )
    with data_tab:
        table = selected_pairs[
            [
                "date",
                "signal_observation_date",
                "signal_available_date",
                "ogli",
                "liquidity_signal",
                "market_return",
                "return_start_date",
                "return_end_date",
            ]
        ].sort_values("date", ascending=False)
        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
            column_config={
                "date": st.column_config.DateColumn("Signal date", format="YYYY-MM-DD"),
                "signal_observation_date": st.column_config.DateColumn(
                    "Source observation", format="YYYY-MM-DD"
                ),
                "signal_available_date": st.column_config.DateColumn(
                    "Assumed available", format="YYYY-MM-DD"
                ),
                "ogli": st.column_config.NumberColumn("OGLI", format="%.1f"),
                "liquidity_signal": st.column_config.NumberColumn("Momentum score", format="%+.2f"),
                "market_return": st.column_config.NumberColumn("Bitcoin return", format="percent"),
                "return_start_date": st.column_config.DateColumn(
                    "Return start", format="YYYY-MM-DD"
                ),
                "return_end_date": st.column_config.DateColumn("Return end", format="YYYY-MM-DD"),
            },
        )

    st.warning(
        "These statistics are sensitive to sample selection, overlapping forward-return windows, "
        "data revisions, publication-lag assumptions, and common macroeconomic drivers. The "
        "available-information view applies a configurable one-week weekly lag; it is a practical "
        "approximation, not a historical release-vintage database. The results do not demonstrate "
        "that liquidity causes market returns and must not be "
        "read as an investable signal.",
        icon=":material/warning:",
    )
    st.caption("Source: Coin Metrics Community Data (`btc.PriceUSD`), licensed CC BY-NC 4.0.")


def euro_area_page() -> None:
    """Present the first non-US measured series without implying a global index."""
    st.title("Euro area measured data")
    st.caption(
        "v0.2a expansion pilot · measured ECB data only · no EUR/USD conversion, weekly "
        "interpolation, euro-area liquidity model, or global aggregation"
    )
    try:
        data, _path, origin = _ecb_data()
    except DashboardDataError as exc:
        st.info(str(exc), icon=":material/public:")
        st.code(
            "uv run python -m open_global_liquidity.pipeline --publish-dashboard-snapshot",
            language="zsh",
        )
        st.markdown(
            "The ECB Data Portal endpoint is public and requires **no account or API key**."
        )
        return

    latest = latest_ecb_readings(data).iloc[0]
    level = float(latest["value_eur_billions"])
    monthly_change = latest["change_eur_billions"]
    growth_yoy = latest["growth_yoy"]
    retrieved_at = pd.to_datetime(latest["retrieved_at"], utc=True)
    with st.container(horizontal=True):
        st.metric(
            "Eurosystem total assets",
            f"€{level:,.0f}bn",
            None if pd.isna(monthly_change) else f"€{float(monthly_change):+,.0f}bn vs prior month",
            border=True,
        )
        st.metric(
            "12-month change",
            "Unavailable" if pd.isna(growth_yoy) else f"{float(growth_yoy):+.1%}",
            border=True,
        )
        st.metric("Latest period", f"{latest['date']:%b %Y}", border=True)
        st.metric("Data mode", origin, border=True)

    max_date = data["date"].max()
    history = st.segmented_control("History", ["5 years", "10 years", "All"], default="10 years")
    if history == "All":
        visible = data
    else:
        years = 5 if history == "5 years" else 10
        visible = data.loc[data["date"] >= max_date - pd.DateOffset(years=years)]
    figure = px.line(
        visible,
        x="date",
        y="value_eur_billions",
        title=f"Eurosystem total assets · {history}",
        labels={"date": "Date", "value_eur_billions": "EUR billions"},
    )
    figure.update_traces(
        line={"width": 2.5}, hovertemplate="%{x|%b %Y}<br>€%{y:,.0f}bn<extra></extra>"
    )
    figure.update_layout(
        hovermode="x unified",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(figure, width="stretch", config={"displaylogo": False})

    st.info(
        "Monthly dates are calendar month-end period labels. They are not modeled publication "
        "timestamps. Values remain nominal EUR stocks and are not inputs to the US OGLI.",
        icon=":material/info:",
    )
    st.subheader("Recent observations")
    recent = data.tail(12).assign(
        date=lambda frame: frame["date"].dt.strftime("%Y-%m-%d"),
        value_eur_billions=lambda frame: frame["value_eur_billions"].round(1),
    )
    st.dataframe(
        recent[["date", "value_eur_billions", "series_id"]].rename(
            columns={
                "date": "Period end",
                "value_eur_billions": "EUR billions",
                "series_id": "ECB series",
            }
        ),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        f"Retrieved {retrieved_at:%Y-%m-%d %H:%M UTC} · Provider: ECB Data Portal · "
        "Euro area changing composition"
    )
    st.link_button(
        "Review official ECB metadata",
        "https://data.ecb.europa.eu/data/concepts/statistical-balance-sheet",
        icon=":material/open_in_new:",
    )


def japan_page() -> None:
    """Present official BOJ total assets without implying a global aggregate."""
    st.title("Japan measured data")
    st.caption(
        "v0.2b expansion pilot · official BOJ data in native yen · no FX conversion, weekly "
        "interpolation, Japan liquidity model, or global aggregation"
    )
    try:
        data, _path, origin = _boj_data()
    except DashboardDataError as exc:
        st.info(str(exc), icon=":material/account_balance:")
        st.code(
            "uv run python -m open_global_liquidity.pipeline --publish-dashboard-snapshot",
            language="zsh",
        )
        st.markdown("The BOJ Time-Series Data Search API is public and requires **no API key**.")
        return

    latest = latest_boj_readings(data).iloc[0]
    level = float(latest["value_jpy_billions"])
    monthly_change = latest["change_jpy_billions"]
    growth_yoy = latest["growth_yoy"]
    retrieved_at = pd.to_datetime(latest["retrieved_at"], utc=True)
    with st.container(horizontal=True):
        st.metric(
            "Bank of Japan total assets",
            f"¥{level / 1_000:,.1f}tn",
            (
                None
                if pd.isna(monthly_change)
                else f"¥{float(monthly_change) / 1_000:+,.1f}tn vs prior month"
            ),
            border=True,
        )
        st.metric(
            "12-month change",
            "Unavailable" if pd.isna(growth_yoy) else f"{float(growth_yoy):+.1%}",
            border=True,
        )
        st.metric("Latest period", f"{latest['date']:%b %Y}", border=True)
        st.metric("Data mode", origin, border=True)

    max_date = data["date"].max()
    history = st.segmented_control(
        "History", ["5 years", "10 years", "All"], default="10 years", key="japan_history"
    )
    if history == "All":
        visible = data
    else:
        years = 5 if history == "5 years" else 10
        visible = data.loc[data["date"] >= max_date - pd.DateOffset(years=years)]
    chart_data = visible.rename(columns={"date": "Date", "value_jpy_billions": "JPY billions"})
    st.line_chart(
        chart_data,
        x="Date",
        y="JPY billions",
        x_label="Period end",
        y_label="JPY billions",
    )
    st.info(
        "Monthly dates are calendar month-end period labels, not modeled publication timestamps. "
        "Values remain nominal JPY stocks and are not inputs to the US OGLI.",
        icon=":material/info:",
    )
    st.subheader("Recent observations")
    recent = data.tail(12).assign(
        date=lambda frame: frame["date"].dt.strftime("%Y-%m-%d"),
        value_jpy_billions=lambda frame: frame["value_jpy_billions"].round(1),
    )
    st.dataframe(
        recent[["date", "value_jpy_billions", "series_id"]].rename(
            columns={
                "date": "Period end",
                "value_jpy_billions": "JPY billions",
                "series_id": "BOJ series",
            }
        ),
        column_config={
            "JPY billions": st.column_config.NumberColumn(format="localized"),
        },
        width="stretch",
        hide_index=True,
    )
    st.caption(
        f"Retrieved {retrieved_at:%Y-%m-%d %H:%M UTC} · Provider: Bank of Japan · "
        "Database BS01 · series MABJMTA"
    )
    st.link_button(
        "Review official BOJ source",
        "https://www.boj.or.jp/en/statistics/boj/other/ac/index.htm",
        icon=":material/open_in_new:",
    )


def research_guide_page() -> None:
    st.title("Research guide")
    st.markdown(
        """
        This page defines the concepts, data, and assumptions behind the current prototype. The
        guiding principle is simple: **measured data, model assumptions, and calibrated parameters
        must never be presented as the same thing.**
        """
    )

    st.subheader("What does global liquidity mean?")
    st.markdown(
        """
        Global liquidity describes the ease of financing in the international financial system.
        It has both a **funding** dimension—the ability to obtain cash or credit—and a **market**
        dimension—the ability to transact in assets without large price disruption. It is shaped
        jointly by central banks, commercial banks, non-bank intermediaries, collateral markets,
        investors, and cross-border currency funding.

        Liquidity is not a single observable quantity. A serious framework therefore compares
        several price and quantity indicators rather than treating one balance-sheet series as a
        complete answer. The BIS likewise describes global liquidity as an unobservable system
        property that must be assessed through multiple indicators.
        """
    )

    with st.container(horizontal=True):
        with st.container(border=True):
            st.markdown("#### Measured data")
            st.write(
                "Public observations with provider, series ID, units, dates, and retrieval time."
            )
            st.badge("Implemented", color="green")
        with st.container(border=True):
            st.markdown("#### Model assumptions")
            st.write(
                "Declared transformations, frequency rules, formulas, and weights chosen here."
            )
            st.badge("Implemented", color="blue")
        with st.container(border=True):
            st.markdown("#### Calibrated parameters")
            st.write("Values fitted against a named public target using a documented procedure.")
            st.badge("Not used in v0.1", color="gray")

    st.subheader("Current US model definitions")
    with st.container(border=True):
        st.markdown("#### Model A — Fed assets")
        st.code("L_A(t) = FedAssets(t)", language=None)
        st.write(
            "The simplest central-bank balance-sheet measure. It ignores liability-side drains "
            "and does not represent all system-wide liquidity."
        )
    with st.container(border=True):
        st.markdown("#### Model B — Net Fed liquidity proxy")
        st.code("L_B(t) = FedAssets(t) - TGA(t) - ON_RRP(t)", language=None)
        st.write(
            "A common public-market proxy. It adjusts total assets for Treasury cash held at the "
            "Fed and balances absorbed through overnight reverse repo. It is not presented as a "
            "Michael Howell or CrossBorder Capital formula."
        )
    with st.container(border=True):
        st.markdown("#### Model C — Reserve-based liquidity")
        st.code("L_C(t) = ReserveBalances(t)", language=None)
        st.write(
            "A direct settlement-liquidity proxy. TGA and ON RRP are not subtracted again because "
            "their effects are already reflected in reserve balances, so another adjustment could "
            "double count those drains."
        )

    st.subheader("Glossary")
    glossary = {
        "Central-bank liquidity": (
            "Official balance-sheet capacity supplied by a central bank, including assets and "
            "reserve liabilities. It is important but narrower than global liquidity."
        ),
        "Bank reserves": (
            "Balances that eligible institutions hold at the Federal Reserve. They support "
            "settlement and monetary-policy implementation but are not directly spendable by "
            "the public."
        ),
        "Treasury General Account (TGA)": (
            "The US Treasury's operating cash account at the Federal Reserve. Changes can shift "
            "balances between the Treasury and the banking system."
        ),
        "Overnight reverse repo (ON RRP)": (
            "A Federal Reserve facility through which eligible counterparties place cash overnight "
            "against Treasury collateral. In the current proxy, the balance is treated as "
            "absorption."
        ),
        "Collateral and haircuts": (
            "Secured funding depends on acceptable collateral and the discount applied to it. "
            "Higher haircuts reduce the amount of financing obtainable from a given asset pool. "
            "Future scope."
        ),
        "Offshore dollar liquidity": (
            "US-dollar credit and funding activity outside the United States, including banking, "
            "bond, and FX-swap channels. It is outside the current US-only release."
        ),
    }
    for term, definition in glossary.items():
        with st.expander(term):
            st.write(definition)

    st.subheader("Frequency and data policy")
    st.markdown(
        """
        - Canonical research frequency: **weekly, Wednesday**.
        - Weekly H.4.1 series require an exact Wednesday observation.
        - Daily ON RRP uses the latest observation on or before Wednesday, with a maximum age of
          seven calendar days.
        - No balance-sheet values are interpolated.
        - Monetary inputs are standardized to **millions of US dollars** before model calculation.
        - Source date, source unit, alignment method, and staleness are retained in processed data.
        - The published weekly index uses current-vintage FRED data. A separate local monthly
          ALFRED pilot recomputes every model inside sealed historical information sets.
        """
    )

    st.subheader("OGLI statistical methodology")
    st.markdown(
        """
        OGLI measures how unusual current liquidity momentum is relative to historical
        observations. For each model, it combines **60% of the expanding z-score of 3-month
        annualized growth** with **40% of the expanding z-score of 12-month year-over-year
        growth**, then applies `100 * Phi(MomentumScore)`.

        The default expanding z-score requires 104 valid observations and uses only information
        available through each date. Full-sample normalization is available in package code for
        exploratory research only because it contains look-ahead. OGLI is not normalized against
        the historical maximum, so new liquidity highs do not mechanically rescale its history.

        The weights, history requirement, and regime boundaries are declared in
        `config/model.yaml`. They are Open Global Liquidity assumptions, not calibrated parameters.
        OGLI is an independent methodology and is not the proprietary CrossBorder Capital GLI.
        """
    )

    st.subheader("Market validation methodology")
    st.markdown(
        """
        The initial validation slice compares each model's OGLI momentum score with the Coin
        Metrics Bitcoin USD price. Horizon zero is the contemporaneous one-week return
        ending at the signal date.
        Positive horizons are forward simple returns through 4, 8, 12, 26, or 52 weeks. The
        observation-date view is retained for exploratory comparison. The default
        available-information view delays the weekly signal by one week because Wednesday H.4.1
        observations are normally published after that Wednesday's market close. This is a
        configurable availability assumption, not a real-time release-vintage archive.

        These choices are statistical transformations configured in `config/model.yaml`. The
        results are not used to select OGLI weights and therefore are not calibrated parameters.
        The dashboard defaults to non-overlapping return windows and retains the overlapping view
        for comparison. Correlations retain Fisher-transformed confidence intervals and add a
        deterministic circular moving-block bootstrap. Dashboard error bars use the bootstrap,
        whose 1,000 resamples, eight-observation blocks, and seed are declared in
        `config/model.yaml`. A block can cover much more than eight calendar weeks in a
        non-overlapping sample.
        These are transparent statistical assumptions, not calibrated parameters. Regime tables
        report means, medians, positive-return shares, and Student-t confidence intervals around
        means. Smaller non-overlapping samples and current-vintage revisions remain important
        limitations. Correlation does not establish causation.

        Coin Metrics publishes the daily `PriceUSD` metric in its community archive under CC BY-NC
        4.0. This project uses it only for independent, non-commercial research and attributes the
        source.
        """
    )

    st.subheader("Point-in-time snapshot provenance")
    st.markdown(
        """
        Every published Parquet snapshot has a companion manifest recording when the bundle was
        generated, the project version, the exact source-code commit, row and date coverage, and a
        SHA-256 content hash. The generation timestamp, source observation dates, and provider
        retrieval timestamps are deliberately separate: they answer different audit questions.

        Hashes establish byte-level integrity of the published files; they do not turn current-
        vintage FRED observations into historical release vintages. The separate monthly ALFRED
        pilot addresses revisions, but strict backtesting still requires source-specific release
        timestamps and availability rules.
        """
    )
    with st.container(border=True):
        st.markdown("#### :material/history: ALFRED point-in-time pilot")
        st.write(
            "A separate local command now fetches monthly ALFRED information sets and recalculates "
            "alignment, all three liquidity models, momentum, and expanding OGLI independently "
            "inside each one. It never enters the published current-vintage index silently."
        )
        st.code(
            "uv run ogli-point-in-time",
            language="zsh",
        )
        st.caption(
            "The existing FRED_API_KEY is sufficient. The pilot uses month-end information dates "
            "from January 2021 and compares revisions at the same weekly signal date."
        )
    provenance = _snapshot_provenance()
    if provenance is None:
        st.info(
            "Run the pipeline with `--publish-dashboard-snapshot` to create the provenance "
            "manifest.",
            icon=":material/info:",
        )
    else:
        generated_at = pd.to_datetime(provenance["generated_at"], utc=True)
        source_commit = str(provenance["source_commit"])
        source_label = source_commit[:8]
        if provenance["working_tree_dirty"] is True:
            source_label += " + local changes"
        with st.container(horizontal=True):
            st.metric("Snapshot generated", f"{generated_at:%Y-%m-%d %H:%M UTC}", border=True)
            st.metric("Pipeline version", str(provenance["pipeline_version"]), border=True)
            st.metric("Code source", source_label, border=True)
            st.metric("Hashed files", str(provenance["snapshot_count"]), border=True)
        files = provenance["files"]
        if isinstance(files, dict):
            manifest_table = pd.DataFrame(
                [
                    {
                        "file": filename,
                        "rows": metadata.get("rows"),
                        "latest_observation": metadata.get("latest_observation"),
                        "sha256": str(metadata.get("sha256", ""))[:12] + "…",
                    }
                    for filename, metadata in files.items()
                    if isinstance(metadata, dict)
                ]
            )
            with st.expander("Inspect the published file manifest"):
                st.dataframe(manifest_table, width="stretch", hide_index=True)

    st.subheader("Data sources and further reading")
    st.markdown(
        """
        **Series used by the US v0.1 research pipeline**

        - [WALCL — Federal Reserve total assets](https://fred.stlouisfed.org/series/WALCL)
        - [WDTGAL — Treasury General Account](https://fred.stlouisfed.org/series/WDTGAL)
        - [RRPONTSYD — Overnight reverse repo](https://fred.stlouisfed.org/series/RRPONTSYD)
        - [WRBWFRBL — Reserve balances](https://fred.stlouisfed.org/series/WRBWFRBL)
        - [Bitcoin PriceUSD — Coin Metrics community data](https://github.com/coinmetrics/data)
        - [DGS10 — 10-year Treasury yield](https://fred.stlouisfed.org/series/DGS10)
        - [DGS2 — 2-year Treasury yield](https://fred.stlouisfed.org/series/DGS2)
        - [DTWEXBGS — Nominal broad U.S. dollar index](https://fred.stlouisfed.org/series/DTWEXBGS)

        **Euro-area v0.2a measured-data pilot**

        - [ECB BSI total assets of the Eurosystem](https://data.ecb.europa.eu/data/concepts/statistical-balance-sheet)
          — monthly nominal EUR stock; not an OGLI input or global aggregate

        **Japan v0.2b measured-data pilot**

        - [BOJ Accounts total assets](https://www.boj.or.jp/en/statistics/boj/other/ac/index.htm)
          — database `BS01`, series `MABJMTA`, monthly native-yen stock; not an OGLI input or
          global aggregate

        **Primary documentation and broader context**

        - [Federal Reserve H.4.1 balance-sheet release](https://www.federalreserve.gov/releases/h41/default.htm)
        - [New York Fed: repo and reverse repo agreements](https://www.newyorkfed.org/markets/domestic-market-operations/monetary-policy-implementation/repo-reverse-repo-agreements)
        - [Coin Metrics metric documentation](https://docs.coinmetrics.io/)
        - [BIS: global liquidity indicators](https://www.bis.org/statistics/dataportal/gli.htm)
        - [BIS: global liquidity background and interpretation](https://www.bis.org/publ/qtrpdf/r_qt1503u.htm)
        """
    )

    st.warning(
        "Open Global Liquidity is independent and unaffiliated. It is inspired by publicly "
        "discussed global-liquidity concepts, including work by Michael Howell and CrossBorder "
        "Capital, but does not reproduce or claim access to their proprietary data, methodology, "
        "or models.",
        icon=":material/info:",
    )


home_page = st.Page(
    landing_page,
    title="Overview",
    icon=":material/home:",
    default=True,
)
data_page = st.Page(
    data_dashboard_page,
    title="Data dashboard",
    icon=":material/monitoring:",
    url_path="dashboard",
)
euro_area_data_page = st.Page(
    euro_area_page,
    title="Euro area data",
    icon=":material/public:",
    url_path="euro-area",
)
japan_data_page = st.Page(
    japan_page,
    title="Japan data",
    icon=":material/account_balance:",
    url_path="japan",
)
markets_index_page = st.Page(
    markets_page,
    title="Liquidity vs markets",
    icon=":material/query_stats:",
    url_path="markets",
)
bitcoin_page = st.Page(
    bitcoin_research_page,
    title="Bitcoin research",
    icon=":material/currency_bitcoin:",
    url_path="bitcoin-research",
)
ogli_index_page = st.Page(
    ogli_page,
    title="OGLI index",
    icon=":material/speed:",
    url_path="ogli",
)
guide_page = st.Page(
    research_guide_page,
    title="Research guide",
    icon=":material/menu_book:",
    url_path="research-guide",
)
vintage_page = st.Page(
    vintage_pilot_page,
    title="Vintage pilot",
    icon=":material/history:",
    url_path="vintage-pilot",
)
navigation = st.navigation(
    [
        home_page,
        ogli_index_page,
        vintage_page,
        bitcoin_page,
        markets_index_page,
        data_page,
        euro_area_data_page,
        japan_data_page,
        guide_page,
    ],
    position="top",
)
navigation.run()

st.divider()
st.caption(
    "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve "
    "Bank of St. Louis. [FRED API Terms of Use]"
    "(https://fred.stlouisfed.org/docs/api/terms_of_use.html) · Original project code: "
    "[Apache-2.0](https://github.com/y-sam/open-global-liquidity/blob/main/LICENSE) · "
    "Third-party data retain their own terms."
)
st.caption(
    "This service uses the Bank of Japan Time-Series Data Search API. The Bank of Japan does not "
    "guarantee this service's content."
)
