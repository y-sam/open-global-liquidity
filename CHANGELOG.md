# Changelog

All notable project changes are documented here. The project follows semantic versioning once a
release is tagged.

## [Unreleased]

### Added

- Keyless U.S. Treasury Fiscal Data provider for the Monthly Statement of the Public Debt Total
  Marketable debt-held-by-public stock.
- Configured Federal Reserve Treasury holdings, SOFR, effective federal funds rate, and 10-year
  Treasury yield inputs for an experimental US collateral pilot.
- Standalone Open Collateral Conditions Score with expanding, non-look-ahead normalization and
  configurable 40/30/30 component weights.
- Collateral dashboard page separating measured inputs, model assumptions, statistical
  transformations, and unimplemented haircut/reuse concepts.
- Frozen-model Bitcoin validation with predeclared timing sensitivities, overlapping and
  non-overlapping samples, Fisher intervals, and a deterministic moving-block bootstrap.
- Added measured MSPD composition for Treasury bills, notes, bonds, TIPS, and floating-rate notes.
  These series are displayed as supply context and do not alter the frozen collateral score.
- Added SOFR and TGCR transaction volumes and benchmark rates as measured repo-market
  context. They remain outside the frozen score pending robustness analysis.
- Added 2-, 5-, and 30-year Treasury yields and an equal-weight 2/5/10/30-year realized-volatility
  composite as an alternative diagnostic. The frozen score still uses its original 10-year input.
- Added a seven-specification collateral robustness laboratory covering alternative weights,
  curve volatility, leave-one-component-out tests, and 36-month rolling normalization. The grid
  was declared without inspecting Bitcoin outcomes and does not alter the frozen baseline.
- Documented the first signal-agreement result through July 2026: implementation variants track
  the baseline closely, while deleting an economic component causes materially larger divergence.
- Replaced the collateral study's blanket primary delay with source-specific assumed availability
  dates based on normal MSPD, H.4.1, New York Fed reference-rate, and Treasury-yield schedules.
  Zero-, one-, and two-month controls now mean additional delays after all inputs are available.

### Research boundary

- The collateral score remains separate from Global Model G. It is not an observed liquidity
  multiplier, does not use MOVE, and is not calibrated against Bitcoin or another asset. The
  primary Bitcoin estimate is documented as inconclusive: 21 observations, correlation +0.24,
  and 95% block-bootstrap interval -0.12 to +0.65 through July 2026.

## [0.3.0] — 2026-09-01

### Added

- Keyless BIS SDMX provider with exact-series, key, frequency, currency, and unit-multiplier
  validation.
- Redistributable monthly China central-bank total-assets snapshot from the BIS, while retaining
  the direct PBoC table as a local-only validation source.
- Four public-domain Federal Reserve H.10 spot exchange-rate inputs for EUR, JPY, GBP, and CNY.
- Configured balanced monthly currency normalization and a five-central-bank USD aggregate with
  source-date and FX-date lineage.
- Global aggregate dashboard page with level, growth, composition, and an auditable methodology
  table.
- Global Model G, an experimental 0–100 expanding-normalized momentum index of the five-bank USD
  aggregate, with configurable weights and regime thresholds.
- Monthly Model G versus subsequent Bitcoin comparisons across 1/3/6/12-month horizons, assumed
  0–3-month availability delays, and overlapping or non-overlapping samples.
- Model G selection across the liquidity-indices, Liquidity vs markets, Bitcoin research, and
  global-aggregate workspaces while retaining the three US/Fed research definitions.
- Versioned global source, detail, aggregate, market-pair, market-summary, and manifest snapshots
  for reproducible hosted deployment.

### Changed

- Extended the balanced global panel to monthly observations beginning in January 2002.
- Made Global Model G the default liquidity definition in the index and Bitcoin comparison
  workspaces; US Models A/B/C remain explicitly labeled alternatives.
- Reused one canonical Streamlit presentation for Model G/Bitcoin statistics so assumptions and
  provenance are consistent across pages.

### Research interpretation

- Current Model G/Bitcoin results are descriptive and sensitive to horizon, lag, and sampling
  policy. They do not establish a stable predictive relationship, causation, or an investable
  signal, and they were not used to calibrate Model G.

### Research boundary

- Global Model G is a current-vintage nominal central-bank-balance-sheet momentum proxy, not a
  complete global-liquidity index. Its availability-delay controls are assumptions because
  historical BIS release vintages have not been reconstructed.
- Model G contains no private-credit, shadow-bank, collateral, repo, FX-swap, or offshore-dollar
  components and does not reproduce CrossBorder Capital's proprietary methodology.

## [0.2.0] — 2026-08-29

### Added

- Keyless, cache-aware ECB Data Portal provider with exact-key, schema, and unit validation.
- Monthly total assets of the Eurosystem as the first non-US measured-data series.
- Separate euro-area Streamlit page with EUR levels, monthly and yearly changes, provenance, and
  explicit period-label and publication-timing limitations.
- Versioned ECB dashboard snapshot in the scheduled refresh and provenance manifest.
- Official BOJ Time-Series Data Search provider for `BS01.MABJMTA`, with a separate native-JPY
  Japan dashboard page and versioned snapshot.
- Official Bank of England database provider for quarterly consolidated total-assets series
  `RPQB75A`, with a separate native-GBP UK dashboard page, explicit five-quarter publication lag,
  and versioned snapshot.
- Keyless PBoC archive provider that discovers the official annual Balance Sheet of Monetary
  Authority tables, validates the bilingual title and unit, and extracts monthly Total Assets.
- Separate China dashboard page, with local data access and an explicit public-redistribution
  boundary based on the PBoC website legal notice.
- Cross-country central-bank page that independently rebases native-currency total-assets series
  to 100 without FX conversion, weighting, interpolation, or aggregation.

### Research boundary

- The US OGLI is unchanged. ECB, BOJ, BoE, and PBoC data are not frequency-aligned,
  currency-converted, weighted, aggregated, or interpreted as country liquidity models in this
  milestone. PBoC observations are not bundled publicly pending explicit redistribution permission.

## [0.1.1] — 2026-08-26

### Added

- Reproducible US public-data ingestion from FRED/ALFRED, Coin Metrics Community Data, and the
  World Bank Pink Sheet.
- Three transparent US liquidity definitions and expanding, non-look-ahead OGLI normalization.
- Weekly momentum, market-comparison, confidence-interval, subperiod, and macro-context outputs.
- Monthly sealed-vintage OGLI pilot with current-vintage revision diagnostics.
- Bitcoin-first research workspace covering forward returns, regimes, transitions, path risk,
  cross-horizon outcomes, and signal revisions.
- Predeclared primary Bitcoin specification: Model B, one-week assumed availability delay,
  non-overlapping samples, and 1/3/6/12-month horizons.
- Directional expansionary-minus-contractionary Bitcoin regime contrasts with Welch intervals and
  deterministic evidence-status labels.
- Streamlit dashboard with public bundled snapshots, provenance manifest, freshness checks, and
  automated GitHub Actions refreshes.
- Apache-2.0 licensing for original project code, with separate third-party data terms and
  source-specific attribution.

### Research interpretation

- Current primary directional contrasts are inconclusive at every estimable horizon.
- The 12-month primary contrast has insufficient expansionary observations for an interval.
- These results are retained as negative/uncertain evidence and are not used to recalibrate OGLI.

### Known limitations

- v0.1 covers the United States only and is not a global aggregate.
- The production OGLI remains a current-vintage index; the monthly ALFRED reconstruction is a
  research pilot rather than an exact tradable-signal database.
- Publication timing is represented by declared weekly delay assumptions, not intraday timestamps.
- Small samples, overlapping windows, revisions, and common macroeconomic drivers limit market
  interpretation.
- The project does not reproduce or claim access to CrossBorder Capital's proprietary methodology.

## [0.1.0] — 2026-08-25

### Added

- Initial tagged research snapshot, ending at commit `8c4bc5b`.

The historical `v0.1.0` tag predates the finalized code license, citation metadata, and release
audit. It is retained unchanged for reproducibility and is superseded by v0.1.1.

[Unreleased]: https://github.com/y-sam/open-global-liquidity/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/y-sam/open-global-liquidity/releases/tag/v0.3.0
[0.2.0]: https://github.com/y-sam/open-global-liquidity/releases/tag/v0.2.0
[0.1.1]: https://github.com/y-sam/open-global-liquidity/releases/tag/v0.1.1
[0.1.0]: https://github.com/y-sam/open-global-liquidity/releases/tag/v0.1.0
