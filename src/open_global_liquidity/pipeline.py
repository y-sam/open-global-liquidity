"""Executable Phase 1 data-ingestion pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from open_global_liquidity.config import ConfigurationError, load_series_config
from open_global_liquidity.data.base import DataValidationError
from open_global_liquidity.data.fred import FredError, FredProvider

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_pipeline(
    *,
    project_root: Path = PROJECT_ROOT,
    start: str | None = None,
    end: str | None = None,
    force_refresh: bool = False,
    publish_dashboard_snapshot: bool = False,
) -> Path:
    """Fetch configured Phase 1 data and write one deterministic processed Parquet file."""
    load_dotenv(project_root / ".env")
    definitions = load_series_config(project_root / "config" / "series.yaml")
    fred_definitions = [item for item in definitions if item.provider.lower() == "fred"]
    if not fred_definitions:
        raise RuntimeError("No FRED series are configured")

    provider = FredProvider(cache_dir=project_root / "data" / "raw" / "fred")
    frames = [
        provider.fetch_definition(
            definition,
            start=start,
            end=end,
            force_refresh=force_refresh,
        )
        for definition in fred_definitions
    ]
    output = pd.concat(frames, ignore_index=True).sort_values(["country", "series_id", "date"])

    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "us_fred_series.parquet"
    output.to_parquet(output_path, index=False)
    LOGGER.info("Wrote %d standardized observations to %s", len(output), output_path)

    if publish_dashboard_snapshot:
        snapshot_dir = project_root / "data" / "reference"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / "us_fred_series_snapshot.parquet"
        output.to_parquet(snapshot_path, index=False)
        LOGGER.info("Published dashboard snapshot to %s", snapshot_path)

    print(
        f"Ingestion complete: {len(output):,} observations across "
        f"{output['series_id'].nunique()} series -> {output_path}"
    )
    return output_path


def build_parser() -> argparse.ArgumentParser:
    """Build the intentionally small command-line interface."""
    parser = argparse.ArgumentParser(description="Run the OGLI public-data ingestion pipeline")
    parser.add_argument("--start", help="Override configured start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="Optional end date (YYYY-MM-DD)")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore the local raw-data cache and download again",
    )
    parser.add_argument(
        "--publish-dashboard-snapshot",
        action="store_true",
        help="Also write the versioned public snapshot used by hosted dashboards",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    args = build_parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        run_pipeline(
            start=args.start,
            end=args.end,
            force_refresh=args.force_refresh,
            publish_dashboard_snapshot=args.publish_dashboard_snapshot,
        )
    except (ConfigurationError, DataValidationError, FredError, OSError) as exc:
        raise SystemExit(f"Pipeline failed: {exc}") from exc


if __name__ == "__main__":
    main()
