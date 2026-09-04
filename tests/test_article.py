import json
from pathlib import Path

import pandas as pd

from open_global_liquidity.reporting.article import build_article_workspace


def test_builds_dated_article_workspace(tmp_path: Path) -> None:
    reference = Path(__file__).resolve().parents[1] / "data" / "reference"
    output = build_article_workspace(reference, tmp_path, pd.Timestamp("2026-09-04"))
    assert (output / "research_note.md").is_file()
    assert (output / "latest_signals.csv").is_file()
    assert (output / "model_h_contributions.csv").is_file()
    metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["forecast_claim"] is False
    assert "post-specification descriptive" in (output / "research_note.md").read_text()
