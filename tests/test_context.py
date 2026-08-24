import numpy as np
import pandas as pd

from open_global_liquidity.analysis.context import build_us_macro_context


def test_macro_context_calculates_ten_year_minus_two_year_slope() -> None:
    frame = pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-03")] * 3,
            "component": ["treasury_yield_10y", "treasury_yield_2y", "broad_usd_index"],
            "value": [4.2, 4.5, 101.25],
        }
    )

    result = build_us_macro_context(frame).iloc[0]

    assert np.isclose(result["yield_curve_10y_2y"], -0.3)
    assert result["broad_usd_index"] == 101.25
    assert result["classification"] == "statistical_transformation"
