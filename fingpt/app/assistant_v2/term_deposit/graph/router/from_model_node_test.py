import pytest
from langchain_core.messages import AIMessage, ToolCall

from app.assistant_v2.term_deposit.graph.router.from_model_node import (
    router_from_model,
    to_end_edge,
    to_review_edge,
    to_select_account_edge,
    to_select_term_deposit_account_edge,
    to_select_term_deposit_product_edge,
    to_tool_edge,
)
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import ActiveAccount, TermDepositAccount, TermDepositProduct, TermUnit


def test_router_from_model_to_review():
    state = {
        TermDepositAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {
            "td_product_1": TermDepositProduct(
                id="td_product_1",
                name="test term deposit product 1",
                interest_rate=1.25,
                term_number=6,
                term_unit=TermUnit("M"),
                minimum_required_balance=0,
                is_available=True,
                maturity_earn=0,
            ),
        },
        TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {
            "account_1": ActiveAccount(
                id="account_1",
                name="test account 1",
                product_type="test product",
                available_balance=1000,
                identifications=None,
                currency="USD",
            ),
        },
        TermDepositAgentStateFields.HUMAN_APPROVAL_ACTIVE_ACCOUNT: True,
        TermDepositAgentStateFields.HUMAN_APPROVAL_TERM_DEPOSIT_PRODUCT: True,
    }
    assert router_from_model(state) == to_review_edge


def test_router_from_model_to_select_term_deposit_account():
    state = {
        TermDepositAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS: {
            "td_account_1": TermDepositAccount(
                id="td_account_1",
                name="test term deposit account 1",
                interest_rate=1.25,
                term_number=6,
                term_unit=TermUnit("M"),
                maturity_date="test_maturity_date_1",
                start_date="test_start_date_1",
                bban="test_bban_1",
                deposit_amount=6000,
                maturity_earn=0.0,
                is_renewable=True,
                is_mature=True,
            ),
        },
        TermDepositAgentStateFields.HUMAN_APPROVAL_TERM_DEPOSIT_ACCOUNT: False,
    }
    assert router_from_model(state) == to_select_term_deposit_account_edge


def test_router_from_model_to_select_term_deposit_product():
    state = {
        TermDepositAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS: {
            "td_account_1": TermDepositAccount(
                id="td_account_1",
                name="test term deposit account 1",
                interest_rate=1.25,
                term_number=6,
                term_unit=TermUnit("M"),
                maturity_date="test_maturity_date_1",
                start_date="test_start_date_1",
                bban="test_bban_1",
                deposit_amount=6000,
                maturity_earn=0.0,
                is_renewable=True,
                is_mature=True,
            ),
        },
        TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {
            "td_product_1": TermDepositProduct(
                id="td_product_1",
                name="test term deposit product 1",
                interest_rate=1.25,
                term_number=6,
                term_unit=TermUnit("M"),
                minimum_required_balance=0,
                is_available=True,
                maturity_earn=0,
            ),
        },
        TermDepositAgentStateFields.HUMAN_APPROVAL_TERM_DEPOSIT_ACCOUNT: True,
    }
    assert router_from_model(state) == to_select_term_deposit_product_edge


def test_router_from_model_to_select_account():
    state = {
        TermDepositAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {
            "account_1": ActiveAccount(
                id="account_1",
                name="test account 1",
                product_type="test product",
                available_balance=1000,
                identifications=None,
                currency="USD",
            ),
            "account_2": ActiveAccount(
                id="account_2",
                name="test account 2",
                product_type="test product",
                available_balance=500,
                identifications=None,
                currency="USD",
            ),
        },
        TermDepositAgentStateFields.HUMAN_APPROVAL_ACTIVE_ACCOUNT: False,
    }
    assert router_from_model(state) == to_select_account_edge


@pytest.mark.asyncio
async def test_router_from_model_to_tool():
    state = {
        TermDepositAgentStateFields.MESSAGES: [
            AIMessage(
                content="test message",
                tool_calls=[ToolCall(id="1", name="some_tool", args={})],
            )
        ],
    }
    assert router_from_model(state) == to_tool_edge


@pytest.mark.asyncio
async def test_router_from_model_to_end():
    state = {
        TermDepositAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {},
        TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {},
    }
    assert router_from_model(state) == to_end_edge
