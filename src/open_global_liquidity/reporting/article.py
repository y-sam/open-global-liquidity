"""Generate a dated research-note workspace from provenance-tracked snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


class ArticleWorkspaceError(ValueError):
    """Raised when publication inputs are missing or invalid."""


def _read(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise ArticleWorkspaceError(f"Required snapshot is missing: {path}")
    return pd.read_parquet(path)


def build_article_workspace(reference_dir: Path, output_root: Path, as_of: pd.Timestamp) -> Path:
    """Create Markdown and CSV evidence files without inventing narrative conclusions."""
    signals = _read(reference_dir / "liquidity_signal_map_snapshot.parquet")
    model_h = _read(reference_dir / "global_model_h_snapshot.parquet")
    signals["available_date"] = pd.to_datetime(signals["available_date"])
    eligible = signals.loc[signals["available_date"] <= as_of].copy()
    if eligible.empty:
        raise ArticleWorkspaceError("No signal was available by the requested publication date")
    latest = eligible.sort_values("available_date").groupby("channel", as_index=False).tail(1)
    latest = latest.sort_values("channel_label")
    h = model_h.loc[pd.to_datetime(model_h["signal_available_date"]) <= as_of].copy()
    if h.empty:
        raise ArticleWorkspaceError("No Model H reading was available by the requested date")
    latest_h = h.iloc[-1]
    prior_h = h.iloc[-2] if len(h) > 1 else latest_h

    output_dir = output_root / as_of.date().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    latest.to_csv(output_dir / "latest_signals.csv", index=False)
    contribution_columns = [column for column in h.columns if column.startswith("contribution_")]
    h[["date", "signal_available_date", "model_h_index", *contribution_columns]].tail(8).to_csv(
        output_dir / "model_h_contributions.csv", index=False
    )
    metadata = {
        "publication_as_of": as_of.date().isoformat(),
        "model_h_observation": pd.Timestamp(latest_h["date"]).date().isoformat(),
        "model_h_available": pd.Timestamp(latest_h["signal_available_date"]).date().isoformat(),
        "classification": "research_note_workspace",
        "forecast_claim": False,
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    rows = "\n".join(
        f"| {row.channel_label} | {row.index_value:.1f} | {row.regime} | "
        f"{pd.Timestamp(row.available_date):%Y-%m-%d} |"
        for row in latest.itertuples(index=False)
    )
    note = f"""# Open Global Liquidity research note — {as_of:%Y-%m-%d}

## Executive summary

_Write the central observation here. Separate what changed from why it may matter._

## Current liquidity map

| Channel | Index | Regime | Available date |
|---|---:|---|---|
{rows}

## What changed

- Model H: **{float(latest_h["model_h_index"]):.1f}**, versus
  **{float(prior_h["model_h_index"]):.1f}** in the prior available quarter.
- Identify the largest pillar contribution using `model_h_contributions.csv`.
- Explain disagreements between channels; do not average them informally.

## Bitcoin context

_Describe subsequent-return evidence with sample size and uncertainty. Do not convert correlation
into causation or a forecast._

## Risks and alternative explanations

- FX translation versus native balance-sheet changes.
- Publication lags and current-vintage revisions.
- Common macroeconomic drivers and overlapping return windows.

## Sources and methodology

Generated from provenance-tracked public dashboard snapshots. Observation dates and modeled
availability dates are distinct. Model H history is post-specification descriptive and is not the
production Model G index.

> Open Global Liquidity is an independent public-data research project. It does not reproduce
> CrossBorder Capital's proprietary methodology, and nothing in this note is investment advice.
"""
    (output_dir / "research_note.md").write_text(note, encoding="utf-8")
    return output_dir


def main() -> None:
    """CLI entry point for a reproducible article workspace."""
    parser = argparse.ArgumentParser(description="Generate an OGLI article workspace")
    parser.add_argument("--as-of", default=pd.Timestamp.now().date().isoformat())
    parser.add_argument("--output", type=Path, default=Path("reports/generated"))
    args = parser.parse_args()
    output = build_article_workspace(Path("data/reference"), args.output, pd.Timestamp(args.as_of))
    print(f"Article workspace written to {output}")
