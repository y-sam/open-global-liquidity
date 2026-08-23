import pandas as pd
import pytest

from open_global_liquidity.transforms.units import UnitConversionError, convert_to_usd_millions


def test_convert_supported_units_to_usd_millions() -> None:
    source = pd.DataFrame(
        {
            "value": [7_000_000.0, 1_250.5],
            "unit": ["Millions of U.S. Dollars", "Billions of U.S. Dollars"],
        }
    )

    result = convert_to_usd_millions(source)

    assert result["value"].tolist() == [7_000_000.0, 1_250_500.0]
    assert result["unit"].tolist() == ["Millions of U.S. Dollars"] * 2
    assert result["source_unit"].tolist() == source["unit"].tolist()


def test_convert_rejects_unsupported_units() -> None:
    source = pd.DataFrame({"value": [1.0], "unit": ["Percent"]})

    with pytest.raises(UnitConversionError, match="Unsupported monetary units"):
        convert_to_usd_millions(source)
