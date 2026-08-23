import numpy as np
import pandas as pd

from open_global_liquidity.transforms.growth import calculate_liquidity_momentum


def test_weekly_changes_and_growth_formulas() -> None:
    dates = pd.date_range("2023-01-04", periods=60, freq="W-WED")
    values = 100 * 1.01 ** np.arange(60)
    models = pd.DataFrame(
        {
            "date": dates,
            "model_id": "model_a",
            "model_name": "Model A",
            "value": values,
        }
    )

    result = calculate_liquidity_momentum(models)
    row = result.iloc[52]

    assert np.isclose(row["change_1m"], values[52] - values[48])
    assert np.isclose(row["change_3m"], values[52] - values[39])
    assert np.isclose(row["change_6m"], values[52] - values[26])
    assert np.isclose(row["change_12m"], values[52] - values[0])
    assert np.isclose(row["growth_3m_annualized"], 1.01**52 - 1)
    assert np.isclose(row["growth_12m_yoy"], 1.01**52 - 1)


def test_growth_is_missing_until_required_history_exists() -> None:
    models = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-03", periods=52, freq="W-WED"),
            "model_id": "model_a",
            "model_name": "Model A",
            "value": np.arange(1, 53, dtype=float),
        }
    )

    result = calculate_liquidity_momentum(models)

    assert result["growth_12m_yoy"].isna().all()
    assert result["growth_3m_annualized"].iloc[:13].isna().all()
    assert result["growth_3m_annualized"].iloc[13:].notna().all()
