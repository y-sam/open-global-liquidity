"""Executable monthly point-in-time OGLI pilot."""

from __future__ import annotations

import argparse
import logging
from datetime import date
from importlib.metadata import version
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from open_global_liquidity.config import ConfigurationError, load_model_config, load_series_config
from open_global_liquidity.data.fred import FredError, FredProvider
from open_global_liquidity.point_in_time import (
    PointInTimeError,
    build_month_end_grid,
    calculate_point_in_time_ogli,
    compare_point_in_time_to_current,
)
from open_global_liquidity.provenance import ProvenanceError, write_snapshot_manifest

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_point_in_time_pipeline(
    *,
    project_root: Path = PROJECT_ROOT,
    start: str | date | None = None,
    end: str | date | None = None,
    force_refresh: bool = False,
    publish_dashboard_snapshot: bool = False,
) -> Path:
    """Fetch monthly ALFRED information sets and write local vintage OGLI research files."""
    load_dotenv(project_root / ".env")
    config = load_model_config(project_root / "config" / "model.yaml")
    definitions = [
        definition
        for definition in load_series_config(project_root / "config" / "series.yaml")
        if definition.country == "US"
        and definition.group == "liquidity"
        and definition.provider.lower() == "fred"
    ]
    if not definitions:
        raise RuntimeError("No US FRED liquidity series are configured")

    requested_end = end or date.today()
    information_dates = build_month_end_grid(
        start or config.point_in_time_pilot.start,
        requested_end,
    )
    if not information_dates:
        raise PointInTimeError("Requested range contains no completed month-end information dates")

    provider = FredProvider(cache_dir=project_root / "data" / "raw" / "fred")
    vintage_inputs = pd.concat(
        [
            provider.fetch_vintage_batch_definition(
                definition,
                vintage_dates=information_dates,
                start=definition.start,
                end=information_dates[-1],
                force_refresh=force_refresh,
            )
            for definition in definitions
        ],
        ignore_index=True,
    ).sort_values(["vintage_date", "series_id", "observation_date"])

    output_dir = project_root / "data" / "vintages" / "fred" / "monthly_pilot"
    output_dir.mkdir(parents=True, exist_ok=True)
    inputs_path = output_dir / "us_liquidity_vintage_inputs.parquet"
    vintage_inputs.to_parquet(inputs_path, index=False)
    LOGGER.info("Wrote %d vintage input observations to %s", len(vintage_inputs), inputs_path)

    point_in_time = calculate_point_in_time_ogli(vintage_inputs, config)
    output_path = output_dir / "us_point_in_time_ogli.parquet"
    point_in_time.to_parquet(output_path, index=False)
    LOGGER.info("Wrote %d point-in-time OGLI results to %s", len(point_in_time), output_path)

    current_path = project_root / "data" / "processed" / "us_ogli.parquet"
    if not current_path.is_file():
        raise PointInTimeError(
            "Current OGLI file is missing. Run `uv run ogli-pipeline` before the "
            "point-in-time pilot."
        )
    comparison = compare_point_in_time_to_current(
        point_in_time,
        pd.read_parquet(current_path),
    )
    comparison_path = output_dir / "us_point_in_time_comparison.parquet"
    comparison.to_parquet(comparison_path, index=False)
    LOGGER.info("Wrote %d current-vintage comparisons to %s", len(comparison), comparison_path)
    if publish_dashboard_snapshot:
        _publish_dashboard_snapshot(comparison, project_root=project_root)

    print(
        f"Point-in-time pilot complete: {len(information_dates)} month ends, "
        f"{point_in_time['model_id'].nunique()} models -> {output_path}"
    )
    return output_path


def _publish_dashboard_snapshot(comparison: pd.DataFrame, *, project_root: Path) -> Path:
    """Publish the small derived comparison and refresh whole-bundle provenance."""
    snapshot_dir = project_root / "data" / "reference"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / "us_point_in_time_comparison_snapshot.parquet"
    comparison.to_parquet(snapshot_path, index=False)
    snapshots = {
        path.name: pd.read_parquet(path) for path in sorted(snapshot_dir.glob("*_snapshot.parquet"))
    }
    write_snapshot_manifest(
        snapshot_dir,
        snapshots,
        project_root=project_root,
        pipeline_version=version("open-global-liquidity"),
    )
    LOGGER.info("Published %d-row point-in-time snapshot to %s", len(comparison), snapshot_path)
    return snapshot_path


def build_parser() -> argparse.ArgumentParser:
    """Build the monthly point-in-time pilot command-line interface."""
    parser = argparse.ArgumentParser(description="Run the monthly ALFRED point-in-time OGLI pilot")
    parser.add_argument("--start", help="First information month (YYYY-MM-DD)")
    parser.add_argument("--end", help="Last completed information month (YYYY-MM-DD)")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Redownload the requested ALFRED batch instead of using its local cache",
    )
    parser.add_argument(
        "--publish-dashboard-snapshot",
        action="store_true",
        help="Also publish the derived comparison used by the hosted dashboard",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    args = build_parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        run_point_in_time_pipeline(
            start=args.start,
            end=args.end,
            force_refresh=args.force_refresh,
            publish_dashboard_snapshot=args.publish_dashboard_snapshot,
        )
    except (
        ConfigurationError,
        FredError,
        OSError,
        PointInTimeError,
        ProvenanceError,
        ValueError,
    ) as exc:
        raise SystemExit(f"Point-in-time pilot failed: {exc}") from exc


if __name__ == "__main__":
    main()
