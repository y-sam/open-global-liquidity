# Open Global Liquidity

> Open Global Liquidity is an independent research project using public data. It is inspired by publicly discussed concepts in global liquidity research, including work by Michael Howell and CrossBorder Capital, but it does not reproduce or claim access to CrossBorder Capital's proprietary methodology, data, or models.

There is no endorsement by or affiliation with Michael Howell or CrossBorder Capital. The future
project index will be named **OGLI — Open Global Liquidity Index**, never the official CrossBorder
Capital GLI.

## Current scope: v0.1, Phase 1

The repository currently proves one auditable US data-ingestion path. It downloads Federal Reserve
total assets (`WALCL`) from the FRED API, caches the source observations, converts them to the
project's long-format schema, and writes Parquet output. Liquidity formulas, normalization,
multi-series analysis, and the Streamlit application are deliberately not implemented yet.

The configured series was checked against the official FRED record: **Assets: Total Assets: Total
Assets (Less Eliminations from Consolidation): Wednesday Level**, weekly as of Wednesday, not
seasonally adjusted, in millions of US dollars. Source: Board of Governors of the Federal Reserve
System (H.4.1), distributed by [FRED](https://fred.stlouisfed.org/series/WALCL).

## Research boundaries

The project will keep three categories separate:

1. **Measured data** — observations and metadata obtained from named public providers.
2. **Model assumptions** — transparent, configurable transformations chosen by this project.
3. **Calibrated parameters** — parameters fitted to an explicitly identified target, if introduced.

Phase 1 contains measured data infrastructure only. FRED observations are current-vintage data and
may contain revisions; the cache is not a vintage-data archive.

## macOS setup

The project requires macOS, zsh, Git, Python 3.12, and `uv`. Do not modify Apple's system Python.
On a new Mac, inspect the tools first:

```zsh
command -v brew && brew --version
command -v git && git --version
command -v python3.12 && python3.12 --version
command -v uv && uv --version
command -v code && code --version
```

Install missing command-line prerequisites with Homebrew:

```zsh
brew install git python@3.12 uv
```

If `code` is missing, open VS Code, press `Cmd+Shift+P`, and run **Shell Command: Install 'code'
command in PATH**. Then open a new terminal.

Set up this repository:

```zsh
git clone <repository-url> open-global-liquidity
cd open-global-liquidity
uv sync
cp .env.example .env
```

Add your free FRED API key to `.env`. That file is ignored by Git and must never be committed.

## Run the pipeline

```zsh
uv run python -m open_global_liquidity.pipeline
```

Useful options:

```zsh
uv run python -m open_global_liquidity.pipeline --start 2020-01-01
uv run python -m open_global_liquidity.pipeline --force-refresh
```

The provider fails clearly when `FRED_API_KEY` is absent, FRED returns an error, the response schema
is invalid, or no observations are returned. A successful run writes:

- `data/raw/fred/WALCL.parquet`: provider observations plus retrieval metadata;
- `data/processed/us_fred_series.parquet`: standardized long-format observations.

The raw cache is reused for 24 hours by default. `--force-refresh` bypasses it. Generated data is
intentionally excluded from Git because it is reproducible from the public API.

## Internal data schema

Processed observations contain `date`, `country`, `provider`, `series_id`, `component`, `value`,
`unit`, `frequency`, and `retrieved_at`. Raw FRED real-time fields are retained in the raw Parquet
cache to support traceability.

## Quality checks

```zsh
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

Tests use mocked HTTP responses and do not require a FRED key or network connection.

## Architecture

- `config/series.yaml` — measured-series definitions and source metadata.
- `src/open_global_liquidity/config.py` — validated configuration loading.
- `src/open_global_liquidity/data/fred.py` — FRED network, error handling, cache, and standardization.
- `src/open_global_liquidity/pipeline.py` — executable orchestration and Parquet output.
- `tests/` — offline ingestion and configuration tests.

## Roadmap

After Phase 1, v0.1 will add verified US series, weekly frequency alignment, three competing US
liquidity definitions, momentum, non-look-ahead OGLI normalization, market validation, and a
Streamlit dashboard. Later versions may add global central banks, FX conversion, collateral and
repo proxies, shadow monetary base concepts, BIS cross-border credit, and explicitly labeled public
benchmark calibration.

## Limitations and disclaimer

This early version is not a liquidity index, trading model, or investment recommendation. It uses
one nominal, non-seasonally-adjusted balance-sheet series. Public data can be revised, delayed,
discontinued, or unavailable. Future statistical relationships will not by themselves establish
causation. Users are responsible for verifying data and conclusions.
