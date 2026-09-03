# Research and production readiness audit

This document records the current development boundary rather than assigning the project a claim of
scientific completeness. It separates what is operational from what still requires research.

## Operational now

- Automated, versioned ingestion from FRED, BIS, ECB, BOJ, BoE, Treasury Fiscal Data, Coin Metrics,
  and the World Bank, with source-specific validation and local caching.
- A balanced five-central-bank monthly USD aggregate and expanding, non-look-ahead Global Model G.
- Separate collateral, offshore-dollar credit, and US bank/MMF private-liquidity layers. Each is
  classified as a model assumption and none is silently incorporated into Model G.
- Bitcoin outcome analysis with predeclared horizons, publication-delay sensitivities,
  overlapping/non-overlapping samples, subperiod checks, and uncertainty intervals where supported.
- A hosted dashboard backed by tracked Parquet snapshots and a SHA-256 provenance manifest.
- Offline lint, formatting, unit, integration, and hosted-snapshot tests.

## Research limits that remain

- Global Model G is a central-bank-balance-sheet momentum measure, not yet a complete global
  liquidity system. It does not include private credit, offshore dollar credit, or collateral as a
  fitted multiplier.
- The global central-bank panel uses current vintages. Exact historical release and revision
  information is not reconstructed for every non-US source.
- The collateral/Bitcoin non-overlapping primary sample remains small and its interval includes
  zero. It is therefore documented as inconclusive rather than promoted into the main index.
- The offshore-dollar and private-liquidity layers still require frozen, predeclared Bitcoin
  validation before any broader composite is justified.
- Nominal balance-sheet aggregation does not measure collateral reuse, credit quality, haircuts,
  bank capital constraints, or all shadow-bank leverage.

## Gate for a broader model

A future broader global model should be introduced only after its component set, timing policy,
frequency alignment, weights, normalization, missing-data policy, and validation plan are committed
before inspecting the final market results. Any empirically chosen parameter must be labeled
`calibrated_parameter`; assumed weights must remain labeled `model_assumption`.

## Current assessment

Engineering and public reproducibility are strong for a research prototype. The largest remaining
gap is economic breadth validated with point-in-time information, not dashboard polish. The next
highest-value work is therefore a frozen offshore-dollar/private-liquidity validation study, followed
by an explicitly experimental broader composite only if the evidence and data timing support it.
