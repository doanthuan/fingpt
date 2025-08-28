import json
import os
from unittest.mock import AsyncMock

import pytest
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langfuse.model import ChatMessageDict

from app.assistant.ticker.nodes import (
    balance_sheet_analyst,
    cash_flow_analyst,
    income_stmt_analyst,
    show_confirm_action,
    summary_analyst,
)
from app.assistant.ticker.state import TickerAgentState
from app.core import RequestContext
from app.entity import ChatPrompt, ChatRespAction, ChatRespDto, SupportedTicker
from app.entity.chat_response import ChatRespMetadataForShowTickerReport
from app.prompt.prompt_service import PromptService


@pytest.fixture()
def _config(mocker, prompt_service):
    os.environ["AZURE_OPENAI_ENDPOINT"] = "fake_endpoint"
    os.environ["OPENAI_API_VERSION"] = "fake_version"
    os.environ["AZURE_OPENAI_DEPLOYMENT"] = "fake_deployment"
    os.environ["AZURE_OPENAI_API_KEY"] = "fake_key"  # pragma: allowlist secret
    # patch the prompt service to return a mock ChatPrompt object with fake message
    mocker.patch.object(
        PromptService,
        "get_prompt",
        return_value=ChatPrompt(
            name="mock_prompt",
            chat_messages=[
                ChatMessageDict(role="system", content="Mock prompt for {user_query}")
            ],
            tmpl=ChatPromptTemplate.from_messages(
                [("system", "Mock prompt for {user_query}")]
            ),
        ),
    )
    yield {
        "configurable": {
            "_ctx": RequestContext("req_id"),
            "_ps": prompt_service,
            "_llm_model": AzureChatOpenAI(),
        }
    }


# Write a test app.assistant.ticker.nodes.income_stmt_analyst function
# This test function uses _config fixture and mocker to patch the function in
# "app.assistant.ticker.nodes._invoke_chain" with a mock response. Assert the response from the function
# contains the expected result.
@pytest.mark.asyncio
async def test_income_stmt_analyst(_config, mocker):
    mocker.patch(
        "app.assistant.ticker.nodes._invoke_chain",
        AsyncMock(return_value="this is a mock report"),
    )
    # The state must contain 3 attributes: income_stmt, company_info, section_7, generate it:
    state = TickerAgentState(
        income_stmt="income_stmt",
        company_info={"industry": "industry"},
        section_7="section_7",
    )
    response = await income_stmt_analyst(state, _config)
    assert "messages" in response
    assert "income_stmt_report" in response
    assert response["income_stmt_report"] == "this is a mock report"


# Write a test app.assistant.ticker.nodes.balance_sheet_analyst function
# This test function uses _config fixture and mocker to patch the function in
# "app.assistant.ticker.nodes._invoke_chain" with a mock response. Assert the response from the function
# contains the expected result.
@pytest.mark.asyncio
async def test_balance_sheet_analyst(_config, mocker):
    mocker.patch(
        "app.assistant.ticker.nodes._invoke_chain",
        AsyncMock(return_value="this is a mock report"),
    )
    # The state must contain 3 attributes: balance_sheet, company_info, section_7, generate it:
    state = TickerAgentState(
        balance_sheet="balance_sheet",
        company_info={"industry": "industry"},
        section_7="section_7",
    )
    response = await balance_sheet_analyst(state, _config)
    assert "messages" in response
    assert "balance_sheet_report" in response
    assert response["balance_sheet_report"] == "this is a mock report"


# Write a test app.assistant.ticker.nodes.test_cash_flow_analyst function
# This test function uses _config fixture and mocker to patch the function in
# "app.assistant.ticker.nodes._invoke_chain" with a mock response. Assert the response from the function
# contains the expected result.
# The state must contain 3 attributes: cash_flow, company_info, section_7
# Generate the state and assert the response contains the expected result.
@pytest.mark.asyncio
async def test_cash_flow_analyst(_config, mocker):
    mocker.patch(
        "app.assistant.ticker.nodes._invoke_chain",
        AsyncMock(return_value="this is a mock report"),
    )
    # The state must contain 3 attributes: cash_flow, company_info, section_7, generate it:
    state = TickerAgentState(
        cash_flow="cash_flow",
        company_info={"industry": "industry"},
        section_7="section_7",
    )
    response = await cash_flow_analyst(state, _config)
    assert "messages" in response
    assert "cash_flow_report" in response
    assert response["cash_flow_report"] == "this is a mock report"


# Write a test app.assistant.ticker.nodes.summary_analyst function
# This test function uses _config fixture and mocker to patch the function in
# "app.assistant.ticker.nodes._invoke_chain" with a mock response. Assert the response from the function
# contains the expected result.
# The state must contain 3 attributes: income_stmt_report, balance_sheet_report, cash_flow_report
# Generate the state and assert the response contains the expected result.
@pytest.mark.asyncio
async def test_summary_analyst(_config, mocker):
    mocker.patch(
        "app.assistant.ticker.nodes._invoke_chain",
        AsyncMock(return_value="this is a mock report"),
    )
    # The state must contain 3 attributes: income_stmt_report, balance_sheet_report, cash_flow_report, generate it:
    state = TickerAgentState(
        income_stmt_report="income_stmt_report",
        balance_sheet_report="balance_sheet_report",
        cash_flow_report="cash_flow_report",
    )
    response = await summary_analyst(state, _config)
    assert "messages" in response
    assert "summary_report" in response
    assert response["summary_report"] == "this is a mock report"


@pytest.mark.asyncio
async def test_show_confirm_action(_config):
    state = TickerAgentState(
        symbol="AAPL",
    )
    expected_response = ChatRespDto(
        thread_id=None,
        response="Let's see the financial report of ticker symbol AAPL!",
        action=ChatRespAction.SHOW_TICKER_REPORT,
        metadata=ChatRespMetadataForShowTickerReport(
            ticker=SupportedTicker.AAPL,
        ),
    )
    response = await show_confirm_action(state, _config)
    actual_dto = ChatRespDto(**json.loads(response["responses"][0]))
    assert actual_dto == expected_response
