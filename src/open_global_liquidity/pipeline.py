"""Executable US measured-data and liquidity-model pipeline."""

from __future__ import annotations

import argparse
import logging
from importlib.metadata import version
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from open_global_liquidity.analysis.context import MacroContextError, build_us_macro_context
from open_global_liquidity.analysis.correlations import (
    add_rolling_correlations,
    calculate_lagged_correlations,
)
from open_global_liquidity.analysis.diagnostics import (
    DIAGNOSTIC_GROUP_COLUMNS,
    calculate_regime_return_statistics,
    select_non_overlapping_returns,
)
from open_global_liquidity.analysis.lead_lag import (
    MarketAnalysisError,
    build_liquidity_market_comparison,
    calculate_market_forward_returns,
)
from open_global_liquidity.analysis.subperiods import calculate_subperiod_correlations
from open_global_liquidity.config import (
    ConfigurationError,
    load_model_config,
    load_series_config,
)
from open_global_liquidity.data.base import DataValidationError
from open_global_liquidity.data.bis import BisError, BisProvider
from open_global_liquidity.data.boe import BoeError, BoeProvider
from open_global_liquidity.data.boj import BojError, BojProvider
from open_global_liquidity.data.coinmetrics import CoinMetricsError, CoinMetricsProvider
from open_global_liquidity.data.ecb import EcbError, EcbProvider
from open_global_liquidity.data.fred import FredError, FredProvider
from open_global_liquidity.data.pboc import PbocError, PbocProvider
from open_global_liquidity.models.global_central_bank import (
    GlobalAggregationError,
    calculate_global_central_bank_assets,
    load_global_aggregation_config,
)
from open_global_liquidity.models.ogli import OGLICalculationError, calculate_ogli
from open_global_liquidity.models.us_liquidity import (
    LiquidityModelError,
    calculate_us_liquidity_models,
)
from open_global_liquidity.provenance import ProvenanceError, write_snapshot_manifest
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
    market_definitions = [item for item in definitions if item.group == "markets"]
    context_definitions = [item for item in definitions if item.group == "context"]
    fx_definitions = [
        item
        for item in definitions
        if item.provider.lower() == "fred" and item.group == "exchange_rates"
    ]
    ecb_definitions = [
        item for item in definitions if item.provider.lower() == "ecb" and item.group == "liquidity"
    ]
    boj_definitions = [
        item for item in definitions if item.provider.lower() == "boj" and item.group == "liquidity"
    ]
    boe_definitions = [
        item for item in definitions if item.provider.lower() == "boe" and item.group == "liquidity"
    ]
    pboc_definitions = [
        item
        for item in definitions
        if item.provider.lower() == "pboc" and item.group == "liquidity"
    ]
    bis_definitions = [
        item for item in definitions if item.provider.lower() == "bis" and item.group == "liquidity"
    ]
    if not liquidity_definitions:
        raise RuntimeError("No FRED liquidity series are configured")
    if not market_definitions:
        raise RuntimeError("No market series are configured")

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

    ecb_output: pd.DataFrame | None = None
    if ecb_definitions:
        ecb_provider = EcbProvider(cache_dir=project_root / "data" / "raw" / "ecb")
        ecb_output = pd.concat(
            [
                ecb_provider.fetch_definition(
                    definition,
                    start=start,
                    end=end,
                    force_refresh=force_refresh,
                )
                for definition in ecb_definitions
            ],
            ignore_index=True,
        ).sort_values(["country", "series_id", "date"])
        ecb_path = output_dir / "euro_area_ecb_series.parquet"
        ecb_output.to_parquet(ecb_path, index=False)
        LOGGER.info("Wrote %d standardized ECB observations to %s", len(ecb_output), ecb_path)

    boj_output: pd.DataFrame | None = None
    if boj_definitions:
        boj_provider = BojProvider(cache_dir=project_root / "data" / "raw" / "boj")
        boj_output = pd.concat(
            [
                boj_provider.fetch_definition(
                    definition,
                    start=start,
                    end=end,
                    force_refresh=force_refresh,
                )
                for definition in boj_definitions
            ],
            ignore_index=True,
        ).sort_values(["country", "series_id", "date"])
        boj_path = output_dir / "japan_boj_series.parquet"
        boj_output.to_parquet(boj_path, index=False)
        LOGGER.info("Wrote %d standardized BOJ observations to %s", len(boj_output), boj_path)

    boe_output: pd.DataFrame | None = None
    if boe_definitions:
        boe_provider = BoeProvider(cache_dir=project_root / "data" / "raw" / "boe")
        boe_output = pd.concat(
            [
                boe_provider.fetch_definition(
                    definition,
                    start=start,
                    end=end,
                    force_refresh=force_refresh,
                )
                for definition in boe_definitions
            ],
            ignore_index=True,
        ).sort_values(["country", "series_id", "date"])
        boe_path = output_dir / "uk_boe_series.parquet"
        boe_output.to_parquet(boe_path, index=False)
        LOGGER.info("Wrote %d standardized BoE observations to %s", len(boe_output), boe_path)

    pboc_output: pd.DataFrame | None = None
    if pboc_definitions:
        pboc_provider = PbocProvider(cache_dir=project_root / "data" / "raw" / "pboc")
        pboc_output = pd.concat(
            [
                pboc_provider.fetch_definition(
                    definition,
                    start=start,
                    end=end,
                    force_refresh=force_refresh,
                )
                for definition in pboc_definitions
            ],
            ignore_index=True,
        ).sort_values(["country", "series_id", "date"])
        pboc_path = output_dir / "china_pboc_series.parquet"
        pboc_output.to_parquet(pboc_path, index=False)
        LOGGER.info("Wrote %d standardized PBoC observations to %s", len(pboc_output), pboc_path)

    bis_output: pd.DataFrame | None = None
    if bis_definitions:
        bis_provider = BisProvider(cache_dir=project_root / "data" / "raw" / "bis")
        bis_output = pd.concat(
            [
                bis_provider.fetch_definition(
                    definition,
                    start=start,
                    end=end,
                    force_refresh=force_refresh,
                )
                for definition in bis_definitions
            ],
            ignore_index=True,
        ).sort_values(["country", "series_id", "date"])
        bis_path = output_dir / "china_bis_series.parquet"
        bis_output.to_parquet(bis_path, index=False)
        LOGGER.info("Wrote %d standardized BIS observations to %s", len(bis_output), bis_path)

    fx_output: pd.DataFrame | None = None
    if fx_definitions:
        fx_output = pd.concat(
            [
                provider.fetch_definition(
                    definition,
                    start=start,
                    end=end,
                    force_refresh=force_refresh,
                )
                for definition in fx_definitions
            ],
            ignore_index=True,
        ).sort_values(["series_id", "date"])
        fx_path = output_dir / "global_fx_series.parquet"
        fx_output.to_parquet(fx_path, index=False)
        LOGGER.info("Wrote %d standardized FX observations to %s", len(fx_output), fx_path)

    global_detail: pd.DataFrame | None = None
    global_aggregate: pd.DataFrame | None = None
    global_config_path = project_root / "config" / "global_aggregation.yaml"
    global_sources = [output.loc[output["component"] == "fed_assets"]]
    global_sources.extend(
        frame for frame in (ecb_output, boj_output, boe_output, bis_output) if frame is not None
    )
    if global_config_path.is_file() and fx_output is not None:
        global_config = load_global_aggregation_config(global_config_path)
        global_detail, global_aggregate = calculate_global_central_bank_assets(
            pd.concat(global_sources, ignore_index=True),
            fx_output,
            global_config,
        )
        global_detail_path = output_dir / "global_central_bank_assets_detail.parquet"
        global_aggregate_path = output_dir / "global_central_bank_assets.parquet"
        global_detail.to_parquet(global_detail_path, index=False)
        global_aggregate.to_parquet(global_aggregate_path, index=False)
        LOGGER.info(
            "Wrote %d balanced global aggregate quarters to %s",
            len(global_aggregate),
            global_aggregate_path,
        )

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

    coinmetrics_provider = CoinMetricsProvider(
        cache_dir=project_root / "data" / "raw" / "coinmetrics"
    )
    market_providers = {"fred": provider, "coinmetrics": coinmetrics_provider}
    market_frames = []
    for definition in market_definitions:
        market_provider = market_providers.get(definition.provider.lower())
        if market_provider is None:
            raise RuntimeError(f"Unsupported market provider: {definition.provider}")
        market_frames.append(
            market_provider.fetch_definition(
                definition,
                start=start,
                end=end,
                force_refresh=force_refresh,
            )
        )
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

    observation_date_comparisons = build_liquidity_market_comparison(
        ogli,
        market_returns,
        liquidity_signal=model_config.market_analysis.liquidity_signal,
        analysis_mode="observation_date",
    )
    available_information_comparisons = build_liquidity_market_comparison(
        ogli,
        market_returns,
        liquidity_signal=model_config.market_analysis.liquidity_signal,
        signal_availability_lag_weeks=(model_config.market_analysis.signal_availability_lag_weeks),
        analysis_mode="available_information",
    )
    comparisons = pd.concat(
        [observation_date_comparisons, available_information_comparisons], ignore_index=True
    )
    comparisons = add_rolling_correlations(
        comparisons,
        window_weeks=model_config.market_analysis.rolling_window_weeks,
        min_periods=model_config.market_analysis.rolling_min_periods,
    )
    selected_non_overlapping = select_non_overlapping_returns(comparisons)
    sample_keys = [*DIAGNOSTIC_GROUP_COLUMNS, "date"]
    selected_keys = selected_non_overlapping[sample_keys].assign(is_non_overlapping=True)
    comparisons = comparisons.merge(
        selected_keys,
        on=sample_keys,
        how="left",
        validate="one_to_one",
    )
    comparisons["is_non_overlapping"] = comparisons["is_non_overlapping"].fillna(False)
    comparisons_path = output_dir / "us_liquidity_market_comparisons.parquet"
    comparisons.to_parquet(comparisons_path, index=False)
    LOGGER.info("Wrote %d liquidity-market comparisons to %s", len(comparisons), comparisons_path)

    overlapping_correlations = calculate_lagged_correlations(
        comparisons,
        min_periods=model_config.market_analysis.correlation_min_periods,
        sample_policy="overlapping",
        confidence_level=model_config.market_analysis.confidence_level,
        bootstrap_resamples=model_config.market_analysis.bootstrap.resamples,
        bootstrap_block_length=model_config.market_analysis.bootstrap.block_length_observations,
        bootstrap_seed=model_config.market_analysis.bootstrap.seed,
    )
    non_overlapping_comparisons = comparisons.loc[comparisons["is_non_overlapping"]].copy()
    non_overlapping_correlations = calculate_lagged_correlations(
        non_overlapping_comparisons,
        min_periods=model_config.market_analysis.non_overlapping_min_periods,
        sample_policy="non_overlapping",
        confidence_level=model_config.market_analysis.confidence_level,
        bootstrap_resamples=model_config.market_analysis.bootstrap.resamples,
        bootstrap_block_length=model_config.market_analysis.bootstrap.block_length_observations,
        bootstrap_seed=model_config.market_analysis.bootstrap.seed,
    )
    correlations = pd.concat(
        [overlapping_correlations, non_overlapping_correlations], ignore_index=True
    ).sort_values(["model_id", "market_id", "analysis_mode", "sample_policy", "horizon_weeks"])
    regime_statistics = pd.concat(
        [
            calculate_regime_return_statistics(
                comparisons,
                sample_policy="overlapping",
                confidence_level=model_config.market_analysis.confidence_level,
            ),
            calculate_regime_return_statistics(
                non_overlapping_comparisons,
                sample_policy="non_overlapping",
                confidence_level=model_config.market_analysis.confidence_level,
            ),
        ],
        ignore_index=True,
    )
    subperiod_correlations = calculate_subperiod_correlations(
        comparisons,
        model_config.market_analysis.research_subperiods,
        overlapping_min_periods=model_config.market_analysis.correlation_min_periods,
        non_overlapping_min_periods=model_config.market_analysis.non_overlapping_min_periods,
        confidence_level=model_config.market_analysis.confidence_level,
        bootstrap_resamples=model_config.market_analysis.bootstrap.resamples,
        bootstrap_block_length=model_config.market_analysis.bootstrap.block_length_observations,
        bootstrap_seed=model_config.market_analysis.bootstrap.seed,
    )
    correlations_path = output_dir / "us_liquidity_market_correlations.parquet"
    correlations.to_parquet(correlations_path, index=False)
    LOGGER.info("Wrote %d lagged-correlation estimates to %s", len(correlations), correlations_path)
    regime_statistics_path = output_dir / "us_liquidity_market_regimes.parquet"
    regime_statistics.to_parquet(regime_statistics_path, index=False)
    LOGGER.info(
        "Wrote %d regime-return estimates to %s",
        len(regime_statistics),
        regime_statistics_path,
    )
    subperiod_path = output_dir / "us_liquidity_market_subperiods.parquet"
    subperiod_correlations.to_parquet(subperiod_path, index=False)
    LOGGER.info(
        "Wrote %d predeclared subperiod estimates to %s",
        len(subperiod_correlations),
        subperiod_path,
    )

    context_outputs: dict[str, pd.DataFrame] = {}
    if context_definitions:
        context_frames = [
            provider.fetch_definition(
                definition,
                start=start,
                end=end,
                force_refresh=force_refresh,
            )
            for definition in context_definitions
        ]
        context_source = pd.concat(context_frames, ignore_index=True).sort_values(
            ["country", "series_id", "date"]
        )
        context_weekly = align_market_closes_to_weekly_wednesday(
            context_source,
            daily_asof_components=model_config.market_alignment.daily_asof_components,
            daily_asof_max_staleness_days=(
                model_config.market_alignment.daily_asof_max_staleness_days
            ),
        )
        context_indicators = build_us_macro_context(context_weekly)
        context_outputs = {
            "us_macro_context_series.parquet": context_source,
            "us_macro_context_weekly.parquet": context_weekly,
            "us_macro_context_indicators.parquet": context_indicators,
        }
        for filename, context_frame in context_outputs.items():
            context_path = output_dir / filename
            context_frame.to_parquet(context_path, index=False)
            LOGGER.info(
                "Wrote %d macro-context observations to %s", len(context_frame), context_path
            )

    if publish_dashboard_snapshot:
        snapshot_dir = project_root / "data" / "reference"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshots = {
            "us_fred_series_snapshot.parquet": output,
            "us_liquidity_weekly_snapshot.parquet": weekly,
            "us_liquidity_models_snapshot.parquet": models,
            "us_ogli_snapshot.parquet": ogli,
            "us_market_series_snapshot.parquet": market_source,
            "us_market_weekly_snapshot.parquet": market_weekly,
            "us_market_returns_snapshot.parquet": market_returns,
            "us_liquidity_market_comparisons_snapshot.parquet": comparisons,
            "us_liquidity_market_correlations_snapshot.parquet": correlations,
            "us_liquidity_market_regimes_snapshot.parquet": regime_statistics,
            "us_liquidity_market_subperiods_snapshot.parquet": subperiod_correlations,
        }
        if ecb_output is not None:
            snapshots["euro_area_ecb_series_snapshot.parquet"] = ecb_output
        if boj_output is not None:
            snapshots["japan_boj_series_snapshot.parquet"] = boj_output
        if boe_output is not None:
            snapshots["uk_boe_series_snapshot.parquet"] = boe_output
        if bis_output is not None:
            snapshots["china_bis_series_snapshot.parquet"] = bis_output
        if fx_output is not None:
            snapshots["global_fx_series_snapshot.parquet"] = fx_output
        if global_detail is not None and global_aggregate is not None:
            snapshots["global_central_bank_assets_detail_snapshot.parquet"] = global_detail
            snapshots["global_central_bank_assets_snapshot.parquet"] = global_aggregate
        if pboc_output is not None:
            LOGGER.warning(
                "PBoC observations are excluded from public snapshots pending explicit "
                "redistribution permission"
            )
        snapshots.update(
            {
                filename.replace(".parquet", "_snapshot.parquet"): frame
                for filename, frame in context_outputs.items()
            }
        )
        for filename, snapshot_frame in snapshots.items():
            snapshot_path = snapshot_dir / filename
            snapshot_frame.to_parquet(snapshot_path, index=False)
            LOGGER.info(
                "Published %d-row dashboard snapshot to %s",
                len(snapshot_frame),
                snapshot_path,
            )
        manifest_path = write_snapshot_manifest(
            snapshot_dir,
            snapshots,
            project_root=project_root,
            pipeline_version=version("open-global-liquidity"),
        )
        LOGGER.info("Published snapshot provenance manifest to %s", manifest_path)
        LOGGER.info(
            "Published Bitcoin market research under Coin Metrics Community Data CC BY-NC 4.0"
        )

    print(
        f"Pipeline complete: {len(output):,} source observations, "
        f"{len(weekly):,} weekly aligned observations, {len(models):,} model observations, "
        f"{ogli['ogli'].notna().sum():,} available OGLI readings, and "
        f"{len(correlations):,} market-correlation estimates "
        f"and {0 if ecb_output is None else len(ecb_output):,} ECB observations "
        f"and {0 if boj_output is None else len(boj_output):,} BOJ observations "
        f"and {0 if boe_output is None else len(boe_output):,} BoE observations "
        f"and {0 if pboc_output is None else len(pboc_output):,} PBoC observations "
        f"and {0 if bis_output is None else len(bis_output):,} BIS observations "
        f"and {0 if global_aggregate is None else len(global_aggregate):,} global quarters "
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
        BisError,
        ConfigurationError,
        BojError,
        BoeError,
        CoinMetricsError,
        EcbError,
        DataValidationError,
        FredError,
        FrequencyAlignmentError,
        GrowthCalculationError,
        GlobalAggregationError,
        LiquidityModelError,
        MarketAnalysisError,
        MacroContextError,
        OGLICalculationError,
        PbocError,
        ProvenanceError,
        UnitConversionError,
        OSError,
    ) as exc:
        raise SystemExit(f"Pipeline failed: {exc}") from exc


if __name__ == "__main__":
    main()
