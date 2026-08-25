"""World Bank Pink Sheet provider for monthly commodity-price observations."""

from __future__ import annotations

import io
import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS, validate_standardized_frame

LOGGER = logging.getLogger(__name__)
MONTHLY_WORKBOOK_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "18675f1d1639c7a34d463f59263ba0a2-0050012025/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)
RAW_COLUMNS = ["date", "value", "retrieved_at"]


class WorldBankError(RuntimeError):
    """Raised when World Bank commodity-data ingestion fails."""


class WorldBankProvider:
    """Fetch the World Bank monthly Pink Sheet with a small Parquet cache.

    The workbook reports nominal monthly averages. This provider currently supports only the
    configured gold series and deliberately preserves that frequency instead of manufacturing
    daily spot observations.
    """

    def __init__(
        self,
        *,
        cache_dir: Path = Path("data/raw/world_bank"),
        timeout_seconds: float = 45.0,
        cache_ttl: timedelta = timedelta(days=7),
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
        """Return configured gold observations in the project's standard long schema."""
        if definition.series_id != "CMO-GOLD-MONTHLY":
            raise WorldBankError(f"Unsupported World Bank series: {definition.series_id}")
        start_date = pd.Timestamp(start or definition.start).normalize()
        end_date = pd.Timestamp(end).normalize() if end is not None else None
        if end_date is not None and end_date < start_date:
            raise ValueError("end must be on or after start")

        raw = self._get_raw(force_refresh=force_refresh)
        selected = raw.loc[raw["date"] >= start_date].copy()
        if end_date is not None:
            selected = selected.loc[selected["date"] <= end_date].copy()
        selected = selected.dropna(subset=["value"])
        if selected.empty:
            raise WorldBankError("World Bank returned no gold observations in the requested range")

        selected["country"] = definition.country
        selected["provider"] = "World Bank"
        selected["series_id"] = definition.series_id
        selected["component"] = definition.component
        selected["unit"] = definition.unit
        selected["frequency"] = definition.frequency
        result = selected[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)
        validate_standardized_frame(result)
        return result

    def _get_raw(self, *, force_refresh: bool) -> pd.DataFrame:
        cache_path = self.cache_dir / "cmo_gold_monthly.parquet"
        if not force_refresh and _cache_is_fresh(cache_path, self.cache_ttl):
            cached = pd.read_parquet(cache_path)
            _validate_raw(cached)
            LOGGER.info("Cache hit for World Bank monthly gold: %s", cache_path)
            return cached

        raw = self._download()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        raw.to_parquet(cache_path, index=False)
        LOGGER.info("Wrote %d World Bank gold observations to %s", len(raw), cache_path)
        return raw

    def _download(self) -> pd.DataFrame:
        try:
            if self._client is None:
                with httpx.Client(
                    timeout=self.timeout_seconds,
                    follow_redirects=True,
                    headers={"User-Agent": "open-global-liquidity/0.1"},
                ) as client:
                    response = client.get(MONTHLY_WORKBOOK_URL)
            else:
                response = self._client.get(
                    MONTHLY_WORKBOOK_URL,
                    timeout=self.timeout_seconds,
                    follow_redirects=True,
                )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise WorldBankError(
                f"World Bank request timed out after {self.timeout_seconds:g} seconds"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise WorldBankError(
                f"World Bank request failed with HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise WorldBankError(f"World Bank request failed: {exc}") from exc

        try:
            workbook = pd.read_excel(
                io.BytesIO(response.content),
                sheet_name="Monthly Prices",
                header=4,
                usecols=[0, 69],
            )
        except (ImportError, OSError, ValueError) as exc:
            raise WorldBankError(f"Could not parse the World Bank monthly workbook: {exc}") from exc
        if workbook.shape[1] != 2 or "Gold" not in workbook.columns:
            raise WorldBankError("World Bank workbook does not contain the expected Gold column")

        date_column = workbook.columns[0]
        result = workbook.rename(columns={date_column: "period", "Gold": "value"})
        period = result["period"].astype("string").str.extract(r"^(\d{4})M(\d{2})$")
        result["date"] = pd.to_datetime(
            period[0] + "-" + period[1] + "-01", errors="coerce"
        ) + pd.offsets.MonthEnd(0)
        result["value"] = pd.to_numeric(result["value"], errors="coerce")
        result["retrieved_at"] = datetime.now(UTC)
        result = result[RAW_COLUMNS].dropna(subset=["date", "value"]).reset_index(drop=True)
        _validate_raw(result)
        LOGGER.info(
            "Downloaded World Bank monthly gold: %d observations from %s to %s",
            len(result),
            result["date"].min().date(),
            result["date"].max().date(),
        )
        return result


def _cache_is_fresh(path: Path, ttl: timedelta) -> bool:
    if not path.is_file():
        return False
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return datetime.now(UTC) - modified <= ttl


def _validate_raw(frame: pd.DataFrame) -> None:
    missing = sorted(set(RAW_COLUMNS) - set(frame.columns))
    if missing:
        raise WorldBankError("Cached World Bank gold data is missing: " + ", ".join(missing))
    if frame.empty or frame["date"].isna().any() or frame["value"].notna().sum() == 0:
        raise WorldBankError("World Bank gold data is empty or invalid")
