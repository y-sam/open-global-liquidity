"""Cache-aware provider for BIS SDMX statistics."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree

import httpx
import pandas as pd

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS, validate_standardized_frame

LOGGER = logging.getLogger(__name__)
BIS_DATA_API_URL = "https://stats.bis.org/api/v2/data/dataflow"
BIS_RAW_COLUMNS = [
    "date",
    "value",
    "obs_status",
    "frequency_code",
    "unit_measure",
    "currency",
    "unit_multiplier",
    "title",
    "retrieved_at",
]
BIS_DOMESTIC_BILLION_UNITS = {
    "USD": "Billions of U.S. Dollars",
    "EUR": "Billions of Euro",
    "JPY": "Billions of Japanese Yen",
    "GBP": "Billions of Sterling",
    "CNY": "Billions of Chinese Yuan",
}


class BisError(RuntimeError):
    """Raised when BIS observations cannot be downloaded or validated safely."""


class BisProvider:
    """Fetch one exact BIS SDMX series and maintain a small Parquet cache.

    The provider supports exact monthly domestic-currency central-bank-total-assets keys. BIS
    reports these series with a 10^9 multiplier, so values are already billions of the configured
    native currency. Monthly periods are represented as calendar month ends; this is a period-label
    convention and not a modeled publication timestamp.
    """

    def __init__(
        self,
        *,
        cache_dir: Path = Path("data/raw/bis"),
        timeout_seconds: float = 30.0,
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
        """Fetch a configured BIS series in the project's standard long format."""
        if definition.provider.lower() != "bis":
            raise ValueError(f"Expected a BIS definition, received {definition.provider}")
        start_date = _coerce_date(start or definition.start, "start")
        end_date = _coerce_date(end, "end") if end is not None else None
        if end_date is not None and end_date < start_date:
            raise ValueError("end must be on or after start")

        raw = self._get_raw(definition.series_id, force_refresh=force_refresh)
        selected = raw.loc[raw["date"] >= pd.Timestamp(start_date)].copy()
        if end_date is not None:
            selected = selected.loc[selected["date"] <= pd.Timestamp(end_date)].copy()
        selected = selected.dropna(subset=["value"])
        if selected.empty:
            raise BisError(
                f"BIS returned no {definition.series_id} observations in the requested date range"
            )
        metadata = set(
            zip(
                selected["frequency_code"],
                selected["unit_measure"],
                selected["currency"],
                selected["unit_multiplier"],
                strict=True,
            )
        )
        _agency, _flow, _version, key = _parse_series_id(definition.series_id)
        key_parts = key.split(".")
        expected_currency = key_parts[4] if len(key_parts) == 6 else ""
        expected_unit = BIS_DOMESTIC_BILLION_UNITS.get(expected_currency)
        if expected_unit is None or definition.unit != expected_unit:
            raise BisError(
                f"Configured unit for {definition.series_id} must be the supported domestic "
                f"currency billions label; received {definition.unit}"
            )
        if metadata != {("M", "XDC", expected_currency, 9)}:
            raise BisError(
                f"BIS metadata for {definition.series_id} does not match monthly "
                f"{expected_currency} billions: "
                f"{sorted(metadata)}"
            )

        selected["country"] = definition.country
        selected["provider"] = "BIS"
        selected["series_id"] = definition.series_id
        selected["component"] = definition.component
        selected["unit"] = definition.unit
        selected["frequency"] = definition.frequency
        result = selected[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)
        validate_standardized_frame(result)
        return result

    def _get_raw(self, series_id: str, *, force_refresh: bool) -> pd.DataFrame:
        cache_path = self.cache_dir / _cache_name(series_id)
        if cache_path.is_file() and not force_refresh:
            age = datetime.now(tz=UTC) - datetime.fromtimestamp(cache_path.stat().st_mtime, tz=UTC)
            if age <= self.cache_ttl:
                frame = pd.read_parquet(cache_path)
                _validate_raw(frame, series_id)
                LOGGER.info("BIS cache hit for %s", series_id)
                return frame

        agency, flow, version, key = _parse_series_id(series_id)
        client = self._client or httpx.Client()
        try:
            response = client.get(
                f"{BIS_DATA_API_URL}/{agency}/{flow}/{version}/{key}",
                headers={
                    "Accept": "application/vnd.sdmx.structurespecificdata+xml;version=2.1",
                    "User-Agent": "open-global-liquidity/0.3",
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise BisError(f"BIS request for {series_id} timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise BisError(
                f"BIS request for {series_id} failed with HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise BisError(f"BIS request for {series_id} failed: {exc}") from exc
        finally:
            if self._client is None:
                client.close()

        raw = _parse_response(response.content, series_id=series_id, expected_key=key)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        raw.to_parquet(cache_path, index=False)
        LOGGER.info("Downloaded BIS %s: %d monthly observations", series_id, len(raw))
        return raw


def _parse_response(content: bytes, *, series_id: str, expected_key: str) -> pd.DataFrame:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise BisError(f"BIS returned invalid XML for {series_id}") from exc
    series = next((element for element in root.iter() if element.tag.endswith("Series")), None)
    if series is None:
        raise BisError(f"BIS returned no series for {series_id}")
    attributes = series.attrib
    actual_key = ".".join(
        attributes.get(name, "")
        for name in (
            "FREQ",
            "REF_AREA",
            "COMP_METHOD",
            "UNIT_MEASURE",
            "CURRENCY",
            "TRANSFORMATION",
        )
    )
    if actual_key != expected_key:
        raise BisError(f"BIS response did not contain the exact requested key {expected_key}")
    try:
        unit_multiplier = int(attributes["UNIT_MULT"])
    except (KeyError, ValueError) as exc:
        raise BisError(f"BIS response for {series_id} has an invalid unit multiplier") from exc

    rows: list[dict[str, object]] = []
    retrieved_at = pd.Timestamp.now(tz=UTC)
    for observation in (element for element in series if element.tag.endswith("Obs")):
        period = observation.attrib.get("TIME_PERIOD")
        try:
            observation_date = pd.Period(period, freq="M").to_timestamp("M")
        except (TypeError, ValueError) as exc:
            raise BisError(f"BIS returned an invalid monthly period for {series_id}") from exc
        rows.append(
            {
                "date": observation_date,
                "value": pd.to_numeric(observation.attrib.get("OBS_VALUE"), errors="coerce"),
                "obs_status": observation.attrib.get("OBS_STATUS"),
                "frequency_code": attributes.get("FREQ"),
                "unit_measure": attributes.get("UNIT_MEASURE"),
                "currency": attributes.get("CURRENCY"),
                "unit_multiplier": unit_multiplier,
                "title": attributes.get("TITLE"),
                "retrieved_at": retrieved_at,
            }
        )
    raw = pd.DataFrame(rows, columns=BIS_RAW_COLUMNS).sort_values("date", ignore_index=True)
    _validate_raw(raw, series_id)
    return raw


def _parse_series_id(series_id: str) -> tuple[str, str, str, str]:
    flow_part, separator, key = series_id.partition("/")
    parts = flow_part.split(",")
    if not separator or len(parts) != 3 or not key or any(not part for part in parts):
        raise ValueError("BIS series_id must use AGENCY,FLOW,VERSION/EXACT.KEY format")
    return parts[0], parts[1], parts[2], key


def _cache_name(series_id: str) -> str:
    return series_id.lower().replace(",", "_").replace("/", "_").replace(".", "_") + ".parquet"


def _validate_raw(frame: pd.DataFrame, series_id: str) -> None:
    missing = sorted(set(BIS_RAW_COLUMNS) - set(frame.columns))
    if missing:
        raise BisError(f"Cached BIS data for {series_id} is missing columns: {', '.join(missing)}")
    if frame.empty:
        raise BisError(f"Cached BIS data for {series_id} is empty")


def _coerce_date(value: str | date, name: str) -> date:
    try:
        return pd.Timestamp(value).date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a valid date") from exc
