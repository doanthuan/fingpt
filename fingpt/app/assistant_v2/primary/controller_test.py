from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel import StateSnapshot

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    LLM_MODEL_KEY,
)
from app.assistant_v2.primary.controller import AssistantController
from app.assistant_v2.primary.graph import AssistantGraph
from app.assistant_v2.primary.state import AssistantConfig, AssistantStateFields
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.core import RequestContext
from app.entity import (
    ApiHeader,
    ChatReqAction,
    ChatReqDto,
    ChatReqMetadataForChoice,
    ChatReqMetadataForQuery,
    ChatReqMetadataType,
    ChatRespDto,
    Contact,
    UnauthorizedError,
)
from app.entity.chat_request import ChatReqMetadataForOffer
from app.entity.chat_response import ChatRespAction
from app.entity.offer import OfferProduct, OfferReq, OfferReqDataForCard, OfferType


@pytest.fixture
def controller(mocker, agent_config, prompt_service):
    llm_service = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {}).get(LLM_MODEL_KEY)
    assistant_graph = AssistantGraph(prompt_service, llm_service)
    mocked_config = RunnableConfig(
        configurable=dict(
            AssistantConfig(
                thread_id=None,
                ctx=RequestContext("PLACEHOLDER"),
                llm_model=llm_service,
                ps=prompt_service,
                pending_response=[
                    ChatRespDto(
                        response="This is a fake response",
                        action="SHOW_REPLY",
                        metadata=None,
                    )
                ],
                user_query=None,
                ebp_access_token=None,
                ebp_cookie=None,
                ebp_edge_domain=None,
            ),
        )
    )
    mocker.patch.object(
        CompiledStateGraph, "aupdate_state", AsyncMock(return_value=None)
    )
    mocker.patch.object(AssistantController, "_get_config", return_value=mocked_config)
    controller = AssistantController(prompt_service, llm_service, assistant_graph, True)
    return controller


@pytest.mark.asyncio
async def test_chat_query(mocker, agent_config, controller, mock_guardrails_pass):
    mocker.patch.object(CompiledStateGraph, "ainvoke", AsyncMock(return_value=None))

    ctx = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {}).get(CONTEXT_KEY)
    header = ApiHeader(cookie="cookie", token="access_token")
    request = ChatReqDto(
        action=ChatReqAction.QUERY,
        metadata=ChatReqMetadataForQuery(
            type=ChatReqMetadataType.QUERY_DATA,
            thread_id="12345",
            user_query="Tell me about Tesla",
        ),
    )
    response = await controller.chat(ctx, header, request)
    assert response.action == "SHOW_REPLY"
    assert response.response == "This is a fake response"
    assert response.metadata is None


@pytest.mark.asyncio
async def test_chat_make_choice(mocker, agent_config, controller):
    mocker.patch.object(CompiledStateGraph, "ainvoke", AsyncMock(return_value=None))
    snapshot_state = StateSnapshot(
        values={
            AssistantStateFields.TRANSFER_AGENT_STATE: {
                TransferAgentStateFields.CONTACT_LIST: {
                    "123": Contact(id="123", account_number="xxx", name="John Doe"),
                    "456": Contact(id="456", account_number="yyy", name="Jane Doe"),
                }
            }
        },
        next=("next_state",),
        config=agent_config,
        metadata={},
        created_at="now",
    )
    aget_state_mocked = mocker.patch.object(
        CompiledStateGraph, "aget_state", AsyncMock(return_value=snapshot_state)
    )
    ctx = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {}).get(CONTEXT_KEY)
    header = ApiHeader(cookie="cookie", token="access_token")
    request = ChatReqDto(
        action=ChatReqAction.MAKE_CHOICE,
        metadata=ChatReqMetadataForChoice(
            type=ChatReqMetadataType.CHOICE_DATA,
            thread_id="12345",
            choice_id="123",
        ),
    )
    response = await controller.chat(ctx, header, request)
    aget_state_mocked.assert_called_once()
    assert response.action == "SHOW_REPLY"
    assert response.response == "This is a fake response"
    assert response.metadata is None


# @pytest.mark.asyncio
# async def test_guardrail_error(mocker, agent_config, controller, mock_guardrails_fail):
#     mocker.patch.object(CompiledStateGraph, "ainvoke", AsyncMock(return_value=None))
#     ctx = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {}).get(CONTEXT_KEY)
#     header = ApiHeader(cookie="cookie", token="access_token")
#     request = ChatReqDto(
#         action=ChatReqAction.QUERY,
#         metadata=ChatReqMetadataForQuery(
#             type=ChatReqMetadataType.QUERY_DATA,
#             thread_id="12345",
#             user_query="Tell me about Tesla",
#         ),
#     )
#     response = await controller.chat(ctx, header, request)
#     assert response.action == "SHOW_REPLY"
#     assert response.response == GUARDRAIL_ERROR_CONTENT
#     assert response.metadata is None


@pytest.mark.asyncio
async def test_unauthorized_error(
    mocker, agent_config, controller, mock_guardrails_pass
):
    mocker.patch.object(CompiledStateGraph, "ainvoke", side_effect=UnauthorizedError())
    ctx = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {}).get(CONTEXT_KEY)
    header = ApiHeader(cookie="cookie", token="access_token")
    request = ChatReqDto(
        action=ChatReqAction.QUERY,
        metadata=ChatReqMetadataForQuery(
            type=ChatReqMetadataType.QUERY_DATA,
            thread_id="12345",
            user_query="Tell me about Tesla",
        ),
    )
    with pytest.raises(HTTPException) as exe_info:
        await controller.chat(ctx, header, request)
    assert exe_info.value.status_code == 401
    assert exe_info.value.detail == "Invalid credentials data"


@pytest.mark.asyncio
async def test_get_offer_credit_card():
    # Mock dependencies
    prompt_srv = MagicMock()
    llm = MagicMock()
    graph = MagicMock()
    ctx = MagicMock()
    agent = AsyncMock()
    header = ApiHeader(token="test_token", cookie="test_cookie")

    # Create controller instance
    controller = AssistantController(prompt_srv, llm, graph)

    # Mock the get_graph method
    controller._get_workflow = AsyncMock(return_value=MagicMock())
    controller._get_workflow.return_value.compile = MagicMock(return_value=agent)

    # Prepare test data
    req_data = ChatReqMetadataForOffer(
        thread_id="test_thread",
        offer=OfferReq(
            product=OfferProduct.CARD,
            message="",
            data=OfferReqDataForCard(
                type=OfferType.RENEWAL, card_id="some_card_id"
            ),  # Add any necessary data for credit card offer
        ),
    )

    # Call the method
    result = await controller._get_offer(ctx, agent, header, req_data)

    # Assertions
    assert isinstance(result, ChatRespDto)
    assert result.action == ChatRespAction.SHOW_OFFER
    assert result.thread_id == "test_thread"

    # Check if the response contains expected content
    expected_date = (datetime.now() + timedelta(days=14)).strftime("%b %d, %Y")
    assert f"Your Credit Card is about to expire on {expected_date}" in result.response
    assert "Benefits" in result.response
    assert "Bills" in result.response
    assert "Travel" in result.response
    assert "Points" in result.response
    assert "Plus" in result.response
    assert "No annual fee" in result.response
    assert "10,000 Bonus Points" in result.response
    assert "Complementary Travel Insurance" in result.response
