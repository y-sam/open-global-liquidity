# Changelog

All notable project changes are documented here. The project follows semantic versioning once a
release is tagged.

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

[0.2.0]: https://github.com/y-sam/open-global-liquidity/releases/tag/v0.2.0
[0.1.1]: https://github.com/y-sam/open-global-liquidity/releases/tag/v0.1.1
[0.1.0]: https://github.com/y-sam/open-global-liquidity/releases/tag/v0.1.0
