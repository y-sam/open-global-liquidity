"""Deployment-local validation and display preparation for Streamlit snapshots.

Economic transformations remain in ``src/open_global_liquidity``. This module deliberately handles
only the presentation contract so Streamlit Cloud never depends on a cached installed project wheel.
"""

from __future__ import annotations

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
]

COMPONENT_LABELS = {
    "fed_assets": "Fed total assets",
    "treasury_general_account": "Treasury General Account",
    "overnight_reverse_repo": "ON reverse repo",
    "reserve_balances": "Reserve balances",
}

_UNIT_TO_BILLIONS = {
    "Millions of U.S. Dollars": 0.001,
    "Billions of U.S. Dollars": 1.0,
}


class DashboardDataError(ValueError):
    """Raised when snapshot data cannot safely support the dashboard."""


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
    missing = sorted(set(MARKET_COMPARISON_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError("Market comparison data is missing columns: " + ", ".join(missing))
    result = frame[MARKET_COMPARISON_COLUMNS].copy()
    for column in ["date", "return_start_date", "return_end_date"]:
        result[column] = pd.to_datetime(result[column])
    return result.sort_values(["model_id", "market_id", "horizon_weeks", "date"]).reset_index(
        drop=True
    )


def load_market_correlations(path: Path) -> pd.DataFrame:
    """Load package-calculated lagged-correlation summaries for local presentation."""
    frame = _read_parquet(path, "Liquidity-market correlation data")
    missing = sorted(set(MARKET_CORRELATION_COLUMNS) - set(frame.columns))
    if missing:
        raise DashboardDataError(
            "Market correlation data is missing columns: " + ", ".join(missing)
        )
    return (
        frame[MARKET_CORRELATION_COLUMNS]
        .sort_values(["model_id", "market_id", "horizon_weeks"])
        .reset_index(drop=True)
    )
