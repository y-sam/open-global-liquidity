"""Cache-aware provider for the PBoC monetary-authority balance sheet."""

from __future__ import annotations

import logging
import re
from datetime import UTC, date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import httpx
import pandas as pd

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.base import STANDARD_COLUMNS, validate_standardized_frame

LOGGER = logging.getLogger(__name__)
PBOC_BASE_URL = "https://www.pbc.gov.cn"
PBOC_STATISTICS_INDEX_URL = "https://www.pbc.gov.cn/diaochatongjisi/116219/116319/index.html"
PBOC_TOTAL_ASSETS_SERIES = "PBOC.BSMA.TOTAL_ASSETS"
PBOC_RAW_COLUMNS = ["date", "value", "source_url", "retrieved_at"]
_YEAR_LABEL = re.compile(r"^(20\d{2})年统计数据$")
_PERIOD_LABEL = re.compile(r"^(20\d{2})[.-](0?[1-9]|1[0-2])$")


class PbocError(RuntimeError):
    """Raised when PBoC data cannot be downloaded or validated safely."""


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((_clean_text(" ".join(self._text)), self._href))
            self._href = None
            self._text = []


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        tag = tag.lower()
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(_clean_text(" ".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None


class PbocProvider:
    """Fetch official monthly PBoC total assets without currency conversion.

    The PBoC publishes one annual ``Balance Sheet of Monetary Authority`` table rather than a
    stable time-series API. This provider discovers each annual money-and-banking page from the
    official archive, selects the HTML table carrying that exact bilingual title, and extracts
    only its ``Total Assets`` row. Month labels are represented as calendar month ends; they are
    period labels, not modeled release timestamps.
    """

    def __init__(
        self,
        *,
        cache_dir: Path = Path("data/raw/pboc"),
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
        """Fetch the configured monetary-authority total-assets row in standard long format."""
        if definition.provider.lower() != "pboc":
            raise ValueError(f"Expected a PBoC definition, received {definition.provider}")
        if definition.series_id != PBOC_TOTAL_ASSETS_SERIES:
            raise ValueError(
                f"PBoC pilot supports only the verified {PBOC_TOTAL_ASSETS_SERIES} table row"
            )
        if (
            definition.unit != "100 Million Yuan"
            or definition.frequency != "Monthly, End of Period"
        ):
            raise PbocError(
                f"PBoC configuration for {definition.series_id} must use 100 Million Yuan "
                "and Monthly, End of Period frequency"
            )
        start_date = _coerce_date(start or definition.start, "start")
        end_date = _coerce_date(end, "end") if end is not None else None
        if end_date is not None and end_date < start_date:
            raise ValueError("end must be on or after start")

        raw = self._get_raw(start_year=start_date.year, force_refresh=force_refresh)
        selected = raw.loc[raw["date"] >= pd.Timestamp(start_date)].copy()
        if end_date is not None:
            selected = selected.loc[selected["date"] <= pd.Timestamp(end_date)].copy()
        selected = selected.dropna(subset=["value"])
        if selected.empty:
            raise PbocError(
                f"PBoC returned no {definition.series_id} observations in the requested date range"
            )

        selected["country"] = definition.country
        selected["provider"] = "PBOC"
        selected["series_id"] = definition.series_id
        selected["component"] = definition.component
        selected["unit"] = definition.unit
        selected["frequency"] = definition.frequency
        result = selected[STANDARD_COLUMNS].sort_values("date").reset_index(drop=True)
        validate_standardized_frame(result)
        return result

    def _get_raw(self, *, start_year: int, force_refresh: bool) -> pd.DataFrame:
        cache_path = self.cache_dir / "monetary_authority_total_assets.parquet"
        if cache_path.is_file() and not force_refresh:
            age = datetime.now(tz=UTC) - datetime.fromtimestamp(cache_path.stat().st_mtime, tz=UTC)
            if age <= self.cache_ttl:
                frame = pd.read_parquet(cache_path)
                _validate_raw(frame)
                if pd.to_datetime(frame["date"]).min().year <= start_year:
                    LOGGER.info("PBoC cache hit for %s", PBOC_TOTAL_ASSETS_SERIES)
                    return frame

        client = self._client or httpx.Client(follow_redirects=True)
        try:
            index_html = self._get_text(client, PBOC_STATISTICS_INDEX_URL, "statistics archive")
            money_pages = _discover_money_pages(index_html, start_year=start_year)
            annual_frames = []
            for year, page_url in money_pages.items():
                page_html = self._get_text(client, page_url, f"{year} money statistics page")
                table_url = _discover_balance_sheet_url(page_html, page_url)
                table_html = self._get_text(client, table_url, f"{year} monetary-authority table")
                annual_frames.append(_parse_balance_sheet_table(table_html, table_url, year))
        finally:
            if self._client is None:
                client.close()

        if not annual_frames:
            raise PbocError("PBoC archive contained no monetary-authority balance-sheet tables")
        raw = (
            pd.concat(annual_frames, ignore_index=True)
            .sort_values(["date", "source_url"])
            .drop_duplicates("date", keep="last")
            .reset_index(drop=True)
        )
        _validate_raw(raw)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        raw.to_parquet(cache_path, index=False)
        LOGGER.info("Downloaded PBoC total assets: %d monthly observations", len(raw))
        return raw

    def _get_text(self, client: httpx.Client, url: str, label: str) -> str:
        try:
            response = client.get(
                url,
                headers={"Accept": "text/html", "User-Agent": "open-global-liquidity/0.2"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise PbocError(f"PBoC request for {label} timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise PbocError(
                f"PBoC request for {label} failed with HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise PbocError(f"PBoC request for {label} failed: {exc}") from exc
        text = _decode_html(response.content, label)
        if not text.strip():
            raise PbocError(f"PBoC returned an empty response for {label}")
        return text


def _discover_money_pages(index_html: str, *, start_year: int) -> dict[int, str]:
    parser = _AnchorParser()
    parser.feed(index_html)
    pages: dict[int, str] = {}
    current_year: int | None = None
    for text, href in parser.anchors:
        match = _YEAR_LABEL.fullmatch(text)
        if match:
            current_year = int(match.group(1))
            continue
        if current_year is not None and "货币统计概览" in text and current_year >= start_year:
            pages.setdefault(current_year, urljoin(PBOC_BASE_URL, href))
    if not pages:
        raise PbocError(f"PBoC statistics archive has no money-statistics pages from {start_year}")
    return dict(sorted(pages.items()))


def _discover_balance_sheet_url(page_html: str, page_url: str) -> str:
    parser = _TableParserWithLinks()
    parser.feed(page_html)
    for text, links in parser.rows:
        if "货币当局资产负债表" not in text or "Monetary Authority" not in text:
            continue
        html_links = [
            href for label, href in links if label.lower() == "htm" or href.endswith(".htm")
        ]
        if len(html_links) != 1:
            raise PbocError("PBoC monetary-authority row must contain exactly one HTML table link")
        return urljoin(page_url, html_links[0])
    raise PbocError("PBoC money-statistics page is missing the monetary-authority balance sheet")


class _TableParserWithLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[tuple[str, list[tuple[str, str]]]] = []
        self._row_text: list[str] | None = None
        self._links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._row_text = []
            self._links = []
        elif tag == "a" and self._row_text is not None:
            self._href = dict(attrs).get("href")
            self._link_text = []

    def handle_data(self, data: str) -> None:
        if self._row_text is not None:
            self._row_text.append(data)
        if self._href is not None:
            self._link_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self._href is not None:
            self._links.append((_clean_text(" ".join(self._link_text)), self._href))
            self._href = None
            self._link_text = []
        elif tag == "tr" and self._row_text is not None:
            self.rows.append((_clean_text(" ".join(self._row_text)), self._links.copy()))
            self._row_text = None


def _parse_balance_sheet_table(html: str, source_url: str, expected_year: int) -> pd.DataFrame:
    parser = _TableParser()
    parser.feed(html)
    table_text = " ".join(cell for row in parser.rows for cell in row)
    if "Unit: 100 Million Yuan" not in table_text:
        raise PbocError(f"PBoC table for {expected_year} does not declare 100 Million Yuan")
    header = next(
        (row for row in parser.rows if any(_PERIOD_LABEL.fullmatch(x) for x in row)), None
    )
    total_assets = next(
        (row for row in parser.rows if any("Total Assets" in cell for cell in row)), None
    )
    if header is None or total_assets is None:
        raise PbocError(f"PBoC table for {expected_year} is missing periods or Total Assets")
    if len(header) != len(total_assets):
        raise PbocError(f"PBoC table for {expected_year} has misaligned header and data columns")

    retrieved_at = pd.Timestamp.now(tz=UTC)
    records: list[dict[str, object]] = []
    for period, raw_value in zip(header, total_assets, strict=True):
        match = _PERIOD_LABEL.fullmatch(period)
        if not match or not raw_value:
            continue
        year, month = int(match.group(1)), int(match.group(2))
        if year != expected_year:
            raise PbocError(f"PBoC {expected_year} table contains unexpected period {period}")
        value = pd.to_numeric(raw_value.replace(",", ""), errors="coerce")
        if pd.isna(value):
            raise PbocError(
                f"PBoC {expected_year} table has invalid Total Assets value {raw_value!r}"
            )
        records.append(
            {
                "date": pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0),
                "value": float(value),
                "source_url": source_url,
                "retrieved_at": retrieved_at,
            }
        )
    if not records:
        raise PbocError(f"PBoC table for {expected_year} contains no published observations")
    return pd.DataFrame(records)


def _validate_raw(frame: pd.DataFrame) -> None:
    missing = sorted(set(PBOC_RAW_COLUMNS) - set(frame.columns))
    if missing:
        raise PbocError(f"Cached PBoC data is missing columns: {', '.join(missing)}")
    if frame.empty or frame["value"].notna().sum() == 0:
        raise PbocError("Cached PBoC data contains no numeric observations")
    if pd.to_datetime(frame["date"], errors="coerce").isna().any():
        raise PbocError("Cached PBoC data contains invalid dates")


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _decode_html(content: bytes, label: str) -> str:
    prefix = content[:2_048].lower()
    declared = re.search(rb"charset\s*=\s*['\"]?([a-z0-9_-]+)", prefix)
    candidates = [declared.group(1).decode("ascii")] if declared else []
    candidates.extend(["utf-8", "gb18030"])
    for encoding in dict.fromkeys(candidates):
        try:
            return content.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    raise PbocError(f"PBoC returned undecodable HTML for {label}")


def _coerce_date(value: str | date, name: str) -> date:
    try:
        return pd.Timestamp(value).date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a valid date") from exc
