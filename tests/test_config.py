from pathlib import Path

import pytest

from open_global_liquidity.config import ConfigurationError, load_model_config, load_series_config


def test_load_walcl_config() -> None:
    definitions = load_series_config(Path("config/series.yaml"))

    assert len(definitions) == 5
    by_id = {definition.series_id: definition for definition in definitions}
    assert set(by_id) == {
        "WALCL",
        "WDTGAL",
        "RRPONTSYD",
        "WRBWFRBL",
        "btc.PriceUSD",
    }
    walcl = by_id["WALCL"]
    assert walcl.series_id == "WALCL"
    assert walcl.classification == "measured_data"
    assert walcl.country == "US"
    assert walcl.unit == "Millions of U.S. Dollars"
    assert by_id["RRPONTSYD"].unit == "Billions of U.S. Dollars"
    assert by_id["WRBWFRBL"].frequency == "Weekly, As of Wednesday"
    assert by_id["btc.PriceUSD"].group == "markets"
    assert by_id["btc.PriceUSD"].provider == "coinmetrics"
    assert by_id["btc.PriceUSD"].unit == "U.S. Dollars per Bitcoin"


def test_config_rejects_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "series.yaml"
    path.write_text("US:\n  liquidity:\n    fed_assets:\n      provider: fred\n")

    with pytest.raises(ConfigurationError, match="missing fields"):
        load_series_config(path)


def test_load_model_config() -> None:
    config = load_model_config(Path("config/model.yaml"))

    assert config.alignment.canonical_frequency == "W-WED"
    assert config.alignment.daily_asof_components == ("overnight_reverse_repo",)
    assert config.alignment.daily_asof_max_staleness_days == 7
    assert [model.model_id for model in config.models] == ["model_a", "model_b", "model_c"]
    assert config.models[1].terms == {
        "fed_assets": 1.0,
        "treasury_general_account": -1.0,
        "overnight_reverse_repo": -1.0,
    }
    assert config.ogli.normalization.default_mode == "expanding"
    assert config.ogli.normalization.min_periods == 104
    assert config.ogli.momentum_weights == {
        "growth_12m_yoy": 0.4,
        "growth_3m_annualized": 0.6,
    }
    assert config.ogli.regimes[-1].max_value == 100
    assert config.market_alignment.daily_asof_components == ("bitcoin",)
    assert config.market_analysis.forward_horizons_weeks == (0, 4, 8, 12, 26, 52)
    assert config.market_analysis.liquidity_signal == "momentum_score"
    assert config.market_analysis.publication_lag_policy == "observation_date_unadjusted"


def test_model_config_rejects_ogli_weights_that_do_not_sum_to_one(tmp_path: Path) -> None:
    source = Path("config/model.yaml").read_text(encoding="utf-8")
    path = tmp_path / "model.yaml"
    path.write_text(source.replace("growth_12m_yoy: 0.40", "growth_12m_yoy: 0.50"))

    with pytest.raises(ConfigurationError, match=r"must sum to 1\.0"):
        load_model_config(path)
