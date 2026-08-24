"""Explicit ALFRED as-of capture for future real-time liquidity research."""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from open_global_liquidity.analysis.revisions import (
    RevisionAnalysisError,
    compare_vintage_to_current,
)
from open_global_liquidity.config import ConfigurationError, load_series_config
from open_global_liquidity.data.fred import FredError, FredProvider

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_vintage_capture(
    *,
    as_of: str | date,
    project_root: Path = PROJECT_ROOT,
    start: str | date | None = None,
    end: str | date | None = None,
    force_refresh: bool = False,
    compare_current: bool = False,
) -> Path:
    """Capture all configured US FRED liquidity inputs as known on one historical date.

    Each as-of date receives its own directory. Rerunning an existing date is deterministic and
    uses the immutable local per-series vintage cache unless ``force_refresh`` is requested.
    This capture does not yet calculate a vintage OGLI; keeping acquisition separate prevents
    current-vintage and as-of frames from being mixed accidentally.
    """
    as_of_date = _coerce_as_of(as_of)
    load_dotenv(project_root / ".env")
    definitions = [
        definition
        for definition in load_series_config(project_root / "config" / "series.yaml")
        if definition.country == "US"
        and definition.group == "liquidity"
        and definition.provider.lower() == "fred"
    ]
    if not definitions:
        raise RuntimeError("No US FRED liquidity series are configured for vintage capture")
    provider = FredProvider(cache_dir=project_root / "data" / "raw" / "fred")
    frames = [
        provider.fetch_vintage_definition(
            definition,
            vintage_date=as_of_date,
            start=start,
            end=end,
            force_refresh=force_refresh,
        )
        for definition in definitions
    ]
    output = pd.concat(frames, ignore_index=True).sort_values(
        ["country", "series_id", "observation_date"]
    )
    output_dir = project_root / "data" / "vintages" / "fred" / f"as_of={as_of_date}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "us_liquidity_vintage.parquet"
    output.to_parquet(output_path, index=False)
    LOGGER.info(
        "Wrote %d ALFRED observations across %d series to %s",
        len(output),
        output["series_id"].nunique(),
        output_path,
    )
    if compare_current:
        current = pd.concat(
            [
                provider.fetch_definition(
                    definition,
                    start=start,
                    end=end,
                    force_refresh=force_refresh,
                )
                for definition in definitions
            ],
            ignore_index=True,
        )
        revisions = compare_vintage_to_current(output, current)
        revision_path = output_dir / "revision_comparison_to_current.parquet"
        revisions.to_parquet(revision_path, index=False)
        LOGGER.info("Wrote %d vintage revision comparisons to %s", len(revisions), revision_path)
    print(
        f"Vintage capture complete: {len(output):,} observations across "
        f"{output['series_id'].nunique()} series as known on {as_of_date} -> {output_path}"
    )
    return output_path


def _coerce_as_of(value: str | date) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"as_of must be an ISO date (YYYY-MM-DD), got {value!r}") from exc


def build_parser() -> argparse.ArgumentParser:
    """Build the vintage-capture command-line interface."""
    parser = argparse.ArgumentParser(description="Capture US liquidity inputs from ALFRED as-of")
    parser.add_argument("--as-of", required=True, help="Historical information date (YYYY-MM-DD)")
    parser.add_argument("--start", help="Override configured observation start (YYYY-MM-DD)")
    parser.add_argument("--end", help="Optional observation end (YYYY-MM-DD)")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Redownload this as-of date instead of using its immutable local cache",
    )
    parser.add_argument(
        "--compare-current",
        action="store_true",
        help="Also compare as-of observations with the current FRED vintage",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    args = build_parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        run_vintage_capture(
            as_of=args.as_of,
            start=args.start,
            end=args.end,
            force_refresh=args.force_refresh,
            compare_current=args.compare_current,
        )
    except (ConfigurationError, FredError, OSError, RevisionAnalysisError, ValueError) as exc:
        raise SystemExit(f"Vintage capture failed: {exc}") from exc


if __name__ == "__main__":
    main()
