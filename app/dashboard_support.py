"""Deployment-local validation and display preparation for Streamlit snapshots.

Economic transformations remain in ``src/open_global_liquidity``. This module deliberately handles
only the presentation contract so Streamlit Cloud never depends on a cached installed project wheel.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

SOURCE_COLUMNS = [
    "date",
    "country",
    "provider",
    "series_id",
    "component",
    "value",
    "unit",
    "frequency",
    "retrieved_at",
]

MODEL_COLUMNS = [
    "date",
    "model_id",
    "model_name",
    "value",
    "unit",
    "frequency",
    "classification",
    "formula",
    "description",
    "is_complete",
]

OGLI_COLUMNS = [
    "date",
    "model_id",
    "model_name",
    "value",
    "change_1m",
    "change_3m",
    "change_6m",
    "change_12m",
    "growth_3m_annualized",
    "growth_12m_yoy",
    "z_growth_3m_annualized",
    "z_growth_12m_yoy",
    "momentum_score",
    "ogli",
    "regime",
    "zscore_mode",
    "zscore_min_periods",
    "ogli_classification",
    "weight_classification",
]

MARKET_COMPARISON_COLUMNS = [
    "date",
    "model_id",
    "model_name",
    "ogli",
    "momentum_score",
    "market_id",
    "series_id",
    "value",
    "unit",
    "horizon_weeks",
    "return_type",
    "market_return",
    "return_start_date",
    "return_end_date",
    "liquidity_signal_name",
    "liquidity_signal",
    "rolling_correlation",
    "rolling_window_weeks",
    "rolling_min_periods",
    "signal_observation_date",
    "signal_available_date",
    "analysis_mode",
    "publication_lag_weeks",
    "regime",
    "is_non_overlapping",
]

MARKET_CORRELATION_COLUMNS = [
    "model_id",
    "model_name",
    "market_id",
    "series_id",
    "horizon_weeks",
    "return_type",
    "liquidity_signal_name",
    "correlation",
    "observations",
    "classification",
    "analysis_mode",
    "sample_policy",
    "confidence_level",
    "correlation_ci_lower",
    "correlation_ci_upper",
    "bootstrap_ci_lower",
    "bootstrap_ci_upper",
    "bootstrap_method",
    "bootstrap_resamples",
    "bootstrap_valid_resamples",
    "bootstrap_block_length",
    "bootstrap_seed",
]

MARKET_REGIME_COLUMNS = [
    "model_id",
    "model_name",
    "market_id",
    "series_id",
    "horizon_weeks",
    "return_type",
    "analysis_mode",
    "regime",
    "sample_policy",
    "observations",
    "mean_return",
    "median_return",
    "positive_share",
    "confidence_level",
    "mean_ci_lower",
    "mean_ci_upper",
    "classification",
]

MARKET_SUBPERIOD_COLUMNS = [
    *MARKET_CORRELATION_COLUMNS,
    "period_id",
    "period_label",
    "period_start",
    "period_end",
    "period_order",
    "period_classification",
]

MACRO_CONTEXT_COLUMNS = [
    "date",
    "treasury_yield_10y",
    "treasury_yield_2y",
    "yield_curve_10y_2y",
    "broad_usd_index",
    "classification",
]

POINT_IN_TIME_COMPARISON_COLUMNS = [
    "information_date",
    "signal_observation_date",
    "model_id",
    "model_name",
    "vintage_ogli",
    "vintage_momentum_score",
    "vintage_regime",
    "current_ogli",
    "current_momentum_score",
    "current_regime",
    "ogli_revision",
    "momentum_revision",
    "comparison_policy",
]

POINT_IN_TIME_MARKET_PAIR_COLUMNS = [
    "information_date",
    "signal_observation_date",
    "signal_available_date",
    "model_id",
    "model_name",
    "vintage_ogli",
    "vintage_momentum_score",
    "vintage_regime",
    "market_id",
    "series_id",
    "provider",
    "unit",
    "source_frequency",
    "publication_lag_weeks",
    "horizon_months",
    "start_target_date",
    "start_observation_date",
    "start_value",
    "end_target_date",
    "end_observation_date",
    "end_value",
    "market_return",
    "is_non_overlapping",
    "classification",
]

POINT_IN_TIME_MARKET_SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "market_id",
    "series_id",
    "publication_lag_weeks",
    "horizon_months",
    "sample_policy",
    "observations",
    "correlation",
    "mean_return",
    "median_return",
    "positive_share",
    "classification",
]

BITCOIN_OUTCOME_COLUMNS = [
    *POINT_IN_TIME_MARKET_PAIR_COLUMNS,
    "current_ogli",
    "current_momentum_score",
    "current_regime",
    "ogli_revision",
    "momentum_revision",
    "regime_agrees_with_current",
    "previous_vintage_regime",
    "regime_transition",
    "transition_direction",
    "maximum_upside_from_start",
    "maximum_downside_from_start",
    "maximum_drawdown_from_peak",
    "bitcoin_research_classification",
]

BITCOIN_REGIME_SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "publication_lag_weeks",
    "horizon_months",
    "sample_policy",
    "analysis_dimension",
    "group_label",
    "observations",
    "mean_return",
    "median_return",
    "positive_share",
    "standard_error",
    "confidence_level",
    "mean_return_ci_lower",
    "mean_return_ci_upper",
    "mean_maximum_upside",
    "mean_maximum_downside",
    "mean_maximum_drawdown",
    "specification_role",
    "specification_classification",
    "classification",
]

BITCOIN_REVISION_SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "publication_lag_weeks",
    "horizon_months",
    "sample_policy",
    "observations",
    "vintage_signal_correlation",
    "current_vintage_signal_correlation",
    "correlation_difference",
    "mean_absolute_momentum_revision",
    "regime_agreement_share",
    "specification_role",
    "specification_classification",
    "classification",
]

BITCOIN_CONTRAST_SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "publication_lag_weeks",
    "horizon_months",
    "sample_policy",
    "expansionary_observations",
    "contractionary_observations",
    "expansionary_mean_return",
    "contractionary_mean_return",
    "expansionary_median_return",
    "contractionary_median_return",
    "expansionary_positive_share",
    "contractionary_positive_share",
    "mean_return_spread",
    "spread_standard_error",
    "confidence_level",
    "spread_ci_lower",
    "spread_ci_upper",
    "interval_status",
    "interval_status_classification",
    "interval_method",
    "regime_group_classification",
    "specification_role",
    "specification_classification",
    "classification",
]

COMPONENT_LABELS = {
    "fed_assets": "Fed total assets",
    "treasury_general_account": "Treasury General Account",
    "overnight_reverse_repo": "ON reverse repo",
    "reserve_balances": "Reserve balances",
}
ECB_COMPONENT_LABELS = {"eurosystem_total_assets": "Eurosystem total assets"}
BOJ_COMPONENT_LABELS = {"boj_total_assets": "Bank of Japan total assets"}
BOE_COMPONENT_LABELS = {"boe_total_assets": "Bank of England total assets"}
PBOC_COMPONENT_LABELS = {
    "pboc_total_assets": "PBoC total assets",
    "china_central_bank_total_assets": "China central-bank total assets",
}

_UNIT_TO_BILLIONS = {
    "Millions of U.S. Dollars": 0.001,
    "Billions of U.S. Dollars": 1.0,
}


class DashboardDataError(ValueError):
    """Raised when snapshot data cannot safely support the dashboard."""


class FreshnessStatus:
    """Presentation-ready assessment of the newest observation in a dataset."""

    __slots__ = ("age_days", "is_stale", "latest_date", "max_age_days")

    def __init__(
        self,
        *,
        latest_date: pd.Timestamp,
        age_days: int,
        max_age_days: int,
        is_stale: bool,
    ) -> None:
        self.latest_date = latest_date
        self.age_days = age_days
        self.max_age_days = max_age_days
        self.is_stale = is_stale


def assess_freshness(
    frame: pd.DataFrame,
    *,
    as_of: datetime | pd.Timestamp | None = None,
    max_age_days: int = 14,
) -> FreshnessStatus:
    """Assess dataset age from observation dates without treating retrieval time as data time."""
    if "date" not in frame.columns or frame.empty:
        raise DashboardDataError("Freshness assessment requires non-empty dated data")
    if max_age_days < 0:
        raise DashboardDataError("Freshness threshold cannot be negative")
    latest = pd.to_datetime(frame["date"], errors="coerce").max()
    if pd.isna(latest):
        raise DashboardDataError("Freshness assessment found no valid observation dates")
    reference = pd.Timestamp(as_of if as_of is not None else datetime.now(UTC))
    if reference.tzinfo is not None:
        reference = reference.tz_convert(None)
    latest = pd.Timestamp(latest)
    if latest.tzinfo is not None:
        latest = latest.tz_convert(None)
    age_days = max(0, (reference.normalize() - latest.normalize()).days)
    return FreshnessStatus(
        latest_date=latest,
        age_days=age_days,
        max_age_days=max_age_days,
        is_stale=age_days > max_age_days,
    )


def resolve_dashboard_data_path(processed_path: Path, snapshot_path: Path) -> tuple[Path, str]:
    """Prefer local processed data and fall back to a bundled public snapshot."""
    if processed_path.is_file():
        return processed_path, "Local processed data"
    if snapshot_path.is_file():
        return snapshot_path, "Bundled public snapshot"
    raise DashboardDataError(
        "No dashboard data is available. Run the pipeline locally or publish a dashboard snapshot."
    )


def _read_parquet(path: Path, label: str) -> pd.DataFrame:
    if not path.is_file():
        raise DashboardDataError(f"{label} not found at {path}")
    try:
        return pd.read_parquet(path)
    except (OSError, ValueError) as exc:
        raise DashboardDataError(f"Could not read {label.lower()} at {path}: {exc}") from exc


def load_dashboard_data(path: Path) -> pd.DataFrame:
    """Load source observations and convert supported nominal stocks to USD billions."""
    frame = _read_parquet(path, "Dashboard source data")
    missing = sorted(set(SOURCE_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Dashboard source data is missing columns: " + ", ".join(missing))
    if frame.empty or frame["value"].notna().sum() == 0:
        raise DashboardDataError("Dashboard source data contains no numeric observations")
    unsupported = sorted(set(frame["unit"].dropna()) - _UNIT_TO_BILLIONS.keys())
    if unsupported:
        raise DashboardDataError(
            "Dashboard cannot convert these source units to USD billions: " + ", ".join(unsupported)
        )

    result = frame[SOURCE_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"])
    if result["date"].isna().any():
        raise DashboardDataError("Dashboard source data contains invalid dates")
    result["value_usd_billions"] = result["value"] * result["unit"].map(_UNIT_TO_BILLIONS)
    result["label"] = result["component"].map(COMPONENT_LABELS).fillna(result["component"])
    return result.sort_values(["component", "date"]).reset_index(drop=True)


def latest_readings(frame: pd.DataFrame) -> pd.DataFrame:
    """Return latest source values and one-observation changes for metric cards."""
    required = {"component", "label", "series_id", "date", "value_usd_billions", "retrieved_at"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardDataError(f"Dashboard data is missing columns: {', '.join(missing)}")

    rows: list[dict[str, object]] = []
    for _component, group in frame.sort_values("date").groupby("component", sort=False):
        valid = group.dropna(subset=["value_usd_billions"])
        if valid.empty:
            continue
        latest = valid.iloc[-1]
        previous = valid.iloc[-2] if len(valid) > 1 else None
        rows.append(
            {
                "component": latest["component"],
                "label": latest["label"],
                "series_id": latest["series_id"],
                "date": latest["date"],
                "value_usd_billions": latest["value_usd_billions"],
                "change_usd_billions": (
                    latest["value_usd_billions"] - previous["value_usd_billions"]
                    if previous is not None
                    else pd.NA
                ),
                "retrieved_at": latest["retrieved_at"],
            }
        )
    if not rows:
        raise DashboardDataError("Dashboard source data contains no complete observations")
    return pd.DataFrame(rows)


def load_ecb_data(path: Path) -> pd.DataFrame:
    """Load the separate euro-area measured-data pilot in nominal EUR billions."""
    frame = _read_parquet(path, "ECB data")
    missing = sorted(set(SOURCE_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("ECB data is missing columns: " + ", ".join(missing))
    expected = {"country": {"EA"}, "provider": {"ECB"}, "unit": {"Millions of Euro"}}
    for column, allowed in expected.items():
        actual = set(frame[column].dropna())
        if actual != allowed:
            raise DashboardDataError(f"ECB data has unexpected {column} values: {sorted(actual)}")
    result = frame[SOURCE_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"])
    result["value_eur_billions"] = result["value"] * 0.001
    result["label"] = result["component"].map(ECB_COMPONENT_LABELS).fillna(result["component"])
    return result.sort_values(["component", "date"]).reset_index(drop=True)


def latest_ecb_readings(frame: pd.DataFrame) -> pd.DataFrame:
    """Return latest EUR level, prior-month change, and year-over-year change."""
    required = {"component", "label", "date", "value_eur_billions", "retrieved_at"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardDataError(f"ECB data is missing columns: {', '.join(missing)}")
    rows: list[dict[str, object]] = []
    for _component, group in frame.sort_values("date").groupby("component", sort=False):
        valid = group.dropna(subset=["value_eur_billions"])
        if valid.empty:
            continue
        latest = valid.iloc[-1]
        previous = valid.iloc[-2] if len(valid) > 1 else None
        prior_year = valid.loc[valid["date"] <= latest["date"] - pd.DateOffset(years=1)]
        year_ago = prior_year.iloc[-1] if not prior_year.empty else None
        rows.append(
            {
                "component": latest["component"],
                "label": latest["label"],
                "date": latest["date"],
                "value_eur_billions": latest["value_eur_billions"],
                "change_eur_billions": (
                    latest["value_eur_billions"] - previous["value_eur_billions"]
                    if previous is not None
                    else pd.NA
                ),
                "growth_yoy": (
                    latest["value_eur_billions"] / year_ago["value_eur_billions"] - 1
                    if year_ago is not None and year_ago["value_eur_billions"] != 0
                    else pd.NA
                ),
                "retrieved_at": latest["retrieved_at"],
            }
        )
    if not rows:
        raise DashboardDataError("ECB data contains no numeric observations")
    return pd.DataFrame(rows)


def load_boj_data(path: Path) -> pd.DataFrame:
    """Load the separate Japan measured-data pilot in nominal JPY billions."""
    frame = _read_parquet(path, "BOJ data")
    missing = sorted(set(SOURCE_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("BOJ data is missing columns: " + ", ".join(missing))
    expected = {"country": {"JP"}, "provider": {"BOJ"}, "unit": {"100 Million Yen"}}
    for column, allowed in expected.items():
        actual = set(frame[column].dropna())
        if actual != allowed:
            raise DashboardDataError(f"BOJ data has unexpected {column} values: {sorted(actual)}")
    result = frame[SOURCE_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"])
    result["value_jpy_billions"] = result["value"] * 0.1
    result["label"] = result["component"].map(BOJ_COMPONENT_LABELS).fillna(result["component"])
    return result.sort_values(["component", "date"]).reset_index(drop=True)


def latest_boj_readings(frame: pd.DataFrame) -> pd.DataFrame:
    """Return latest JPY level, prior-month change, and year-over-year growth."""
    required = {"component", "label", "date", "value_jpy_billions", "retrieved_at"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardDataError(f"BOJ data is missing columns: {', '.join(missing)}")
    rows: list[dict[str, object]] = []
    for _component, group in frame.sort_values("date").groupby("component", sort=False):
        valid = group.dropna(subset=["value_jpy_billions"])
        if valid.empty:
            continue
        latest = valid.iloc[-1]
        previous = valid.iloc[-2] if len(valid) > 1 else None
        prior_year = valid.loc[valid["date"] <= latest["date"] - pd.DateOffset(years=1)]
        year_ago = prior_year.iloc[-1] if not prior_year.empty else None
        rows.append(
            {
                "component": latest["component"],
                "label": latest["label"],
                "date": latest["date"],
                "value_jpy_billions": latest["value_jpy_billions"],
                "change_jpy_billions": (
                    latest["value_jpy_billions"] - previous["value_jpy_billions"]
                    if previous is not None
                    else pd.NA
                ),
                "growth_yoy": (
                    latest["value_jpy_billions"] / year_ago["value_jpy_billions"] - 1
                    if year_ago is not None and year_ago["value_jpy_billions"] != 0
                    else pd.NA
                ),
                "retrieved_at": latest["retrieved_at"],
            }
        )
    if not rows:
        raise DashboardDataError("BOJ data contains no numeric observations")
    return pd.DataFrame(rows)


def load_boe_data(path: Path) -> pd.DataFrame:
    """Load the separate UK measured-data pilot in nominal GBP billions."""
    frame = _read_parquet(path, "BoE data")
    missing = sorted(set(SOURCE_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("BoE data is missing columns: " + ", ".join(missing))
    expected = {"country": {"GB"}, "provider": {"BOE"}, "unit": {"Millions of Sterling"}}
    for column, allowed in expected.items():
        actual = set(frame[column].dropna())
        if actual != allowed:
            raise DashboardDataError(f"BoE data has unexpected {column} values: {sorted(actual)}")
    result = frame[SOURCE_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"])
    result["value_gbp_billions"] = result["value"] * 0.001
    result["label"] = result["component"].map(BOE_COMPONENT_LABELS).fillna(result["component"])
    return result.sort_values(["component", "date"]).reset_index(drop=True)


def latest_boe_readings(frame: pd.DataFrame) -> pd.DataFrame:
    """Return latest GBP level, quarterly change, and year-over-year growth."""
    required = {"component", "label", "date", "value_gbp_billions", "retrieved_at"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardDataError(f"BoE data is missing columns: {', '.join(missing)}")
    rows: list[dict[str, object]] = []
    for _component, group in frame.sort_values("date").groupby("component", sort=False):
        valid = group.dropna(subset=["value_gbp_billions"])
        if valid.empty:
            continue
        latest = valid.iloc[-1]
        previous = valid.iloc[-2] if len(valid) > 1 else None
        prior_year = valid.loc[valid["date"] <= latest["date"] - pd.DateOffset(years=1)]
        year_ago = prior_year.iloc[-1] if not prior_year.empty else None
        rows.append(
            {
                "component": latest["component"],
                "label": latest["label"],
                "date": latest["date"],
                "value_gbp_billions": latest["value_gbp_billions"],
                "change_gbp_billions": (
                    latest["value_gbp_billions"] - previous["value_gbp_billions"]
                    if previous is not None
                    else pd.NA
                ),
                "growth_yoy": (
                    latest["value_gbp_billions"] / year_ago["value_gbp_billions"] - 1
                    if year_ago is not None and year_ago["value_gbp_billions"] != 0
                    else pd.NA
                ),
                "retrieved_at": latest["retrieved_at"],
            }
        )
    if not rows:
        raise DashboardDataError("BoE data contains no numeric observations")
    return pd.DataFrame(rows)


def load_pboc_data(path: Path) -> pd.DataFrame:
    """Load public BIS or private PBoC China total assets in nominal CNY billions."""
    frame = _read_parquet(path, "China central-bank data")
    missing = sorted(set(SOURCE_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("China data is missing columns: " + ", ".join(missing))
    actual_country = set(frame["country"].dropna())
    source_contract = (set(frame["provider"].dropna()), set(frame["unit"].dropna()))
    allowed_contracts = {
        (("BIS",), ("Billions of Chinese Yuan",)): 1.0,
        (("PBOC",), ("100 Million Yuan",)): 0.1,
    }
    normalized_contract = tuple(sorted(source_contract[0])), tuple(sorted(source_contract[1]))
    if actual_country != {"CN"} or normalized_contract not in allowed_contracts:
        raise DashboardDataError(
            "China data has an unsupported country/provider/unit contract: "
            f"{sorted(actual_country)}, {normalized_contract}"
        )
    result = frame[SOURCE_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    if result["date"].isna().any():
        raise DashboardDataError("PBoC data contains invalid dates")
    result["value_cny_billions"] = result["value"] * allowed_contracts[normalized_contract]
    result["label"] = result["component"].map(PBOC_COMPONENT_LABELS).fillna(result["component"])
    return result.sort_values(["component", "date"]).reset_index(drop=True)


def latest_pboc_readings(frame: pd.DataFrame) -> pd.DataFrame:
    """Return latest CNY level, prior-month change, and year-over-year growth."""
    required = {"component", "label", "date", "value_cny_billions", "retrieved_at"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardDataError(f"PBoC data is missing columns: {', '.join(missing)}")
    rows: list[dict[str, object]] = []
    for _component, group in frame.sort_values("date").groupby("component", sort=False):
        valid = group.dropna(subset=["value_cny_billions"])
        if valid.empty:
            continue
        latest = valid.iloc[-1]
        previous = valid.iloc[-2] if len(valid) > 1 else None
        prior_year = valid.loc[valid["date"] <= latest["date"] - pd.DateOffset(years=1)]
        year_ago = prior_year.iloc[-1] if not prior_year.empty else None
        rows.append(
            {
                "component": latest["component"],
                "label": latest["label"],
                "date": latest["date"],
                "value_cny_billions": latest["value_cny_billions"],
                "provider": latest["provider"],
                "change_cny_billions": (
                    latest["value_cny_billions"] - previous["value_cny_billions"]
                    if previous is not None
                    else pd.NA
                ),
                "growth_yoy": (
                    latest["value_cny_billions"] / year_ago["value_cny_billions"] - 1
                    if year_ago is not None and year_ago["value_cny_billions"] != 0
                    else pd.NA
                ),
                "retrieved_at": latest["retrieved_at"],
            }
        )
    if not rows:
        raise DashboardDataError("PBoC data contains no numeric observations")
    return pd.DataFrame(rows)


def build_central_bank_index_comparison(
    series: dict[str, pd.DataFrame], *, start: str | pd.Timestamp
) -> pd.DataFrame:
    """Rebase separate native-currency central-bank asset series to 100 after ``start``."""
    start_date = pd.Timestamp(start)
    rows: list[pd.DataFrame] = []
    for label, frame in series.items():
        required = {"date", "native_value"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise DashboardDataError(
                f"Central-bank comparison for {label} is missing columns: {', '.join(missing)}"
            )
        selected = frame.loc[pd.to_datetime(frame["date"]) >= start_date, ["date", "native_value"]]
        selected = selected.dropna(subset=["native_value"]).sort_values("date").copy()
        if selected.empty:
            continue
        base = float(selected.iloc[0]["native_value"])
        if base <= 0:
            raise DashboardDataError(f"Central-bank comparison for {label} has an invalid base")
        selected["central_bank"] = label
        selected["index"] = selected["native_value"] / base * 100
        selected["base_date"] = selected.iloc[0]["date"]
        rows.append(selected[["date", "central_bank", "index", "base_date"]])
    if not rows:
        raise DashboardDataError("Central-bank comparison contains no observations")
    return pd.concat(rows, ignore_index=True).sort_values(["central_bank", "date"])


def load_liquidity_model_data(path: Path) -> pd.DataFrame:
    """Load package-calculated model levels for display in USD billions."""
    frame = _read_parquet(path, "Liquidity model data")
    missing = sorted(set(MODEL_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Liquidity model data is missing columns: " + ", ".join(missing))
    if frame.empty:
        raise DashboardDataError("Liquidity model data contains no observations")
    if set(frame["unit"].dropna()) != {"Millions of U.S. Dollars"}:
        raise DashboardDataError("Liquidity model data must use Millions of U.S. Dollars")

    result = frame[MODEL_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"])
    result["value_usd_billions"] = result["value"] * 0.001
    return result.sort_values(["model_id", "date"]).reset_index(drop=True)


def latest_model_readings(frame: pd.DataFrame) -> pd.DataFrame:
    """Return latest complete model values and one-week changes."""
    required = {"model_id", "model_name", "date", "value_usd_billions", "formula"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardDataError(f"Liquidity model data is missing columns: {', '.join(missing)}")

    rows: list[dict[str, object]] = []
    for _model_id, group in frame.sort_values("date").groupby("model_id", sort=False):
        valid = group.dropna(subset=["value_usd_billions"])
        if valid.empty:
            continue
        latest = valid.iloc[-1]
        previous = valid.iloc[-2] if len(valid) > 1 else None
        rows.append(
            {
                "model_id": latest["model_id"],
                "model_name": latest["model_name"],
                "date": latest["date"],
                "value_usd_billions": latest["value_usd_billions"],
                "change_usd_billions": (
                    latest["value_usd_billions"] - previous["value_usd_billions"]
                    if previous is not None
                    else pd.NA
                ),
                "formula": latest["formula"],
            }
        )
    if not rows:
        raise DashboardDataError("Liquidity model data contains no complete observations")
    return pd.DataFrame(rows)


def load_ogli_data(path: Path) -> pd.DataFrame:
    """Load package-calculated OGLI observations without recalculating them in Streamlit."""
    frame = _read_parquet(path, "OGLI data")
    missing = sorted(set(OGLI_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("OGLI data is missing columns: " + ", ".join(missing))
    if frame.empty:
        raise DashboardDataError("OGLI data contains no observations")

    result = frame[OGLI_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"])
    invalid = result["ogli"].dropna().loc[lambda values: (values < 0) | (values > 100)]
    if not invalid.empty:
        raise DashboardDataError("OGLI data contains values outside 0-100")
    return result.sort_values(["model_id", "date"]).reset_index(drop=True)


def latest_ogli_readings(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the latest available OGLI row for each model."""
    required = {"model_id", "model_name", "date", "ogli", "regime"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardDataError(f"OGLI data is missing columns: {', '.join(missing)}")
    available = frame.dropna(subset=["ogli"])
    if available.empty:
        raise DashboardDataError("OGLI data contains no available normalized readings")
    return (
        available.sort_values("date")
        .groupby("model_id", as_index=False, sort=False)
        .tail(1)
        .reset_index(drop=True)
    )


def load_market_comparisons(path: Path) -> pd.DataFrame:
    """Load package-calculated liquidity-market pairs for local presentation."""
    frame = _read_parquet(path, "Liquidity-market comparison data")
    legacy_required = set(MARKET_COMPARISON_COLUMNS) - {
        "signal_observation_date",
        "signal_available_date",
        "analysis_mode",
        "publication_lag_weeks",
        "regime",
        "is_non_overlapping",
    }
    missing = sorted(legacy_required - set(frame.columns))
    if missing:
        raise DashboardDataError("Market comparison data is missing columns: " + ", ".join(missing))
    defaults = {
        "signal_observation_date": frame["date"],
        "signal_available_date": frame["date"],
        "analysis_mode": "observation_date",
        "publication_lag_weeks": 0,
        "regime": pd.NA,
        "is_non_overlapping": False,
    }
    for column, value in defaults.items():
        if column not in frame.columns:
            frame[column] = value
    result = frame[MARKET_COMPARISON_COLUMNS].copy()
    for column in [
        "date",
        "return_start_date",
        "return_end_date",
        "signal_observation_date",
        "signal_available_date",
    ]:
        result[column] = pd.to_datetime(result[column])
    return result.sort_values(["model_id", "market_id", "horizon_weeks", "date"]).reset_index(
        drop=True
    )


def load_market_correlations(path: Path) -> pd.DataFrame:
    """Load package-calculated lagged-correlation summaries for local presentation."""
    frame = _read_parquet(path, "Liquidity-market correlation data")
    legacy_required = set(MARKET_CORRELATION_COLUMNS) - {
        "analysis_mode",
        "sample_policy",
        "confidence_level",
        "correlation_ci_lower",
        "correlation_ci_upper",
        "bootstrap_ci_lower",
        "bootstrap_ci_upper",
        "bootstrap_method",
        "bootstrap_resamples",
        "bootstrap_valid_resamples",
        "bootstrap_block_length",
        "bootstrap_seed",
    }
    missing = sorted(legacy_required - set(frame.columns))
    if missing:
        raise DashboardDataError(
            "Market correlation data is missing columns: " + ", ".join(missing)
        )
    defaults = {
        "analysis_mode": "observation_date",
        "sample_policy": "overlapping",
        "confidence_level": 0.95,
        "correlation_ci_lower": pd.NA,
        "correlation_ci_upper": pd.NA,
        "bootstrap_ci_lower": pd.NA,
        "bootstrap_ci_upper": pd.NA,
        "bootstrap_method": "unavailable_in_legacy_snapshot",
        "bootstrap_resamples": 0,
        "bootstrap_valid_resamples": 0,
        "bootstrap_block_length": pd.NA,
        "bootstrap_seed": pd.NA,
    }
    for column, value in defaults.items():
        if column not in frame.columns:
            frame[column] = value
    return (
        frame[MARKET_CORRELATION_COLUMNS]
        .sort_values(["model_id", "market_id", "horizon_weeks"])
        .reset_index(drop=True)
    )


def load_market_regime_statistics(path: Path) -> pd.DataFrame:
    """Load package-calculated Bitcoin outcome summaries by OGLI regime."""
    frame = _read_parquet(path, "Market regime statistics")
    missing = sorted(set(MARKET_REGIME_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Market regime data is missing columns: " + ", ".join(missing))
    return (
        frame[MARKET_REGIME_COLUMNS]
        .sort_values(["model_id", "analysis_mode", "sample_policy", "horizon_weeks", "regime"])
        .reset_index(drop=True)
    )


def load_market_subperiod_statistics(path: Path) -> pd.DataFrame:
    """Load package-calculated Bitcoin correlations in predeclared research periods."""
    frame = _read_parquet(path, "Market subperiod statistics")
    bootstrap_defaults = {
        "bootstrap_ci_lower": pd.NA,
        "bootstrap_ci_upper": pd.NA,
        "bootstrap_method": "unavailable_in_legacy_snapshot",
        "bootstrap_resamples": 0,
        "bootstrap_valid_resamples": 0,
        "bootstrap_block_length": pd.NA,
        "bootstrap_seed": pd.NA,
    }
    for column, value in bootstrap_defaults.items():
        if column not in frame.columns:
            frame[column] = value
    missing = sorted(set(MARKET_SUBPERIOD_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Market subperiod data is missing columns: " + ", ".join(missing))
    result = frame[MARKET_SUBPERIOD_COLUMNS].copy()
    result["period_start"] = pd.to_datetime(result["period_start"])
    result["period_end"] = pd.to_datetime(result["period_end"])
    return result.sort_values(
        ["period_order", "model_id", "analysis_mode", "sample_policy", "horizon_weeks"]
    ).reset_index(drop=True)


def load_snapshot_manifest(path: Path) -> dict[str, object]:
    """Load and validate the public snapshot's point-in-time provenance record."""
    if not path.is_file():
        raise DashboardDataError(f"Snapshot provenance manifest not found at {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DashboardDataError(f"Could not read snapshot provenance manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise DashboardDataError("Snapshot provenance manifest must be a JSON object")
    required = {
        "schema_version",
        "classification",
        "generated_at",
        "pipeline_version",
        "source_commit",
        "working_tree_dirty",
        "snapshot_count",
        "files",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise DashboardDataError("Snapshot provenance manifest is missing: " + ", ".join(missing))
    if manifest["schema_version"] != 1 or manifest["classification"] != "snapshot_provenance":
        raise DashboardDataError("Snapshot provenance manifest has an unsupported schema")
    files = manifest["files"]
    if not isinstance(files, dict) or manifest["snapshot_count"] != len(files):
        raise DashboardDataError("Snapshot provenance manifest file count is inconsistent")
    generated_at = pd.to_datetime(manifest["generated_at"], utc=True, errors="coerce")
    if pd.isna(generated_at):
        raise DashboardDataError("Snapshot provenance manifest has an invalid generation time")
    for filename, metadata in files.items():
        if not isinstance(filename, str) or not isinstance(metadata, dict):
            raise DashboardDataError("Snapshot provenance manifest has an invalid file entry")
        digest = metadata.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise DashboardDataError(f"Snapshot provenance hash is invalid for {filename}")
    return manifest


def load_macro_context(path: Path) -> pd.DataFrame:
    """Load measured Treasury/dollar context and the package-calculated curve slope."""
    frame = _read_parquet(path, "Macro context data")
    missing = sorted(set(MACRO_CONTEXT_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Macro context data is missing columns: " + ", ".join(missing))
    result = frame[MACRO_CONTEXT_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"])
    return result.sort_values("date").reset_index(drop=True)


def load_point_in_time_comparison(path: Path) -> pd.DataFrame:
    """Load the local monthly vintage pilot without recalculating it in Streamlit."""
    frame = _read_parquet(path, "Point-in-time OGLI comparison")
    missing = sorted(set(POINT_IN_TIME_COMPARISON_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError(
            "Point-in-time OGLI comparison is missing columns: " + ", ".join(missing)
        )
    result = frame[POINT_IN_TIME_COMPARISON_COLUMNS].copy()
    result["information_date"] = pd.to_datetime(result["information_date"], errors="coerce")
    result["signal_observation_date"] = pd.to_datetime(
        result["signal_observation_date"], errors="coerce"
    )
    if result.empty or result[["information_date", "signal_observation_date"]].isna().any().any():
        raise DashboardDataError("Point-in-time OGLI comparison has no valid dated observations")
    for column in ["vintage_ogli", "current_ogli"]:
        invalid = result[column].dropna().loc[lambda values: (values < 0) | (values > 100)]
        if not invalid.empty:
            raise DashboardDataError(f"Point-in-time comparison has invalid {column} values")
    if set(result["comparison_policy"].dropna()) != {"same_observation_date"}:
        raise DashboardDataError("Point-in-time comparison has an unsupported date policy")
    return result.sort_values(["information_date", "model_id"]).reset_index(drop=True)


def load_point_in_time_market_pairs(path: Path) -> pd.DataFrame:
    """Load package-calculated vintage-signal and forward-market outcome pairs."""
    frame = _read_parquet(path, "Point-in-time market pairs")
    missing = sorted(set(POINT_IN_TIME_MARKET_PAIR_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Point-in-time market pairs are missing: " + ", ".join(missing))
    result = frame[POINT_IN_TIME_MARKET_PAIR_COLUMNS].copy()
    date_columns = [
        "information_date",
        "signal_observation_date",
        "signal_available_date",
        "start_target_date",
        "start_observation_date",
        "end_target_date",
        "end_observation_date",
    ]
    for column in date_columns:
        result[column] = pd.to_datetime(result[column], errors="coerce")
    if result.empty or result[date_columns].isna().any().any():
        raise DashboardDataError("Point-in-time market pairs contain invalid dates")
    if set(result["classification"]) != {"statistical_transformation"}:
        raise DashboardDataError("Point-in-time market pairs have an unsupported classification")
    return result.sort_values(
        ["market_id", "model_id", "publication_lag_weeks", "horizon_months", "information_date"]
    ).reset_index(drop=True)


def load_point_in_time_market_summary(path: Path) -> pd.DataFrame:
    """Load descriptive point-in-time market summaries calculated by the package."""
    frame = _read_parquet(path, "Point-in-time market summary")
    missing = sorted(set(POINT_IN_TIME_MARKET_SUMMARY_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Point-in-time market summary is missing: " + ", ".join(missing))
    result = frame[POINT_IN_TIME_MARKET_SUMMARY_COLUMNS].copy()
    if result.empty or not set(result["sample_policy"]).issubset(
        {"overlapping", "non_overlapping"}
    ):
        raise DashboardDataError("Point-in-time market summary has an unsupported sample policy")
    return result.sort_values(
        ["market_id", "model_id", "sample_policy", "publication_lag_weeks", "horizon_months"]
    ).reset_index(drop=True)


def load_bitcoin_outcomes(path: Path) -> pd.DataFrame:
    """Load package-calculated Bitcoin path outcomes and vintage diagnostics."""
    frame = _read_parquet(path, "Bitcoin research outcomes")
    missing = sorted(set(BITCOIN_OUTCOME_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Bitcoin research outcomes are missing: " + ", ".join(missing))
    result = frame[BITCOIN_OUTCOME_COLUMNS].copy()
    date_columns = [
        "information_date",
        "signal_available_date",
        "start_observation_date",
        "end_observation_date",
    ]
    for column in date_columns:
        result[column] = pd.to_datetime(result[column], errors="coerce")
    if result.empty or result[date_columns].isna().any().any():
        raise DashboardDataError("Bitcoin research outcomes contain invalid dates")
    if set(result["bitcoin_research_classification"]) != {"statistical_transformation"}:
        raise DashboardDataError("Bitcoin research outcomes have an unsupported classification")
    if set(result["market_id"]) != {"bitcoin"}:
        raise DashboardDataError("Bitcoin research outcomes contain a non-Bitcoin market")
    invalid_paths = (
        result["maximum_upside_from_start"].lt(0)
        | result["maximum_downside_from_start"].gt(0)
        | result["maximum_drawdown_from_peak"].gt(0)
        | result["maximum_drawdown_from_peak"].lt(-1)
    )
    if invalid_paths.any():
        raise DashboardDataError("Bitcoin research outcomes contain impossible path statistics")
    return result.sort_values(
        ["model_id", "publication_lag_weeks", "horizon_months", "information_date"]
    ).reset_index(drop=True)


def load_bitcoin_regime_summary(path: Path) -> pd.DataFrame:
    """Load Bitcoin return and path-risk summaries by vintage regime and transition."""
    frame = _read_parquet(path, "Bitcoin regime summary")
    missing = sorted(set(BITCOIN_REGIME_SUMMARY_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Bitcoin regime summary is missing: " + ", ".join(missing))
    result = frame[BITCOIN_REGIME_SUMMARY_COLUMNS].copy()
    if result.empty or not set(result["analysis_dimension"]).issubset(
        {"overall", "vintage_regime", "transition_direction"}
    ):
        raise DashboardDataError("Bitcoin regime summary has an unsupported dimension")
    if not set(result["sample_policy"]).issubset({"overlapping", "non_overlapping"}):
        raise DashboardDataError("Bitcoin regime summary has an unsupported sample policy")
    if set(result["classification"]) != {"descriptive_statistic"}:
        raise DashboardDataError("Bitcoin regime summary has an unsupported classification")
    if not set(result["specification_role"]).issubset({"primary", "robustness_check"}):
        raise DashboardDataError("Bitcoin regime summary has an unsupported specification role")
    if set(result["specification_classification"]) != {"model_assumption"}:
        raise DashboardDataError("Bitcoin regime summary misclassifies its specification role")
    primary = result.loc[result["specification_role"] == "primary"]
    if primary.empty or any(
        primary[column].nunique() != 1
        for column in ["model_id", "publication_lag_weeks", "sample_policy"]
    ):
        raise DashboardDataError("Bitcoin regime summary has an ambiguous primary specification")
    invalid_ranges = (
        result["observations"].le(0)
        | ~result["positive_share"].between(0, 1)
        | ~result["confidence_level"].between(0, 1, inclusive="neither")
        | result["standard_error"].dropna().lt(0).reindex(result.index, fill_value=False)
        | result["mean_maximum_upside"].lt(0)
        | result["mean_maximum_downside"].gt(0)
        | result["mean_maximum_drawdown"].gt(0)
        | result["mean_maximum_drawdown"].lt(-1)
    )
    complete_intervals = (
        result[["mean_return_ci_lower", "mean_return", "mean_return_ci_upper"]].notna().all(axis=1)
    )
    invalid_intervals = complete_intervals & (
        result["mean_return_ci_lower"].gt(result["mean_return"])
        | result["mean_return_ci_upper"].lt(result["mean_return"])
    )
    if invalid_ranges.any() or invalid_intervals.any():
        raise DashboardDataError("Bitcoin regime summary contains invalid statistics")
    return result.sort_values(
        [
            "model_id",
            "sample_policy",
            "publication_lag_weeks",
            "horizon_months",
            "analysis_dimension",
            "group_label",
        ]
    ).reset_index(drop=True)


def load_bitcoin_revision_summary(path: Path) -> pd.DataFrame:
    """Load vintage-versus-revised Bitcoin signal comparison summaries."""
    frame = _read_parquet(path, "Bitcoin revision summary")
    missing = sorted(set(BITCOIN_REVISION_SUMMARY_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Bitcoin revision summary is missing: " + ", ".join(missing))
    result = frame[BITCOIN_REVISION_SUMMARY_COLUMNS].copy()
    if result.empty or not set(result["sample_policy"]).issubset(
        {"overlapping", "non_overlapping"}
    ):
        raise DashboardDataError("Bitcoin revision summary has an unsupported sample policy")
    if set(result["classification"]) != {"descriptive_statistic"}:
        raise DashboardDataError("Bitcoin revision summary has an unsupported classification")
    if not set(result["specification_role"]).issubset({"primary", "robustness_check"}):
        raise DashboardDataError("Bitcoin revision summary has an unsupported specification role")
    if set(result["specification_classification"]) != {"model_assumption"}:
        raise DashboardDataError("Bitcoin revision summary misclassifies its specification role")
    if result.loc[result["specification_role"] == "primary"].empty:
        raise DashboardDataError("Bitcoin revision summary has no primary specification")
    invalid_ranges = (
        result["observations"].le(0)
        | result["mean_absolute_momentum_revision"].lt(0)
        | ~result["regime_agreement_share"].between(0, 1)
    )
    correlations = result[["vintage_signal_correlation", "current_vintage_signal_correlation"]]
    if invalid_ranges.any() or correlations.abs().gt(1).any().any():
        raise DashboardDataError("Bitcoin revision summary contains invalid statistics")
    return result.sort_values(
        ["model_id", "sample_policy", "publication_lag_weeks", "horizon_months"]
    ).reset_index(drop=True)


def load_bitcoin_contrast_summary(path: Path) -> pd.DataFrame:
    """Load directional expansionary-minus-contractionary Bitcoin return contrasts."""
    frame = _read_parquet(path, "Bitcoin directional contrast summary")
    missing = sorted(set(BITCOIN_CONTRAST_SUMMARY_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Bitcoin contrast summary is missing: " + ", ".join(missing))
    result = frame[BITCOIN_CONTRAST_SUMMARY_COLUMNS].copy()
    if result.empty or not set(result["sample_policy"]).issubset(
        {"overlapping", "non_overlapping"}
    ):
        raise DashboardDataError("Bitcoin contrast summary has an unsupported sample policy")
    if set(result["classification"]) != {"descriptive_statistic"}:
        raise DashboardDataError("Bitcoin contrast summary has an unsupported classification")
    if set(result["regime_group_classification"]) != {"model_assumption"}:
        raise DashboardDataError("Bitcoin contrast summary misclassifies its regime groups")
    if set(result["interval_status_classification"]) != {"statistical_transformation"}:
        raise DashboardDataError("Bitcoin contrast summary misclassifies its interval status")
    allowed_statuses = {
        "insufficient_sample",
        "inconclusive",
        "positive_interval",
        "negative_interval",
    }
    if not set(result["interval_status"]).issubset(allowed_statuses):
        raise DashboardDataError("Bitcoin contrast summary has an unsupported interval status")
    if set(result["specification_classification"]) != {"model_assumption"}:
        raise DashboardDataError("Bitcoin contrast summary misclassifies its specification role")
    if not set(result["specification_role"]).issubset({"primary", "robustness_check"}):
        raise DashboardDataError("Bitcoin contrast summary has an unsupported specification role")
    if result.loc[result["specification_role"] == "primary"].empty:
        raise DashboardDataError("Bitcoin contrast summary has no primary specification")
    count_columns = ["expansionary_observations", "contractionary_observations"]
    share_columns = ["expansionary_positive_share", "contractionary_positive_share"]
    if (
        result[count_columns].lt(0).any().any()
        or not result[share_columns].apply(lambda column: column.dropna().between(0, 1).all()).all()
    ):
        raise DashboardDataError("Bitcoin contrast summary contains invalid statistics")
    complete_intervals = (
        result[["spread_ci_lower", "mean_return_spread", "spread_ci_upper"]].notna().all(axis=1)
    )
    invalid_intervals = complete_intervals & (
        result["spread_ci_lower"].gt(result["mean_return_spread"])
        | result["spread_ci_upper"].lt(result["mean_return_spread"])
    )
    if invalid_intervals.any():
        raise DashboardDataError("Bitcoin contrast summary contains an invalid interval")
    return result.sort_values(
        ["model_id", "sample_policy", "publication_lag_weeks", "horizon_months"]
    ).reset_index(drop=True)


def load_global_central_bank_aggregate(path: Path) -> pd.DataFrame:
    """Load the package-calculated balanced quarterly USD aggregate."""
    frame = _read_parquet(path, "Global central-bank aggregate")
    required = {
        "date",
        "total_usd_millions",
        "total_usd_trillions",
        "component_count",
        "change_1q",
        "growth_yoy",
        "classification",
        "name",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardDataError("Global aggregate is missing: " + ", ".join(missing))
    if set(frame["classification"]) != {"model_assumption"}:
        raise DashboardDataError("Global aggregate must be classified as a model assumption")
    result = frame[list(required)].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    if result.empty or result["date"].isna().any() or (result["total_usd_millions"] <= 0).any():
        raise DashboardDataError("Global aggregate contains invalid observations")
    return result.sort_values("date").reset_index(drop=True)


def load_global_central_bank_detail(path: Path) -> pd.DataFrame:
    """Load USD-converted component contributions supporting the aggregate."""
    frame = _read_parquet(path, "Global central-bank detail")
    required = {
        "date",
        "source_date",
        "component",
        "central_bank",
        "native_value",
        "native_unit",
        "fx_component",
        "fx_date",
        "fx_rate",
        "value_usd_millions",
        "is_balanced",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardDataError("Global aggregate detail is missing: " + ", ".join(missing))
    result = frame[list(required)].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result["source_date"] = pd.to_datetime(result["source_date"], errors="coerce")
    result["fx_date"] = pd.to_datetime(result["fx_date"], errors="coerce")
    result = result.loc[result["is_balanced"]].copy()
    if result.empty or result[["date", "source_date", "fx_date"]].isna().any().any():
        raise DashboardDataError("Global aggregate detail contains invalid observations")
    return result.sort_values(["date", "central_bank"]).reset_index(drop=True)
