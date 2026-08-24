import numpy as np
import pandas as pd
import pytest

from open_global_liquidity.analysis.bootstrap import moving_block_bootstrap_correlation
from open_global_liquidity.analysis.lead_lag import MarketAnalysisError


def test_moving_block_bootstrap_is_deterministic_and_contains_observed_relationship() -> None:
    rng = np.random.default_rng(7)
    signal = pd.Series(rng.normal(size=120)).rolling(4, min_periods=1).mean()
    outcome = signal * 0.4 + rng.normal(scale=0.7, size=120)

    first = moving_block_bootstrap_correlation(
        signal,
        outcome,
        resamples=500,
        block_length=6,
        seed=91,
    )
    second = moving_block_bootstrap_correlation(
        signal,
        outcome,
        resamples=500,
        block_length=6,
        seed=91,
    )

    assert first == second
    observed = signal.corr(pd.Series(outcome))
    assert first[0] < observed < first[1]
    assert first[2] == 500


def test_moving_block_bootstrap_rejects_too_few_resamples() -> None:
    with pytest.raises(MarketAnalysisError, match="at least 100"):
        moving_block_bootstrap_correlation([1.0, 2.0], [1.0, 2.0], resamples=50)
