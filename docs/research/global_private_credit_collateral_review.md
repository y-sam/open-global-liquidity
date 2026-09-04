# Global private-credit and collateral source review

**Review date:** 2026-09-04  
**Classification:** source-selection research; no calibrated parameters

## Integrated now

The BIS Global Liquidity Indicators provide quarterly bank-loan and international-debt-security
credit to non-bank borrowers by currency. BIS describes these indicators as tracking financing in
the three major reserve currencies to borrowers outside the respective currency areas. Its
statistics may be reused with attribution, without implying BIS endorsement.

The project therefore integrates these exact public API series:

- `Q.USD.3P.N.A.I.B.USD` — USD credit outside the United States;
- `Q.EUR.3P.N.A.I.B.EUR` — EUR credit outside the euro area;
- `Q.JPY.3P.N.A.I.B.JPY` — JPY credit outside Japan.

Only the established USD series drives the Offshore Dollar Credit Momentum Index and frozen Model
H. EUR and JPY remain separately rebased context. Native-currency amounts are never summed.

## Deferred private-credit candidates

BIS credit-to-the-non-financial-sector, locational banking, and debt-securities datasets are
machine-accessible and reuse-compatible. They are promising, but overlap materially with existing
GLI bank-loan and bond components. Exact borrower-sector and instrument decompositions must be
specified before ingestion to prevent double counting.

## Deferred collateral candidates

No sufficiently harmonized, high-frequency, global public series for repo haircuts, collateral
reuse, or dealer balance-sheet capacity was identified. The FSB's global non-bank monitoring data
are valuable annual structural context, while its government-bond repo review explicitly discusses
international data gaps. Annual aggregates should not be mixed mechanically into the current
monthly or quarterly liquidity scores.

The US collateral score therefore remains separate. A global collateral multiplier will require a
predeclared country panel, common definitions, usable release histories, and explicit missing-data
rules before implementation.

## Primary sources

- [BIS Global Liquidity Indicators](https://data.bis.org/topics/GLI)
- [BIS terms of permitted use](https://data.bis.org/help/legal)
- [BIS credit to the non-financial sector](https://data.bis.org/topics/TOTAL_CREDIT/data)
- [BIS bulk downloads](https://data.bis.org/bulkdownload)
- [FSB Global Monitoring Report on NBFI 2025](https://www.fsb.org/2025/12/global-monitoring-report-on-nonbank-financial-intermediation-2025/)
- [FSB government bond-backed repo review](https://www.fsb.org/2026/02/vulnerabilities-in-government-bond-backed-repo-markets/)
