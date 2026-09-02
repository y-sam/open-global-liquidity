"""Keyless U.S. Treasury Fiscal Data ingestion for marketable collateral supply."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS, validate_standardized_frame

LOGGER = logging.getLogger(__name__)
MSPD_TABLE_1_URL = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/debt/mspd/mspd_table_1"
)


class TreasuryFiscalDataError(RuntimeError):
    """Raised when Treasury Fiscal Data returns an unusable response."""


class TreasuryFiscalDataProvider:
    """Fetch the monthly MSPD Total Marketable debt-held-by-public observation.

    The selected field is a gross par-value stock. It is measured source data, not a direct
    measure of repo-eligible collateral actually available to private intermediaries.
    """

    def __init__(
        self,
        *,
        cache_dir: Path = Path("data/raw/treasury"),
        timeout_seconds: float = 30.0,
        cache_ttl: timedelta = timedelta(hours=24),
        client: httpx.Client | None = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.timeout_seconds = timeout_seconds
        self.cache_ttl = cache_ttl
        self._client = client

    def fetch_definition(
        self,
        definition: SeriesDefinition,
        *,
        start: str | date | None = None,
        end: str | date | None = None,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Return the configured MSPD series in the project standard schema."""
        start_date = _coerce_date(start or definition.start, "start")
        end_date = _coerce_date(end, "end") if end is not None else None
        if end_date is not None and end_date < start_date:
            raise ValueError("end must be on or after start")

        cache_path = self.cache_dir / "mspd_total_marketable_public.parquet"
        if _cache_is_fresh(cache_path, self.cache_ttl) and not force_refresh:
            cached = pd.read_parquet(cache_path)
            cached_dates = pd.to_datetime(cached.get("date"), errors="coerce")
            if not cached_dates.empty and cached_dates.min() <= pd.Timestamp(start_date):
                frame = cached
                LOGGER.info("Treasury Fiscal Data cache hit: %s", cache_path)
            else:
                LOGGER.info("Treasury cache does not cover requested start; refreshing")
                frame = self._download(definition, start_date)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                frame.to_parquet(cache_path, index=False)
        else:
            frame = self._download(definition, start_date)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            frame.to_parquet(cache_path, index=False)
            LOGGER.info("Cached %d Treasury observations at %s", len(frame), cache_path)

        selected = frame.loc[frame["date"] >= pd.Timestamp(start_date)].copy()
        if end_date is not None:
            selected = selected.loc[selected["date"] <= pd.Timestamp(end_date)].copy()
        if selected.empty:
            raise TreasuryFiscalDataError(
                "Treasury returned no observations in the requested range"
            )
        validate_standardized_frame(selected)
        return selected[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)

    def _download(self, definition: SeriesDefinition, start: date) -> pd.DataFrame:
        params = {
            "fields": "record_date,security_type_desc,debt_held_public_mil_amt",
            "filter": (
                f"record_date:gte:{start.isoformat()},security_type_desc:eq:Total Marketable"
            ),
            "sort": "record_date",
            "page[size]": "10000",
        }
        try:
            if self._client is None:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.get(MSPD_TABLE_1_URL, params=params)
            else:
                response = self._client.get(MSPD_TABLE_1_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise TreasuryFiscalDataError(f"Treasury Fiscal Data request failed: {exc}") from exc

        rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list) or not rows:
            raise TreasuryFiscalDataError("Treasury response is missing expected MSPD data")
        raw = pd.DataFrame(rows)
        required = {"record_date", "security_type_desc", "debt_held_public_mil_amt"}
        missing = sorted(required - set(raw.columns))
        if missing:
            raise TreasuryFiscalDataError(
                "Treasury response is missing fields: " + ", ".join(missing)
            )
        if set(raw["security_type_desc"]) != {"Total Marketable"}:
            raise TreasuryFiscalDataError("Treasury response contains an unexpected security type")
        dates = pd.to_datetime(raw["record_date"], errors="coerce")
        values = pd.to_numeric(raw["debt_held_public_mil_amt"], errors="coerce")
        if dates.isna().any() or values.isna().any() or (values < 0).any():
            raise TreasuryFiscalDataError("Treasury response contains invalid dates or amounts")
        if dates.duplicated().any():
            raise TreasuryFiscalDataError("Treasury response contains duplicate monthly dates")
        retrieved_at = pd.Timestamp.now(tz=UTC)
        result = pd.DataFrame(
            {
                "date": dates,
                "country": definition.country,
                "provider": "U.S. Treasury Fiscal Data",
                "series_id": definition.series_id,
                "component": definition.component,
                "value": values,
                "unit": definition.unit,
                "frequency": definition.frequency,
                "retrieved_at": retrieved_at,
            }
        )[STANDARD_COLUMNS]
        validate_standardized_frame(result)
        return result.sort_values("date").reset_index(drop=True)


def _coerce_date(value: str | date, name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an ISO date") from exc


def _cache_is_fresh(path: Path, ttl: timedelta) -> bool:
    if not path.is_file():
        return False
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return datetime.now(tz=UTC) - modified <= ttl
