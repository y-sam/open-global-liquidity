from pathlib import Path

import pytest

from open_global_liquidity.config import ConfigurationError, load_model_config, load_series_config


def test_load_walcl_config() -> None:
    definitions = load_series_config(Path("config/series.yaml"))

    assert len(definitions) == 35
    by_id = {definition.series_id: definition for definition in definitions}
    assert set(by_id) == {
        "WALCL",
        "WDTGAL",
        "RRPONTSYD",
        "WRBWFRBL",
        "btc.PriceUSD",
        "DGS10",
        "DGS2",
        "DTWEXBGS",
        "CMO-GOLD-MONTHLY",
        "BSI.M.U2.N.C.T00.A.1.Z5.0000.Z01.E",
        "BS01.MABJMTA",
        "RPQB75A",
        "PBOC.BSMA.TOTAL_ASSETS",
        "BIS,WS_CBTA,1.0/M.CN.B.XDC.CNY.N",
        "BIS,WS_CBTA,1.0/M.US.B.XDC.USD.N",
        "BIS,WS_CBTA,1.0/M.XM.B.XDC.EUR.N",
        "BIS,WS_CBTA,1.0/M.JP.B.XDC.JPY.N",
        "BIS,WS_CBTA,1.0/M.GB.B.XDC.GBP.N",
        "DEXUSEU",
        "DEXJPUS",
        "DEXUSUK",
        "DEXCHUS",
        "MSPD.TABLE1.TOTAL_MARKETABLE.DEBT_HELD_PUBLIC",
        "MSPD.TABLE1.MARKETABLE.BILLS.DEBT_HELD_PUBLIC",
        "MSPD.TABLE1.MARKETABLE.NOTES.DEBT_HELD_PUBLIC",
        "MSPD.TABLE1.MARKETABLE.BONDS.DEBT_HELD_PUBLIC",
        "MSPD.TABLE1.MARKETABLE.TIPS.DEBT_HELD_PUBLIC",
        "MSPD.TABLE1.MARKETABLE.FRNS.DEBT_HELD_PUBLIC",
        "TREAST",
        "SOFR",
        "SOFRVOL",
        "TGCRRATE",
        "TGCRVOLUME",
        "DFF",
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
    assert by_id["CMO-GOLD-MONTHLY"].group == "point_in_time_markets"
    ecb = by_id["BSI.M.U2.N.C.T00.A.1.Z5.0000.Z01.E"]
    assert ecb.country == "EA"
    assert ecb.provider == "ecb"
    assert ecb.unit == "Millions of Euro"
    assert ecb.frequency == "Monthly, End of Period"
    boj = by_id["BS01.MABJMTA"]
    assert boj.country == "JP"
    assert boj.provider == "boj"
    assert boj.unit == "100 Million Yen"
    boe = by_id["RPQB75A"]
    assert boe.country == "GB"
    assert boe.provider == "boe"
    assert boe.unit == "Millions of Sterling"
    pboc = by_id["PBOC.BSMA.TOTAL_ASSETS"]
    assert pboc.country == "CN"
    assert pboc.provider == "pboc"
    assert pboc.unit == "100 Million Yuan"
    china = by_id["BIS,WS_CBTA,1.0/M.CN.B.XDC.CNY.N"]
    assert china.country == "CN"
    assert china.provider == "bis"
    assert china.unit == "Billions of Chinese Yuan"
    assert by_id["DEXUSEU"].group == "exchange_rates"
    assert by_id["DEXJPUS"].unit == "Japanese Yen to One U.S. Dollar"
    collateral_components = {
        definition.component for definition in definitions if definition.group == "collateral"
    }
    assert collateral_components == {
        "marketable_treasury_debt_public",
        "marketable_treasury_bills_public",
        "marketable_treasury_notes_public",
        "marketable_treasury_bonds_public",
        "marketable_treasury_tips_public",
        "marketable_treasury_frns_public",
        "fed_treasury_holdings",
        "secured_overnight_financing_rate",
        "secured_overnight_financing_volume",
        "tri_party_general_collateral_rate",
        "tri_party_general_collateral_volume",
        "effective_federal_funds_rate",
        "treasury_yield_10y_collateral",
    }


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
    assert config.market_alignment.daily_asof_components == (
        "bitcoin",
        "treasury_yield_10y",
        "treasury_yield_2y",
        "broad_usd_index",
    )
    assert config.market_analysis.forward_horizons_weeks == (0, 4, 8, 12, 26, 52)
    assert config.market_analysis.liquidity_signal == "momentum_score"
    assert config.market_analysis.publication_lag_policy == "observation_and_available_information"
    assert config.market_analysis.signal_availability_lag_weeks == 1
    assert config.market_analysis.non_overlapping_min_periods == 8
    assert config.market_analysis.confidence_level == 0.95
    assert config.market_analysis.bootstrap.resamples == 1_000
    assert config.market_analysis.bootstrap.block_length_observations == 8
    assert [period.period_id for period in config.market_analysis.research_subperiods] == [
        "pre_2020",
        "pandemic_cycle",
        "recent_cycle",
    ]
    assert config.market_analysis.research_subperiods[-1].end is None
    assert config.point_in_time_pilot.frequency == "month_end"
    assert config.point_in_time_pilot.start.isoformat() == "2021-01-31"
    assert config.point_in_time_pilot.current_comparison_policy == "same_observation_date"
    assert config.point_in_time_pilot.market_publication_lag_weeks == (0, 1, 2, 4)
    assert config.point_in_time_pilot.market_forward_horizons_months == (1, 3, 6, 12)
    assert config.point_in_time_pilot.market_non_overlapping_correlation_min_periods == 8
    primary = config.point_in_time_pilot.primary_bitcoin_specification
    assert primary.classification == "model_assumption"
    assert primary.model_id == "model_b"
    assert primary.publication_lag_weeks == 1
    assert primary.sample_policy == "non_overlapping"
    assert primary.forward_horizons_months == (1, 3, 6, 12)
    directional = config.point_in_time_pilot.bitcoin_directional_regimes
    assert directional.classification == "model_assumption"
    assert directional.expansionary == ("Above normal", "Expansion", "Strong expansion")
    assert directional.contractionary == (
        "Below normal",
        "Contraction",
        "Strong contraction",
    )
    assert directional.excluded == ("Neutral",)


def test_model_config_rejects_ogli_weights_that_do_not_sum_to_one(tmp_path: Path) -> None:
    source = Path("config/model.yaml").read_text(encoding="utf-8")
    path = tmp_path / "model.yaml"
    path.write_text(source.replace("growth_12m_yoy: 0.40", "growth_12m_yoy: 0.50"))

    with pytest.raises(ConfigurationError, match=r"must sum to 1\.0"):
        load_model_config(path)
