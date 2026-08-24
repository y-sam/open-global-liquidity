from datetime import UTC

import pandas as pd
import pytest

from open_global_liquidity.analysis.revisions import (
    RevisionAnalysisError,
    compare_vintage_to_current,
)
from open_global_liquidity.data.base import STANDARD_COLUMNS
from open_global_liquidity.data.fred import VINTAGE_COLUMNS


def _vintage() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "observation_date": pd.to_datetime(["2020-01-01", "2020-01-08"]),
            "vintage_date": pd.to_datetime(["2020-01-10"] * 2),
            "country": ["US"] * 2,
            "provider": ["ALFRED"] * 2,
            "series_id": ["WALCL"] * 2,
            "component": ["fed_assets"] * 2,
            "value": [100.0, 110.0],
            "unit": ["Millions of U.S. Dollars"] * 2,
            "frequency": ["Weekly, As of Wednesday"] * 2,
            "realtime_start": ["2020-01-10"] * 2,
            "realtime_end": ["9999-12-31"] * 2,
            "retrieved_at": [pd.Timestamp("2024-01-01", tz=UTC)] * 2,
        }
    )[VINTAGE_COLUMNS]


def _current() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-01-08"]),
            "country": ["US"] * 2,
            "provider": ["FRED"] * 2,
            "series_id": ["WALCL"] * 2,
            "component": ["fed_assets"] * 2,
            "value": [102.0, 110.0],
            "unit": ["Millions of U.S. Dollars"] * 2,
            "frequency": ["Weekly, As of Wednesday"] * 2,
            "retrieved_at": [pd.Timestamp("2024-01-02", tz=UTC)] * 2,
        }
    )[STANDARD_COLUMNS]


def test_revision_comparison_keeps_values_and_classifies_changes() -> None:
    result = compare_vintage_to_current(_vintage(), _current())

    assert result["revision"].tolist() == [2.0, 0.0]
    assert result["revision_pct"].tolist() == [0.02, 0.0]
    assert result["revision_status"].tolist() == ["revised", "unchanged"]
    assert set(result["classification"]) == {"statistical_transformation"}


def test_revision_comparison_rejects_incomplete_current_data() -> None:
    with pytest.raises(RevisionAnalysisError, match="Current data is missing"):
        compare_vintage_to_current(_vintage(), pd.DataFrame({"date": []}))
