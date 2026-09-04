from pathlib import Path

from open_global_liquidity.models.availability import load_global_availability_registry


def test_global_availability_registry_exposes_vintage_limitations() -> None:
    registry = load_global_availability_registry(Path("config/global_availability.yaml"))

    assert len(registry) == 9
    assert set(registry["model_role"]) == {"central_bank_asset", "fx_translation"}
    assert registry["point_in_time_status"].eq("lag_adjusted_current_vintage").all()
    bis = registry.loc[registry["provider"] == "BIS"]
    assert len(bis) == 5
    assert bis["conservative_lag_months"].eq(2).all()
    assert bis["historical_value_vintages"].eq("unavailable").all()
    h10 = registry.loc[registry["model_role"] == "fx_translation"]
    assert h10["conservative_lag_days"].eq(7).all()
