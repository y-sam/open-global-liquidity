from datetime import UTC

import pandas as pd
import pytest

from open_global_liquidity.transforms.frequency import (
    FrequencyAlignmentError,
    align_to_weekly_wednesday,
)


def _row(date: str, component: str, value: float, frequency: str) -> dict[str, object]:
    return {
        "date": pd.Timestamp(date),
        "country": "US",
        "provider": "FRED",
        "series_id": component.upper(),
        "component": component,
        "value": value,
        "unit": "Millions of U.S. Dollars",
        "frequency": frequency,
        "retrieved_at": pd.Timestamp("2024-01-20", tz=UTC),
        "source_unit": "Millions of U.S. Dollars",
    }


def test_aligns_weekly_exactly_and_daily_asof_without_future_data() -> None:
    rows = [
        _row("2024-01-03", "fed_assets", 8_000_000.0, "Weekly, As of Wednesday"),
        _row("2024-01-10", "fed_assets", 8_100_000.0, "Weekly, As of Wednesday"),
        _row("2024-01-03", "reserve_balances", 3_000_000.0, "Weekly, As of Wednesday"),
        _row("2024-01-10", "reserve_balances", 3_100_000.0, "Weekly, As of Wednesday"),
        _row("2024-01-03", "treasury_general_account", 700_000.0, "Weekly, As of Wednesday"),
        _row("2024-01-10", "treasury_general_account", 750_000.0, "Weekly, As of Wednesday"),
        _row("2024-01-02", "overnight_reverse_repo", 600_000.0, "Daily"),
        _row("2024-01-04", "overnight_reverse_repo", 999_000.0, "Daily"),
        _row("2024-01-10", "overnight_reverse_repo", 500_000.0, "Daily"),
    ]

    result = align_to_weekly_wednesday(
        pd.DataFrame(rows),
        daily_asof_components=["overnight_reverse_repo"],
        daily_asof_max_staleness_days=7,
    )
    rrp = result.loc[result["component"] == "overnight_reverse_repo"].set_index("date")

    assert rrp.loc[pd.Timestamp("2024-01-03"), "value"] == 600_000.0
    assert rrp.loc[pd.Timestamp("2024-01-03"), "source_date"] == pd.Timestamp("2024-01-02")
    assert rrp.loc[pd.Timestamp("2024-01-03"), "staleness_days"] == 1
    assert rrp.loc[pd.Timestamp("2024-01-10"), "value"] == 500_000.0
    assert set(result["frequency"]) == {"Weekly, As of Wednesday"}


def test_weekly_series_does_not_forward_fill_missing_wednesday() -> None:
    rows = [
        _row("2024-01-03", "fed_assets", 8_000_000.0, "Weekly, As of Wednesday"),
        _row("2024-01-17", "fed_assets", 8_200_000.0, "Weekly, As of Wednesday"),
        _row("2024-01-03", "reserve_balances", 3_000_000.0, "Weekly, As of Wednesday"),
        _row("2024-01-17", "reserve_balances", 3_200_000.0, "Weekly, As of Wednesday"),
    ]

    result = align_to_weekly_wednesday(
        pd.DataFrame(rows), daily_asof_components=[], daily_asof_max_staleness_days=7
    )
    missing = result.loc[
        (result["component"] == "fed_assets") & (result["date"] == pd.Timestamp("2024-01-10")),
        "value",
    ]

    assert missing.isna().all()


def test_daily_series_requires_explicit_asof_policy() -> None:
    source = pd.DataFrame([_row("2024-01-03", "daily_component", 1.0, "Daily")])

    with pytest.raises(FrequencyAlignmentError, match="explicit as-of"):
        align_to_weekly_wednesday(source, daily_asof_components=[], daily_asof_max_staleness_days=7)
