# v0.1.0 release checklist

## Automated verification

- [x] Python version is pinned to 3.12 and dependencies are locked with `uv.lock`.
- [x] `ruff format --check .` passes in GitHub Actions.
- [x] `ruff check .` passes in GitHub Actions.
- [x] The complete offline test suite passes in GitHub Actions.
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
- [ ] Decide whether to add `CITATION.cff` with the maintainer's preferred public name and contact.
- [ ] Approve creation of the `v0.1.0` Git tag and GitHub release.

The code license must not imply that third-party data is relicensed under the same terms. Until the
items above are resolved, `0.1.0` remains an unreleased project version.
