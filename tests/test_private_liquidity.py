from pathlib import Path

import pandas as pd
import pytest

from open_global_liquidity.models.private_liquidity import (
    PrivateLiquidityError,
    calculate_private_liquidity,
    load_private_liquidity_config,
)


def _source(periods: int = 24) -> pd.DataFrame:
    rows = []
    for index, quarter_end in enumerate(pd.date_range("2018-03-31", periods=periods, freq="QE")):
        bank_date = pd.bdate_range(end=quarter_end, periods=1)[0]
        rows.extend(
            [
                (bank_date, "bank_credit", 15_000 + index * 100),
                (bank_date, "bank_loans_and_leases", 10_000 + index * 80),
                (quarter_end, "money_market_fund_assets", 5_000_000 + index * 50_000),
            ]
        )
    return pd.DataFrame(rows, columns=["date", "component", "value"]).assign(
        provider="FRED",
        series_id=lambda frame: frame["component"],
        retrieved_at=pd.Timestamp("2026-01-01", tz="UTC"),
    )


def test_private_liquidity_is_bounded_and_does_not_add_loans_twice() -> None:
    config = load_private_liquidity_config(Path("config/private_liquidity.yaml"))
    result = calculate_private_liquidity(_source(), config)

    assert result["private_liquidity_index"].dropna().between(0, 100).all()
    assert result["loan_share_of_bank_credit"].between(0, 1).all()
    assert "bank_loans_billions" in result
    assert result["signal_available_date"].equals(result["date"] + pd.offsets.MonthEnd(3))


def test_private_liquidity_rejects_missing_mmf() -> None:
    source = _source().loc[lambda frame: frame["component"] != "money_market_fund_assets"]

    with pytest.raises(PrivateLiquidityError, match="lacks configured"):
        calculate_private_liquidity(
            source, load_private_liquidity_config(Path("config/private_liquidity.yaml"))
        )


def test_private_liquidity_normalizes_fred_quarter_start_labels() -> None:
    source = _source()
    mmf = source["component"].eq("money_market_fund_assets")
    source.loc[mmf, "date"] = source.loc[mmf, "date"].dt.to_period("Q").dt.start_time

    result = calculate_private_liquidity(
        source, load_private_liquidity_config(Path("config/private_liquidity.yaml"))
    )

    assert result["date"].dt.is_quarter_end.all()
    assert len(result) == 24
