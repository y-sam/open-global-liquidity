"""Comparable long-format map of independently constructed liquidity signals."""

from __future__ import annotations

import pandas as pd


class SignalMapError(ValueError):
    """Raised when a required liquidity signal cannot be mapped."""


def build_liquidity_signal_map(
    global_model: pd.DataFrame,
    offshore_dollar: pd.DataFrame,
    private_liquidity: pd.DataFrame,
    collateral: pd.DataFrame,
) -> pd.DataFrame:
    """Standardize four separate liquidity channels without combining their information."""
    definitions = (
        (
            global_model,
            "global_model_g",
            "Global central-bank liquidity",
            "global_cb_index",
            "global_cb_momentum_score",
            None,
            "global_cb_regime",
            2,
        ),
        (
            offshore_dollar,
            "offshore_dollar_credit",
            "Offshore dollar credit",
            "offshore_dollar_credit_index",
            "momentum_score",
            "signal_available_date",
            "regime",
            0,
        ),
        (
            private_liquidity,
            "us_private_liquidity",
            "US private liquidity",
            "private_liquidity_index",
            "private_liquidity_momentum",
            "signal_available_date",
            "private_liquidity_regime",
            0,
        ),
        (
            collateral,
            "us_collateral_conditions",
            "US collateral conditions",
            "collateral_conditions_index",
            "collateral_conditions_score",
            "signal_available_date",
            "collateral_regime",
            0,
        ),
    )
    outputs: list[pd.DataFrame] = []
    for (
        frame,
        channel,
        label,
        index_col,
        score_col,
        available_col,
        regime_col,
        lag_months,
    ) in definitions:
        required = {"date", index_col, score_col, regime_col}
        if available_col:
            required.add(available_col)
        missing = required - set(frame.columns)
        if missing:
            raise SignalMapError(f"{channel} is missing: {', '.join(sorted(missing))}")
        selected = frame.dropna(subset=[index_col, score_col]).copy()
        selected["observation_date"] = pd.to_datetime(selected["date"])
        selected["available_date"] = (
            pd.to_datetime(selected[available_col])
            if available_col
            else selected["observation_date"] + pd.offsets.MonthEnd(lag_months)
        )
        selected["channel"] = channel
        selected["channel_label"] = label
        selected["index_value"] = selected[index_col]
        selected["momentum_score"] = selected[score_col]
        selected["regime"] = selected[regime_col]
        selected["direction"] = selected["momentum_score"].map(
            lambda value: "Supportive / expanding" if value >= 0 else "Restrictive / contracting"
        )
        outputs.append(
            selected[
                [
                    "observation_date",
                    "available_date",
                    "channel",
                    "channel_label",
                    "index_value",
                    "momentum_score",
                    "regime",
                    "direction",
                ]
            ]
        )
    result = pd.concat(outputs, ignore_index=True)
    result["classification"] = "model_output_comparison"
    result["aggregation_status"] = "not_aggregated"
    return result.sort_values(["available_date", "channel"]).reset_index(drop=True)
