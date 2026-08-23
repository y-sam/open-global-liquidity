import numpy as np
import pandas as pd

from open_global_liquidity.transforms.normalize import historical_zscore


def test_full_sample_population_zscore() -> None:
    result = historical_zscore(pd.Series([1.0, 2.0, 3.0]), mode="full_sample", min_periods=2)

    np.testing.assert_allclose(result, [-1.2247448714, 0.0, 1.2247448714])


def test_expanding_zscore_uses_only_history_through_current_row() -> None:
    result = historical_zscore(pd.Series([1.0, 2.0, 3.0]), mode="expanding", min_periods=2)

    assert np.isnan(result.iloc[0])
    assert result.iloc[1] == 1.0
    assert np.isclose(result.iloc[2], 1.2247448714)


def test_minimum_history_and_zero_variance_return_missing() -> None:
    too_short = historical_zscore(pd.Series([1.0, 2.0, 3.0]), mode="full_sample", min_periods=4)
    constant = historical_zscore(pd.Series([2.0, 2.0, 2.0]), mode="expanding", min_periods=2)

    assert too_short.isna().all()
    assert constant.isna().all()
