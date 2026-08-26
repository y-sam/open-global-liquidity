"""Bitcoin-focused research from sealed OGLI vintages and public daily prices."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

from open_global_liquidity.analysis.point_in_time_markets import PAIR_COLUMNS


class BitcoinResearchError(ValueError):
    """Raised when Bitcoin research inputs are incomplete or inconsistent."""


REGIME_ORDER = {
    "Strong contraction": 0,
    "Contraction": 1,
    "Below normal": 2,
    "Neutral": 3,
    "Above normal": 4,
    "Expansion": 5,
    "Strong expansion": 6,
}

OUTCOME_COLUMNS = [
    *PAIR_COLUMNS,
    "current_ogli",
    "current_momentum_score",
    "current_regime",
    "ogli_revision",
    "momentum_revision",
    "regime_agrees_with_current",
    "previous_vintage_regime",
    "regime_transition",
    "transition_direction",
    "maximum_upside_from_start",
    "maximum_downside_from_start",
    "maximum_drawdown_from_peak",
    "bitcoin_research_classification",
]

REGIME_SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "publication_lag_weeks",
    "horizon_months",
    "sample_policy",
    "analysis_dimension",
    "group_label",
    "observations",
    "mean_return",
    "median_return",
    "positive_share",
    "standard_error",
    "confidence_level",
    "mean_return_ci_lower",
    "mean_return_ci_upper",
    "mean_maximum_upside",
    "mean_maximum_downside",
    "mean_maximum_drawdown",
    "specification_role",
    "specification_classification",
    "classification",
]

REVISION_SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "publication_lag_weeks",
    "horizon_months",
    "sample_policy",
    "observations",
    "vintage_signal_correlation",
    "current_vintage_signal_correlation",
    "correlation_difference",
    "mean_absolute_momentum_revision",
    "regime_agreement_share",
    "specification_role",
    "specification_classification",
    "classification",
]

CONTRAST_SUMMARY_COLUMNS = [
    "model_id",
    "model_name",
    "publication_lag_weeks",
    "horizon_months",
    "sample_policy",
    "expansionary_observations",
    "contractionary_observations",
    "expansionary_mean_return",
    "contractionary_mean_return",
    "expansionary_median_return",
    "contractionary_median_return",
    "expansionary_positive_share",
    "contractionary_positive_share",
    "mean_return_spread",
    "spread_standard_error",
    "confidence_level",
    "spread_ci_lower",
    "spread_ci_upper",
    "interval_status",
    "interval_status_classification",
    "interval_method",
    "regime_group_classification",
    "specification_role",
    "specification_classification",
    "classification",
]


def build_bitcoin_research_outcomes(
    market_pairs: pd.DataFrame,
    market_levels: pd.DataFrame,
    point_in_time_comparison: pd.DataFrame,
) -> pd.DataFrame:
    """Enrich Bitcoin forward returns with path risk, transitions, and revision context.

    Market returns and path statistics are retrospective outcomes and never enter OGLI. Current-
    vintage fields are counterfactual diagnostics calculated with revised data; only ``vintage_*``
    fields represent the sealed information set available on the stated information date.
    """
    missing_pairs = sorted(set(PAIR_COLUMNS) - set(market_pairs.columns))
    if missing_pairs:
        raise BitcoinResearchError("Market pairs are missing: " + ", ".join(missing_pairs))
    level_required = {"date", "component", "value"}
    missing_levels = sorted(level_required - set(market_levels.columns))
    if missing_levels:
        raise BitcoinResearchError("Market levels are missing: " + ", ".join(missing_levels))
    comparison_required = {
        "information_date",
        "model_id",
        "current_ogli",
        "current_momentum_score",
        "current_regime",
        "ogli_revision",
        "momentum_revision",
    }
    missing_comparison = sorted(comparison_required - set(point_in_time_comparison.columns))
    if missing_comparison:
        raise BitcoinResearchError(
            "Point-in-time comparison is missing: " + ", ".join(missing_comparison)
        )

    outcomes = market_pairs.loc[market_pairs["market_id"] == "bitcoin"].copy()
    bitcoin = market_levels.loc[market_levels["component"] == "bitcoin", ["date", "value"]].copy()
    if outcomes.empty or bitcoin.empty:
        raise BitcoinResearchError("Bitcoin pairs and daily Bitcoin levels cannot be empty")
    bitcoin["date"] = pd.to_datetime(bitcoin["date"]).dt.normalize()
    bitcoin["value"] = pd.to_numeric(bitcoin["value"], errors="coerce")
    bitcoin = bitcoin.dropna().sort_values("date")
    if bitcoin.duplicated("date").any() or bitcoin["value"].le(0).any():
        raise BitcoinResearchError("Daily Bitcoin levels contain duplicates or non-positive values")

    path_keys = outcomes[
        ["start_observation_date", "end_observation_date", "start_value"]
    ].drop_duplicates()
    path_rows: list[dict[str, object]] = []
    for row in path_keys.itertuples(index=False):
        start_date = pd.Timestamp(row.start_observation_date)
        end_date = pd.Timestamp(row.end_observation_date)
        path = bitcoin.loc[bitcoin["date"].between(start_date, end_date), "value"]
        if path.empty:
            continue
        returns_from_start = path / float(row.start_value) - 1.0
        drawdowns = path / path.cummax() - 1.0
        path_rows.append(
            {
                "start_observation_date": start_date,
                "end_observation_date": end_date,
                "start_value": float(row.start_value),
                "maximum_upside_from_start": returns_from_start.max(),
                "maximum_downside_from_start": returns_from_start.min(),
                "maximum_drawdown_from_peak": drawdowns.min(),
            }
        )
    path_statistics = pd.DataFrame(path_rows)
    outcomes = outcomes.merge(
        path_statistics,
        on=["start_observation_date", "end_observation_date", "start_value"],
        how="left",
        validate="many_to_one",
    )
    if outcomes["maximum_drawdown_from_peak"].isna().any():
        raise BitcoinResearchError("Bitcoin price history does not cover every forward-return path")

    comparison = point_in_time_comparison[list(comparison_required)].copy()
    comparison["information_date"] = pd.to_datetime(comparison["information_date"]).dt.normalize()
    outcomes["information_date"] = pd.to_datetime(outcomes["information_date"]).dt.normalize()
    outcomes = outcomes.merge(
        comparison,
        on=["information_date", "model_id"],
        how="left",
        validate="many_to_one",
    )
    if outcomes["current_momentum_score"].isna().any():
        raise BitcoinResearchError("Current-vintage comparison is incomplete for Bitcoin outcomes")
    outcomes["regime_agrees_with_current"] = outcomes["vintage_regime"].eq(
        outcomes["current_regime"]
    )

    signals = (
        outcomes[["information_date", "model_id", "vintage_regime"]]
        .drop_duplicates()
        .sort_values(["model_id", "information_date"])
    )
    signals["previous_vintage_regime"] = signals.groupby("model_id")["vintage_regime"].shift(1)
    signals["regime_transition"] = signals.apply(_transition_label, axis=1)
    signals["transition_direction"] = signals.apply(_transition_direction, axis=1)
    outcomes = outcomes.merge(
        signals[
            [
                "information_date",
                "model_id",
                "previous_vintage_regime",
                "regime_transition",
                "transition_direction",
            ]
        ],
        on=["information_date", "model_id"],
        how="left",
        validate="many_to_one",
    )
    outcomes["bitcoin_research_classification"] = "statistical_transformation"
    return (
        outcomes[OUTCOME_COLUMNS]
        .sort_values(["model_id", "publication_lag_weeks", "horizon_months", "information_date"])
        .reset_index(drop=True)
    )


def summarize_bitcoin_regimes(
    outcomes: pd.DataFrame,
    *,
    confidence_level: float = 0.95,
) -> pd.DataFrame:
    """Summarize returns and path risk overall, by vintage regime, and by transition.

    The mean-return interval is the classical Student-t interval. It is a descriptive uncertainty
    diagnostic, not a forecast interval; overlapping-window dependence can make it too narrow.
    """
    missing = sorted(set(OUTCOME_COLUMNS) - set(outcomes.columns))
    if missing:
        raise BitcoinResearchError("Bitcoin outcomes are missing: " + ", ".join(missing))
    if not 0 < confidence_level < 1:
        raise BitcoinResearchError("confidence_level must be between 0 and 1")
    rows: list[dict[str, object]] = []
    base_groups = ["model_id", "model_name", "publication_lag_weeks", "horizon_months"]
    for sample_policy in ("overlapping", "non_overlapping"):
        sample = (
            outcomes
            if sample_policy == "overlapping"
            else outcomes.loc[outcomes["is_non_overlapping"]]
        )
        overall = sample.assign(_summary_group="All outcomes")
        dimensions = {
            "overall": (overall, "_summary_group"),
            "vintage_regime": (sample, "vintage_regime"),
            "transition_direction": (
                sample.loc[sample["transition_direction"] != "Initial observation"],
                "transition_direction",
            ),
        }
        for dimension, (dimension_sample, group_column) in dimensions.items():
            for keys, group in dimension_sample.groupby([*base_groups, group_column], sort=True):
                values = group.dropna(subset=["market_return", "maximum_drawdown_from_peak"])
                observations = len(values)
                mean_return = values["market_return"].mean()
                standard_error = values["market_return"].sem() if observations >= 2 else math.nan
                if observations >= 2 and np.isfinite(standard_error):
                    critical = stats.t.ppf((1 + confidence_level) / 2, df=observations - 1)
                    margin = critical * standard_error
                    ci_lower, ci_upper = mean_return - margin, mean_return + margin
                else:
                    ci_lower, ci_upper = math.nan, math.nan
                rows.append(
                    {
                        **dict(zip(base_groups, keys[:-1], strict=True)),
                        "sample_policy": sample_policy,
                        "analysis_dimension": dimension,
                        "group_label": keys[-1],
                        "observations": observations,
                        "mean_return": mean_return,
                        "median_return": values["market_return"].median(),
                        "positive_share": values["market_return"].gt(0).mean(),
                        "standard_error": standard_error,
                        "confidence_level": confidence_level,
                        "mean_return_ci_lower": ci_lower,
                        "mean_return_ci_upper": ci_upper,
                        "mean_maximum_upside": values["maximum_upside_from_start"].mean(),
                        "mean_maximum_downside": values["maximum_downside_from_start"].mean(),
                        "mean_maximum_drawdown": values["maximum_drawdown_from_peak"].mean(),
                        "classification": "descriptive_statistic",
                    }
                )
    return (
        pd.DataFrame(rows, columns=REGIME_SUMMARY_COLUMNS)
        .sort_values(
            [
                "model_id",
                "sample_policy",
                "publication_lag_weeks",
                "horizon_months",
                "analysis_dimension",
                "group_label",
            ]
        )
        .reset_index(drop=True)
    )


def summarize_bitcoin_revision_comparison(
    outcomes: pd.DataFrame,
    *,
    overlapping_min_periods: int = 12,
    non_overlapping_min_periods: int = 8,
) -> pd.DataFrame:
    """Compare real-time-vintage and revised-signal correlations with the same outcomes."""
    missing = sorted(set(OUTCOME_COLUMNS) - set(outcomes.columns))
    if missing:
        raise BitcoinResearchError("Bitcoin outcomes are missing: " + ", ".join(missing))
    if overlapping_min_periods < 3 or non_overlapping_min_periods < 3:
        raise BitcoinResearchError("Revision comparison minimum periods must be at least 3")
    group_columns = ["model_id", "model_name", "publication_lag_weeks", "horizon_months"]
    rows: list[dict[str, object]] = []
    for sample_policy in ("overlapping", "non_overlapping"):
        sample = (
            outcomes
            if sample_policy == "overlapping"
            else outcomes.loc[outcomes["is_non_overlapping"]]
        )
        minimum = (
            overlapping_min_periods
            if sample_policy == "overlapping"
            else non_overlapping_min_periods
        )
        for keys, group in sample.groupby(group_columns, sort=True):
            valid = group.dropna(
                subset=["vintage_momentum_score", "current_momentum_score", "market_return"]
            )
            observations = len(valid)
            vintage_correlation = math.nan
            current_correlation = math.nan
            if observations >= minimum:
                vintage_correlation = valid["vintage_momentum_score"].corr(valid["market_return"])
                current_correlation = valid["current_momentum_score"].corr(valid["market_return"])
            rows.append(
                {
                    **dict(zip(group_columns, keys, strict=True)),
                    "sample_policy": sample_policy,
                    "observations": observations,
                    "vintage_signal_correlation": vintage_correlation,
                    "current_vintage_signal_correlation": current_correlation,
                    "correlation_difference": current_correlation - vintage_correlation,
                    "mean_absolute_momentum_revision": valid["momentum_revision"].abs().mean(),
                    "regime_agreement_share": valid["regime_agrees_with_current"].mean(),
                    "classification": "descriptive_statistic",
                }
            )
    return (
        pd.DataFrame(rows, columns=REVISION_SUMMARY_COLUMNS)
        .sort_values(["model_id", "sample_policy", "publication_lag_weeks", "horizon_months"])
        .reset_index(drop=True)
    )


def summarize_bitcoin_directional_contrasts(
    outcomes: pd.DataFrame,
    *,
    expansionary_regimes: tuple[str, ...],
    contractionary_regimes: tuple[str, ...],
    confidence_level: float = 0.95,
) -> pd.DataFrame:
    """Compare Bitcoin returns after expansionary versus contractionary vintage regimes.

    The reported spread is the expansionary-group arithmetic mean minus the contractionary-group
    arithmetic mean. Its classical Welch interval allows unequal sample variances. It is a
    descriptive interval, not a causal estimate or forecast; serial dependence and small samples
    can make it too narrow or unstable.
    """
    missing = sorted(set(OUTCOME_COLUMNS) - set(outcomes.columns))
    if missing:
        raise BitcoinResearchError("Bitcoin outcomes are missing: " + ", ".join(missing))
    if not 0 < confidence_level < 1:
        raise BitcoinResearchError("confidence_level must be between 0 and 1")
    expansionary = set(expansionary_regimes)
    contractionary = set(contractionary_regimes)
    if not expansionary or not contractionary or expansionary & contractionary:
        raise BitcoinResearchError(
            "Directional Bitcoin regime groups must be non-empty and disjoint"
        )

    group_columns = ["model_id", "model_name", "publication_lag_weeks", "horizon_months"]
    rows: list[dict[str, object]] = []
    for sample_policy in ("overlapping", "non_overlapping"):
        sample = (
            outcomes
            if sample_policy == "overlapping"
            else outcomes.loc[outcomes["is_non_overlapping"]]
        )
        for keys, group in sample.groupby(group_columns, sort=True):
            expansionary_returns = group.loc[
                group["vintage_regime"].isin(expansionary), "market_return"
            ].dropna()
            contractionary_returns = group.loc[
                group["vintage_regime"].isin(contractionary), "market_return"
            ].dropna()
            expansionary_mean = expansionary_returns.mean()
            contractionary_mean = contractionary_returns.mean()
            spread = expansionary_mean - contractionary_mean
            standard_error, ci_lower, ci_upper = _welch_mean_difference_interval(
                expansionary_returns,
                contractionary_returns,
                confidence_level=confidence_level,
            )
            interval_status = _classify_contrast_interval(ci_lower, ci_upper)
            rows.append(
                {
                    **dict(zip(group_columns, keys, strict=True)),
                    "sample_policy": sample_policy,
                    "expansionary_observations": len(expansionary_returns),
                    "contractionary_observations": len(contractionary_returns),
                    "expansionary_mean_return": expansionary_mean,
                    "contractionary_mean_return": contractionary_mean,
                    "expansionary_median_return": expansionary_returns.median(),
                    "contractionary_median_return": contractionary_returns.median(),
                    "expansionary_positive_share": expansionary_returns.gt(0).mean(),
                    "contractionary_positive_share": contractionary_returns.gt(0).mean(),
                    "mean_return_spread": spread,
                    "spread_standard_error": standard_error,
                    "confidence_level": confidence_level,
                    "spread_ci_lower": ci_lower,
                    "spread_ci_upper": ci_upper,
                    "interval_status": interval_status,
                    "interval_status_classification": "statistical_transformation",
                    "interval_method": "welch_mean_difference_t_interval",
                    "regime_group_classification": "model_assumption",
                    "specification_role": None,
                    "specification_classification": None,
                    "classification": "descriptive_statistic",
                }
            )
    return (
        pd.DataFrame(rows, columns=CONTRAST_SUMMARY_COLUMNS)
        .sort_values(["model_id", "sample_policy", "publication_lag_weeks", "horizon_months"])
        .reset_index(drop=True)
    )


def _welch_mean_difference_interval(
    first: pd.Series,
    second: pd.Series,
    *,
    confidence_level: float,
) -> tuple[float, float, float]:
    if len(first) < 2 or len(second) < 2:
        return math.nan, math.nan, math.nan
    first_component = first.var(ddof=1) / len(first)
    second_component = second.var(ddof=1) / len(second)
    standard_error = math.sqrt(first_component + second_component)
    if not np.isfinite(standard_error):
        return math.nan, math.nan, math.nan
    spread = first.mean() - second.mean()
    if standard_error == 0:
        return 0.0, spread, spread
    degrees_of_freedom = (first_component + second_component) ** 2 / (
        first_component**2 / (len(first) - 1) + second_component**2 / (len(second) - 1)
    )
    critical = stats.t.ppf((1 + confidence_level) / 2, df=degrees_of_freedom)
    margin = critical * standard_error
    return standard_error, spread - margin, spread + margin


def _classify_contrast_interval(lower: float, upper: float) -> str:
    if not np.isfinite(lower) or not np.isfinite(upper):
        return "insufficient_sample"
    if lower > 0:
        return "positive_interval"
    if upper < 0:
        return "negative_interval"
    return "inconclusive"


def label_bitcoin_specification_role(
    summary: pd.DataFrame,
    *,
    model_id: str,
    publication_lag_weeks: int,
    sample_policy: str,
    forward_horizons_months: tuple[int, ...],
) -> pd.DataFrame:
    """Label predeclared primary rows without changing their calculated statistics.

    The designation is a model assumption used for presentation and interpretation. It is not an
    empirical calibration, and every non-primary row remains available as a robustness check.
    """
    required = {"model_id", "publication_lag_weeks", "sample_policy", "horizon_months"}
    missing = sorted(required - set(summary.columns))
    if missing:
        raise BitcoinResearchError("Bitcoin summary is missing: " + ", ".join(missing))
    if sample_policy not in {"overlapping", "non_overlapping"}:
        raise BitcoinResearchError("Primary Bitcoin sample policy is unsupported")
    if not forward_horizons_months:
        raise BitcoinResearchError("Primary Bitcoin horizons cannot be empty")
    result = summary.copy()
    primary = (
        result["model_id"].eq(model_id)
        & result["publication_lag_weeks"].eq(publication_lag_weeks)
        & result["sample_policy"].eq(sample_policy)
        & result["horizon_months"].isin(forward_horizons_months)
    )
    result["specification_role"] = primary.map({True: "primary", False: "robustness_check"})
    result["specification_classification"] = "model_assumption"
    return result


def _transition_label(row: pd.Series) -> str:
    previous = row["previous_vintage_regime"]
    current = row["vintage_regime"]
    if pd.isna(previous):
        return "Initial observation"
    if previous == current:
        return f"No change: {current}"
    return f"{previous} → {current}"


def _transition_direction(row: pd.Series) -> str:
    previous = row["previous_vintage_regime"]
    current = row["vintage_regime"]
    if pd.isna(previous):
        return "Initial observation"
    if previous not in REGIME_ORDER or current not in REGIME_ORDER:
        raise BitcoinResearchError("Bitcoin outcomes contain an unknown OGLI regime")
    difference = REGIME_ORDER[current] - REGIME_ORDER[previous]
    if difference > 0:
        return "Expansionary transition"
    if difference < 0:
        return "Contractionary transition"
    return "No regime change"
