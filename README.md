# Open Global Liquidity

**Live Streamlit dashboard:** [https://open-global-liquidity.streamlit.app/](https://open-global-liquidity.streamlit.app/)

> Open Global Liquidity is an independent research project using public data. It is inspired by publicly discussed concepts in global liquidity research, including work by Michael Howell and CrossBorder Capital, but it does not reproduce or claim access to CrossBorder Capital's proprietary methodology, data, or models.

There is no endorsement by or affiliation with Michael Howell or CrossBorder Capital. The future
project index will be named **OGLI — Open Global Liquidity Index**, never the official CrossBorder
Capital GLI.

## Current scope: v0.1 US liquidity models

The repository provides an auditable US data-ingestion path, experimental OGLI momentum index, and
Streamlit dashboard. It
downloads four liquidity-related Federal Reserve series from FRED, caches source observations,
converts them to the project's long-format schema, aligns them to Wednesdays, and calculates three
competing model levels. It then calculates liquidity momentum and maps a configurable composite
through the standard normal CDF onto the OGLI 0–100 scale. The dashboard keeps measured components,
model assumptions, and statistical transformations separate.

The configured measured liquidity series are:

- [`WALCL`](https://fred.stlouisfed.org/series/WALCL): Federal Reserve total assets, Wednesday level;
- [`WDTGAL`](https://fred.stlouisfed.org/series/WDTGAL): Treasury General Account, Wednesday level;
- [`RRPONTSYD`](https://fred.stlouisfed.org/series/RRPONTSYD): overnight reverse repos, daily;
- [`WRBWFRBL`](https://fred.stlouisfed.org/series/WRBWFRBL): reserve balances, Wednesday level.

The primary market-validation series is:

- [`btc.PriceUSD`](https://community-api.coinmetrics.io/v4/): Coin Metrics' daily Bitcoin USD price,
  published as Community Data under CC BY-NC 4.0. It is used for independent,
  non-commercial research and can therefore support the complete hosted comparison workspace.

Measured macro context, kept separate from OGLI inputs, now includes:

- [`DGS10`](https://fred.stlouisfed.org/series/DGS10): 10-year Treasury constant-maturity yield;
- [`DGS2`](https://fred.stlouisfed.org/series/DGS2): 2-year Treasury constant-maturity yield;
- [`DTWEXBGS`](https://fred.stlouisfed.org/series/DTWEXBGS): nominal broad U.S. dollar index.

The implemented models are transparent project assumptions:

- **Model A — Fed assets:** `fed_assets`;
- **Model B — Net Fed liquidity proxy:** `fed_assets - TGA - ON RRP`;
- **Model C — Reserve-based liquidity:** `reserve_balances`.

Model B is a common public-market proxy, not a Michael Howell or CrossBorder Capital formula.
Model C uses reserve balances directly; TGA and RRP are not subtracted again because their effects
are already reflected in reserves and another subtraction could double count those drains.
The default OGLI uses expanding, non-look-ahead z-scores with a 104-observation minimum history.

## Research boundaries

The project will keep three categories separate:

1. **Measured data** — observations and metadata obtained from named public providers.
2. **Model assumptions** — transparent, configurable transformations chosen by this project.
3. **Calibrated parameters** — parameters fitted to an explicitly identified target, if introduced.

This milestone contains measured data plus explicitly classified model assumptions. No parameters
have been empirically calibrated. FRED observations are current-vintage data and may contain
revisions; the cache is not a vintage-data archive.

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
Bitcoin market data comes from Coin Metrics Community Data and requires no account or API key.

## Run the pipeline

```zsh
uv run python -m open_global_liquidity.pipeline
```

Useful options:

```zsh
uv run python -m open_global_liquidity.pipeline --start 2020-01-01
uv run python -m open_global_liquidity.pipeline --force-refresh
uv run python -m open_global_liquidity.pipeline --start 2020-01-01 --publish-dashboard-snapshot
```

The provider fails clearly when `FRED_API_KEY` is absent, FRED returns an error, the response schema
is invalid, or no observations are returned. A successful run writes:

- `data/raw/fred/<SERIES_ID>.parquet`: FRED observations plus retrieval metadata;
- `data/raw/coinmetrics/btc_priceusd.parquet`: cached Bitcoin USD prices;
- `data/processed/us_fred_series.parquet`: standardized long-format source observations;
- `data/processed/us_liquidity_weekly.parquet`: USD-million Wednesday inputs with source-date and
  staleness lineage;
- `data/processed/us_liquidity_models.parquet`: the three weekly model levels and formulas.
- `data/processed/us_ogli.parquet`: weekly changes, growth, z-scores, composite momentum, OGLI,
  and regimes for all three models.
- `data/processed/us_market_series.parquet`: standardized local market observations;
- `data/processed/us_market_weekly.parquet`: Wednesday-aligned market closes and lineage;
- `data/processed/us_market_returns.parquet`: contemporaneous and forward market returns;
- `data/processed/us_liquidity_market_comparisons.parquet`: signal/outcome pairs and rolling
  correlations;
- `data/processed/us_liquidity_market_correlations.parquet`: correlation summaries by model and
  return horizon.
- `data/processed/us_liquidity_market_regimes.parquet`: Bitcoin return summaries by OGLI regime,
  timing policy, horizon, and sample policy.
- `data/processed/us_macro_context_*.parquet`: measured Treasury/dollar context and the transparent
  10-year-minus-2-year curve slope.

Weekly source series require an exact Wednesday observation. Daily ON RRP uses the latest available
observation on or before Wednesday, capped at seven calendar days. No balance-sheet values are
interpolated. These assumptions live in `config/model.yaml`.

The raw cache is reused for 24 hours by default. `--force-refresh` bypasses it. Generated data is
intentionally excluded from Git because it is reproducible from the public API.

The explicit `--publish-dashboard-snapshot` option also writes
thirteen Git-versioned public-data artifacts:

- `data/reference/us_fred_series_snapshot.parquet` — measured source observations;
- `data/reference/us_liquidity_weekly_snapshot.parquet` — aligned weekly inputs and lineage;
- `data/reference/us_liquidity_models_snapshot.parquet` — Models A/B/C.
- `data/reference/us_ogli_snapshot.parquet` — momentum and expanding-normalized OGLI results.
- `data/reference/us_market_series_snapshot.parquet` — daily Bitcoin USD prices.
- `data/reference/us_market_weekly_snapshot.parquet` — Wednesday-aligned Bitcoin prices.
- `data/reference/us_market_returns_snapshot.parquet` — configured Bitcoin return outcomes.
- `data/reference/us_liquidity_market_comparisons_snapshot.parquet` — individual OGLI/Bitcoin
  pairs and trailing correlations.
- `data/reference/us_liquidity_market_correlations_snapshot.parquet` — aggregate model/horizon
  correlation estimates and sample sizes.
- `data/reference/us_liquidity_market_regimes_snapshot.parquet` — mean, median, positive share,
  and confidence intervals by OGLI regime.
- `data/reference/us_macro_context_series_snapshot.parquet` — standardized measured macro sources.
- `data/reference/us_macro_context_weekly_snapshot.parquet` — Wednesday-aligned context data.
- `data/reference/us_macro_context_indicators_snapshot.parquet` — yields, curve slope, and broad
  dollar index for dashboard presentation.

These small artifacts let the hosted dashboard run without local processed data, a `.env` file, a
FRED key, or a download on every visitor session. Publishing snapshots is an explicit maintainer
action. Review the generated files before committing them; the dashboard displays the active data
mode and source retrieval time.

### Automated weekly refresh

The `Refresh public dashboard data` GitHub Actions workflow runs every Friday at 12:00 UTC and can
also be started manually from the repository's **Actions** tab. It installs the locked Python 3.12
environment, downloads fresh FRED and Coin Metrics observations, regenerates the thirteen public
snapshots, and runs formatting, linting, and offline tests. Only successful runs can commit changed
snapshot files to `main`; a new commit then prompts Streamlit Community Cloud to redeploy.

The workflow requires a repository Actions secret named `FRED_API_KEY` and **Read and write**
workflow permissions. Coin Metrics Community Data does not require a key. The workflow deliberately
uses the start dates in `config/series.yaml`, preserving the complete configured Bitcoin history.
Never store the FRED key in the workflow file or repository.

Bitcoin market source data, individual returns, paired comparisons, scatter points, and rolling
correlations are available in the hosted dashboard. Coin Metrics Community Data is licensed under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/); this project attributes Coin
Metrics and uses the data only for independent, non-commercial research. S&P 500 analysis has been
deferred until suitable public-display and derived-data rights are available.

## Launch the dashboard

Run the pipeline first, then launch Streamlit:

```zsh
uv run python -m open_global_liquidity.pipeline --start 2020-01-01
uv run streamlit run app/streamlit_app.py
```

Streamlit opens the dashboard at `http://localhost:8501`. The app shows latest measured balances,
the three model levels, an OGLI page, a Liquidity vs markets workspace, a log-scale Bitcoin/OGLI
timeline, Bitcoin-focused landing metrics, history, a component explorer, recent source
observations, and methodology notes. Top navigation separates a
plain-language landing page, the OGLI index, market validation, the data dashboard, and a research
guide with definitions, assumptions, limitations, and primary-source links. All
model calculations come from the package and pipeline, not Streamlit.

The app prefers processed source and model files during local research. If those ignored files are
absent, as on Streamlit Community Cloud, it independently falls back to the tracked source and
model snapshots and labels each active data mode. The application presentation layer does not call
FRED or load `.env`; API credentials are needed only when a maintainer deliberately refreshes data.

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
An isolated Streamlit deployment test also removes `FRED_API_KEY`, provides no `.env` or processed
directory, and verifies that the public snapshots still render the landing-page metrics.

## Architecture

- `config/series.yaml` — measured-series definitions and source metadata.
- `config/model.yaml` — classified weekly-alignment and model assumptions.
- `src/open_global_liquidity/config.py` — validated configuration loading.
- `src/open_global_liquidity/data/fred.py` — FRED network, error handling, cache, and standardization.
- `src/open_global_liquidity/data/coinmetrics.py` — no-key Coin Metrics community ingestion and
  caching.
- `src/open_global_liquidity/transforms/` — unit conversion, alignment, growth, and z-scores.
- `src/open_global_liquidity/models/us_liquidity.py` — configurable Model A/B/C calculations.
- `src/open_global_liquidity/models/ogli.py` — composite momentum, normal-CDF mapping, and regimes.
- `src/open_global_liquidity/analysis/lead_lag.py` — market returns and signal/outcome alignment.
- `src/open_global_liquidity/analysis/correlations.py` — full-sample and rolling correlations.
- `src/open_global_liquidity/dashboard.py` — tested dashboard data loading and unit conversion.
- `src/open_global_liquidity/pipeline.py` — executable orchestration and Parquet output.
- `app/streamlit_app.py` — presentation-only Streamlit application.
- `tests/` — offline ingestion and configuration tests.

## OGLI methodology

OGLI is specified as `100 × Φ(MomentumScore)`, where the momentum score is
a configurable weighted composite of standardized 3-month annualized and 12-month year-over-year
growth. The current weights are 60% and 40%, respectively. The default historical mode uses
expanding z-scores with a 104-observation minimum history, so future
observations cannot rewrite earlier values. Full-sample normalization is research-only
because it contains look-ahead. OGLI will **not** use min-max normalization or represent liquidity
as a percentage of its historical maximum.

The weights and regime thresholds are configurable research assumptions, not empirically calibrated
parameters. OGLI is an independent Open Global Liquidity methodology and is not the proprietary
CrossBorder Capital GLI.

## Initial market-validation methodology

For each OGLI model, the pipeline compares the configured `momentum_score` with Bitcoin USD price
returns. Horizon zero is a one-week contemporaneous return; positive horizons are simple returns
through 4, 8, 12, 26, or 52 weeks. It retains two explicitly labeled timing views: an exploratory
observation-date alignment and an available-information alignment that delays the weekly OGLI
signal by one week. The lag is a configurable approximation for the Thursday publication of
Wednesday H.4.1 observations; it is not a real-time release-vintage database.

The dashboard defaults to non-overlapping outcome windows for robustness and retains the full
overlapping sample for comparison. Correlation tables include Fisher-transformed 95% confidence
intervals. Regime summaries report arithmetic mean, median, positive-return share, sample size, and
a classical Student-t 95% interval around the mean. These intervals assume the retained sample is
independent and identically distributed enough for descriptive inference; they are not forecast
intervals.

Forward returns are retrospective outcome variables and never OGLI inputs. The overlapping view has
dependent observations, while the non-overlapping view has materially smaller samples. Neither the
one-week availability assumption nor current-vintage FRED observations fully reproduce what an
investor knew historically. Correlation does not establish causation, and the results do not
calibrate OGLI weights or regimes.

The dashboard timeline places Bitcoin's unmodified USD price on a logarithmic axis beside OGLI's
unmodified 0-100 series. Sharing a chart and observation dates does not imply that either series
causes, predicts, or has been fitted to the other.

## Roadmap

The next market additions may include gold after its source and redistribution terms are verified.
Treasury yields, the 10-year-minus-2-year slope, and the broad dollar index are now available as
measured context but are not OGLI inputs. S&P 500 may return after appropriate public-display rights
are secured. Later versions may add global
central banks, FX conversion, collateral and repo proxies, shadow monetary base concepts, BIS
cross-border credit, and explicitly labeled public benchmark calibration.

## Limitations and disclaimer

This early version is an experimental normalized momentum index, not a trading model or investment
recommendation. It uses four nominal, non-seasonally-adjusted balance-sheet series standardized to
a weekly research frequency. Public data can be revised, delayed, discontinued, or unavailable.
Future statistical relationships will not by themselves establish causation. Users are responsible
for verifying data and conclusions.
