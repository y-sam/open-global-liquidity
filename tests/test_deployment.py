import os
import subprocess
import sys
from datetime import UTC
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


def _write_public_snapshots(data_root: Path) -> None:
    reference = data_root / "reference"
    reference.mkdir(parents=True)
    dates = pd.to_datetime(["2024-01-03", "2024-01-10"])
    retrieved_at = pd.Timestamp("2024-01-11", tz=UTC)

    source_rows: list[dict[str, object]] = []
    components = {
        "fed_assets": ("WALCL", [8_000_000.0, 8_100_000.0], "Millions of U.S. Dollars"),
        "treasury_general_account": (
            "WDTGAL",
            [500_000.0, 510_000.0],
            "Millions of U.S. Dollars",
        ),
        "overnight_reverse_repo": (
            "RRPONTSYD",
            [1_000.0, 900.0],
            "Billions of U.S. Dollars",
        ),
        "reserve_balances": (
            "WRBWFRBL",
            [3_000_000.0, 3_100_000.0],
            "Millions of U.S. Dollars",
        ),
    }
    for component, (series_id, values, unit) in components.items():
        for date, value in zip(dates, values, strict=True):
            source_rows.append(
                {
                    "date": date,
                    "country": "US",
                    "provider": "FRED",
                    "series_id": series_id,
                    "component": component,
                    "value": value,
                    "unit": unit,
                    "frequency": (
                        "Daily"
                        if component == "overnight_reverse_repo"
                        else "Weekly, As of Wednesday"
                    ),
                    "retrieved_at": retrieved_at,
                }
            )
    pd.DataFrame(source_rows).to_parquet(reference / "us_fred_series_snapshot.parquet", index=False)

    model_rows: list[dict[str, object]] = []
    model_definitions = {
        "model_a": ("Model A — Fed assets", [8_000_000.0, 8_100_000.0], "fed_assets"),
        "model_b": (
            "Model B — Net Fed liquidity proxy",
            [6_500_000.0, 6_690_000.0],
            "fed_assets - treasury_general_account - overnight_reverse_repo",
        ),
        "model_c": (
            "Model C — Reserve-based liquidity",
            [3_000_000.0, 3_100_000.0],
            "reserve_balances",
        ),
    }
    for model_id, (model_name, values, formula) in model_definitions.items():
        for date, value in zip(dates, values, strict=True):
            model_rows.append(
                {
                    "date": date,
                    "model_id": model_id,
                    "model_name": model_name,
                    "value": value,
                    "unit": "Millions of U.S. Dollars",
                    "frequency": "Weekly, As of Wednesday",
                    "classification": "model_assumption",
                    "formula": formula,
                    "description": "Deployment test model",
                    "is_complete": True,
                }
            )
    pd.DataFrame(model_rows).to_parquet(
        reference / "us_liquidity_models_snapshot.parquet", index=False
    )


def test_streamlit_deployment_mode_needs_no_local_data_or_fred_secret(
    monkeypatch, tmp_path: Path
) -> None:
    data_root = tmp_path / "data"
    _write_public_snapshots(data_root)
    monkeypatch.setenv("OGLI_DATA_ROOT", str(data_root))
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    assert not (tmp_path / ".env").exists()
    assert not (data_root / "processed").exists()

    app_path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    app = AppTest.from_file(app_path, default_timeout=20).run()

    assert not app.exception
    assert not app.error
    assert [title.value for title in app.title] == [
        "See the financial system through a liquidity lens"
    ]
    assert len(app.metric) == 4
    assert app.metric[0].label == "Net Fed liquidity proxy"


def test_streamlit_prefers_checkout_over_stale_installed_package(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    _write_public_snapshots(data_root)
    stale_root = tmp_path / "stale_site_packages"
    stale_package = stale_root / "open_global_liquidity"
    stale_package.mkdir(parents=True)
    stale_package.joinpath("__init__.py").write_text("", encoding="utf-8")
    stale_package.joinpath("dashboard.py").write_text("STALE_PACKAGE = True\n", encoding="utf-8")

    project_root = Path(__file__).resolve().parents[1]
    app_path = project_root / "app" / "streamlit_app.py"
    checkout_dashboard = project_root / "src" / "open_global_liquidity" / "dashboard.py"
    script = f"""
from pathlib import Path
from streamlit.testing.v1 import AppTest

import open_global_liquidity.dashboard as stale_dashboard
assert stale_dashboard.STALE_PACKAGE
app = AppTest.from_file({str(app_path)!r}, default_timeout=20).run()
assert not app.exception, app.exception
assert not app.error, app.error
import open_global_liquidity.dashboard as dashboard
assert Path(dashboard.__file__).resolve() == Path({str(checkout_dashboard)!r}).resolve()
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(stale_root)
    environment["OGLI_DATA_ROOT"] = str(data_root)
    environment.pop("FRED_API_KEY", None)

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=project_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
