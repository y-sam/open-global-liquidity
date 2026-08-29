from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from open_global_liquidity.config import SeriesDefinition
from open_global_liquidity.data.pboc import (
    PBOC_STATISTICS_INDEX_URL,
    PbocError,
    PbocProvider,
    _decode_html,
    _discover_balance_sheet_url,
    _discover_money_pages,
    _parse_balance_sheet_table,
)


def _definition() -> SeriesDefinition:
    return SeriesDefinition(
        country="CN",
        group="liquidity",
        name="pboc_total_assets",
        classification="measured_data",
        provider="pboc",
        series_id="PBOC.BSMA.TOTAL_ASSETS",
        component="pboc_total_assets",
        title="PBoC total assets",
        description="Measured test data",
        unit="100 Million Yuan",
        frequency="Monthly, End of Period",
        seasonal_adjustment="Not Seasonally Adjusted",
        start=date(2025, 1, 31),
        source="PBoC",
        source_url=PBOC_STATISTICS_INDEX_URL,
    )


def test_discovers_annual_money_pages_and_exact_balance_sheet_link() -> None:
    index = """
    <a href='/2024/index.html'>2024年统计数据</a>
    <a href='/2024/money/index.html'>货币统计概览</a>
    <a href='/2025/index.html'>2025年统计数据</a>
    <a href='/2025/money/index.html'>货币统计概览</a>
    """
    pages = _discover_money_pages(index, start_year=2025)
    assert pages == {2025: "https://www.pbc.gov.cn/2025/money/index.html"}

    money_page = """
    <table><tr><td>货币当局资产负债表<br>Balance Sheet of Monetary Authority</td>
    <td><a href='/tables/authority.htm'>htm</a></td>
    <td><a href='/tables/authority.xlsx'>xls</a></td></tr></table>
    """
    assert _discover_balance_sheet_url(money_page, pages[2025]) == (
        "https://www.pbc.gov.cn/tables/authority.htm"
    )


def test_parses_only_published_total_assets_months() -> None:
    table = """
    <table>
      <tr><td>Unit: 100 Million Yuan</td></tr>
      <tr><td>项目 Item</td><td>2025.01</td><td>2025.02</td><td>2025.03</td></tr>
      <tr><td>国外资产 Foreign Assets</td><td>1</td><td>2</td><td></td></tr>
      <tr><td>总资产 Total Assets</td><td>400,000.25</td><td>401000.5</td><td></td></tr>
    </table>
    """
    result = _parse_balance_sheet_table(table, "https://example.com/table.htm", 2025)

    assert result["date"].tolist() == [pd.Timestamp("2025-01-31"), pd.Timestamp("2025-02-28")]
    assert result["value"].tolist() == [400_000.25, 401_000.5]
    assert result["source_url"].unique().tolist() == ["https://example.com/table.htm"]


def test_fetch_definition_uses_archive_discovery_and_standardizes(tmp_path: Path) -> None:
    index = """
    <a href='/2025/index.html'>2025年统计数据</a>
    <a href='/2025/money/index.html'>货币统计概览</a>
    """
    money_page = """
    <table><tr><td>货币当局资产负债表 Balance Sheet of Monetary Authority</td>
    <td><a href='/2025/authority.htm'>htm</a></td></tr></table>
    """
    table = """
    <table><tr><td>Unit: 100 Million Yuan</td></tr>
    <tr><td>项目 Item</td><td>2025.01</td><td>2025.02</td></tr>
    <tr><td>总资产 Total Assets</td><td>400000</td><td>410000</td></tr></table>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        responses = {
            PBOC_STATISTICS_INDEX_URL: index,
            "https://www.pbc.gov.cn/2025/money/index.html": money_page,
            "https://www.pbc.gov.cn/2025/authority.htm": table,
        }
        return httpx.Response(200, text=responses[str(request.url)])

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = PbocProvider(cache_dir=tmp_path, client=client).fetch_definition(_definition())

    assert result["provider"].unique().tolist() == ["PBOC"]
    assert result["series_id"].unique().tolist() == ["PBOC.BSMA.TOTAL_ASSETS"]
    assert result["value"].tolist() == [400_000.0, 410_000.0]
    assert (tmp_path / "monetary_authority_total_assets.parquet").is_file()


def test_parser_rejects_wrong_units_and_decodes_declared_gb2312() -> None:
    encoded = '<meta charset="gb2312">货币当局'.encode("gb2312")
    assert _decode_html(encoded, "test") == '<meta charset="gb2312">货币当局'

    wrong_unit = """
    <table><tr><td>Unit: Yuan</td></tr>
    <tr><td>Item</td><td>2025.01</td></tr>
    <tr><td>Total Assets</td><td>1</td></tr></table>
    """
    with pytest.raises(PbocError, match="100 Million Yuan"):
        _parse_balance_sheet_table(wrong_unit, "https://example.com", 2025)
