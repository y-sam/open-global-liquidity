# Open Global Liquidity

**Release status:** v0.1.0 is release-candidate research software. See the
[changelog](CHANGELOG.md) and [release checklist](RELEASE_CHECKLIST.md). An open-source code license
and explicit third-party data notices must be finalized before the first formal release.

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

Additional point-in-time outcome series are:

- [World Bank Commodity Price Data (Pink Sheet)](https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/worldbank-commodities-price-data-the-pink-sheet):
  monthly-average gold price in nominal USD per troy ounce, redistributed with attribution under
  the World Bank dataset terms (default CC BY 4.0 for World Bank-produced open datasets);
- [`DTWEXBGS`](https://fred.stlouisfed.org/series/DTWEXBGS): daily nominal broad U.S. dollar index
  from Federal Reserve H.10 via FRED (public domain; citation requested).

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
have been empirically calibrated. The main weekly pipeline uses current-vintage FRED observations.
A separate local monthly pilot reconstructs OGLI from ALFRED information sets and never silently
replaces the published current-vintage index.

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
The same `FRED_API_KEY` also authorizes ALFRED historical-vintage requests; no separate ALFRED
account or key is required.

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
- `data/processed/us_liquidity_market_subperiods.parquet`: identical correlation diagnostics for
  the predeclared Pre-2020, 2020-2022, and 2023-present research periods.
- `data/processed/us_macro_context_*.parquet`: measured Treasury/dollar context and the transparent
  10-year-minus-2-year curve slope.

Weekly source series require an exact Wednesday observation. Daily ON RRP uses the latest available
observation on or before Wednesday, capped at seven calendar days. No balance-sheet values are
interpolated. These assumptions live in `config/model.yaml`.

### Capture an ALFRED as-of dataset

The separate vintage command downloads the four configured liquidity inputs exactly as ALFRED
reports them on a specified historical information date:

```zsh
uv run python -m open_global_liquidity.vintage_pipeline --as-of 2020-03-20
uv run python -m open_global_liquidity.vintage_pipeline --as-of 2020-03-20 --compare-current
```

It writes
`data/vintages/fred/as_of=2020-03-20/us_liquidity_vintage.parquet`. Each row keeps the observation
date, requested vintage date, ALFRED real-time bounds, provider metadata, and retrieval timestamp.
Different as-of dates use separate directories, and per-series vintage responses are cached under
`data/raw/fred/vintages/`. Both locations are ignored by Git because a historical vintage archive
can grow substantially.

This command is research infrastructure only: it does **not** yet calculate a vintage OGLI or
replace the published current-vintage pipeline. That separation prevents an as-of frame from being
silently mixed with revised current data. The optional comparison writes
`revision_comparison_to_current.parquet`, preserving both values and labeling each observation as
revised, unchanged, or missing from the current vintage. A difference identifies a revision but
does not infer its economic or methodological cause.

### Run the monthly point-in-time OGLI pilot

The point-in-time pilot fetches all configured US liquidity inputs in batched ALFRED requests,
recalculates weekly alignment, Models A/B/C, growth, and expanding OGLI independently inside every
month-end information set, and compares the result with today's calculation at the exact same
weekly signal observation date:

```zsh
uv run ogli-point-in-time
uv run ogli-point-in-time --publish-dashboard-snapshot
```

The configured pilot begins on 2021-01-31. `RRPONTSYD` has usable history only from December 2017,
and the index then needs 52 weeks for year-over-year growth plus 104 valid observations for its
expanding normalization. A bounded ALFRED probe found December 2020 to be the earliest month-end
with valid OGLI under the existing rules, so moving the production start earlier would add only one
month. A material extension would require weakening the declared history rule, which this project
does not do.

The command writes ten ignored local files under `data/vintages/fred/monthly_pilot/`: the long
ALFRED input archive, one monthly reading per model and information date, exact-date
current-vintage comparisons, standardized Bitcoin/gold/dollar levels, point-in-time outcome pairs,
descriptive market summaries, Bitcoin path outcomes, regime/transition summaries, directional
regime contrasts, and vintage-versus-revised signal diagnostics. Raw multi-vintage responses are cached under
`data/raw/fred/vintage_batches/`. These files are reproducible but intentionally not committed.
The explicit publication option writes the small derived comparison and market-research files to
`data/reference/`; it does not publish the raw ALFRED archive. The pilot does not reconstruct
intraday release timestamps or exact trade availability. Instead, it reports predeclared 0-, 1-,
2-, and 4-week availability-delay assumptions, so it is not a strict tradable-signal backtest.

The raw cache is reused for 24 hours by default. `--force-refresh` bypasses it. Generated data is
intentionally excluded from Git because it is reproducible from the public API.

The publication commands together write twenty-two Git-versioned Parquet
artifacts plus a JSON provenance manifest:

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
- `data/reference/us_liquidity_market_subperiods_snapshot.parquet` — correlation stability across
  predeclared Bitcoin research periods.
- `data/reference/us_macro_context_series_snapshot.parquet` — standardized measured macro sources.
- `data/reference/us_macro_context_weekly_snapshot.parquet` — Wednesday-aligned context data.
- `data/reference/us_macro_context_indicators_snapshot.parquet` — yields, curve slope, and broad
  dollar index for dashboard presentation.
- `data/reference/us_point_in_time_comparison_snapshot.parquet` — derived monthly vintage/current
  OGLI comparisons; raw ALFRED observations remain excluded.
- `data/reference/us_point_in_time_market_series_snapshot.parquet` — standardized public Bitcoin,
  World Bank monthly-average gold, and broad-dollar outcome levels.
- `data/reference/us_point_in_time_market_pairs_snapshot.parquet` — vintage OGLI signals paired
  with subsequent 1-, 3-, 6-, and 12-month returns under four availability-delay assumptions.
- `data/reference/us_point_in_time_market_summary_snapshot.parquet` — correlations, sample sizes,
  mean/median returns, and positive-return shares for overlapping and non-overlapping samples.
- `data/reference/us_point_in_time_bitcoin_outcomes_snapshot.parquet` — point-in-time signals,
  forward Bitcoin returns, maximum upside/downside, peak-to-trough drawdown, and revision labels.
- `data/reference/us_point_in_time_bitcoin_regimes_snapshot.parquet` — cross-horizon return and
  path-risk summaries plus descriptive Student-t mean-return intervals overall, by point-in-time
  OGLI regime, and by expansionary/contractionary transition direction.
- `data/reference/us_point_in_time_bitcoin_revisions_snapshot.parquet` — real-time-vintage versus
  recomputed-today signal correlations, regime agreement, and revision magnitudes.
- `data/reference/us_point_in_time_bitcoin_contrasts_snapshot.parquet` — predeclared directional
  regime comparisons reporting expansionary and contractionary Bitcoin outcomes, their arithmetic
  mean spread, group sample sizes, and a descriptive Welch interval.
- `data/reference/dashboard_snapshot_manifest.json` — generation time, pipeline version, source
  commit, row/date coverage, and SHA-256 digest for every published Parquet file.

These small artifacts let the hosted dashboard run without local processed data, a `.env` file, a
FRED key, or a download on every visitor session. Publishing snapshots is an explicit maintainer
action. Review the generated files before committing them; the dashboard displays the active data
mode and source retrieval time.

### Automated weekly refresh

The `Refresh public dashboard data` GitHub Actions workflow runs every Friday at 12:00 UTC and can
also be started manually from the repository's **Actions** tab. It installs the locked Python 3.12
environment, downloads fresh FRED, ALFRED, Coin Metrics, and World Bank observations, regenerates
the twenty-two public Parquet snapshots and provenance manifest, and runs formatting, linting, and
offline tests. Only successful runs can commit changed
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
uv run ogli-point-in-time
uv run streamlit run app/streamlit_app.py
```

Streamlit opens the dashboard at `http://localhost:8501`. The app shows latest measured balances,
the three model levels, an OGLI page, a point-in-time pilot, a dedicated Bitcoin research page with
cross-horizon comparison, a
Liquidity vs markets workspace, a log-scale Bitcoin/OGLI timeline, Bitcoin-focused landing metrics,
history, a component explorer, recent source
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
- `src/open_global_liquidity/analysis/bootstrap.py` — deterministic moving-block correlation
  intervals.
- `src/open_global_liquidity/analysis/revisions.py` — ALFRED-versus-current revision comparisons.
- `src/open_global_liquidity/analysis/subperiods.py` — predeclared Bitcoin stability diagnostics.
- `src/open_global_liquidity/provenance.py` — snapshot hashes and point-in-time manifest metadata.
- `src/open_global_liquidity/vintage_pipeline.py` — explicit local ALFRED as-of capture.
- `src/open_global_liquidity/point_in_time.py` — sealed-vintage OGLI and exact-date comparison.
- `src/open_global_liquidity/point_in_time_pipeline.py` — monthly ALFRED pilot orchestration.
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
intervals and deterministic circular moving-block bootstrap intervals. The dashboard uses the
bootstrap interval for correlation error bars because contiguous block resampling preserves some
local time dependence that an IID calculation would discard. The current 1,000 resamples,
eight-observation block length, and seed are declared in `config/model.yaml`; they are research
assumptions, not calibrated parameters. In a non-overlapping sample, eight retained observations
can span far more than eight calendar weeks. Regime summaries report arithmetic mean, median,
positive-return share, sample size, and a classical Student-t 95% interval around the mean. None of
these intervals are forecast intervals.

The same calculation is repeated over three date partitions declared in `config/model.yaml`:
Pre-2020, 2020-2022, and 2023-present. Membership is based on the liquidity observation date, and
non-overlapping windows are reselected inside each partition. These boundaries are research
assumptions chosen for interpretable cycle comparisons, not change points fitted to maximize
Bitcoin correlation. Small samples, wide confidence intervals, and unstable signs are expected and
must remain visible.

Forward returns are retrospective outcome variables and never OGLI inputs. The overlapping view has
dependent observations, while the non-overlapping view has materially smaller samples. Neither the
one-week availability assumption nor current-vintage FRED observations fully reproduce what an
investor knew historically. Correlation does not establish causation, and the results do not
calibrate OGLI weights or regimes.

The monthly ALFRED pilot now implements a scheduled month-end grid and calculates every model
separately inside each sealed information set. It compares historical and current-vintage results
only at the same weekly signal date. It also compares the vintage momentum score with subsequent
Bitcoin, gold, and broad-dollar returns over 1, 3, 6, and 12 months. The predeclared 0-, 1-, 2-, and
4-week delays test sensitivity to assumed signal usability; they do not claim to reconstruct exact
release timestamps. Gold is the World Bank Pink Sheet monthly average, not a spot or month-end
fixing. A positive dollar return means dollar strength and is never sign-inverted to improve fit.
Both overlapping and mechanically non-overlapping samples are retained. Correlations require at
least 12 overlapping observations or 8 non-overlapping observations; the lower non-overlapping
threshold preserves a limited view of six-month outcomes while keeping sparser estimates hidden
and explicitly warning that small samples are fragile. A stricter investable
backtest still requires source-specific publication timestamps and availability rules; the
published index therefore remains clearly labeled current-vintage.

### Primary Bitcoin research specification

The landing page emphasizes a predeclared point-in-time Bitcoin specification: **Model B — Net Fed
liquidity proxy**, a **one-week assumed availability delay**, **non-overlapping outcome windows**,
and **1-, 3-, 6-, and 12-month horizons**. This designation is stored in `config/model.yaml`,
validated by the package, and attached to the published summary rows as a `model_assumption`.

This is a presentation and interpretation policy, not an empirical calibration. It was selected to
use the commonly discussed net-liquidity proxy, allow a conservative delay between observation and
signal use, and reduce dependence between outcome windows. All other models, delays, and the larger
overlapping samples remain visible as robustness checks. Bitcoin outcomes never enter the OGLI
calculation, and the primary designation does not imply forecast validity or investment utility.

The primary landing-page comparison reports the mean Bitcoin return after expansionary
point-in-time regimes minus the mean after contractionary point-in-time regimes. `Above normal`,
`Expansion`, and `Strong expansion` form the expansionary group; `Below normal`, `Contraction`, and
`Strong contraction` form the contractionary group; `Neutral` observations are excluded. This
grouping is a declared `model_assumption`. The spread's classical Welch interval permits unequal
group variances but does not correct for serial dependence, multiple comparisons, revisions, or
small-sample selection. An interval crossing zero is not evidence of a stable directional
relationship, and no contrast is used to calculate or calibrate OGLI.
The package assigns a deterministic interval status: `positive_interval` when the full interval is
above zero, `negative_interval` when it is below zero, `inconclusive` when it crosses zero, and
`insufficient_sample` when either group cannot support an interval. This status is a statistical
transformation of the reported interval, not a new hypothesis test or calibrated threshold.

Published snapshots are auditable at the bundle level through
`data/reference/dashboard_snapshot_manifest.json`. Its generation timestamp is distinct from each
series' observation and retrieval timestamps. The manifest's source commit identifies the code used
for the run, while SHA-256 hashes detect any later byte-level change. This integrity record does not
solve the separate current-vintage/revision limitation.

The dashboard timeline places Bitcoin's unmodified USD price on a logarithmic axis beside OGLI's
unmodified 0-100 series. Sharing a chart and observation dates does not imply that either series
causes, predicts, or has been fitted to the other.

## Roadmap

Bitcoin is the primary market comparison. Gold now uses the World Bank Pink Sheet monthly dataset,
and the Federal Reserve broad dollar index is included without changing its sign. Both remain
outcome/context variables rather than OGLI inputs. Treasury yields and the 10-year-minus-2-year
slope remain measured context. S&P 500 may return after appropriate public-display rights are
secured. Later versions may add global
central banks, FX conversion, collateral and repo proxies, shadow monetary base concepts, BIS
cross-border credit, and explicitly labeled public benchmark calibration.

## Limitations and disclaimer

This early version is an experimental normalized momentum index, not a trading model or investment
recommendation. It uses four nominal, non-seasonally-adjusted balance-sheet series standardized to
a weekly research frequency. Public data can be revised, delayed, discontinued, or unavailable.
Future statistical relationships will not by themselves establish causation. Users are responsible
for verifying data and conclusions.
