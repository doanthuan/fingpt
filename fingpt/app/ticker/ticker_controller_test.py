import pytest

from app.assistant import TickerAgent
from app.core.context import RequestContext
from app.entity import (
    ChatReqAction,
    ChatReqDto,
    ChatReqMetadataForQuery,
    ChatReqMetadataType,
    RawDataFormat,
    RawDataReqDto,
    SupportedTicker,
)
from app.finance.fin_service import FinService
from app.finance.sec_service import SecService
from app.ticker.report_service import ReportService
from app.ticker.ticker_controller import TickerController


@pytest.fixture
def ctx():
    req_id = "12345 67890"
    context = RequestContext(req_id)
    return context


@pytest.fixture
def ticker_agent(prompt_service):
    return TickerAgent(FinService(), SecService(), prompt_service)


@pytest.fixture
def ticker_controller(prompt_service):
    fin_srv = FinService()
    sec_srv = SecService()
    prompt_srv = prompt_service
    report_srv = ReportService(fin_srv, sec_srv, prompt_srv)
    ticker_agent = TickerAgent(fin_srv, sec_srv, prompt_srv)
    return TickerController(report_srv, ticker_agent)


@pytest.fixture
def sec_api_key():
    return "SEC_API_KEY"


@pytest.fixture
def raw_data_req():
    return RawDataReqDto(
        symbol=SupportedTicker.MSFT, raw_data_format=RawDataFormat.MARKDOWN
    )


@pytest.fixture
def chat_req_dto():
    return ChatReqDto(
        action=ChatReqAction.QUERY,
        metadata=ChatReqMetadataForQuery(
            type=ChatReqMetadataType.QUERY_DATA,
            thread_id="12345",
            user_query="Tell me about Tesla",
        ),
    )


@pytest.fixture()
def mock_ticker(mocker):

    mocker.patch.object(
        ReportService, "raw_data_report", return_value={"raw_data_report": "dump_value"}
    )

    mocker.patch.object(
        TickerAgent, "ticker_report", return_value={"ticker_report": "dump_value"}
    )


async def test_raw_data_report(
    ticker_controller, ctx, raw_data_req, sec_api_key, mock_ticker
):

    expected_result = {"raw_data_report": "dump_value", "ticker_report": "dump_value"}

    actual_result = await ticker_controller.raw_data_report(
        ctx=ctx,
        headers={
            "sec-api-key": sec_api_key,
        },
        req=raw_data_req,
    )

    assert expected_result == actual_result
