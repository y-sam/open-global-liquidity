# Third-party data terms and attribution

The Apache License 2.0 in `LICENSE` applies to original Open Global Liquidity **code and
documentation only**. It does not grant rights in third-party observations, metadata, names, or
trademarks. Downloading, transforming, aggregating, or storing a source series in Parquet does not
replace its original terms.

This file records the sources used by the project and is not legal advice. Users and redistributors remain
responsible for checking the current source terms for their intended use.

## European Central Bank

The v0.2a pilot obtains `BSI.M.U2.N.C.T00.A.1.Z5.0000.Z01.E`, total assets of the
Eurosystem, from the public ECB Data Portal API. The
[ESCB statistics reuse policy](https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html)
permits free reuse of publicly released ESCB statistics when the source is quoted, applicable
disclaimers are respected, and third-party data are excluded unless separately permitted. The
[ECB disclaimer and copyright page](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html)
also requires accurate reproduction, ECB attribution, and an explicit statement when information
has been modified.

Attribution: Source: ECB statistics, ECB Data Portal, total assets of the Eurosystem, series
`BSI.M.U2.N.C.T00.A.1.Z5.0000.Z01.E`. Open Global Liquidity changes the monthly period label to a
calendar month-end timestamp and divides reported EUR millions by 1,000 for dashboard display in
EUR billions; source values remain available in the standardized Parquet artifact.

## Bank of Japan

The v0.2b pilot obtains Bank of Japan Accounts total assets from database `BS01`, series
`MABJMTA`, through the public BOJ Time-Series Data Search API. The
[BOJ API manual](https://www.stat-search.boj.or.jp/info/api_manual_en.pdf) describes the keyless
JSON and CSV interfaces. The
[API use notice](https://www.stat-search.boj.or.jp/info/api_notice_en.pdf) asks a released service
to acknowledge its use of the BOJ API, disclaim any BOJ guarantee of the service content, and
notify the BOJ Research and Statistics Department when the service is released.

Application credit: This service uses the Bank of Japan Time-Series Data Search API. The Bank of
Japan does not guarantee this service's content.

Attribution: Bank of Japan, Bank of Japan Accounts, total assets, database `BS01`, series
`MABJMTA`. Open Global Liquidity maps monthly survey periods to calendar month-end timestamps and
converts source values from 100 million yen to JPY billions for display. The original source units
remain in the standardized Parquet artifact. The Bank of Japan is not affiliated with or
responsible for Open Global Liquidity.

## Bank of England

The v0.2c pilot obtains quarterly consolidated central-bank total assets/liabilities, series
`RPQB75A`, from the public Bank of England Statistical Interactive Database. The Bank's
[legal terms](https://www.bankofengland.co.uk/legal) state that reproduction of Database data is
subject to the UK Open Government Licence, except where otherwise stated. The selected total-assets
series is not one of the exchange-rate datasets identified by the Bank as potentially containing
third-party rights.

Attribution: Bank of England, Statistical Interactive Database, quarterly amounts outstanding of
Central Bank assets/liabilities total, series `RPQB75A`. The complete balance sheet is published
with a five-quarter lag. Open Global Liquidity divides source GBP millions by 1,000 for dashboard
display in GBP billions; the standardized Parquet artifact retains the source unit. The Bank of
England is not affiliated with or responsible for Open Global Liquidity.

## People's Bank of China

The v0.2d pilot reads the `Total Assets` row from the official monthly Balance Sheet of Monetary
Authority, published in 100 million yuan. The PBoC does not provide a stable series API: the
provider discovers each annual Money and Banking Statistics page and verifies the exact bilingual
table title and unit before extraction. `PBOC.BSMA.TOTAL_ASSETS` is a project identifier, not an
official PBoC series code.

The [PBoC legal notice](https://www.pbc.gov.cn/rmyh/109345/index.html) states that website materials
are PBoC copyright unless otherwise noted and describes permission and attribution requirements for
downloaded reuse. It also says the Chinese version controls over the English version. Consequently,
this repository does **not** bundle or redistribute PBoC observations or a China snapshot. The
provider and transformations are open-source code; users may generate a local research cache from
the public archive and remain responsible for obtaining any permission required for their use.

Local attribution: People's Bank of China, Money and Banking Statistics, Balance Sheet of Monetary
Authority, Total Assets. Open Global Liquidity maps monthly labels to calendar month-end timestamps
and divides 100 million yuan by 10 for local display in CNY billions. No PBoC data is used in OGLI.

## Bank for International Settlements

The public China dashboard uses `M.CN.B.XDC.CNY.N`. Global Model G uses the monthly BIS-spliced
domestic-currency Central Bank Total Assets series for the United States, euro area, Japan, United
Kingdom, and China: `M.US.B.XDC.USD.N`, `M.XM.B.XDC.EUR.N`, `M.JP.B.XDC.JPY.N`,
`M.GB.B.XDC.GBP.N`, and `M.CN.B.XDC.CNY.N`. The China metadata says that from January 2002 it uses
the monthly PBoC balance sheet.
The [BIS permitted-use terms](https://data.bis.org/help/legal) state that use of BIS statistics is
unrestricted when the BIS is cited, presentation is not misleading or suggestive of endorsement,
and the other stated conditions are observed. The [dataset overview](https://data.bis.org/topics/CBTA)
documents coverage, units, frequency, and compilation concepts.

Attribution: Bank for International Settlements, Central bank total assets, monthly domestic
currency, BIS-spliced, the five exact series listed above. Open Global Liquidity maps monthly
periods to calendar month-end timestamps and converts native-currency billions to USD using named
H.10 inputs. The BIS is not affiliated with this project, and the series are not investment advice.
The direct PBoC extraction remains local-only and is used only as a research validation source.

## U.S. Treasury Fiscal Data

The v0.4a collateral pilot obtains the `Total Marketable` row from table 1 of the Monthly Statement
of the Public Debt through the keyless U.S. Treasury Fiscal Data API. It uses the
`debt_held_public_mil_amt` field, reported monthly in millions of U.S. dollars. Treasury describes
this category as debt held outside the United States Government and notes that it includes Federal
Reserve Banks. Open Global Liquidity subtracts separately measured Fed Treasury holdings only in a
derived model-assumption layer; it does not alter the source observation.

The v0.4b composition view also obtains the exact `Marketable` rows for Bills, Notes, Bonds,
Treasury Inflation-Protected Securities, and Floating Rate Notes. These measured par-value stocks
are displayed without security-class weights and are not new inputs to the collateral score.

Attribution: U.S. Department of the Treasury, Bureau of the Fiscal Service, Monthly Statement of
the Public Debt, Summary of Treasury Securities Outstanding, Total Marketable, debt held by the
public. The Treasury source is not affiliated with and does not endorse Open Global Liquidity.

## New York Fed reference-rate data

The v0.4a collateral pilot uses SOFR as a measured reference rate and transforms it into a monthly
median spread over the effective federal funds rate. Under the New York Fed Terms of Use, reference
rate content may be used, copied, distributed, and modified subject to its attribution,
modification-labeling, pass-through, and non-endorsement conditions.

The v0.4b repo-context view also displays SOFR, TGCR, and BGCR benchmark rates and their published
underlying transaction volumes. Open Global Liquidity transforms daily observations to monthly
medians for display and does not describe those volumes as the total repo market.

Required notice: The Secured Overnight Financing Rate data are subject to the Terms of Use posted
at newyorkfed.org. The New York Fed is not responsible for publication of the SOFR data by Open
Global Liquidity, does not sanction or endorse this republication, and has no liability for its
use. Open Global Liquidity is not affiliated with the New York Fed. The SOFR data include inputs
licensed to the New York Fed by DTCC Solutions LLC; those parties have no liability for this
material. Derived monthly spreads and collateral scores are clearly identified as Open Global
Liquidity transformations rather than New York Fed publications.

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
| `DEXUSEU` | Board of Governors of the Federal Reserve System, H.10 | Public Domain: Citation Requested | Board of Governors of the Federal Reserve System (US), `DEXUSEU`, retrieved from FRED, Federal Reserve Bank of St. Louis |
| `DEXJPUS` | Board of Governors of the Federal Reserve System, H.10 | Public Domain: Citation Requested | Board of Governors of the Federal Reserve System (US), `DEXJPUS`, retrieved from FRED, Federal Reserve Bank of St. Louis |
| `DEXUSUK` | Board of Governors of the Federal Reserve System, H.10 | Public Domain: Citation Requested | Board of Governors of the Federal Reserve System (US), `DEXUSUK`, retrieved from FRED, Federal Reserve Bank of St. Louis |
| `DEXCHUS` | Board of Governors of the Federal Reserve System, H.10 | Public Domain: Citation Requested | Board of Governors of the Federal Reserve System (US), `DEXCHUS`, retrieved from FRED, Federal Reserve Bank of St. Louis |
| `RRPONTSYD` | Federal Reserve Bank of New York | Copyrighted: Citation Required | Federal Reserve Bank of New York, `RRPONTSYD`, retrieved from FRED, Federal Reserve Bank of St. Louis |

The rights labels above were reviewed on 2026-08-30. Each series page linked from
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
