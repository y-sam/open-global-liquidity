from pathlib import Path

import pytest

from open_global_liquidity.config import ConfigurationError, load_series_config


def test_load_walcl_config() -> None:
    definitions = load_series_config(Path("config/series.yaml"))

    assert len(definitions) == 4
    by_id = {definition.series_id: definition for definition in definitions}
    assert set(by_id) == {"WALCL", "WDTGAL", "RRPONTSYD", "WRBWFRBL"}
    walcl = by_id["WALCL"]
    assert walcl.series_id == "WALCL"
    assert walcl.classification == "measured_data"
    assert walcl.country == "US"
    assert walcl.unit == "Millions of U.S. Dollars"
    assert by_id["RRPONTSYD"].unit == "Billions of U.S. Dollars"
    assert by_id["WRBWFRBL"].frequency == "Weekly, As of Wednesday"


def test_config_rejects_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "series.yaml"
    path.write_text("US:\n  liquidity:\n    fed_assets:\n      provider: fred\n")

    with pytest.raises(ConfigurationError, match="missing fields"):
        load_series_config(path)
