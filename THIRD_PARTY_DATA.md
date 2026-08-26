# Third-party data terms and attribution

The Apache License 2.0 in `LICENSE` applies to original Open Global Liquidity **code and
documentation only**. It does not grant rights in third-party observations, metadata, names, or
trademarks. Downloading, transforming, aggregating, or storing a source series in Parquet does not
replace its original terms.

This file records the sources used by v0.1 and is not legal advice. Users and redistributors remain
responsible for checking the current source terms for their intended use.

## FRED and ALFRED

The pipeline accesses FRED and ALFRED through the Federal Reserve Bank of St. Louis API. The
[FRED API Terms of Use](https://fred.stlouisfed.org/docs/api/terms_of_use.html) state that series can
be owned by third parties and that API access does not override source-owner restrictions.

Required application notice:

> This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of
> St. Louis.

The application links to the FRED API terms. FRED®, ALFRED®, and Federal Reserve Bank names and
marks are not licensed under Apache-2.0.

### Series used in v0.1

| Series | Original source | FRED rights label | Requested attribution |
|---|---|---|---|
| `WALCL` | Board of Governors of the Federal Reserve System, H.4.1 | Public Domain: Citation Requested | Board of Governors of the Federal Reserve System (US), `WALCL`, retrieved from FRED, Federal Reserve Bank of St. Louis |
| `WDTGAL` | Board of Governors of the Federal Reserve System, H.4.1 | Public Domain: Citation Requested | Board of Governors of the Federal Reserve System (US), `WDTGAL`, retrieved from FRED, Federal Reserve Bank of St. Louis |
| `WRBWFRBL` | Board of Governors of the Federal Reserve System, H.4.1 | Public Domain: Citation Requested | Board of Governors of the Federal Reserve System (US), `WRBWFRBL`, retrieved from FRED, Federal Reserve Bank of St. Louis |
| `DGS10` | Board of Governors of the Federal Reserve System, H.15 | Public Domain: Citation Requested | Board of Governors of the Federal Reserve System (US), `DGS10`, retrieved from FRED, Federal Reserve Bank of St. Louis |
| `DGS2` | Board of Governors of the Federal Reserve System, H.15 | Public Domain: Citation Requested | Board of Governors of the Federal Reserve System (US), `DGS2`, retrieved from FRED, Federal Reserve Bank of St. Louis |
| `DTWEXBGS` | Board of Governors of the Federal Reserve System, H.10 | Public Domain: Citation Requested | Board of Governors of the Federal Reserve System (US), `DTWEXBGS`, retrieved from FRED, Federal Reserve Bank of St. Louis |
| `RRPONTSYD` | Federal Reserve Bank of New York | Copyrighted: Citation Required | Federal Reserve Bank of New York, `RRPONTSYD`, retrieved from FRED, Federal Reserve Bank of St. Louis |

The rights labels above were reviewed on 2026-08-26. Each series page linked from
`config/series.yaml` is the controlling source for current notes and attribution. The repository
preserves provider, series identifier, retrieval time, unit, and frequency with standardized
observations.

## Coin Metrics Community Data

Bitcoin `btc.PriceUSD` comes from the keyless Coin Metrics Community API. Coin Metrics publishes
its community archive under
[Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/).
That license requires attribution, a license link, and an indication of changes, and limits use to
non-commercial purposes.

Attribution: Coin Metrics Community Data, `btc.PriceUSD`, transformed by Open Global Liquidity from
daily USD levels into weekly levels, returns, paired research samples, and aggregate statistics.

The hosted project is independent, non-commercial research. Anyone wishing to use the Bitcoin
observations or derived snapshots commercially must determine whether separate permission or a
commercial Coin Metrics license is required. Apache-2.0 does not remove this restriction.

## World Bank Commodity Price Data

Gold observations come from the World Bank Commodity Price Data (Pink Sheet), series
`CMO-GOLD-MONTHLY`. The World Bank's
[Data Access and Licensing](https://datacatalog.worldbank.org/public-licenses) page states that
CC BY 4.0, with its additional dataset terms, is the default for World Bank-produced open datasets
unless a dataset is labeled otherwise.

Attribution: World Bank Prospects Group, Commodity Price Data (The Pink Sheet), monthly gold price;
transformed by Open Global Liquidity for weekly research alignment and forward-return summaries.
Users should confirm the dataset's current metadata and additional World Bank terms before reuse.

## Bundled snapshots

Files under `data/reference/` are reproducibility artifacts, not Apache-2.0 data releases. They can
contain source observations, transformations, and statistics derived from one or more sources
above. Their inclusion in this repository does not change the underlying terms. In particular,
artifacts containing Coin Metrics observations or transformations remain subject to its
non-commercial condition.

The snapshot manifest records generation time, code commit, coverage, and SHA-256 hashes. These
fields support provenance but do not constitute a new license grant.
