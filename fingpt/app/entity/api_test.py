import pytest

from app.entity.api import (
    AuthReqDto,
    AuthRespDto,
    AuthUserType,
    LlmName,
    RawDataFormat,
    RawDataReqDto,
    SupportedTicker,
    TickerReqDto,
    TransactionReportReqDto,
)


def test_llm_name():
    llm_name = LlmName

    assert llm_name.GPT_4 == "gpt-4"


def test_auth_user_type():
    user_type = AuthUserType

    assert user_type.RETAIL == "retail"


def test_support_ticker():
    support_ticker = SupportedTicker

    assert support_ticker.AMZN == "AMZN"
    assert support_ticker.TSLA == "TSLA"


def test_ticker_request_dto():
    request_dto = TickerReqDto()

    assert request_dto.symbol == "TSLA"


def test_auth_req_dto():
    req = AuthReqDto(username="test_username", user_type=AuthUserType.RETAIL)

    assert req.username == "test_username"
    assert req.password == "********"
    assert req.user_type == AuthUserType.RETAIL


@pytest.fixture
def response():
    resp = AuthRespDto(
        agreement_id="agree123",
        edge_domain="domain.com",
        access_token="token123",
        cookie="cookie123",
    )
    return resp


def test_auth_res_dto(response):

    assert response.agreement_id == "agree123"
    assert response.edge_domain == "domain.com"
    assert response.access_token == "token123"
    assert response.cookie == "cookie123"


def test_raw_data_format():
    raw_data_format = RawDataFormat

    assert raw_data_format.MARKDOWN == "MARKDOWN"
    assert raw_data_format.CSV == "CSV"


def test_raw_data_req_dto():
    raw_req = RawDataReqDto()

    assert raw_req.symbol == "TSLA"
    assert raw_req.raw_data_format == "CSV"


def test_transaction_report_req_dto_default():
    transaction_req = TransactionReportReqDto(thread_id="")

    assert (
        transaction_req.user_query == "Show me all the recent restaurant transactions?"
    )
    assert transaction_req.thread_id == ""


def test_transaction_report_req_dto_custom():
    transaction_req = TransactionReportReqDto(user_query="Hello", thread_id="12345")

    assert transaction_req.user_query == "Hello"
    assert transaction_req.thread_id == "12345"
