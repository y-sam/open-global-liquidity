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
    build_central_bank_index_comparison,
    latest_boe_readings,
    latest_boj_readings,
    latest_ecb_readings,
    latest_model_readings,
    latest_ogli_readings,
    latest_pboc_readings,
    latest_readings,
    load_auxiliary_bitcoin_pairs,
    load_auxiliary_bitcoin_summary,
    load_bitcoin_contrast_summary,
    load_bitcoin_outcomes,
    load_bitcoin_regime_summary,
    load_bitcoin_revision_summary,
    load_boe_data,
    load_boj_data,
    load_collateral_bitcoin_pairs,
    load_collateral_bitcoin_summary,
    load_collateral_composition,
    load_collateral_conditions,
    load_collateral_robustness,
    load_cross_border_credit,
    load_dashboard_data,
    load_data_quality_inventory,
    load_ecb_data,
    load_global_availability_registry,
    load_global_bitcoin_pairs,
    load_global_bitcoin_summary,
    load_global_central_bank_aggregate,
    load_global_central_bank_detail,
    load_liquidity_model_data,
    load_liquidity_signal_map,
    load_macro_context,
    load_market_comparisons,
    load_market_correlations,
    load_market_regime_statistics,
    load_market_subperiod_statistics,
    load_model_h,
    load_model_h_display_spec,
    load_ogli_data,
    load_pboc_data,
    load_point_in_time_comparison,
    load_point_in_time_market_pairs,
    load_point_in_time_market_summary,
    load_private_liquidity,
    load_repo_context,
    load_snapshot_manifest,
    prepare_global_index_display,
    resolve_dashboard_data_path,
)

DATA_ROOT = Path(os.environ.get("OGLI_DATA_ROOT", PROJECT_ROOT / "data"))
PROCESSED_DATA_PATH = DATA_ROOT / "processed" / "us_fred_series.parquet"
SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "us_fred_series_snapshot.parquet"
ECB_DATA_PATH = DATA_ROOT / "processed" / "euro_area_ecb_series.parquet"
ECB_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "euro_area_ecb_series_snapshot.parquet"
BOJ_DATA_PATH = DATA_ROOT / "processed" / "japan_boj_series.parquet"
BOJ_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "japan_boj_series_snapshot.parquet"
BOE_DATA_PATH = DATA_ROOT / "processed" / "uk_boe_series.parquet"
BOE_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "uk_boe_series_snapshot.parquet"
PBOC_DATA_PATH = DATA_ROOT / "processed" / "china_pboc_series.parquet"
PBOC_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "china_pboc_series_snapshot.parquet"
BIS_CHINA_DATA_PATH = DATA_ROOT / "processed" / "china_bis_series.parquet"
BIS_CHINA_SNAPSHOT_DATA_PATH = DATA_ROOT / "reference" / "china_bis_series_snapshot.parquet"
GLOBAL_AGGREGATE_DATA_PATH = DATA_ROOT / "processed" / "global_central_bank_assets.parquet"
GLOBAL_AGGREGATE_SNAPSHOT_DATA_PATH = (
    DATA_ROOT / "reference" / "global_central_bank_assets_snapshot.parquet"
)
GLOBAL_DETAIL_DATA_PATH = DATA_ROOT / "processed" / "global_central_bank_assets_detail.parquet"
GLOBAL_DETAIL_SNAPSHOT_DATA_PATH = (
    DATA_ROOT / "reference" / "global_central_bank_assets_detail_snapshot.parquet"
)
GLOBAL_AVAILABILITY_PATH = DATA_ROOT / "processed" / "global_availability_registry.parquet"
GLOBAL_AVAILABILITY_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "global_availability_registry_snapshot.parquet"
)
MODEL_H_DATA_PATH = DATA_ROOT / "processed" / "global_model_h.parquet"
MODEL_H_SNAPSHOT_PATH = DATA_ROOT / "reference" / "global_model_h_snapshot.parquet"
SIGNAL_MAP_PATH = DATA_ROOT / "processed" / "liquidity_signal_map.parquet"
SIGNAL_MAP_SNAPSHOT_PATH = DATA_ROOT / "reference" / "liquidity_signal_map_snapshot.parquet"
DATA_QUALITY_PATH = DATA_ROOT / "processed" / "data_quality_inventory.parquet"
DATA_QUALITY_SNAPSHOT_PATH = DATA_ROOT / "reference" / "data_quality_inventory_snapshot.parquet"
GLOBAL_BITCOIN_PAIRS_PATH = DATA_ROOT / "processed" / "global_central_bank_bitcoin_pairs.parquet"
GLOBAL_BITCOIN_PAIRS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "global_central_bank_bitcoin_pairs_snapshot.parquet"
)
GLOBAL_BITCOIN_SUMMARY_PATH = (
    DATA_ROOT / "processed" / "global_central_bank_bitcoin_summary.parquet"
)
GLOBAL_BITCOIN_SUMMARY_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "global_central_bank_bitcoin_summary_snapshot.parquet"
)
CROSS_BORDER_DATA_PATH = DATA_ROOT / "processed" / "global_cross_border_credit_indicators.parquet"
CROSS_BORDER_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "global_cross_border_credit_indicators_snapshot.parquet"
)
PRIVATE_LIQUIDITY_PATH = DATA_ROOT / "processed" / "us_private_liquidity_indicators.parquet"
PRIVATE_LIQUIDITY_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_private_liquidity_indicators_snapshot.parquet"
)
AUXILIARY_BITCOIN_PAIRS_PATH = DATA_ROOT / "processed" / "global_auxiliary_bitcoin_pairs.parquet"
AUXILIARY_BITCOIN_PAIRS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "global_auxiliary_bitcoin_pairs_snapshot.parquet"
)
AUXILIARY_BITCOIN_SUMMARY_PATH = (
    DATA_ROOT / "processed" / "global_auxiliary_bitcoin_summary.parquet"
)
AUXILIARY_BITCOIN_SUMMARY_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "global_auxiliary_bitcoin_summary_snapshot.parquet"
)
COLLATERAL_CONDITIONS_PATH = DATA_ROOT / "processed" / "us_collateral_conditions.parquet"
COLLATERAL_CONDITIONS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_collateral_conditions_snapshot.parquet"
)
COLLATERAL_SOURCE_PATH = DATA_ROOT / "processed" / "us_collateral_source.parquet"
COLLATERAL_SOURCE_SNAPSHOT_PATH = DATA_ROOT / "reference" / "us_collateral_source_snapshot.parquet"
COLLATERAL_ROBUSTNESS_PATH = DATA_ROOT / "processed" / "us_collateral_robustness.parquet"
COLLATERAL_ROBUSTNESS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_collateral_robustness_snapshot.parquet"
)
COLLATERAL_BITCOIN_PAIRS_PATH = DATA_ROOT / "processed" / "us_collateral_bitcoin_pairs.parquet"
COLLATERAL_BITCOIN_PAIRS_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_collateral_bitcoin_pairs_snapshot.parquet"
)
COLLATERAL_BITCOIN_SUMMARY_PATH = DATA_ROOT / "processed" / "us_collateral_bitcoin_summary.parquet"
COLLATERAL_BITCOIN_SUMMARY_SNAPSHOT_PATH = (
    DATA_ROOT / "reference" / "us_collateral_bitcoin_summary_snapshot.parquet"
)
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
    "insufficient_sample": "Estimate only — interval unavailable",
    "inconclusive": "Direction uncertain",
    "positive_interval": "Positive interval excludes zero",
    "negative_interval": "Negative interval excludes zero",
}


def _contrast_evidence_label(row: pd.Series) -> str:
    """Describe estimate direction separately from interval precision."""
    status = str(row["interval_status"])
    spread = row["mean_return_spread"]
    if status == "insufficient_sample":
        return "Estimate shown; too few observations for an interval"
    if status == "inconclusive":
        direction = "Positive" if spread > 0 else "Negative" if spread < 0 else "Flat"
        return f"{direction} estimate; interval crosses zero"
    return CONTRAST_STATUS_LABELS[status]


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
def _load_boe(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache measured Bank of England data until its file modification timestamp changes."""
    del modified_ns
    return load_boe_data(Path(path))


@st.cache_data(show_spinner=False)
def _load_pboc(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache measured PBoC data until its file modification timestamp changes."""
    del modified_ns
    return load_pboc_data(Path(path))


@st.cache_data(show_spinner=False)
def _load_global_aggregate(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache the package-calculated monthly aggregate."""
    del modified_ns
    return load_global_central_bank_aggregate(Path(path))


@st.cache_data(show_spinner=False)
def _load_global_detail(path: str, modified_ns: int) -> pd.DataFrame:
    """Cache the package-calculated aggregate contributions."""
    del modified_ns
    return load_global_central_bank_detail(Path(path))


@st.cache_data(show_spinner=False)
def _load_global_bitcoin_pairs(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_global_bitcoin_pairs(Path(path))


@st.cache_data(show_spinner=False)
def _load_global_bitcoin_summary(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_global_bitcoin_summary(Path(path))


@st.cache_data(show_spinner=False)
def _load_global_availability(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_global_availability_registry(Path(path))


@st.cache_data(show_spinner=False)
def _load_model_h(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_model_h(Path(path))


@st.cache_data(show_spinner=False)
def _load_signal_map(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_liquidity_signal_map(Path(path))


@st.cache_data(show_spinner=False)
def _load_data_quality(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_data_quality_inventory(Path(path))


@st.cache_data(show_spinner=False)
def _load_collateral_conditions(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_collateral_conditions(Path(path))


@st.cache_data(show_spinner=False)
def _load_cross_border_credit(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_cross_border_credit(Path(path))


@st.cache_data(show_spinner=False)
def _load_private_liquidity(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_private_liquidity(Path(path))


@st.cache_data(show_spinner=False)
def _load_auxiliary_bitcoin_pairs(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_auxiliary_bitcoin_pairs(Path(path))


@st.cache_data(show_spinner=False)
def _load_auxiliary_bitcoin_summary(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_auxiliary_bitcoin_summary(Path(path))


@st.cache_data(show_spinner=False)
def _load_collateral_composition(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_collateral_composition(Path(path))


@st.cache_data(show_spinner=False)
def _load_repo_context(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_repo_context(Path(path))


@st.cache_data(show_spinner=False)
def _load_collateral_robustness(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_collateral_robustness(Path(path))


@st.cache_data(show_spinner=False)
def _load_collateral_bitcoin_pairs(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_collateral_bitcoin_pairs(Path(path))


@st.cache_data(show_spinner=False)
def _load_collateral_bitcoin_summary(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return load_collateral_bitcoin_summary(Path(path))


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


def _boe_data() -> tuple[pd.DataFrame, Path, str]:
    path, origin = resolve_dashboard_data_path(BOE_DATA_PATH, BOE_SNAPSHOT_DATA_PATH)
    return _load_boe(str(path), path.stat().st_mtime_ns), path, origin


def _china_data() -> tuple[pd.DataFrame, Path, str]:
    """Prefer redistributable BIS China data; retain the direct PBoC table locally."""
    try:
        path, origin = resolve_dashboard_data_path(
            BIS_CHINA_DATA_PATH, BIS_CHINA_SNAPSHOT_DATA_PATH
        )
    except DashboardDataError:
        path, origin = resolve_dashboard_data_path(PBOC_DATA_PATH, PBOC_SNAPSHOT_DATA_PATH)
        origin = f"{origin} · private PBoC validation source"
    return _load_pboc(str(path), path.stat().st_mtime_ns), path, origin


def _global_data() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    aggregate_path, origin = resolve_dashboard_data_path(
        GLOBAL_AGGREGATE_DATA_PATH, GLOBAL_AGGREGATE_SNAPSHOT_DATA_PATH
    )
    detail_path, detail_origin = resolve_dashboard_data_path(
        GLOBAL_DETAIL_DATA_PATH, GLOBAL_DETAIL_SNAPSHOT_DATA_PATH
    )
    if detail_origin != origin:
        raise DashboardDataError("Global aggregate and detail use different data modes")
    return (
        _load_global_aggregate(str(aggregate_path), aggregate_path.stat().st_mtime_ns),
        _load_global_detail(str(detail_path), detail_path.stat().st_mtime_ns),
        origin,
    )


def _global_bitcoin_data() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    pairs_path, origin = resolve_dashboard_data_path(
        GLOBAL_BITCOIN_PAIRS_PATH, GLOBAL_BITCOIN_PAIRS_SNAPSHOT_PATH
    )
    summary_path, summary_origin = resolve_dashboard_data_path(
        GLOBAL_BITCOIN_SUMMARY_PATH, GLOBAL_BITCOIN_SUMMARY_SNAPSHOT_PATH
    )
    if summary_origin != origin:
        raise DashboardDataError("Global Bitcoin pairs and summary use different data modes")
    return (
        _load_global_bitcoin_pairs(str(pairs_path), pairs_path.stat().st_mtime_ns),
        _load_global_bitcoin_summary(str(summary_path), summary_path.stat().st_mtime_ns),
        origin,
    )


def _cross_border_data() -> tuple[pd.DataFrame, str]:
    path, origin = resolve_dashboard_data_path(CROSS_BORDER_DATA_PATH, CROSS_BORDER_SNAPSHOT_PATH)
    return _load_cross_border_credit(str(path), path.stat().st_mtime_ns), origin


def _global_availability_data() -> tuple[pd.DataFrame, str]:
    path, origin = resolve_dashboard_data_path(
        GLOBAL_AVAILABILITY_PATH, GLOBAL_AVAILABILITY_SNAPSHOT_PATH
    )
    return _load_global_availability(str(path), path.stat().st_mtime_ns), origin


def _model_h_data() -> tuple[pd.DataFrame, str]:
    path, origin = resolve_dashboard_data_path(MODEL_H_DATA_PATH, MODEL_H_SNAPSHOT_PATH)
    return _load_model_h(str(path), path.stat().st_mtime_ns), origin


def _signal_map_data() -> tuple[pd.DataFrame, str]:
    path, origin = resolve_dashboard_data_path(SIGNAL_MAP_PATH, SIGNAL_MAP_SNAPSHOT_PATH)
    return _load_signal_map(str(path), path.stat().st_mtime_ns), origin


def _data_quality_data() -> tuple[pd.DataFrame, str]:
    path, origin = resolve_dashboard_data_path(DATA_QUALITY_PATH, DATA_QUALITY_SNAPSHOT_PATH)
    return _load_data_quality(str(path), path.stat().st_mtime_ns), origin


def _private_liquidity_data() -> tuple[pd.DataFrame, str]:
    path, origin = resolve_dashboard_data_path(
        PRIVATE_LIQUIDITY_PATH, PRIVATE_LIQUIDITY_SNAPSHOT_PATH
    )
    return _load_private_liquidity(str(path), path.stat().st_mtime_ns), origin


def _auxiliary_bitcoin_data() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    pairs_path, origin = resolve_dashboard_data_path(
        AUXILIARY_BITCOIN_PAIRS_PATH, AUXILIARY_BITCOIN_PAIRS_SNAPSHOT_PATH
    )
    summary_path, summary_origin = resolve_dashboard_data_path(
        AUXILIARY_BITCOIN_SUMMARY_PATH, AUXILIARY_BITCOIN_SUMMARY_SNAPSHOT_PATH
    )
    if summary_origin != origin:
        raise DashboardDataError("Auxiliary Bitcoin pairs and summary use different data modes")
    return (
        _load_auxiliary_bitcoin_pairs(str(pairs_path), pairs_path.stat().st_mtime_ns),
        _load_auxiliary_bitcoin_summary(str(summary_path), summary_path.stat().st_mtime_ns),
        origin,
    )


def _collateral_data() -> tuple[pd.DataFrame, str]:
    path, origin = resolve_dashboard_data_path(
        COLLATERAL_CONDITIONS_PATH,
        COLLATERAL_CONDITIONS_SNAPSHOT_PATH,
    )
    return _load_collateral_conditions(str(path), path.stat().st_mtime_ns), origin


def _collateral_composition_data() -> tuple[pd.DataFrame, str]:
    path, origin = resolve_dashboard_data_path(
        COLLATERAL_SOURCE_PATH, COLLATERAL_SOURCE_SNAPSHOT_PATH
    )
    return _load_collateral_composition(str(path), path.stat().st_mtime_ns), origin


def _repo_context_data() -> tuple[pd.DataFrame, str]:
    path, origin = resolve_dashboard_data_path(
        COLLATERAL_SOURCE_PATH, COLLATERAL_SOURCE_SNAPSHOT_PATH
    )
    return _load_repo_context(str(path), path.stat().st_mtime_ns), origin


def _collateral_robustness_data() -> tuple[pd.DataFrame, str]:
    path, origin = resolve_dashboard_data_path(
        COLLATERAL_ROBUSTNESS_PATH, COLLATERAL_ROBUSTNESS_SNAPSHOT_PATH
    )
    return _load_collateral_robustness(str(path), path.stat().st_mtime_ns), origin


def _collateral_bitcoin_data() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    pairs_path, origin = resolve_dashboard_data_path(
        COLLATERAL_BITCOIN_PAIRS_PATH, COLLATERAL_BITCOIN_PAIRS_SNAPSHOT_PATH
    )
    summary_path, summary_origin = resolve_dashboard_data_path(
        COLLATERAL_BITCOIN_SUMMARY_PATH, COLLATERAL_BITCOIN_SUMMARY_SNAPSHOT_PATH
    )
    if summary_origin != origin:
        raise DashboardDataError("Collateral Bitcoin pairs and summary use different data modes")
    return (
        _load_collateral_bitcoin_pairs(str(pairs_path), pairs_path.stat().st_mtime_ns),
        _load_collateral_bitcoin_summary(str(summary_path), summary_path.stat().st_mtime_ns),
        origin,
    )


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
        labels={"date": "", "ogli": "Liquidity momentum index (0-100)"},
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


def _render_global_model_g_bitcoin(*, key_prefix: str, show_heading: bool = True) -> None:
    """Render the shared current-vintage Model G versus Bitcoin workspace."""
    if show_heading:
        st.subheader("Global Model G vs subsequent Bitcoin returns")
    st.badge(
        "Global Model G · five central banks · monthly",
        icon=":material/public:",
        color="blue",
    )
    st.caption(
        "Current-vintage global analysis. Model G combines central-bank assets for the United "
        "States, euro area, Japan, United Kingdom, and China after USD translation."
    )
    try:
        global_pairs, global_summary, global_market_origin = _global_bitcoin_data()
    except DashboardDataError:
        global_pairs = pd.DataFrame()
        global_summary = pd.DataFrame()
        global_market_origin = "Unavailable"
    if global_summary.empty:
        st.info(
            "The monthly Global Model G and Bitcoin comparison has not been generated in this "
            "environment.",
            icon=":material/currency_bitcoin:",
        )
        return

    lag_options = sorted(global_summary["availability_lag_months"].unique())
    horizon_options = sorted(global_summary["horizon_months"].unique())
    with st.container(horizontal=True):
        selected_global_lag = st.selectbox(
            "Assumed availability delay",
            lag_options,
            index=lag_options.index(2) if 2 in lag_options else 0,
            format_func=lambda value: f"{value} month{'s' if value != 1 else ''}",
            key=f"{key_prefix}_global_bitcoin_lag",
        )
        selected_global_sample = st.segmented_control(
            "Sample",
            ["Non-overlapping", "Overlapping"],
            default="Non-overlapping",
            key=f"{key_prefix}_global_bitcoin_sample",
        )
        selected_global_horizon = st.selectbox(
            "Forward horizon",
            horizon_options,
            index=horizon_options.index(3) if 3 in horizon_options else 0,
            format_func=lambda value: f"{value} month{'s' if value != 1 else ''}",
            key=f"{key_prefix}_global_bitcoin_horizon",
        )
    sample_key = "non_overlapping" if selected_global_sample == "Non-overlapping" else "overlapping"
    visible_summary = global_summary.loc[
        (global_summary["availability_lag_months"] == selected_global_lag)
        & (global_summary["sample_policy"] == sample_key)
    ].copy()
    selected_result = visible_summary.loc[
        visible_summary["horizon_months"] == selected_global_horizon
    ].iloc[0]
    with st.container(horizontal=True):
        st.metric(
            "Pearson correlation",
            (
                "Insufficient sample"
                if pd.isna(selected_result["correlation"])
                else f"{float(selected_result['correlation']):+.2f}"
            ),
            border=True,
        )
        st.metric("Paired observations", f"{int(selected_result['observations']):,}", border=True)
        st.metric(
            "Median Bitcoin return",
            f"{float(selected_result['median_return']):.1%}",
            border=True,
        )
        st.metric(
            "Positive outcomes",
            f"{float(selected_result['positive_share']):.0%}",
            border=True,
        )
    correlation_chart = px.bar(
        visible_summary,
        x="horizon_months",
        y="correlation",
        text="correlation",
        title="Model G momentum correlation with subsequent Bitcoin returns",
        labels={"horizon_months": "Forward horizon (months)", "correlation": "Correlation"},
    )
    correlation_chart.update_traces(
        marker_color="#D97706",
        texttemplate="%{text:+.2f}",
        textposition="outside",
    )
    correlation_chart.add_hline(y=0, line_color="gray", line_width=1)
    correlation_chart.update_yaxes(range=[-1, 1])
    correlation_chart.update_xaxes(dtick=1)
    st.plotly_chart(correlation_chart, width="stretch", config={"displaylogo": False})

    selected_pairs = global_pairs.loc[
        (global_pairs["availability_lag_months"] == selected_global_lag)
        & (global_pairs["horizon_months"] == selected_global_horizon)
    ].copy()
    if sample_key == "non_overlapping":
        selected_pairs = selected_pairs.loc[selected_pairs["is_non_overlapping"]]
    scatter = px.scatter(
        selected_pairs,
        x="global_cb_momentum_score",
        y="market_return",
        hover_data={"signal_date": "|%Y-%m-%d", "global_cb_regime": True},
        title="Monthly global central-bank momentum and later Bitcoin return",
        labels={
            "global_cb_momentum_score": "Global Model G momentum score",
            "market_return": "Subsequent Bitcoin return",
        },
    )
    scatter.update_yaxes(tickformat=".0%")
    st.plotly_chart(scatter, width="stretch", config={"displaylogo": False})
    st.warning(
        "This is a current-vintage descriptive comparison. The selected availability delay is "
        "an assumption because historical BIS release timestamps are not reconstructed. "
        "Correlation does not establish causation or an investable signal, and Bitcoin outcomes "
        "are never inputs to Model G.",
        icon=":material/warning:",
    )
    st.caption(f"Data mode: {global_market_origin} · Bitcoin: Coin Metrics Community Data")


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
    st.badge("Independent public-data research · v0.3 development", icon=":material/science:")
    st.title("See the financial system through a liquidity lens")
    st.markdown(
        """
        **Global liquidity is the ease with which financing can be created, obtained, and moved
        through the financial system.** It reflects more than central-bank money: bank balance
        sheets, credit creation, collateral, funding markets, and cross-border finance all matter.

        Open Global Liquidity turns public data into transparent, reproducible indicators. The
        project now has two deliberately separate layers: **Global Model G** measures momentum in
        the USD-normalized assets of five central banks, while **US OGLI Models A/B/C** remain
        higher-frequency domestic diagnostics. Model G is global central-bank liquidity—not yet a
        complete measure of global credit, collateral, or shadow-bank liquidity.
        """
    )

    try:
        global_aggregate, _global_detail, global_origin = _global_data()
    except DashboardDataError:
        global_aggregate = pd.DataFrame()
        global_origin = "Unavailable"
    if not global_aggregate.empty:
        global_latest = global_aggregate.iloc[-1]
        indexed = global_aggregate.dropna(subset=["global_cb_index"])
        global_index_latest = indexed.iloc[-1] if not indexed.empty else None
        st.subheader("Latest global central-bank snapshot")
        with st.container(horizontal=True):
            st.metric(
                "Five-bank assets",
                f"${float(global_latest['total_usd_trillions']):,.1f}tn",
                (
                    "Unavailable"
                    if pd.isna(global_latest["growth_yoy"])
                    else f"{float(global_latest['growth_yoy']):+.1%} year over year"
                ),
                border=True,
            )
            if global_index_latest is not None:
                st.metric(
                    "Global CB momentum index",
                    f"{float(global_index_latest['global_cb_index']):.1f}",
                    str(global_index_latest["global_cb_regime"]),
                    border=True,
                )
            st.metric(
                "Latest balanced month",
                f"{pd.Timestamp(global_latest['date']):%b %Y}",
                "Harmonized monthly BIS panel",
                border=True,
            )
            st.metric(
                "Coverage",
                f"{int(global_latest['component_count'])} central banks",
                global_origin,
                border=True,
            )
        st.caption(
            "Global Model G uses Federal Reserve, Eurosystem, Bank of Japan, Bank of England, and "
            "China central-bank assets translated into USD. Open the Global aggregate page for "
            "the formula, composition, FX audit trail, and full history."
        )

    try:
        signal_map, signal_origin = _signal_map_data()
    except DashboardDataError:
        signal_map = pd.DataFrame()
        signal_origin = "Unavailable"
    if not signal_map.empty:
        latest_signals = (
            signal_map.sort_values("available_date").groupby("channel", as_index=False).tail(1)
        )
        st.subheader("Liquidity signal map")
        st.caption(
            "Independent channel readings—not a combined forecast. Different observation and "
            "availability dates are retained."
        )
        with st.container(horizontal=True):
            for row in latest_signals.itertuples(index=False):
                with st.container(border=True):
                    st.markdown(f"**{row.channel_label}**")
                    st.metric("Index", f"{float(row.index_value):.1f}", str(row.regime))
                    st.caption(
                        f"{row.direction} · available {pd.Timestamp(row.available_date):%Y-%m-%d}"
                    )
        st.caption(f"Data mode: {signal_origin}.")

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

        st.subheader("Latest US liquidity diagnostics · Models A/B/C")
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
                estimable = primary_contrasts.loc[
                    primary_contrasts["interval_status"] != "insufficient_sample"
                ]
                st.info(
                    f"Uncertainty check: {len(estimable)} of {len(primary_contrasts)} primary "
                    "horizons have estimable intervals, and none currently excludes zero. The "
                    "point estimates remain visible; this means the sample cannot determine "
                    "their direction precisely, not that the calculation failed.",
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
    st.title("Open liquidity momentum indices")
    st.caption(
        "Global Model G plus three US/Fed research definitions. Every index is an independent "
        "Open Global Liquidity methodology—not CrossBorder Capital's proprietary GLI."
    )
    global_data = pd.DataFrame()
    global_origin = "Unavailable"
    try:
        global_aggregate, _global_detail, global_origin = _global_data()
        global_data = prepare_global_index_display(global_aggregate)
    except DashboardDataError:
        pass

    us_data = pd.DataFrame()
    us_origin = "Unavailable"
    try:
        us_data, us_origin = _ogli_data()
        latest_by_model = latest_ogli_readings(us_data)
    except DashboardDataError:
        latest_by_model = pd.DataFrame()
    if global_data.empty and us_data.empty:
        st.error("Neither the global nor US liquidity-index dataset is available.")
        st.code(
            "uv run python -m open_global_liquidity.pipeline",
            language="zsh",
        )
        return

    model_options: dict[str, str] = {}
    if not global_data.empty:
        model_options["Global Model G — five central banks"] = "global_model_g"
    if not latest_by_model.empty:
        model_options.update(
            {
                f"US · {name}": model_id
                for name, model_id in latest_by_model[["model_name", "model_id"]].itertuples(
                    index=False, name=None
                )
            }
        )
    with st.sidebar:
        st.header("Index controls")
        selected_name = st.selectbox(
            "Liquidity definition",
            list(model_options),
            index=0,
        )
        history = st.segmented_control(
            "History",
            ["1 year", "3 years", "5 years", "All"],
            default="5 years",
            key="ogli_history",
        )

    model_id = model_options[selected_name]
    is_global = model_id == "global_model_g"
    if is_global:
        model_data = global_data.copy()
        data_origin = global_origin
        model_data["model_name"] = "Global Model G — central-bank assets momentum"
        frequency_label = "Monthly"
        short_growth_label = "1m annualized growth"
        index_label = "Global Model G"
    else:
        model_data = us_data.loc[(us_data["model_id"] == model_id) & us_data["ogli"].notna()].copy()
        model_data = model_data.rename(
            columns={"ogli": "index_value", "growth_3m_annualized": "short_growth"}
        )
        data_origin = us_origin
        frequency_label = "Weekly"
        short_growth_label = "3m annualized growth"
        index_label = "US OGLI"
    with st.sidebar:
        st.caption(f"Scope: {'Global central banks' if is_global else 'United States / Fed'}")
        st.caption(f"Frequency: {frequency_label}")
        st.caption(f"Data mode: {data_origin}")

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
            index_label,
            f"{latest['index_value']:.1f}",
            border=True,
            chart_data=model_data["index_value"].tail(26).tolist(),
        )
        st.metric("Liquidity regime", str(latest["regime"]), border=True)
        st.metric(
            "Momentum score", f"{latest['momentum_score']:+.2f} standard deviations", border=True
        )
        st.metric(
            short_growth_label,
            f"{latest['short_growth']:.1%}",
            border=True,
        )
        st.metric("12m YoY growth", f"{latest['growth_12m_yoy']:.1%}", border=True)

    st.plotly_chart(
        _ogli_figure(
            visible.rename(columns={"index_value": "ogli"}),
            f"{selected_name} · normalized momentum history",
        ),
        width="stretch",
        config={"displaylogo": False},
    )
    st.caption(
        f"Latest reading {latest['date']:%Y-%m-%d} · "
        f"{latest['zscore_mode']} z-score · minimum {latest['zscore_min_periods']} observations"
    )

    with st.container(border=True):
        st.subheader("How to read the selected index")
        st.markdown(
            """
            The index measures how unusual current liquidity momentum is relative to its own
            historical observations. It uses z-score normalization and the standard normal
            cumulative distribution function. It is not normalized against the historical
            maximum, so new liquidity highs do not mechanically rescale the historical index.

            **Around 50 is statistically neutral.** Higher readings indicate momentum above its
            historical norm; lower readings indicate momentum below its historical norm. This is
            a relative momentum measure, not the dollar level of liquidity and not a forecast.
            """
        )

    with st.expander("Formula, weights, and regimes"):
        short_formula = "1m annualized growth" if is_global else "3m annualized growth"
        output_name = "Global Model G" if is_global else "US OGLI"
        st.code(
            f"Momentum = 0.60 * z({short_formula}) + 0.40 * z(12m YoY growth)\n"
            f"{output_name} = 100 * Phi(Momentum)",
            language=None,
        )
        st.write(
            "The 60/40 weights and regime thresholds are configurable Open Global Liquidity "
            "research assumptions. They are not calibrated parameters and are not Howell or "
            "CrossBorder Capital parameters."
        )
        if is_global:
            st.info(
                "Global Model G aggregates Federal Reserve, Eurosystem, Bank of Japan, Bank of "
                "England, and China central-bank total assets after USD conversion. It is global "
                "central-bank liquidity, not yet a complete global OGLI covering private credit, "
                "repo, collateral, offshore dollars, or shadow banking.",
                icon=":material/public:",
            )
        else:
            st.info(
                "Models A/B/C use only US Federal Reserve-related inputs. They remain available as "
                "domestic diagnostics and are not presented as global models.",
                icon=":material/account_balance:",
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
        loaded = None
        us_research_error = str(exc)
    else:
        us_research_error = None
    if loaded is None:
        with st.sidebar:
            st.header("Bitcoin research controls")
            st.selectbox(
                "Liquidity definition",
                ["Global Model G — five central banks"],
                key="bitcoin_model",
            )
        _render_global_model_g_bitcoin(key_prefix="bitcoin_research", show_heading=False)
        st.info(
            (
                f"US point-in-time research is unavailable: {us_research_error}"
                if us_research_error is not None
                else "US point-in-time research outputs have not been generated in this "
                "environment. The existing FRED key is sufficient and Coin Metrics Community "
                "Data requires no key."
            ),
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
    us_model_options = dict(
        outcomes[["model_name", "model_id"]].drop_duplicates().itertuples(index=False)
    )
    model_options = {"Global Model G — five central banks": "global_model_g", **us_model_options}
    with st.sidebar:
        st.header("Bitcoin research controls")
        selected_name = st.selectbox(
            "Liquidity definition",
            list(model_options),
            index=0,
            key="bitcoin_model",
        )
        if model_options[selected_name] != "global_model_g":
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
        if model_options[selected_name] == "global_model_g":
            st.caption("Global monthly controls and data provenance are shown in the workspace.")
        else:
            st.caption(f"US point-in-time data mode: {data_origin}")

    model_id = model_options[selected_name]
    if model_id == "global_model_g":
        _render_global_model_g_bitcoin(key_prefix="bitcoin_research", show_heading=False)
        return

    st.badge(
        "US point-in-time: Model B · 1-week delay · non-overlapping · 1/3/6/12 months",
        icon=":material/check_circle:",
        color="blue",
    )
    st.caption(
        "This primary US display policy is a predeclared model assumption. Change any control to "
        "inspect robustness alternatives; no Bitcoin outcome was used to calculate OGLI."
    )
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
            st.metric("Evidence status", _contrast_evidence_label(contrast_row), border=True)
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
        contrast_history["evidence_status"] = contrast_history.apply(
            _contrast_evidence_label, axis=1
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
                    "evidence_status",
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
                "evidence_status": st.column_config.TextColumn("Evidence status"),
            },
        )
        st.caption(
            "Expansionary regimes are Above normal, Expansion, and Strong expansion. "
            "Contractionary regimes are Below normal, Contraction, and Strong contraction. "
            "Neutral observations are excluded. Error bars are classical Welch intervals and "
            "do not adjust for serial dependence, multiple comparisons, or data revisions."
        )
        with st.expander("Why are the intervals often wide—and what do all combinations show?"):
            status_counts = contrast_summaries["interval_status"].value_counts()
            st.markdown(
                f"The point-in-time pilot starts in 2021. Non-overlapping sampling, longer "
                f"forward horizons, and the expansionary/contractionary split sharply reduce "
                f"independent observations. Across all **{len(contrast_summaries)}** predeclared "
                f"model, lag, horizon, and sample combinations: "
                f"**{int(status_counts.get('positive_interval', 0))}** have a positive interval "
                f"excluding zero, **{int(status_counts.get('negative_interval', 0))}** have a "
                "negative interval excluding zero, "
                f"**{int(status_counts.get('inconclusive', 0))}** "
                f"cross zero, and **{int(status_counts.get('insufficient_sample', 0))}** cannot "
                "estimate an interval. These are robustness diagnostics, not independent tests or "
                "a parameter-selection menu."
            )
            robustness = contrast_summaries.copy()
            robustness["Evidence status"] = robustness.apply(_contrast_evidence_label, axis=1)
            st.dataframe(
                robustness[
                    [
                        "model_name",
                        "publication_lag_weeks",
                        "horizon_months",
                        "sample_policy",
                        "expansionary_observations",
                        "contractionary_observations",
                        "mean_return_spread",
                        "Evidence status",
                    ]
                ],
                width="stretch",
                hide_index=True,
                column_config={
                    "model_name": "US liquidity model",
                    "publication_lag_weeks": "Delay (weeks)",
                    "horizon_months": "Horizon (months)",
                    "sample_policy": "Sample",
                    "expansionary_observations": "Expansionary n",
                    "contractionary_observations": "Contractionary n",
                    "mean_return_spread": st.column_config.NumberColumn(
                        "Mean spread", format="percent"
                    ),
                },
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
        comparisons = None
        correlations = pd.DataFrame(
            columns=["model_name", "model_id", "analysis_mode", "sample_policy"]
        )
        data_origin = "US comparison unavailable"
        us_market_error = str(exc)
    else:
        us_market_error = None
    if comparisons is not None:
        _show_freshness(comparisons, "Bitcoin/OGLI comparison")

    us_model_options = dict(
        correlations[["model_name", "model_id"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    model_options = {"Global Model G — five central banks": "global_model_g", **us_model_options}
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
            index=0,
            key="market_model",
        )
        if model_options[selected_model] != "global_model_g":
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
        if model_options[selected_model] == "global_model_g":
            st.caption("Global monthly controls and data provenance are shown in the workspace.")
        else:
            st.caption(f"US/Fed data mode: {data_origin}")

    model_id = model_options[selected_model]
    if model_id == "global_model_g":
        _render_global_model_g_bitcoin(key_prefix="markets", show_heading=False)
        return
    if us_market_error is not None:
        st.info(us_market_error, icon=":material/info:")
        st.markdown(
            "US/Fed Bitcoin comparison files are unavailable. Run the pipeline to refresh the "
            "public Coin Metrics market snapshot:"
        )
        st.code(
            "uv run python -m open_global_liquidity.pipeline --start 2020-01-01",
            language="zsh",
        )
        return
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


def united_kingdom_page() -> None:
    """Present official Bank of England total assets without implying a global aggregate."""
    st.title("United Kingdom measured data")
    st.caption(
        "v0.2c expansion pilot · official quarterly Bank of England data in native sterling · "
        "no FX conversion, UK liquidity model, or global aggregation"
    )
    try:
        data, _path, origin = _boe_data()
    except DashboardDataError as exc:
        st.info(str(exc), icon=":material/account_balance:")
        st.code(
            "uv run python -m open_global_liquidity.pipeline --publish-dashboard-snapshot",
            language="zsh",
        )
        st.markdown("The Bank of England database download is public and requires **no API key**.")
        return

    latest = latest_boe_readings(data).iloc[0]
    level = float(latest["value_gbp_billions"])
    quarterly_change = latest["change_gbp_billions"]
    growth_yoy = latest["growth_yoy"]
    retrieved_at = pd.to_datetime(latest["retrieved_at"], utc=True)
    with st.container(horizontal=True):
        st.metric(
            "Bank of England total assets",
            f"£{level:,.1f}bn",
            (
                None
                if pd.isna(quarterly_change)
                else f"£{float(quarterly_change):+,.1f}bn vs prior quarter"
            ),
            border=True,
        )
        st.metric(
            "12-month change",
            "Unavailable" if pd.isna(growth_yoy) else f"{float(growth_yoy):+.1%}",
            border=True,
        )
        st.metric("Latest observation", f"{latest['date']:%d %b %Y}", border=True)
        st.metric("Data mode", origin, border=True)

    max_date = data["date"].max()
    history = st.segmented_control(
        "History", ["5 years", "10 years", "All"], default="10 years", key="uk_history"
    )
    if history == "All":
        visible = data
    else:
        years = 5 if history == "5 years" else 10
        visible = data.loc[data["date"] >= max_date - pd.DateOffset(years=years)]
    chart_data = visible.rename(columns={"date": "Date", "value_gbp_billions": "GBP billions"})
    st.line_chart(
        chart_data,
        x="Date",
        y="GBP billions",
        x_label="Observation date",
        y_label="GBP billions",
    )
    st.info(
        "Dates and levels are preserved from the quarterly consolidated BoE series. The complete "
        "balance sheet is published with a five-quarter lag. Values remain nominal GBP stocks "
        "and are not inputs to the US OGLI.",
        icon=":material/info:",
    )
    st.subheader("Recent observations")
    recent = data.tail(12).assign(
        date=lambda frame: frame["date"].dt.strftime("%Y-%m-%d"),
        value_gbp_billions=lambda frame: frame["value_gbp_billions"].round(1),
    )
    st.dataframe(
        recent[["date", "value_gbp_billions", "series_id"]].rename(
            columns={
                "date": "Observation date",
                "value_gbp_billions": "GBP billions",
                "series_id": "BoE series",
            }
        ),
        column_config={"GBP billions": st.column_config.NumberColumn(format="localized")},
        width="stretch",
        hide_index=True,
    )
    st.caption(
        f"Retrieved {retrieved_at:%Y-%m-%d %H:%M UTC} · Provider: Bank of England · "
        "Series RPQB75A · quarterly, not seasonally adjusted · five-quarter publication lag"
    )
    st.link_button(
        "Review official BoE metadata",
        "https://www.bankofengland.co.uk/boeapps/database/index.asp?EC=RPQB75A&From=Template",
        icon=":material/open_in_new:",
    )


def china_page() -> None:
    """Present the redistributable BIS China central-bank total-assets series."""
    st.title("China measured data")
    st.caption(
        "v0.3 source transition · monthly BIS-spliced China central-bank total assets in native "
        "renminbi · direct PBoC observations remain a local validation source"
    )
    try:
        data, _path, origin = _china_data()
    except DashboardDataError:
        st.info(
            "China central-bank observations have not yet been generated in this environment. "
            "Run the pipeline to fetch the public BIS series and the local PBoC validation table.",
            icon=":material/license:",
        )
        st.code(
            "uv run python -m open_global_liquidity.pipeline --force-refresh",
            language="zsh",
        )
        st.markdown("The BIS API and official PBoC archive require **no account or API key**.")
        with st.container(horizontal=True):
            st.link_button(
                "Review BIS series",
                "https://data.bis.org/topics/CBTA/BIS,WS_CBTA,1.0/M.CN.B.XDC.CNY.N",
                icon=":material/open_in_new:",
            )
            st.link_button(
                "Review BIS permitted use",
                "https://data.bis.org/help/legal",
                icon=":material/open_in_new:",
            )
        return

    latest = latest_pboc_readings(data).iloc[0]
    level = float(latest["value_cny_billions"])
    monthly_change = latest["change_cny_billions"]
    growth_yoy = latest["growth_yoy"]
    retrieved_at = pd.to_datetime(latest["retrieved_at"], utc=True)
    with st.container(horizontal=True):
        st.metric(
            "China central-bank assets",
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
        "History", ["5 years", "10 years", "All"], default="10 years", key="china_history"
    )
    if history == "All":
        visible = data
    else:
        years = 5 if history == "5 years" else 10
        visible = data.loc[data["date"] >= max_date - pd.DateOffset(years=years)]
    chart_data = visible.rename(columns={"date": "Date", "value_cny_billions": "CNY billions"})
    st.line_chart(
        chart_data,
        x="Date",
        y="CNY billions",
        x_label="Period end",
        y_label="CNY billions",
    )
    st.info(
        "Monthly dates are calendar month-end period labels, not modeled publication timestamps. "
        "The BIS series is a BIS-spliced compilation and, from January 2002, uses the monthly PBoC "
        "balance sheet. Values remain nominal CNY stocks and are not inputs to the US OGLI.",
        icon=":material/info:",
    )
    st.subheader("Recent observations")
    recent = data.tail(12).assign(
        date=lambda frame: frame["date"].dt.strftime("%Y-%m-%d"),
        value_cny_billions=lambda frame: frame["value_cny_billions"].round(1),
    )
    st.dataframe(
        recent[["date", "value_cny_billions", "series_id"]].rename(
            columns={
                "date": "Period end",
                "value_cny_billions": "CNY billions",
                "series_id": "BIS series key or private project identifier",
            }
        ),
        column_config={"CNY billions": st.column_config.NumberColumn(format="localized")},
        width="stretch",
        hide_index=True,
    )
    st.caption(
        f"Retrieved {retrieved_at:%Y-%m-%d %H:%M UTC} · Provider: {latest['provider']} · "
        "China central-bank total assets · nominal CNY billions"
    )
    with st.container(horizontal=True):
        st.link_button(
            "Review BIS series",
            "https://data.bis.org/topics/CBTA/BIS,WS_CBTA,1.0/M.CN.B.XDC.CNY.N",
            icon=":material/open_in_new:",
        )
        st.link_button(
            "BIS permitted-use terms",
            "https://data.bis.org/help/legal",
            icon=":material/license:",
        )


def central_banks_page() -> None:
    """Compare central-bank asset changes without constructing a global aggregate."""
    st.title("Central-bank balance sheets")
    st.caption(
        "v0.2 cross-country comparison · separate native-currency series rebased to 100 · no FX "
        "conversion, country weights, interpolation, or global OGLI"
    )
    choices = {"5 years": 5, "10 years": 10, "Since 2013": 13}
    history = st.segmented_control(
        "Comparison window",
        list(choices),
        default="5 years",
        key="central_bank_history",
    )
    start = pd.Timestamp.now().normalize() - pd.DateOffset(years=choices[history])

    sources: dict[str, pd.DataFrame] = {}
    metadata: list[dict[str, object]] = []

    try:
        us, _path, _origin = _source_data()
        fed = us.loc[us["component"] == "fed_assets"].copy()
        sources["Federal Reserve"] = fed[["date", "value_usd_billions"]].rename(
            columns={"value_usd_billions": "native_value"}
        )
        metadata.append(
            {
                "Central bank": "Federal Reserve",
                "Native unit": "USD billions",
                "Frequency": "Weekly",
                "Latest period": fed["date"].max(),
            }
        )
    except DashboardDataError:
        pass

    loaders = [
        ("Eurosystem", _ecb_data, "value_eur_billions", "EUR billions", "Monthly"),
        ("Bank of Japan", _boj_data, "value_jpy_billions", "JPY billions", "Monthly"),
        ("Bank of England", _boe_data, "value_gbp_billions", "GBP billions", "Quarterly"),
        ("China", _china_data, "value_cny_billions", "CNY billions", "Monthly"),
    ]
    unavailable: list[str] = []
    for label, loader, value_column, unit, frequency in loaders:
        try:
            frame, _path, _origin = loader()
        except DashboardDataError:
            unavailable.append(label)
            continue
        sources[label] = frame[["date", value_column]].rename(
            columns={value_column: "native_value"}
        )
        metadata.append(
            {
                "Central bank": label,
                "Native unit": unit,
                "Frequency": frequency,
                "Latest period": frame["date"].max(),
            }
        )

    comparison = build_central_bank_index_comparison(sources, start=start)
    latest_index = comparison.sort_values("date").groupby("central_bank", as_index=False).tail(1)
    with st.container(horizontal=True):
        st.metric("Series available", str(comparison["central_bank"].nunique()), border=True)
        st.metric(
            "Largest cumulative rise",
            str(latest_index.loc[latest_index["index"].idxmax(), "central_bank"]),
            f"{latest_index['index'].max() - 100:+.1f}%",
            border=True,
        )
        st.metric("Method", "Native-currency index", "First observation = 100", border=True)

    figure = px.line(
        comparison,
        x="date",
        y="index",
        color="central_bank",
        title=f"Central-bank total assets · {history.lower()} · independently rebased",
        labels={"date": "Date", "index": "Index", "central_bank": "Central bank"},
    )
    figure.add_hline(y=100, line_dash="dot", line_color="gray")
    figure.update_traces(line={"width": 2.3}, hovertemplate="%{x|%b %Y}<br>%{y:.1f}<extra></extra>")
    figure.update_layout(
        hovermode="x unified",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(figure, width="stretch", config={"displaylogo": False})
    st.warning(
        "The lines compare percentage changes in separate native-currency balance sheets. They do "
        "not compare absolute size and must not be added together. Different frequencies, release "
        "lags, accounting frameworks, and institutional structures remain visible limitations.",
        icon=":material/warning:",
    )
    if unavailable:
        st.info(
            "Unavailable in this environment: " + ", ".join(unavailable) + ".",
            icon=":material/license:",
        )
    st.subheader("Source coverage")
    coverage = pd.DataFrame(metadata)
    coverage["Latest period"] = pd.to_datetime(coverage["Latest period"]).dt.strftime("%Y-%m-%d")
    st.dataframe(coverage, width="stretch", hide_index=True)


def global_aggregate_page() -> None:
    """Present the v0.3 balanced monthly USD central-bank asset aggregate."""
    st.title("Global central-bank aggregate")
    st.caption(
        "v0.3 monthly research panel · BIS-spliced United States, euro area, Japan, United "
        "Kingdom, and China total assets · translated at month-end spot FX rates"
    )
    try:
        aggregate, detail, origin = _global_data()
    except DashboardDataError:
        st.info(
            "The v0.3 aggregate has not been generated in this environment. Run the pipeline to "
            "download the BIS central-bank series and four public H.10 exchange rates.",
            icon=":material/currency_exchange:",
        )
        st.code("uv run python -m open_global_liquidity.pipeline", language="zsh")
        return

    latest = aggregate.iloc[-1]
    latest_index_rows = aggregate.dropna(subset=["global_cb_index"])
    latest_index = latest_index_rows.iloc[-1] if not latest_index_rows.empty else None
    latest_date = pd.Timestamp(latest["date"])
    latest_detail = detail.loc[detail["date"] == latest_date].copy()
    latest_detail["share"] = (
        latest_detail["value_usd_millions"] / latest_detail["value_usd_millions"].sum()
    )
    with st.container(horizontal=True):
        st.metric(
            "Combined assets",
            f"${float(latest['total_usd_trillions']):,.1f}tn",
            (
                "Unavailable"
                if pd.isna(latest["change_1m"])
                else f"{float(latest['change_1m']):+.1%} month over month"
            ),
            border=True,
        )
        st.metric(
            "12-month change",
            "Unavailable"
            if pd.isna(latest["growth_yoy"])
            else f"{float(latest['growth_yoy']):+.1%}",
            border=True,
        )
        st.metric("Latest balanced month", f"{latest_date:%b %Y}", border=True)
        st.metric(
            "Coverage", f"{int(latest['component_count'])} central banks", origin, border=True
        )

    st.subheader("Global Model G — central-bank assets momentum")
    if latest_index is None:
        st.info(
            "The expanding normalization does not yet have the configured 60 monthly growth "
            "observations.",
            icon=":material/history:",
        )
    else:
        with st.container(horizontal=True):
            st.metric(
                "Global CB momentum index",
                f"{float(latest_index['global_cb_index']):.1f}",
                str(latest_index["global_cb_regime"]),
                border=True,
            )
            st.metric(
                "Momentum score",
                f"{float(latest_index['global_cb_momentum_score']):+.2f}",
                "Expanding z-score",
                border=True,
            )
            st.metric(
                "Latest indexed month",
                f"{pd.Timestamp(latest_index['date']):%b %Y}",
                "Five-bank monthly panel",
                border=True,
            )
        index_figure = px.line(
            latest_index_rows,
            x="date",
            y="global_cb_index",
            title="Global central-bank balance-sheet momentum · non-look-ahead normalization",
            labels={"date": "Month end", "global_cb_index": "0-100 index"},
        )
        index_figure.add_hline(y=50, line_dash="dot", line_color="gray")
        index_figure.update_yaxes(range=[0, 100])
        index_figure.update_traces(line={"width": 2.7, "color": "#7C3AED"})
        st.plotly_chart(index_figure, width="stretch", config={"displaylogo": False})
        st.caption(
            "60% expanding z-score of one-month annualized growth + 40% expanding z-score of "
            "12-month growth, mapped through the standard normal CDF. Around 50 is neutral "
            "relative to information available through that month. Weights are assumptions."
        )

    _render_global_model_g_bitcoin(key_prefix="global_aggregate")

    st.subheader("Global Model H — broader liquidity challenger")
    try:
        model_h, model_h_origin = _model_h_data()
    except DashboardDataError:
        st.info("Model H descriptive history will appear after the next public data refresh.")
    else:
        latest_h = model_h.iloc[-1]
        with st.container(horizontal=True):
            st.metric("Latest Model H", f"{float(latest_h['model_h_index']):.1f}", border=True)
            st.metric(
                "Momentum score",
                f"{float(latest_h['model_h_momentum_score']):+.2f}",
                border=True,
            )
            st.metric(
                "Available after",
                f"{pd.Timestamp(latest_h['signal_available_date']):%b %Y}",
                border=True,
            )
        h_chart = px.line(
            model_h,
            x="date",
            y="model_h_index",
            labels={"date": "Quarter end", "model_h_index": "0-100 index"},
            title="Model H descriptive history · three equal-weight liquidity pillars",
        )
        h_chart.add_hline(y=50, line_dash="dot", line_color="gray")
        h_chart.update_yaxes(range=[0, 100])
        h_chart.update_traces(line={"width": 2.7, "color": "#0D9488"})
        st.plotly_chart(h_chart, width="stretch", config={"displaylogo": False})
        st.warning(
            "This history was calculated after the Model H design was frozen and is therefore "
            "post-specification descriptive—not prospective validation. Model G remains the "
            "production global index. No Bitcoin outcomes were used in this calculation.",
            icon=":material/science:",
        )
        st.caption(f"Data mode: {model_h_origin}.")

    figure = px.line(
        aggregate,
        x="date",
        y="total_usd_trillions",
        title="Selected central-bank total assets translated into U.S. dollars",
        labels={"date": "Month end", "total_usd_trillions": "USD trillions"},
    )
    figure.update_traces(line={"width": 2.7, "color": "#2563EB"})
    figure.update_layout(
        hovermode="x unified",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(figure, width="stretch", config={"displaylogo": False})

    st.subheader(f"Composition at {latest_date:%b %Y}")
    contribution_chart = px.bar(
        latest_detail.sort_values("value_usd_millions", ascending=False),
        x="central_bank",
        y="value_usd_millions",
        text="share",
        labels={"central_bank": "Central bank", "value_usd_millions": "USD millions"},
    )
    contribution_chart.update_traces(
        marker_color="#D97706",
        texttemplate="%{text:.1%}",
        hovertemplate="%{x}<br>$%{y:,.0f}m<extra></extra>",
    )
    contribution_chart.update_layout(
        margin={"l": 10, "r": 10, "t": 15, "b": 10},
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(contribution_chart, width="stretch", config={"displaylogo": False})

    st.warning(
        "Model G is a global central-bank balance-sheet model, not a complete global OGLI. "
        "Changes reflect "
        "both native balance-sheet movements and exchange-rate translation. The balanced panel "
        "uses harmonized monthly BIS-spliced series through their latest common period. "
        "Conservative publication delays are documented in the availability registry, but "
        "historical value vintages are not reconstructed.",
        icon=":material/warning:",
    )
    with st.expander("Method and audit trail"):
        st.markdown(
            """
            - **Measured data:** five BIS central-bank total-asset series and four Federal Reserve
              H.10 spot exchange rates.
            - **Model assumptions:** month-end frequency, latest-prior observations within
              configured staleness limits, period-end FX translation, and a complete five-bank
              balanced panel.
            - **Calibrated parameters:** none.
            - Direct USD quotes multiply native-currency millions; inverse quotes divide them.
              Missing values are never interpolated.
            """
        )
        audit = latest_detail.assign(
            source_date=lambda frame: frame["source_date"].dt.strftime("%Y-%m-%d"),
            fx_date=lambda frame: frame["fx_date"].dt.strftime("%Y-%m-%d"),
            value_usd_billions=lambda frame: frame["value_usd_millions"] / 1_000,
        )
        st.dataframe(
            audit[
                [
                    "central_bank",
                    "source_series_id",
                    "source_date",
                    "native_unit",
                    "fx_component",
                    "fx_series_id",
                    "fx_date",
                    "fx_rate",
                    "value_usd_billions",
                ]
            ].rename(
                columns={
                    "central_bank": "Central bank",
                    "source_series_id": "BIS series",
                    "source_date": "Source observation",
                    "native_unit": "Native unit",
                    "fx_component": "FX input",
                    "fx_series_id": "H.10 series",
                    "fx_date": "FX observation",
                    "fx_rate": "FX rate",
                    "value_usd_billions": "USD billions",
                }
            ),
            width="stretch",
            hide_index=True,
        )

    st.subheader("Availability and vintage coverage")
    try:
        availability, availability_origin = _global_availability_data()
    except DashboardDataError:
        st.info("The availability registry will appear after the next public data refresh.")
    else:
        display = availability.assign(
            assumed_lag=lambda frame: frame.apply(
                lambda row: (
                    f"{int(row['conservative_lag_months'])} months"
                    if int(row["conservative_lag_months"]) > 0
                    else f"{int(row['conservative_lag_days'])} days"
                ),
                axis=1,
            )
        )
        st.dataframe(
            display[
                [
                    "component",
                    "provider",
                    "model_role",
                    "assumed_lag",
                    "historical_release_calendar",
                    "historical_value_vintages",
                ]
            ].rename(
                columns={
                    "component": "Model input",
                    "provider": "Provider",
                    "model_role": "Role",
                    "assumed_lag": "Conservative lag",
                    "historical_release_calendar": "Release calendar",
                    "historical_value_vintages": "Historical vintages",
                }
            ),
            width="stretch",
            hide_index=True,
        )
        st.warning(
            "This registry supports lag-adjusted current-vintage research. It does not make "
            "Global Model G genuinely point-in-time because historical BIS value vintages have "
            "not been reconstructed.",
            icon=":material/history:",
        )
        st.caption(
            f"Registry as of {availability['registry_as_of'].max():%d %b %Y} · "
            f"Data mode: {availability_origin}"
        )


def _render_auxiliary_bitcoin_validation(model_id: str) -> None:
    """Render package-calculated, predeclared auxiliary-signal Bitcoin evidence."""
    st.subheader("Predeclared Bitcoin validation")
    try:
        pairs, summary, origin = _auxiliary_bitcoin_data()
    except DashboardDataError:
        st.info(
            "This validation will appear after the next public data refresh.",
            icon=":material/schedule:",
        )
        return
    model_summary = summary.loc[summary["model_id"] == model_id].copy()
    primary = model_summary.loc[model_summary["specification_role"] == "primary"]
    if primary.empty:
        st.warning("The frozen primary specification is unavailable in this snapshot.")
        return
    row = primary.iloc[0]
    correlation = row["correlation"]
    with st.container(horizontal=True):
        st.metric(
            "Primary correlation",
            "Insufficient sample" if pd.isna(correlation) else f"{float(correlation):+.2f}",
            border=True,
        )
        st.metric("Non-overlapping observations", f"{int(row['observations'])}", border=True)
        st.metric("Interval reading", str(row["interval_reading"]), border=True)
        st.metric(
            "Median Bitcoin return",
            (
                "Unavailable"
                if pd.isna(row["median_return"])
                else f"{float(row['median_return']):+.1%}"
            ),
            border=True,
        )
    st.caption(
        "Primary specification: source-modeled availability date, no additional delay, six-month "
        "Bitcoin return, non-overlapping sample. The protocol was frozen on 4 September 2026 "
        "before inspecting these results."
    )
    lag = int(row["additional_availability_lag_months"])
    horizon_rows = model_summary.loc[
        (model_summary["additional_availability_lag_months"] == lag)
        & (model_summary["sample_policy"] == "non_overlapping")
    ].copy()
    horizon_rows["Horizon"] = horizon_rows["horizon_months"].map(lambda value: f"{value}m")
    figure = px.bar(
        horizon_rows,
        x="Horizon",
        y="correlation",
        title="Correlation sensitivity across predeclared horizons",
        labels={"correlation": "Pearson correlation"},
    )
    figure.update_traces(
        marker_color="#F59E0B",
        text=horizon_rows["correlation"].map(
            lambda value: "n/a" if pd.isna(value) else f"{value:+.2f}"
        ),
        textposition="outside",
    )
    figure.update_yaxes(range=[-1, 1])
    st.plotly_chart(figure, width="stretch", config={"displaylogo": False})
    primary_pairs = pairs.loc[
        (pairs["model_id"] == model_id)
        & (pairs["specification_role"] == "primary")
        & pairs["is_non_overlapping"]
    ]
    if not primary_pairs.empty:
        scatter = px.scatter(
            primary_pairs,
            x="signal_score",
            y="market_return",
            hover_data={"signal_date": "|%Y-%m-%d", "signal_regime": True},
            title="Frozen signal versus subsequent six-month Bitcoin return",
            labels={
                "signal_score": "Liquidity momentum score",
                "market_return": "Bitcoin return",
            },
        )
        scatter.update_yaxes(tickformat=".0%")
        st.plotly_chart(scatter, width="stretch", config={"displaylogo": False})
    st.warning(
        "These are descriptive associations, not forecasts or calibration results. Quarterly "
        "signals create modest non-overlapping samples, Bitcoin volatility is high, and current "
        "source vintages may differ from information available historically.",
        icon=":material/warning:",
    )
    st.caption(f"Validation data mode: {origin}")


def private_liquidity_page() -> None:
    """Present the separate US commercial-bank and money-fund liquidity layer."""
    st.title("US private liquidity")
    st.caption(
        "Quarterly commercial-bank credit and money-market-fund assets · experimental, "
        "non-calibrated, and separate from Global Model G"
    )
    try:
        data, origin = _private_liquidity_data()
    except DashboardDataError:
        st.info("The US private-liquidity snapshot is awaiting the next data refresh.")
        return
    indexed = data.dropna(subset=["private_liquidity_index"])
    if indexed.empty:
        st.warning("The expanding normalization has insufficient quarterly history.")
        return
    latest = indexed.iloc[-1]
    with st.container(horizontal=True):
        st.metric(
            "Private liquidity index",
            f"{float(latest['private_liquidity_index']):.1f}",
            str(latest["private_liquidity_regime"]),
            border=True,
        )
        st.metric(
            "Commercial-bank credit",
            f"${float(latest['bank_credit_billions']) / 1_000:,.2f}tn",
            f"{float(latest['bank_growth_yoy']):+.1%} year over year",
            border=True,
        )
        st.metric(
            "Money-fund assets",
            f"${float(latest['mmf_assets_millions']) / 1_000_000:,.2f}tn",
            f"{float(latest['mmf_growth_yoy']):+.1%} year over year",
            border=True,
        )
        st.metric(
            "Loans / bank credit",
            f"{float(latest['loan_share_of_bank_credit']):.1%}",
            f"Assumed available {pd.Timestamp(latest['signal_available_date']):%d %b %Y}",
            border=True,
        )

    index_chart = px.line(
        indexed,
        x="date",
        y="private_liquidity_index",
        title="Open US Private Liquidity Momentum Index",
        labels={"date": "Quarter end", "private_liquidity_index": "0-100 index"},
    )
    index_chart.update_traces(line={"width": 2.7, "color": "#A855F7"})
    index_chart.add_hline(y=50, line_dash="dot", line_color="gray")
    index_chart.update_yaxes(range=[0, 100])
    st.plotly_chart(index_chart, width="stretch", config={"displaylogo": False})

    momentum = data[["date", "bank_momentum", "mmf_momentum"]].rename(
        columns={"bank_momentum": "Bank credit", "mmf_momentum": "Money-market funds"}
    )
    momentum = momentum.melt("date", var_name="component", value_name="momentum")
    component_chart = px.line(
        momentum,
        x="date",
        y="momentum",
        color="component",
        title="Component momentum",
        labels={"date": "Quarter end", "momentum": "Standardized score", "component": ""},
    )
    component_chart.add_hline(y=0, line_dash="dot", line_color="gray")
    st.plotly_chart(component_chart, width="stretch", config={"displaylogo": False})

    levels = data.assign(
        bank_credit_trillions=data["bank_credit_billions"] / 1_000,
        bank_loans_trillions=data["bank_loans_billions"] / 1_000,
        mmf_assets_trillions=data["mmf_assets_millions"] / 1_000_000,
    )[["date", "bank_credit_trillions", "bank_loans_trillions", "mmf_assets_trillions"]]
    levels = levels.rename(
        columns={
            "bank_credit_trillions": "Total bank credit",
            "bank_loans_trillions": "Loans and leases (inside bank credit)",
            "mmf_assets_trillions": "Money-market-fund assets",
        }
    ).melt("date", var_name="component", value_name="usd_trillions")
    level_chart = px.line(
        levels,
        x="date",
        y="usd_trillions",
        color="component",
        title="Measured private-liquidity stocks",
        labels={"date": "Quarter end", "usd_trillions": "USD trillions", "component": ""},
    )
    level_chart.update_yaxes(tickprefix="$", ticksuffix="tn")
    st.plotly_chart(level_chart, width="stretch", config={"displaylogo": False})
    st.info(
        "Loans and leases are a subset of total bank credit. They are displayed for composition "
        "only and are not added to the composite, preventing double counting.",
        icon=":material/info:",
    )
    st.subheader("Methodology and limits")
    st.latex(r"M_t = 0.50M^{BankCredit}_t + 0.50M^{MMFAssets}_t")
    st.markdown(
        "Each component momentum is 60% expanding z-score of quarterly annualized growth plus "
        "40% expanding z-score of year-over-year growth. The combined score is mapped through "
        "the normal CDF. Weights and the three-month availability lag are assumptions; calibrated "
        "parameters are **none**."
    )
    st.warning(
        "This current-vintage pilot mixes seasonally adjusted weekly H.8 bank data with unadjusted "
        "quarterly Z.1 money-fund assets, which can be substantially revised. It does not measure "
        "credit quality, bank capital constraints, non-bank leverage, or all shadow banking. It "
        "is not yet part of Global Model G or a trading signal.",
        icon=":material/warning:",
    )
    _render_auxiliary_bitcoin_validation("us_private_liquidity")
    st.caption(f"Data mode: {origin} · Sources: Federal Reserve H.8 and Z.1 via FRED.")


def cross_border_credit_page() -> None:
    """Present the separate BIS offshore-dollar credit momentum layer."""
    st.title("Offshore dollar credit")
    st.caption(
        "Quarterly BIS global liquidity indicator · US-dollar bank loans and debt securities "
        "to non-bank borrowers outside the United States"
    )
    try:
        data, origin = _cross_border_data()
    except DashboardDataError:
        st.info(
            "The offshore-dollar credit snapshot has not been generated in this environment.",
            icon=":material/public:",
        )
        st.code(
            "uv run python -m open_global_liquidity.pipeline --publish-dashboard-snapshot",
            language="zsh",
        )
        return
    indexed = data.dropna(subset=["offshore_dollar_credit_index"])
    if indexed.empty:
        st.warning("The expanding normalization has insufficient quarterly history.")
        return
    latest = indexed.iloc[-1]
    with st.container(horizontal=True):
        st.metric(
            "Offshore dollar credit",
            f"${float(latest['usd_credit_nonbanks_outside_us_millions']) / 1_000_000:,.2f}tn",
            f"{float(latest['growth_12m_yoy']):+.1%} year over year",
            border=True,
        )
        st.metric(
            "Credit momentum index",
            f"{float(latest['offshore_dollar_credit_index']):.1f}",
            str(latest["regime"]),
            border=True,
        )
        st.metric(
            "Quarterly annualized growth",
            f"{float(latest['growth_qoq_annualized']):+.1%}",
            border=True,
        )
        st.metric(
            "Assumed available",
            f"{pd.Timestamp(latest['signal_available_date']):%d %b %Y}",
            f"Data mode: {origin}",
            border=True,
        )

    index_chart = px.line(
        indexed,
        x="date",
        y="offshore_dollar_credit_index",
        title="Open Offshore Dollar Credit Momentum Index",
        labels={"date": "Quarter end", "offshore_dollar_credit_index": "0-100 index"},
    )
    index_chart.update_traces(line={"width": 2.7, "color": "#14B8A6"})
    index_chart.add_hline(y=50, line_dash="dot", line_color="gray")
    index_chart.update_yaxes(range=[0, 100])
    st.plotly_chart(index_chart, width="stretch", config={"displaylogo": False})

    level = data.assign(usd_trillions=data["usd_credit_nonbanks_outside_us_millions"] / 1_000_000)
    level_chart = px.line(
        level,
        x="date",
        y="usd_trillions",
        title="Measured US-dollar credit stock outside the United States",
        labels={"date": "Quarter end", "usd_trillions": "USD trillions"},
    )
    level_chart.update_traces(line={"width": 2.5, "color": "#2563EB"})
    level_chart.update_yaxes(tickprefix="$", ticksuffix="tn")
    st.plotly_chart(level_chart, width="stretch", config={"displaylogo": False})

    growth = data[["date", "growth_qoq_annualized", "growth_12m_yoy"]].rename(
        columns={
            "growth_qoq_annualized": "Quarter-over-quarter annualized",
            "growth_12m_yoy": "Year over year",
        }
    )
    growth = growth.melt("date", var_name="measure", value_name="growth")
    growth_chart = px.line(
        growth,
        x="date",
        y="growth",
        color="measure",
        title="Offshore dollar credit growth",
        labels={"date": "Quarter end", "growth": "Growth rate", "measure": ""},
    )
    growth_chart.add_hline(y=0, line_dash="dot", line_color="gray")
    growth_chart.update_yaxes(tickformat=".0%")
    st.plotly_chart(growth_chart, width="stretch", config={"displaylogo": False})

    st.subheader("Transparent methodology")
    st.latex(r"M_t = 0.60z(g^{QoQ,ann}_t) + 0.40z(g^{YoY}_t)")
    st.latex(r"OffshoreDollarIndex_t = 100\,\Phi(M_t)")
    st.markdown(
        "**Measured data:** BIS quarterly US-dollar credit—bank loans plus debt securities—to "
        "non-bank borrowers outside the United States.\n\n"
        "**Model assumptions:** the 60/40 momentum weights, expanding 12-quarter minimum, regime "
        "thresholds, and four-month-end assumed publication lag.\n\n"
        "**Calibrated parameters:** none. The model was not fitted to Bitcoin or another asset."
    )
    st.warning(
        "This layer does not measure FX swaps, derivatives, collateral reuse, credit quality, or "
        "all offshore-dollar liabilities. Quarterly positions may be revised. It remains separate "
        "from Global Model G pending point-in-time validation and must not be read as a trading "
        "signal or CrossBorder Capital's proprietary GLI.",
        icon=":material/warning:",
    )
    _render_auxiliary_bitcoin_validation("offshore_dollar_credit")
    st.link_button(
        "Review the exact BIS series",
        "https://data.bis.org/topics/GLI/BIS,WS_GLI,1.0/Q.USD.3P.N.A.I.B.USD",
        icon=":material/open_in_new:",
    )


def collateral_conditions_page() -> None:
    """Present the standalone v0.4a US collateral and secured-funding pilot."""
    st.title("Collateral conditions")
    st.caption(
        "Experimental US Treasury collateral and secured-funding conditions · maintained "
        "separately from Global Model G"
    )
    try:
        data, origin = _collateral_data()
    except DashboardDataError:
        st.info(
            "The v0.4a collateral snapshot has not been generated in this environment. The "
            "Treasury source is keyless; the existing FRED key covers the remaining inputs.",
            icon=":material/account_balance:",
        )
        st.code(
            "uv run python -m open_global_liquidity.pipeline --publish-dashboard-snapshot",
            language="zsh",
        )
        return

    indexed = data.dropna(subset=["collateral_conditions_index"])
    if indexed.empty:
        st.warning("The expanding normalization does not yet have 24 usable monthly observations.")
        return
    latest = indexed.iloc[-1]
    with st.container(horizontal=True):
        st.metric(
            "Collateral conditions",
            f"{float(latest['collateral_conditions_index']):.1f}",
            str(latest["collateral_regime"]),
            border=True,
        )
        st.metric(
            "Private collateral proxy",
            f"${float(latest['private_collateral_proxy_millions']) / 1_000_000:,.1f}tn",
            f"{float(latest['collateral_supply_growth_yoy']):+.1%} year over year",
            border=True,
        )
        st.metric(
            "SOFR minus EFFR",
            f"{float(latest['funding_spread_bps']):+.1f} bp",
            "Higher is treated as tighter",
            border=True,
        )
        st.metric(
            "10-year yield volatility",
            f"{float(latest['treasury_volatility_bps']):.1f} bp",
            "21-observation annualized proxy",
            border=True,
        )

    with st.sidebar:
        st.header("Collateral controls")
        history = st.segmented_control(
            "History",
            ["3 years", "5 years", "All"],
            default="5 years",
            key="collateral_history",
        )
        st.caption(f"Data mode: {origin}")
        st.caption("Frequency: monthly")
        st.caption("Normalization: expanding, 24 observations")
    visible = indexed
    if history != "All":
        years = 3 if history == "3 years" else 5
        visible = indexed.loc[
            indexed["date"] >= indexed["date"].max() - timedelta(days=years * 365)
        ]

    index_chart = px.line(
        visible,
        x="date",
        y="collateral_conditions_index",
        title="Open Collateral Conditions Score",
        labels={"date": "Month end", "collateral_conditions_index": "0-100 score"},
    )
    index_chart.update_traces(line={"width": 2.7, "color": "#0EA5E9"})
    index_chart.add_hline(y=50, line_dash="dot", line_color="gray")
    index_chart.update_yaxes(range=[0, 100])
    st.plotly_chart(index_chart, width="stretch", config={"displaylogo": False})

    st.subheader("Marketable Treasury collateral composition")
    try:
        composition, composition_origin = _collateral_composition_data()
    except DashboardDataError:
        st.info("Treasury security-class composition is awaiting the next data refresh.")
    else:
        composition_labels = {
            "marketable_treasury_bills_public": "Bills",
            "marketable_treasury_notes_public": "Notes",
            "marketable_treasury_bonds_public": "Bonds",
            "marketable_treasury_tips_public": "TIPS",
            "marketable_treasury_frns_public": "Floating-rate notes",
        }
        composition["security_class"] = composition["component"].map(composition_labels)
        composition_chart = px.area(
            composition,
            x="date",
            y="value_usd_trillions",
            color="security_class",
            title="Marketable Treasury debt held by the public · par value",
            labels={
                "date": "Month end",
                "value_usd_trillions": "USD trillions",
                "security_class": "Security class",
            },
        )
        composition_chart.update_yaxes(tickprefix="$", ticksuffix="tn")
        st.plotly_chart(composition_chart, width="stretch", config={"displaylogo": False})
        latest_composition = composition.loc[composition["date"] == composition["date"].max()]
        composition_total = latest_composition["value"].sum()
        shares = latest_composition.assign(share=latest_composition["value"] / composition_total)
        st.dataframe(
            shares[["security_class", "value_usd_trillions", "share"]],
            hide_index=True,
            width="stretch",
            column_config={
                "security_class": "Security class",
                "value_usd_trillions": st.column_config.NumberColumn(
                    "Par value", format="$%.2f tn"
                ),
                "share": st.column_config.NumberColumn("Share", format="percent"),
            },
        )
        st.caption(
            f"Measured MSPD composition · data mode: {composition_origin}. Federal Financing "
            "Bank securities are excluded because they are not one of the five selected Treasury "
            "marketable classes. Composition does not measure repo eligibility or collateral reuse."
        )

    st.subheader("Treasury repo market context")
    try:
        repo, repo_origin = _repo_context_data()
    except DashboardDataError:
        st.info("SOFR and TGCR rate-and-volume context is awaiting the next data refresh.")
    else:
        repo["month"] = repo["date"].dt.to_period("M").dt.to_timestamp("M")
        repo_monthly = repo.groupby(["month", "component"], as_index=False)["value"].median()
        rate_labels = {
            "secured_overnight_financing_rate": "SOFR",
            "tri_party_general_collateral_rate": "TGCR",
        }
        volume_labels = {
            "secured_overnight_financing_volume": "SOFR volume",
            "tri_party_general_collateral_volume": "TGCR volume",
        }
        rates = repo_monthly.loc[repo_monthly["component"].isin(rate_labels)].copy()
        rates["series"] = rates["component"].map(rate_labels)
        volumes = repo_monthly.loc[repo_monthly["component"].isin(volume_labels)].copy()
        volumes["series"] = volumes["component"].map(volume_labels)
        left, right = st.columns(2)
        left.plotly_chart(
            px.line(
                rates,
                x="month",
                y="value",
                color="series",
                title="Monthly median rates",
                labels={"month": "Month", "value": "Percent", "series": ""},
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        right.plotly_chart(
            px.line(
                volumes,
                x="month",
                y="value",
                color="series",
                title="Monthly median volumes",
                labels={"month": "Month", "value": "USD billions", "series": ""},
            ),
            width="stretch",
            config={"displaylogo": False},
        )
        st.caption(
            f"Measured New York Fed reference-rate context · data mode: {repo_origin}. Volumes "
            "describe transactions underlying each benchmark and are not total repo-market size. "
            "These series do not yet enter the collateral score."
        )

    supportive = visible[
        [
            "date",
            "z_collateral_supply_growth_yoy",
            "z_funding_spread_bps",
            "z_treasury_volatility_bps",
        ]
    ].copy()
    supportive["z_funding_spread_bps"] *= -1
    supportive["z_treasury_volatility_bps"] *= -1
    supportive = supportive.rename(
        columns={
            "z_collateral_supply_growth_yoy": "Collateral supply growth",
            "z_funding_spread_bps": "Secured funding conditions",
            "z_treasury_volatility_bps": "Rate-volatility conditions",
        }
    ).melt("date", var_name="component", value_name="supportive_zscore")
    component_chart = px.line(
        supportive,
        x="date",
        y="supportive_zscore",
        color="component",
        title="Standardized component signals · positive means more supportive",
        labels={"date": "Month end", "supportive_zscore": "Expanding z-score", "component": ""},
    )
    component_chart.add_hline(y=0, line_dash="dot", line_color="gray")
    st.plotly_chart(component_chart, width="stretch", config={"displaylogo": False})

    curve_columns = {
        "treasury_volatility_2y_bps": "2-year",
        "treasury_volatility_5y_bps": "5-year",
        "treasury_volatility_10y_bps": "10-year",
        "treasury_volatility_30y_bps": "30-year",
        "treasury_volatility_curve_bps": "Equal-weight curve composite",
    }
    if set(curve_columns).issubset(data.columns):
        curve = (
            data[["date", *curve_columns]]
            .rename(columns=curve_columns)
            .melt("date", var_name="tenor", value_name="volatility_bps")
        )
        curve_chart = px.line(
            curve,
            x="date",
            y="volatility_bps",
            color="tenor",
            title="Realized Treasury yield volatility across the curve",
            labels={"date": "Month end", "volatility_bps": "Annualized basis points", "tenor": ""},
        )
        st.plotly_chart(curve_chart, width="stretch", config={"displaylogo": False})
        st.caption(
            "The curve composite is the unweighted mean of separately calculated 2-, 5-, 10-, "
            "and 30-year realized-yield volatilities. It is an alternative diagnostic; the "
            "frozen score continues to use the 10-year series."
        )

    st.subheader("Collateral signal robustness laboratory")
    st.caption(
        "Seven specifications were declared before examining Bitcoin outcomes. This section "
        "tests whether the collateral signal itself is stable under alternative weights, curve "
        "volatility, component exclusions, and a rolling normalization window."
    )
    try:
        robustness, robustness_origin = _collateral_robustness_data()
    except DashboardDataError:
        st.info("Collateral robustness results are awaiting the next data refresh.")
    else:
        robustness_visible = robustness
        if history != "All":
            years = 3 if history == "3 years" else 5
            robustness_visible = robustness.loc[
                robustness["date"] >= robustness["date"].max() - timedelta(days=years * 365)
            ]
        robustness_chart = px.line(
            robustness_visible,
            x="date",
            y="robustness_index",
            color="model_name",
            title="Predeclared collateral-index variants",
            labels={
                "date": "Month end",
                "robustness_index": "0-100 index",
                "model_name": "Specification",
            },
        )
        robustness_chart.add_hline(y=50, line_dash="dot", line_color="gray")
        robustness_chart.update_yaxes(range=[0, 100])
        st.plotly_chart(robustness_chart, width="stretch", config={"displaylogo": False})

        latest_robustness = robustness.loc[robustness["date"] == robustness["date"].max()].copy()
        baseline_latest = latest_robustness.loc[
            latest_robustness["model_id"] == "baseline", "robustness_index"
        ].iloc[0]
        latest_robustness["difference_from_baseline"] = (
            latest_robustness["robustness_index"] - baseline_latest
        )
        st.dataframe(
            latest_robustness[
                [
                    "model_name",
                    "robustness_index",
                    "difference_from_baseline",
                    "normalization",
                    "volatility_input",
                ]
            ],
            hide_index=True,
            width="stretch",
            column_config={
                "model_name": "Specification",
                "robustness_index": st.column_config.NumberColumn("Latest index", format="%.1f"),
                "difference_from_baseline": st.column_config.NumberColumn(
                    "Difference vs baseline", format="%+.1f"
                ),
                "normalization": "Normalization",
                "volatility_input": "Volatility input",
            },
        )
        st.caption(
            f"Model-assumption sensitivity · data mode: {robustness_origin}. These alternatives "
            "are diagnostics, not optimized models. Bitcoin returns were not used to define, "
            "select, or rank them."
        )

    st.subheader("Frozen-model validation against subsequent Bitcoin returns")
    st.caption(
        "The collateral formula and weights were fixed before this comparison. The primary "
        "specification uses the source-specific availability date with no additional delay, a "
        "three-month forward return, and non-overlapping observations; one- and two-month "
        "additional delays remain visible as sensitivity checks."
    )
    try:
        pairs, summary, validation_origin = _collateral_bitcoin_data()
    except DashboardDataError:
        st.info("Collateral/Bitcoin validation snapshots are awaiting the next data refresh.")
    else:
        with st.container(horizontal=True):
            lag = st.selectbox(
                "Additional timing delay",
                sorted(summary["availability_lag_months"].unique()),
                index=0,
                format_func=lambda value: (
                    "No additional delay"
                    if value == 0
                    else f"{value} additional month{'s' if value != 1 else ''}"
                ),
                key="collateral_bitcoin_lag",
            )
            horizon = st.selectbox(
                "Forward horizon",
                sorted(summary["horizon_months"].unique()),
                index=1,
                format_func=lambda value: f"{value} month{'s' if value != 1 else ''}",
                key="collateral_bitcoin_horizon",
            )
            sample_label = st.segmented_control(
                "Sample",
                ["Non-overlapping", "Overlapping"],
                default="Non-overlapping",
                key="collateral_bitcoin_sample",
            )
        policy = "non_overlapping" if sample_label == "Non-overlapping" else "overlapping"
        selected = summary.loc[
            (summary["availability_lag_months"] == lag)
            & (summary["horizon_months"] == horizon)
            & (summary["sample_policy"] == policy)
        ].iloc[0]
        correlation = selected["correlation"]
        with st.container(horizontal=True):
            st.metric(
                "Pearson correlation",
                "Insufficient sample" if pd.isna(correlation) else f"{float(correlation):+.2f}",
                border=True,
            )
            st.metric("Paired observations", f"{int(selected['observations']):,}", border=True)
            st.metric(
                "Median Bitcoin return", f"{float(selected['median_return']):.1%}", border=True
            )
            st.metric("Positive outcomes", f"{float(selected['positive_share']):.0%}", border=True)
        visible_summary = summary.loc[
            (summary["availability_lag_months"] == lag) & (summary["sample_policy"] == policy)
        ].copy()
        validation_chart = px.bar(
            visible_summary,
            x="horizon_months",
            y="correlation",
            text="correlation",
            title="Collateral-score correlation with subsequent Bitcoin returns",
            labels={"horizon_months": "Forward horizon (months)", "correlation": "Correlation"},
        )
        validation_chart.update_traces(texttemplate="%{text:+.2f}", textposition="outside")
        validation_chart.add_hline(y=0, line_color="gray", line_width=1)
        validation_chart.update_yaxes(range=[-1, 1])
        st.plotly_chart(validation_chart, width="stretch", config={"displaylogo": False})
        selected_pairs = pairs.loc[
            (pairs["availability_lag_months"] == lag) & (pairs["horizon_months"] == horizon)
        ]
        if policy == "non_overlapping":
            selected_pairs = selected_pairs.loc[selected_pairs["is_non_overlapping"]]
        scatter = px.scatter(
            selected_pairs,
            x="collateral_conditions_score",
            y="market_return",
            hover_data={
                "signal_date": "|%Y-%m-%d",
                "source_available_date": "|%Y-%m-%d",
                "collateral_regime": True,
            },
            title="Collateral conditions and later Bitcoin return",
            labels={
                "collateral_conditions_score": "Collateral conditions score",
                "market_return": "Subsequent Bitcoin return",
            },
        )
        scatter.update_yaxes(tickformat=".0%")
        st.plotly_chart(scatter, width="stretch", config={"displaylogo": False})
        if pd.notna(selected["bootstrap_ci_lower"]):
            st.caption(
                f"95% moving-block bootstrap interval: {selected['bootstrap_ci_lower']:+.2f} "
                f"to {selected['bootstrap_ci_upper']:+.2f}. Data mode: {validation_origin}."
            )
        st.warning(
            "This is current-vintage, retrospective validation with a short sample. Confidence "
            "intervals, sample counts, and inconclusive results are retained. Correlation is not "
            "causation or a trading signal, and no result changes the collateral model weights.",
            icon=":material/warning:",
        )

    st.subheader("Transparent v0.4a formula")
    st.latex(
        r"C_t = 0.40z(\Delta_{12m}\,PrivateCollateral)"
        r" - 0.30z(SOFR-EFFR) - 0.30z(RealizedYieldVolatility)"
    )
    st.latex(r"CollateralIndex_t = 100\,\Phi(C_t)")
    st.markdown(
        "**Measured data:** Treasury MSPD marketable debt held by the public; Fed Treasury "
        "holdings; SOFR; effective federal funds rate; and the 10-year Treasury yield.\n\n"
        "**Model assumptions:** subtracting Fed holdings, interpreting supply growth as "
        "supportive, treating wider funding spreads and higher volatility as constraining, and "
        "the 40/30/30 weights.\n\n"
        "**Calibrated parameters:** none. Bitcoin and other asset outcomes were not used to choose "
        "the weights."
    )
    st.warning(
        "This score does not observe repo haircuts, collateral reuse, dealer balance-sheet "
        "capacity, securities lending, or collateral velocity. It is not yet multiplied into "
        "Model G and must not be interpreted as a complete liquidity multiplier.",
        icon=":material/warning:",
    )
    st.caption(
        "The Secured Overnight Financing Rate data are subject to the Terms of Use posted at "
        "newyorkfed.org. The New York Fed is not responsible for publication of the SOFR data by "
        "Open Global Liquidity, does not sanction or endorse this republication, and has no "
        "liability for its use. Open Global Liquidity is not affiliated with the New York Fed."
    )


def data_quality_page() -> None:
    """Expose public snapshot completeness and timing metadata without a false quality score."""
    st.title("Data quality and availability")
    st.caption(
        "Per-file coverage, missingness, duplicates, retrieval metadata, and Model G vintage "
        "limitations. Frequencies differ, so the app does not publish an arbitrary aggregate score."
    )
    try:
        inventory, origin = _data_quality_data()
    except DashboardDataError as exc:
        st.error(str(exc))
        return
    provenance = _snapshot_provenance()
    with st.container(horizontal=True):
        st.metric("Inventoried snapshots", str(len(inventory)), border=True)
        st.metric("Rows represented", f"{int(inventory['rows'].sum()):,}", border=True)
        st.metric(
            "Exact duplicate rows", f"{int(inventory['duplicate_rows'].sum()):,}", border=True
        )
        st.metric(
            "Hashed by manifest",
            str(provenance["snapshot_count"]) if provenance else "Unavailable",
            border=True,
        )
    st.dataframe(
        inventory,
        column_config={
            "earliest_observation": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "latest_observation": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "latest_retrieval": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm"),
        },
        hide_index=True,
        width="stretch",
    )
    st.warning(
        "Null cells are not automatically errors: growth windows, unmatched forward returns, and "
        "summary tables legitimately contain nulls. Review each dataset in context. Global Model G "
        "is lag-adjusted current-vintage because historical BIS value vintages are not "
        "reconstructed.",
        icon=":material/fact_check:",
    )
    st.caption(f"Data mode: {origin}.")


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

    st.subheader("Preregistered broader Model H")
    model_h = load_model_h_display_spec(PROJECT_ROOT / "config" / "model_h_preregistration.yaml")
    with st.container(border=True):
        st.markdown(f"#### {model_h['name']}")
        st.badge("Design frozen · descriptive history available", color="orange")
        st.write(
            "A quarterly challenger combining three equally weighted economic pillars. It does "
            "not replace Global Model G; its historical readings are explicitly descriptive."
        )
        st.dataframe(
            model_h["pillars"],
            column_config={"Assumed weight": st.column_config.NumberColumn(format="percent")},
            hide_index=True,
            width="stretch",
        )
        st.code(str(model_h["score_formula"]), language=None)
        st.caption(
            f"Frozen {model_h['frozen_on']:%Y-%m-%d}; prospective evaluation begins "
            f"{model_h['prospective_start']:%Y-%m-%d}. Historical results produced later must be "
            "labeled post-specification descriptive."
        )
        st.warning(str(model_h["research_boundary"]), icon=":material/science:")

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

        **United Kingdom v0.2c measured-data pilot**

        - [BoE consolidated central-bank total assets](https://www.bankofengland.co.uk/boeapps/database/index.asp?EC=RPQB75A&From=Template)
          — series `RPQB75A`, quarterly native-sterling stock published with a five-quarter lag;
          not an OGLI input or global aggregate

        **China and v0.3 aggregation**

        - [BIS China central-bank total assets](https://data.bis.org/topics/CBTA/BIS,WS_CBTA,1.0/M.CN.B.XDC.CNY.N)
          — public monthly BIS-spliced CNY series used by the hosted dashboard
        - [BIS permitted-use terms](https://data.bis.org/help/legal)
        - [PBoC Money and Banking Statistics archive](https://www.pbc.gov.cn/diaochatongjisi/116219/116319/index.html)
          — direct local validation source only; observations are not redistributed

        The **Central banks** page still rebases each native-currency series independently to 100.
        The separate **Global aggregate** page converts five total-asset stocks with four public
        H.10 exchange rates and sums only balanced months. It also reports Global Model G, an
        expanding-normalized central-bank momentum index. The aggregation and momentum weights are
        declared assumptions; it is not a complete global OGLI, and historical publication lags
        are not yet reconstructed.

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
quality_page = st.Page(
    data_quality_page,
    title="Data quality",
    icon=":material/fact_check:",
    url_path="data-quality",
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
uk_data_page = st.Page(
    united_kingdom_page,
    title="UK data",
    icon=":material/account_balance:",
    url_path="united-kingdom",
)
china_data_page = st.Page(
    china_page,
    title="China data",
    icon=":material/account_balance:",
    url_path="china",
)
central_bank_data_page = st.Page(
    central_banks_page,
    title="Central banks",
    icon=":material/public:",
    url_path="central-banks",
)
global_aggregate_data_page = st.Page(
    global_aggregate_page,
    title="Global aggregate",
    icon=":material/currency_exchange:",
    url_path="global-aggregate",
)
cross_border_data_page = st.Page(
    cross_border_credit_page,
    title="Offshore dollar credit",
    icon=":material/language:",
    url_path="offshore-dollar-credit",
)
private_liquidity_data_page = st.Page(
    private_liquidity_page,
    title="US private liquidity",
    icon=":material/account_balance:",
    url_path="private-liquidity",
)
collateral_data_page = st.Page(
    collateral_conditions_page,
    title="Collateral conditions",
    icon=":material/account_balance_wallet:",
    url_path="collateral-conditions",
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
    title="Liquidity indices",
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
        collateral_data_page,
        data_page,
        quality_page,
        central_bank_data_page,
        global_aggregate_data_page,
        cross_border_data_page,
        private_liquidity_data_page,
        euro_area_data_page,
        japan_data_page,
        uk_data_page,
        china_data_page,
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
    "Global Model G central-bank statistics: Bank for International Settlements, Central bank "
    "total assets, United States, euro area, Japan, United Kingdom, and China. BIS statistics are "
    "used under its permitted-use terms; the BIS does not endorse or provide investment advice "
    "through this project."
)
st.caption(
    "This service uses the Bank of Japan Time-Series Data Search API. The Bank of Japan does not "
    "guarantee this service's content."
)
