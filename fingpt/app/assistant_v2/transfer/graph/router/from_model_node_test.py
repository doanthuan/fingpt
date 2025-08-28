import pytest
from langchain_core.messages import AIMessage, ToolCall

from app.assistant_v2.transfer.constant import GET_CONTACT_TOOL_NAME
from app.assistant_v2.transfer.graph.router.from_model_node import (
    router_from_model,
    to_end_edge,
    to_review_edge,
    to_select_account_edge,
    to_select_contact_edge,
    to_tool_edge,
)
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.entity import ActiveAccount, Contact


def test_router_from_model_to_review():
    state = {
        TransferAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        TransferAgentStateFields.SELECTED_CONTACT: Contact(
            id="contact_1", name="test contact"
        ),
        TransferAgentStateFields.SELECTED_ACCOUNT: ActiveAccount(
            id="account_1",
            name="test account",
            product_type="test product",
            available_balance=1000,
            identifications=None,
            currency="USD",
        ),
    }
    assert router_from_model(state) == to_review_edge


def test_router_from_model_to_select_contact():
    state = {
        TransferAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        TransferAgentStateFields.CONTACT_LIST: [
            Contact(
                id="contact_1",
                name="test contact 1",
            ),
            Contact(
                id="contact_2",
                name="test contact 2",
            ),
        ],
        TransferAgentStateFields.ACTIVE_ACCOUNTS: [
            ActiveAccount(
                id="account_1",
                name="test account",
                product_type="test product",
                available_balance=1000,
                identifications=None,
                currency="USD",
            )
        ],
    }
    assert router_from_model(state) == to_select_contact_edge


@pytest.mark.asyncio
async def test_router_from_model_to_select_account():
    state = {
        TransferAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        TransferAgentStateFields.CONTACT_LIST: [
            Contact(id="contact_1", name="test contact")
        ],
        TransferAgentStateFields.ACTIVE_ACCOUNTS: [
            ActiveAccount(
                id="account_1",
                name="test account 1",
                product_type="test product",
                available_balance=1000,
                identifications=None,
                currency="USD",
            ),
            ActiveAccount(
                id="account_2",
                name="test account 2",
                product_type="test product",
                available_balance=500,
                identifications=None,
                currency="USD",
            ),
        ],
    }
    assert router_from_model(state) == to_select_account_edge


@pytest.mark.asyncio
async def test_router_from_model_to_tool():
    state = {
        TransferAgentStateFields.MESSAGES: [
            AIMessage(
                content="test message",
                tool_calls=[ToolCall(id="1", name=GET_CONTACT_TOOL_NAME, args={})],
            )
        ],
        TransferAgentStateFields.CONTACT_LIST: [
            Contact(
                id="contact_1",
                name="test contact",
            )
        ],
        TransferAgentStateFields.ACTIVE_ACCOUNTS: [
            ActiveAccount(
                id="account_1",
                name="test account",
                product_type="test product",
                available_balance=1000,
                identifications=None,
                currency="USD",
            )
        ],
    }
    assert router_from_model(state) == to_tool_edge


@pytest.mark.asyncio
async def test_router_from_model_to_end():
    state = {
        TransferAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        TransferAgentStateFields.CONTACT_LIST: [],
        TransferAgentStateFields.ACTIVE_ACCOUNTS: [],
    }
    assert router_from_model(state) == to_end_edge
