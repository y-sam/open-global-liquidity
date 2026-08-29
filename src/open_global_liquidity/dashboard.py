"""Reusable, non-UI data preparation for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from open_global_liquidity.data.base import STANDARD_COLUMNS, validate_standardized_frame

COMPONENT_LABELS = {
    "fed_assets": "Fed total assets",
    "treasury_general_account": "Treasury General Account",
    "overnight_reverse_repo": "ON reverse repo",
    "reserve_balances": "Reserve balances",
}
ECB_COMPONENT_LABELS = {"eurosystem_total_assets": "Eurosystem total assets"}
BOJ_COMPONENT_LABELS = {"boj_total_assets": "Bank of Japan total assets"}
BOE_COMPONENT_LABELS = {"boe_total_assets": "Bank of England total assets"}

_UNIT_TO_BILLIONS = {
    "Millions of U.S. Dollars": 0.001,
    "Billions of U.S. Dollars": 1.0,
}

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


class DashboardDataError(ValueError):
    """Raised when processed data cannot safely support the dashboard."""


def resolve_dashboard_data_path(processed_path: Path, snapshot_path: Path) -> tuple[Path, str]:
    """Prefer locally processed data and fall back to a versioned public snapshot."""
    if processed_path.is_file():
        return processed_path, "Local processed data"
    if snapshot_path.is_file():
        return snapshot_path, "Bundled public snapshot"
    raise DashboardDataError(
        "No dashboard data is available. Run the pipeline locally or publish a dashboard snapshot."
    )


def load_dashboard_data(path: Path) -> pd.DataFrame:
    """Load validated pipeline output and express dollar levels in common USD billions.

    Unit conversion is a display transformation, not an economic model: source observations in
    millions are divided by 1,000, while observations already in billions are unchanged.
    """
    if not path.is_file():
        raise DashboardDataError(
            f"Processed data not found at {path}. Run the ingestion pipeline first."
        )
    try:
        frame = pd.read_parquet(path)
    except (OSError, ValueError) as exc:
        raise DashboardDataError(f"Could not read processed data at {path}: {exc}") from exc

    validate_standardized_frame(frame)
    unsupported = sorted(set(frame["unit"].dropna()) - _UNIT_TO_BILLIONS.keys())
    if unsupported:
        raise DashboardDataError(
            "Dashboard cannot convert these source units to USD billions: " + ", ".join(unsupported)
        )

    result = frame[STANDARD_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"])
    result["value_usd_billions"] = result["value"] * result["unit"].map(_UNIT_TO_BILLIONS)
    result["label"] = result["component"].map(COMPONENT_LABELS).fillna(result["component"])
    return result.sort_values(["component", "date"]).reset_index(drop=True)


def latest_readings(frame: pd.DataFrame) -> pd.DataFrame:
    """Return latest values and one-observation changes for dashboard metric cards."""
    required = {"component", "label", "series_id", "date", "value_usd_billions", "retrieved_at"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardDataError(f"Dashboard data is missing columns: {', '.join(missing)}")
    if frame.empty:
        raise DashboardDataError("Dashboard data contains no observations")

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
        raise DashboardDataError("Dashboard data contains no numeric observations")
    return pd.DataFrame(rows)


def load_ecb_data(path: Path) -> pd.DataFrame:
    """Load the separate euro-area measured-data pilot in nominal EUR billions."""
    if not path.is_file():
        raise DashboardDataError(f"ECB data not found at {path}. Run the ingestion pipeline first.")
    try:
        frame = pd.read_parquet(path)
    except (OSError, ValueError) as exc:
        raise DashboardDataError(f"Could not read ECB data at {path}: {exc}") from exc
    validate_standardized_frame(frame)
    expected = {"country": {"EA"}, "provider": {"ECB"}, "unit": {"Millions of Euro"}}
    for column, allowed in expected.items():
        actual = set(frame[column].dropna())
        if actual != allowed:
            raise DashboardDataError(f"ECB data has unexpected {column} values: {sorted(actual)}")
    result = frame[STANDARD_COLUMNS].copy()
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
    if not path.is_file():
        raise DashboardDataError(f"BOJ data not found at {path}. Run the ingestion pipeline first.")
    try:
        frame = pd.read_parquet(path)
    except (OSError, ValueError) as exc:
        raise DashboardDataError(f"Could not read BOJ data at {path}: {exc}") from exc
    validate_standardized_frame(frame)
    expected = {"country": {"JP"}, "provider": {"BOJ"}, "unit": {"100 Million Yen"}}
    for column, allowed in expected.items():
        actual = set(frame[column].dropna())
        if actual != allowed:
            raise DashboardDataError(f"BOJ data has unexpected {column} values: {sorted(actual)}")
    result = frame[STANDARD_COLUMNS].copy()
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
    if not path.is_file():
        raise DashboardDataError(f"BoE data not found at {path}. Run the ingestion pipeline first.")
    try:
        frame = pd.read_parquet(path)
    except (OSError, ValueError) as exc:
        raise DashboardDataError(f"Could not read BoE data at {path}: {exc}") from exc
    validate_standardized_frame(frame)
    expected = {"country": {"GB"}, "provider": {"BOE"}, "unit": {"Millions of Sterling"}}
    for column, allowed in expected.items():
        actual = set(frame[column].dropna())
        if actual != allowed:
            raise DashboardDataError(f"BoE data has unexpected {column} values: {sorted(actual)}")
    result = frame[STANDARD_COLUMNS].copy()
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


def load_liquidity_model_data(path: Path) -> pd.DataFrame:
    """Load package-calculated liquidity models for display in USD billions."""
    if not path.is_file():
        raise DashboardDataError(
            f"Liquidity model data not found at {path}. Run the pipeline first."
        )
    try:
        frame = pd.read_parquet(path)
    except (OSError, ValueError) as exc:
        raise DashboardDataError(f"Could not read liquidity model data at {path}: {exc}") from exc
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
    """Return the latest complete model values and one-week changes."""
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
