"""Transparent lead-lag preparation for liquidity and market research."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


class MarketAnalysisError(ValueError):
    """Raised when market or liquidity data cannot support the requested analysis."""


def calculate_market_forward_returns(
    weekly_markets: pd.DataFrame,
    *,
    horizons_weeks: Iterable[int] = (0, 4, 8, 12, 26, 52),
) -> pd.DataFrame:
    """Calculate contemporaneous and forward simple returns from weekly market closes.

    Horizon zero is deliberately defined as the one-week return ending at date ``t``. A positive
    horizon ``h`` is the simple return from the close aligned at ``t`` to the close at ``t+h``.
    Forward returns are outcome variables for retrospective analysis and must never be used as
    contemporaneous OGLI inputs.
    """
    required = {"date", "component", "series_id", "value", "unit"}
    missing = sorted(required - set(weekly_markets.columns))
    if missing:
        raise MarketAnalysisError(f"Weekly market data is missing columns: {', '.join(missing)}")
    if weekly_markets.empty:
        raise MarketAnalysisError("Weekly market data contains no observations")
    if weekly_markets.duplicated(["date", "component"]).any():
        raise MarketAnalysisError("Weekly market data contains duplicate date/components")

    horizons = tuple(int(item) for item in horizons_weeks)
    if not horizons or horizons[0] != 0 or tuple(sorted(set(horizons))) != horizons:
        raise MarketAnalysisError("Return horizons must be unique, increasing, and start at zero")

    frames: list[pd.DataFrame] = []
    for market_id, market in weekly_markets.groupby("component", sort=True):
        market = market.sort_values("date").copy()
        if (market["value"].dropna() <= 0).any():
            raise MarketAnalysisError(f"Market {market_id} contains non-positive index levels")
        for horizon in horizons:
            result = market[["date", "series_id", "value", "unit"]].copy()
            result["market_id"] = market_id
            result["horizon_weeks"] = horizon
            if horizon == 0:
                result["market_return"] = market["value"].pct_change(fill_method=None)
                result["return_start_date"] = market["date"].shift(1)
                result["return_end_date"] = market["date"]
                result["return_type"] = "contemporaneous_1w"
            else:
                result["market_return"] = market["value"].shift(-horizon) / market["value"] - 1
                result["return_start_date"] = market["date"]
                result["return_end_date"] = market["date"].shift(-horizon)
                result["return_type"] = "forward"
            frames.append(result)

    columns = [
        "date",
        "market_id",
        "series_id",
        "value",
        "unit",
        "horizon_weeks",
        "return_type",
        "market_return",
        "return_start_date",
        "return_end_date",
    ]
    return (
        pd.concat(frames, ignore_index=True)[columns]
        .sort_values(["market_id", "horizon_weeks", "date"])
        .reset_index(drop=True)
    )


def build_liquidity_market_comparison(
    ogli: pd.DataFrame,
    market_returns: pd.DataFrame,
    *,
    liquidity_signal: str = "momentum_score",
) -> pd.DataFrame:
    """Join a named liquidity signal at ``t`` to market outcomes anchored at ``t``."""
    ogli_required = {
        "date",
        "model_id",
        "model_name",
        "ogli",
        "momentum_score",
        "growth_3m_annualized",
        "growth_12m_yoy",
    }
    market_required = {
        "date",
        "market_id",
        "series_id",
        "horizon_weeks",
        "return_type",
        "market_return",
        "return_start_date",
        "return_end_date",
    }
    missing_ogli = sorted(ogli_required - set(ogli.columns))
    missing_market = sorted(market_required - set(market_returns.columns))
    if missing_ogli:
        raise MarketAnalysisError(f"OGLI comparison data is missing: {', '.join(missing_ogli)}")
    if missing_market:
        raise MarketAnalysisError(
            f"Market return comparison data is missing: {', '.join(missing_market)}"
        )
    if liquidity_signal not in ogli.columns:
        raise MarketAnalysisError(f"Configured liquidity signal does not exist: {liquidity_signal}")

    liquidity = ogli[
        [
            "date",
            "model_id",
            "model_name",
            "ogli",
            "momentum_score",
            "growth_3m_annualized",
            "growth_12m_yoy",
        ]
    ].copy()
    liquidity["liquidity_signal_name"] = liquidity_signal
    liquidity["liquidity_signal"] = ogli[liquidity_signal]
    result = liquidity.merge(market_returns, on="date", how="inner", validate="many_to_many")
    result["classification"] = "statistical_transformation"
    return result.sort_values(["model_id", "market_id", "horizon_weeks", "date"]).reset_index(
        drop=True
    )
