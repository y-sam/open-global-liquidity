import pandas as pd

from open_global_liquidity.analysis.signal_map import build_liquidity_signal_map


def test_builds_non_aggregated_signal_map() -> None:
    date = pd.Timestamp("2025-03-31")
    available = pd.Timestamp("2025-07-31")
    global_model = pd.DataFrame(
        {
            "date": [date],
            "global_cb_index": [60.0],
            "global_cb_momentum_score": [0.2],
            "global_cb_regime": ["Expansion"],
        }
    )
    offshore = pd.DataFrame(
        {
            "date": [date],
            "offshore_dollar_credit_index": [40.0],
            "momentum_score": [-0.2],
            "signal_available_date": [available],
            "regime": ["Contraction"],
        }
    )
    private = pd.DataFrame(
        {
            "date": [date],
            "private_liquidity_index": [55.0],
            "private_liquidity_momentum": [0.1],
            "signal_available_date": [available],
            "private_liquidity_regime": ["Expansion"],
        }
    )
    collateral = pd.DataFrame(
        {
            "date": [date],
            "collateral_conditions_index": [45.0],
            "collateral_conditions_score": [-0.1],
            "signal_available_date": [available],
            "collateral_regime": ["Below normal"],
        }
    )
    result = build_liquidity_signal_map(global_model, offshore, private, collateral)
    assert len(result) == 4
    assert result["aggregation_status"].eq("not_aggregated").all()
    assert set(result["direction"]) == {"Supportive / expanding", "Restrictive / contracting"}
