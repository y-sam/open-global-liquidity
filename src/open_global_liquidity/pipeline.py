"""Executable US measured-data and liquidity-model pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from open_global_liquidity.config import (
    ConfigurationError,
    load_model_config,
    load_series_config,
)
from open_global_liquidity.data.base import DataValidationError
from open_global_liquidity.data.fred import FredError, FredProvider
from open_global_liquidity.models.us_liquidity import (
    LiquidityModelError,
    calculate_us_liquidity_models,
)
from open_global_liquidity.transforms.frequency import (
    FrequencyAlignmentError,
    align_to_weekly_wednesday,
)
from open_global_liquidity.transforms.units import UnitConversionError, convert_to_usd_millions

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
    """Fetch measured data and write source, weekly-aligned, and model Parquet outputs."""
    load_dotenv(project_root / ".env")
    definitions = load_series_config(project_root / "config" / "series.yaml")
    model_config = load_model_config(project_root / "config" / "model.yaml")
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

    weekly = align_to_weekly_wednesday(
        convert_to_usd_millions(output),
        daily_asof_components=model_config.alignment.daily_asof_components,
        daily_asof_max_staleness_days=(model_config.alignment.daily_asof_max_staleness_days),
    )
    weekly_path = output_dir / "us_liquidity_weekly.parquet"
    weekly.to_parquet(weekly_path, index=False)
    LOGGER.info("Wrote %d weekly aligned observations to %s", len(weekly), weekly_path)

    models = calculate_us_liquidity_models(weekly, model_config.models)
    models_path = output_dir / "us_liquidity_models.parquet"
    models.to_parquet(models_path, index=False)
    LOGGER.info("Wrote %d model observations to %s", len(models), models_path)

    if publish_dashboard_snapshot:
        snapshot_dir = project_root / "data" / "reference"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshots = {
            "us_fred_series_snapshot.parquet": output,
            "us_liquidity_weekly_snapshot.parquet": weekly,
            "us_liquidity_models_snapshot.parquet": models,
        }
        for filename, snapshot_frame in snapshots.items():
            snapshot_path = snapshot_dir / filename
            snapshot_frame.to_parquet(snapshot_path, index=False)
            LOGGER.info(
                "Published %d-row dashboard snapshot to %s",
                len(snapshot_frame),
                snapshot_path,
            )

    print(
        f"Pipeline complete: {len(output):,} source observations, "
        f"{len(weekly):,} weekly aligned observations, and {len(models):,} model observations "
        f"-> {output_dir}"
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
        help="Also write the Git-versioned public snapshots used by hosted dashboards",
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
    except (
        ConfigurationError,
        DataValidationError,
        FredError,
        FrequencyAlignmentError,
        LiquidityModelError,
        UnitConversionError,
        OSError,
    ) as exc:
        raise SystemExit(f"Pipeline failed: {exc}") from exc


if __name__ == "__main__":
    main()
