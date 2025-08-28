import pickle
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest
import yfinance

from app.core.context import RequestContext
from app.entity import RawDataFormat
from app.finance.fin_service import FinService
from app.finance.sec_service import SecService
from app.prompt.prompt_service import PromptService
from app.ticker.report_service import ReportService


@pytest.fixture
def ctx():
    req_id = "12345 67890"
    context = RequestContext(req_id)
    return context


@pytest.fixture
def symbol():
    return "MSFT"


@pytest.fixture
def report_srv(prompt_service):
    return ReportService(FinService(), SecService(), prompt_service)


@pytest.fixture
def sec_api_key():
    return "SEC_API_KEY"


@pytest.fixture
def raw_data_format():
    return "MARKDOWN"


@pytest.fixture()
def mock_ticker(mocker):

    data_dir = Path(__file__).parent.resolve() / "mock_data"

    # Load mock data
    with open(data_dir / "msft_data.pkl", "rb") as f:
        info = pickle.load(f)

    history_data = pd.read_parquet(data_dir / "msft_6_month_data.parquet")

    financial_data = pd.read_parquet(data_dir / "msft_financials.parquet")
    balance_sheet_data = pd.read_parquet(data_dir / "msft_balance_sheet.parquet")
    cash_flow_data = pd.read_parquet(data_dir / "msft_cash_flow.parquet")

    # Apply mock value to target objects
    mocker.patch.object(
        yfinance.Ticker, "info", new_callable=mock.PropertyMock, return_value=info
    )
    mocker.patch.object(yfinance.Ticker, "history", return_value=history_data)
    mocker.patch.object(
        yfinance.Ticker,
        "financials",
        new_callable=mock.PropertyMock,
        return_value=financial_data,
    )
    mocker.patch.object(
        yfinance.Ticker,
        "balance_sheet",
        new_callable=mock.PropertyMock,
        return_value=balance_sheet_data,
    )
    mocker.patch.object(
        yfinance.Ticker,
        "cash_flow",
        new_callable=mock.PropertyMock,
        return_value=cash_flow_data,
    )


pytest.mark.asyncio


async def test_raw_data_report():
    # Mock dependencies
    fin_srv = MagicMock(spec=FinService)
    sec_srv = MagicMock(spec=SecService)
    prompt_srv = MagicMock(spec=PromptService)

    # Create ReportService instance
    report_service = ReportService(fin_srv, sec_srv, prompt_srv)

    # Mock context
    ctx = MagicMock(spec=RequestContext)
    ctx.logger.return_value = MagicMock()

    # Set up mock return values
    fin_srv.get_company_info = AsyncMock(return_value={"name": "Test Company"})
    fin_srv.get_income_stmt = AsyncMock(
        return_value=MagicMock(
            empty=False, to_csv=lambda: "income_csv", to_markdown=lambda: "income_md"
        )
    )
    fin_srv.get_balance_sheet = AsyncMock(
        return_value=MagicMock(
            empty=False, to_csv=lambda: "balance_csv", to_markdown=lambda: "balance_md"
        )
    )
    fin_srv.get_cash_flow = AsyncMock(
        return_value=MagicMock(
            empty=False,
            to_csv=lambda: "cash_flow_csv",
            to_markdown=lambda: "cash_flow_md",
        )
    )
    fin_srv.analyst_recommendation = AsyncMock(return_value=["Buy"])
    sec_srv.get_section = AsyncMock(return_value="Section 7 text")
    fin_srv.get_home_chart_data = AsyncMock(return_value={"chart": "data"})
    fin_srv.get_sp500_chart_data = AsyncMock(return_value={"sp500": "data"})
    fin_srv.get_key_data = AsyncMock(return_value={"key": "data"})

    # Test with CSV format
    result_csv = await report_service.raw_data_report(
        ctx=ctx,
        symbol="AAPL",
        sec_api_key="test_key",  # pragma: allowlist secret
        raw_data_format=RawDataFormat.CSV,
    )

    # Assertions for CSV format
    assert result_csv["company_info"] == {"name": "Test Company"}
    assert result_csv["analyst_recommendation"] == "Buy"
    assert result_csv["section_7_text"] == "Section 7 text"
    assert result_csv["home_chart_data"] == {"chart": "data"}
    assert result_csv["sp500_chart_data"] == {"sp500": "data"}
    assert result_csv["key_data"] == {"key": "data"}
    assert result_csv["income_stmt"] == "income_csv"
    assert result_csv["balance_sheet"] == "balance_csv"
    assert result_csv["cash_flow"] == "cash_flow_csv"

    # Test with Markdown format
    result_md = await report_service.raw_data_report(
        ctx=ctx,
        symbol="AAPL",
        sec_api_key="test_key",  # pragma: allowlist secret
        raw_data_format=RawDataFormat.MARKDOWN,
    )

    # Assertions for Markdown format
    assert result_md["income_stmt"] == "income_md"
    assert result_md["balance_sheet"] == "balance_md"
    assert result_md["cash_flow"] == "cash_flow_md"
