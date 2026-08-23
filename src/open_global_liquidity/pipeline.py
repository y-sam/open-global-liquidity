"""Executable US measured-data and liquidity-model pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from open_global_liquidity.analysis.correlations import (
    add_rolling_correlations,
    calculate_lagged_correlations,
)
from open_global_liquidity.analysis.lead_lag import (
    MarketAnalysisError,
    build_liquidity_market_comparison,
    calculate_market_forward_returns,
)
from open_global_liquidity.config import (
    ConfigurationError,
    load_model_config,
    load_series_config,
)
from open_global_liquidity.data.base import DataValidationError
from open_global_liquidity.data.fred import FredError, FredProvider
from open_global_liquidity.models.ogli import OGLICalculationError, calculate_ogli
from open_global_liquidity.models.us_liquidity import (
    LiquidityModelError,
    calculate_us_liquidity_models,
)
from open_global_liquidity.transforms.frequency import (
    FrequencyAlignmentError,
    align_market_closes_to_weekly_wednesday,
    align_to_weekly_wednesday,
)
from open_global_liquidity.transforms.growth import (
    GrowthCalculationError,
    calculate_liquidity_momentum,
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
    liquidity_definitions = [
        item
        for item in definitions
        if item.provider.lower() == "fred" and item.group == "liquidity"
    ]
    market_definitions = [
        item for item in definitions if item.provider.lower() == "fred" and item.group == "markets"
    ]
    if not liquidity_definitions:
        raise RuntimeError("No FRED liquidity series are configured")
    if not market_definitions:
        raise RuntimeError("No FRED market series are configured")

    provider = FredProvider(cache_dir=project_root / "data" / "raw" / "fred")
    liquidity_frames = [
        provider.fetch_definition(
            definition,
            start=start,
            end=end,
            force_refresh=force_refresh,
        )
        for definition in liquidity_definitions
    ]
    output = pd.concat(liquidity_frames, ignore_index=True).sort_values(
        ["country", "series_id", "date"]
    )

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

    ogli = calculate_ogli(calculate_liquidity_momentum(models), model_config.ogli)
    ogli_path = output_dir / "us_ogli.parquet"
    ogli.to_parquet(ogli_path, index=False)
    LOGGER.info(
        "Wrote %d OGLI observations (%d available) to %s",
        len(ogli),
        ogli["ogli"].notna().sum(),
        ogli_path,
    )

    market_frames = [
        provider.fetch_definition(
            definition,
            start=start,
            end=end,
            force_refresh=force_refresh,
        )
        for definition in market_definitions
    ]
    market_source = pd.concat(market_frames, ignore_index=True).sort_values(
        ["country", "series_id", "date"]
    )
    market_source_path = output_dir / "us_market_series.parquet"
    market_source.to_parquet(market_source_path, index=False)
    LOGGER.info(
        "Wrote %d standardized market observations to %s", len(market_source), market_source_path
    )

    market_weekly = align_market_closes_to_weekly_wednesday(
        market_source,
        daily_asof_components=model_config.market_alignment.daily_asof_components,
        daily_asof_max_staleness_days=(model_config.market_alignment.daily_asof_max_staleness_days),
    )
    market_weekly_path = output_dir / "us_market_weekly.parquet"
    market_weekly.to_parquet(market_weekly_path, index=False)
    LOGGER.info(
        "Wrote %d aligned market observations to %s", len(market_weekly), market_weekly_path
    )

    market_returns = calculate_market_forward_returns(
        market_weekly,
        horizons_weeks=model_config.market_analysis.forward_horizons_weeks,
    )
    market_returns_path = output_dir / "us_market_returns.parquet"
    market_returns.to_parquet(market_returns_path, index=False)
    LOGGER.info("Wrote %d market return outcomes to %s", len(market_returns), market_returns_path)

    comparisons = build_liquidity_market_comparison(
        ogli,
        market_returns,
        liquidity_signal=model_config.market_analysis.liquidity_signal,
    )
    comparisons = add_rolling_correlations(
        comparisons,
        window_weeks=model_config.market_analysis.rolling_window_weeks,
        min_periods=model_config.market_analysis.rolling_min_periods,
    )
    comparisons_path = output_dir / "us_liquidity_market_comparisons.parquet"
    comparisons.to_parquet(comparisons_path, index=False)
    LOGGER.info("Wrote %d liquidity-market comparisons to %s", len(comparisons), comparisons_path)

    correlations = calculate_lagged_correlations(
        comparisons,
        min_periods=model_config.market_analysis.correlation_min_periods,
    )
    correlations_path = output_dir / "us_liquidity_market_correlations.parquet"
    correlations.to_parquet(correlations_path, index=False)
    LOGGER.info("Wrote %d lagged-correlation estimates to %s", len(correlations), correlations_path)

    if publish_dashboard_snapshot:
        snapshot_dir = project_root / "data" / "reference"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshots = {
            "us_fred_series_snapshot.parquet": output,
            "us_liquidity_weekly_snapshot.parquet": weekly,
            "us_liquidity_models_snapshot.parquet": models,
            "us_ogli_snapshot.parquet": ogli,
            "us_liquidity_market_correlations_snapshot.parquet": correlations,
        }
        for filename, snapshot_frame in snapshots.items():
            snapshot_path = snapshot_dir / filename
            snapshot_frame.to_parquet(snapshot_path, index=False)
            LOGGER.info(
                "Published %d-row dashboard snapshot to %s",
                len(snapshot_frame),
                snapshot_path,
            )
        LOGGER.warning(
            "Raw market observations, returns, and paired comparisons were not published: "
            "SP500 source metadata restricts redistribution"
        )

    print(
        f"Pipeline complete: {len(output):,} source observations, "
        f"{len(weekly):,} weekly aligned observations, {len(models):,} model observations, "
        f"{ogli['ogli'].notna().sum():,} available OGLI readings, and "
        f"{len(correlations):,} market-correlation estimates "
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
        GrowthCalculationError,
        LiquidityModelError,
        MarketAnalysisError,
        OGLICalculationError,
        UnitConversionError,
        OSError,
    ) as exc:
        raise SystemExit(f"Pipeline failed: {exc}") from exc


if __name__ == "__main__":
    main()
