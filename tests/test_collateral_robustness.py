from pathlib import Path

import numpy as np
import pandas as pd

from open_global_liquidity.analysis.collateral_robustness import (
    calculate_robustness_signals,
    load_robustness_config,
)


def test_predeclared_robustness_grid_does_not_change_baseline() -> None:
    dates = pd.date_range("2018-01-31", periods=72, freq="ME")
    conditions = pd.DataFrame({"date": dates})
    conditions["collateral_supply_growth_yoy"] = np.linspace(-0.1, 0.2, len(dates))
    conditions["funding_spread_bps"] = np.sin(np.arange(len(dates)))
    conditions["treasury_volatility_bps"] = 80 + np.cos(np.arange(len(dates))) * 10
    conditions["treasury_volatility_curve_bps"] = 75 + np.sin(np.arange(len(dates))) * 8
    for source, target in (
        ("collateral_supply_growth_yoy", "z_collateral_supply_growth_yoy"),
        ("funding_spread_bps", "z_funding_spread_bps"),
        ("treasury_volatility_bps", "z_treasury_volatility_bps"),
        ("treasury_volatility_curve_bps", "z_treasury_volatility_curve_bps"),
    ):
        conditions[target] = (
            conditions[source] - conditions[source].expanding(24).mean()
        ) / conditions[source].expanding(24).std(ddof=0)
    conditions["collateral_conditions_score"] = (
        0.4 * conditions["z_collateral_supply_growth_yoy"]
        - 0.3 * conditions["z_funding_spread_bps"]
        - 0.3 * conditions["z_treasury_volatility_bps"]
    )
    config = load_robustness_config(Path("config/collateral.yaml"))

    result = calculate_robustness_signals(conditions, config)
    baseline = result.loc[result["model_id"] == "baseline"].set_index("date")
    expected = conditions.set_index("date")["collateral_conditions_score"]

    pd.testing.assert_series_equal(
        baseline["robustness_score"], expected, check_names=False, check_exact=False, rtol=1e-5
    )
    assert set(result["model_id"]) == {item.model_id for item in config.variants}
    assert result["robustness_index"].dropna().between(0, 100).all()
