"""Deterministic resampling tools for descriptive market-validation uncertainty."""

from __future__ import annotations

import numpy as np
import pandas as pd

from open_global_liquidity.analysis.lead_lag import MarketAnalysisError


def moving_block_bootstrap_correlation(
    signal: pd.Series | np.ndarray,
    outcome: pd.Series | np.ndarray,
    *,
    confidence_level: float = 0.95,
    resamples: int = 1_000,
    block_length: int = 8,
    seed: int = 42,
) -> tuple[float, float, int]:
    """Estimate a percentile interval for Pearson correlation using circular moving blocks.

    Paired observations are resampled in contiguous blocks, preserving some local serial
    dependence that an IID bootstrap would destroy. The circular rule allows blocks beginning near
    the sample end to wrap to the beginning. This is a robustness diagnostic, not a forecast
    interval, and its block length remains a configurable research assumption.
    """
    if not 0 < confidence_level < 1:
        raise MarketAnalysisError("Bootstrap confidence_level must be between 0 and 1")
    if resamples < 100:
        raise MarketAnalysisError("Bootstrap resamples must be at least 100")
    if block_length < 1:
        raise MarketAnalysisError("Bootstrap block_length must be positive")
    paired = pd.DataFrame(
        {
            "signal": np.asarray(signal, dtype=float),
            "outcome": np.asarray(outcome, dtype=float),
        }
    ).dropna()
    observations = len(paired)
    if observations < 2:
        return float("nan"), float("nan"), 0

    x = paired["signal"].to_numpy()
    y = paired["outcome"].to_numpy()
    effective_block_length = min(block_length, observations)
    blocks_per_sample = int(np.ceil(observations / effective_block_length))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, observations, size=(resamples, blocks_per_sample))
    offsets = np.arange(effective_block_length)
    indices = ((starts[..., None] + offsets) % observations).reshape(resamples, -1)
    indices = indices[:, :observations]

    x_samples = x[indices]
    y_samples = y[indices]
    x_centered = x_samples - x_samples.mean(axis=1, keepdims=True)
    y_centered = y_samples - y_samples.mean(axis=1, keepdims=True)
    numerator = np.sum(x_centered * y_centered, axis=1)
    denominator = np.sqrt(np.sum(x_centered**2, axis=1) * np.sum(y_centered**2, axis=1))
    correlations = np.divide(
        numerator,
        denominator,
        out=np.full(resamples, np.nan),
        where=denominator > 0,
    )
    valid = correlations[np.isfinite(correlations)]
    if valid.size == 0:
        return float("nan"), float("nan"), 0
    alpha = (1 - confidence_level) / 2
    lower, upper = np.quantile(valid, [alpha, 1 - alpha])
    return float(lower), float(upper), int(valid.size)
