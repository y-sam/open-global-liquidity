# Release checklist

## v0.3.0 global aggregation milestone

- [x] Five exact BIS central-bank total-assets series and four H.10 FX inputs are configured with
      explicit identifiers, units, quote conventions, and staleness limits.
- [x] The aggregate uses balanced monthly period-end observations, never interpolates, and retains
      source-date and FX-date lineage.
- [x] Global Model G is classified as an experimental statistical transformation with configurable
      momentum weights and regime thresholds.
- [x] Model G is available across the liquidity-index and Bitcoin research workspaces while the
      three US/Fed definitions remain separately labeled.
- [x] Model G/Bitcoin comparisons expose lag, horizon, and sample-policy sensitivity and do not feed
      market outcomes into the index.
- [x] BIS, Federal Reserve H.10, and Coin Metrics reuse terms and attribution are documented
      separately from the Apache-2.0 code license.
- [x] Public global source, detail, aggregate, Bitcoin-pair, Bitcoin-summary, and provenance
      snapshots are included in the scheduled refresh workflow.
- [x] The current-vintage and incomplete-global-liquidity limitations are visible in code,
      configuration, documentation, and the dashboard.
- [x] The v0.3.0 release candidate passes GitHub Actions and the hosted Model G workspaces are
      verified.

## v0.2.0 international measured-data milestone

- [x] ECB, BOJ, BoE, and PBoC providers validate exact source definitions and native units.
- [x] Country series remain separate from the US OGLI and from one another.
- [x] The central-bank comparison independently rebases native-currency levels and does not
      aggregate them.
- [x] Public snapshot rights are documented source by source.
- [x] PBoC observations are excluded from public snapshots pending explicit reuse permission.
- [x] Offline provider, pipeline, dashboard, and configuration tests cover the v0.2 additions.
- [x] GitHub Actions and the hosted Central banks and China pages are verified at the v0.2.0
      release commit.

## v0.1.1 release checklist

## Automated verification

- [x] Python version is pinned to 3.12 and dependencies are locked with `uv.lock`.
- [x] `ruff format --check .` passes in GitHub Actions.
- [x] `ruff check .` passes in GitHub Actions.
- [x] The complete offline test suite passes in GitHub Actions.
- [x] Push and pull-request verification is defined in `.github/workflows/ci.yml`.
- [x] The production refresh regenerates all public dashboard snapshots.
- [x] The snapshot manifest records code commit, generation time, row coverage, and SHA-256 hashes.
- [x] The hosted Streamlit landing page and Bitcoin research workspace have been manually checked.

## Research audit

- [x] Measured data, model assumptions, and statistical transformations are labeled separately.
- [x] The primary Bitcoin specification is declared in `config/model.yaml`.
- [x] Alternative models, lags, horizons, and overlapping samples remain available as robustness
      checks.
- [x] Current inconclusive and insufficient-sample results remain visible.
- [x] No market outcome is used to calculate or calibrate OGLI.
- [x] OGLI is clearly distinguished from CrossBorder Capital's proprietary GLI.

## Maintainer decisions required before tagging

- [x] Choose and add the repository's open-source **code license** (Apache-2.0).
- [x] Review and document the separate redistribution terms for every bundled data snapshot in
      `THIRD_PARTY_DATA.md`.
- [x] Add `CITATION.cff` with the maintainer-approved public name and contact.
- [x] Approve creation of the `v0.1.1` Git tag and GitHub release.

The code license does not imply that third-party data are relicensed under the same terms. The
completed items above constitute maintainer approval to tag and publish `v0.1.1` after automated
verification passes.
