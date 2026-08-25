import pandas as pd
import pytest

from open_global_liquidity.analysis.bitcoin import (
    build_bitcoin_research_outcomes,
    label_bitcoin_specification_role,
    summarize_bitcoin_regimes,
    summarize_bitcoin_revision_comparison,
)
from open_global_liquidity.analysis.point_in_time_markets import PAIR_COLUMNS


def _pairs() -> pd.DataFrame:
    dates = pd.to_datetime(["2024-01-31", "2024-02-29", "2024-03-31", "2024-04-30"])
    starts = pd.to_datetime(["2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01"])
    regimes = ["Neutral", "Above normal", "Above normal", "Contraction"]
    rows = []
    for index, (information_date, start_date, regime) in enumerate(
        zip(dates, starts, regimes, strict=True)
    ):
        end_date = start_date + pd.DateOffset(months=1)
        start_value = 100.0 + index * 10
        market_return = 0.05 + index * 0.03
        row = {column: None for column in PAIR_COLUMNS}
        row.update(
            {
                "information_date": information_date,
                "signal_observation_date": information_date - pd.Timedelta(days=3),
                "signal_available_date": start_date,
                "model_id": "model_b",
                "model_name": "Model B",
                "vintage_ogli": 50.0 + index * 5,
                "vintage_momentum_score": -0.2 + index * 0.2,
                "vintage_regime": regime,
                "market_id": "bitcoin",
                "series_id": "btc.PriceUSD",
                "provider": "Coin Metrics",
                "unit": "U.S. Dollars per Bitcoin",
                "source_frequency": "Daily",
                "publication_lag_weeks": 0,
                "horizon_months": 1,
                "start_target_date": start_date,
                "start_observation_date": start_date,
                "start_value": start_value,
                "end_target_date": end_date,
                "end_observation_date": end_date,
                "end_value": start_value * (1 + market_return),
                "market_return": market_return,
                "is_non_overlapping": True,
                "classification": "statistical_transformation",
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _levels() -> pd.DataFrame:
    dates = pd.date_range("2024-02-01", "2024-06-01", freq="D")
    values = pd.Series([100.0 + index for index in range(len(dates))], dtype=float)
    values.iloc[10] = 80.0
    values.iloc[20] = 130.0
    return pd.DataFrame({"date": dates, "component": "bitcoin", "value": values})


def _comparison() -> pd.DataFrame:
    pairs = _pairs()
    return pd.DataFrame(
        {
            "information_date": pairs["information_date"],
            "model_id": "model_b",
            "current_ogli": pairs["vintage_ogli"] + 1,
            "current_momentum_score": pairs["vintage_momentum_score"] + 0.05,
            "current_regime": pairs["vintage_regime"],
            "ogli_revision": 1.0,
            "momentum_revision": 0.05,
        }
    )


def test_build_bitcoin_outcomes_adds_path_risk_and_transitions() -> None:
    outcomes = build_bitcoin_research_outcomes(_pairs(), _levels(), _comparison())

    first = outcomes.iloc[0]
    assert first["maximum_downside_from_start"] == pytest.approx(-0.2)
    assert first["maximum_upside_from_start"] == pytest.approx(0.3)
    assert first["maximum_drawdown_from_peak"] < 0
    assert outcomes["transition_direction"].tolist() == [
        "Initial observation",
        "Expansionary transition",
        "No regime change",
        "Contractionary transition",
    ]
    assert outcomes["regime_agrees_with_current"].all()


def test_bitcoin_summaries_keep_regimes_transitions_and_revision_labels() -> None:
    outcomes = build_bitcoin_research_outcomes(_pairs(), _levels(), _comparison())

    regimes = summarize_bitcoin_regimes(outcomes)
    revisions = summarize_bitcoin_revision_comparison(
        outcomes,
        overlapping_min_periods=3,
        non_overlapping_min_periods=3,
    )

    assert set(regimes["analysis_dimension"]) == {
        "overall",
        "vintage_regime",
        "transition_direction",
    }
    overall = regimes.loc[regimes["analysis_dimension"] == "overall"]
    assert set(overall["group_label"]) == {"All outcomes"}
    assert overall["observations"].eq(4).all()
    assert "Expansionary transition" in set(regimes["group_label"])
    assert set(regimes["confidence_level"]) == {0.95}
    assert regimes.loc[regimes["observations"] >= 2, "mean_return_ci_lower"].notna().all()
    assert revisions["regime_agreement_share"].eq(1.0).all()
    assert revisions["observations"].eq(4).all()


def test_primary_bitcoin_specification_is_a_label_not_a_calculation() -> None:
    outcomes = build_bitcoin_research_outcomes(_pairs(), _levels(), _comparison())
    summary = summarize_bitcoin_regimes(outcomes)

    labeled = label_bitcoin_specification_role(
        summary,
        model_id="model_b",
        publication_lag_weeks=0,
        sample_policy="non_overlapping",
        forward_horizons_months=(1,),
    )

    primary = labeled.loc[labeled["specification_role"] == "primary"]
    assert not primary.empty
    assert set(primary["sample_policy"]) == {"non_overlapping"}
    assert set(labeled["specification_classification"]) == {"model_assumption"}
    pd.testing.assert_series_equal(labeled["mean_return"], summary["mean_return"])
