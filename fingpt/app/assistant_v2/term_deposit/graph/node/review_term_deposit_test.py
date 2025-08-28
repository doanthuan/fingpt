from datetime import date, timedelta

import pytest
from langchain_core.messages import HumanMessage

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.assistant_v2.term_deposit.graph.node.review_term_deposit import (
    review_term_deposit_func,
)
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import (
    AccountIdentification,
    ActiveAccount,
    ChatRespAction,
    TermDepositAccount,
    TermDepositProduct,
    TermUnit,
)


@pytest.mark.asyncio
async def test_review_term_deposit(agent_config):
    # Mock the state and config
    state = {
        TermDepositAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {
            "account_1": ActiveAccount(
                id="account_1",
                name="test account",
                product_type="test product",
                available_balance=1000,
                identifications=AccountIdentification(),
                currency="USD",
                booked_balance=1000,
            )
        },
        TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS: {},
        TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {
            "product_1": TermDepositProduct(
                id="product_1",
                name="test product",
                minimum_required_balance=500,
                interest_rate=5.0,
                term_number=1,
                term_unit=TermUnit("Y"),
                is_available=True,
                maturity_earn=50,
            )
        },
        TermDepositAgentStateFields.DEPOSIT_AMOUNT: 500,
    }

    # Call the function
    output = await review_term_deposit_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert TermDepositAgentStateFields.MESSAGES in output
    assert output[TermDepositAgentStateFields.MESSAGES][0].content == "It's okay."
    assert TermDepositAgentStateFields.RESUME_NODE in output
    assert output[TermDepositAgentStateFields.RESUME_NODE] is None
    assert output[TermDepositAgentStateFields.ACTIVE_ACCOUNTS] == {}
    assert output[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS] == {}
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert (
        config_data[PENDING_RESPONSE_KEY][0].action == ChatRespAction.MAKE_TERM_DEPOSIT
    )


@pytest.mark.asyncio
async def test_review_term_deposit_not_sufficient_funds(agent_config):
    # Mock the state and config
    state = {
        TermDepositAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {
            "account_1": ActiveAccount(
                id="account_1",
                name="test account",
                product_type="test product",
                available_balance=1000,
                identifications=AccountIdentification(),
                currency="USD",
            )
        },
        TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS: {},
        TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {
            "product_1": TermDepositProduct(
                id="product_1",
                name="test product",
                minimum_required_balance=700,
                interest_rate=5.0,
                term_number=1,
                term_unit=TermUnit("Y"),
                maturity_earn=50,
            )
        },
        TermDepositAgentStateFields.DEPOSIT_AMOUNT: 600,
    }

    # Call the function
    output = await review_term_deposit_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert output[TermDepositAgentStateFields.RESUME_NODE] is None
    assert output[TermDepositAgentStateFields.ACTIVE_ACCOUNTS] == {}
    assert output[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS] == {}
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].action == ChatRespAction.SHOW_REPLY


@pytest.mark.asyncio
async def test_review_term_deposit_renewal(agent_config):
    # Mock the state and config
    state = {
        TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {},
        TermDepositAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS: {
            "td_account_1": TermDepositAccount(
                id="td_account_1",
                name="test td account",
                deposit_amount=500,
                maturity_date=(date.today() - timedelta(days=1)).isoformat(),
                interest_rate=5.0,
                term_number=1,
                term_unit=TermUnit("Y"),
                maturity_earn=50,
                start_date="test_start_date",
                bban="test_bban",
                is_renewable=True,
                is_mature=True,
            )
        },
        TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {
            "td_product_1": TermDepositProduct(
                id="td_product_1",
                name="test td product",
                minimum_required_balance=500,
                interest_rate=5.0,
                term_number=1,
                term_unit=TermUnit("Y"),
                maturity_earn=50,
                is_available=True,
            )
        },
        TermDepositAgentStateFields.DEPOSIT_AMOUNT: 500,
    }

    # Call the function
    output = await review_term_deposit_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert TermDepositAgentStateFields.MESSAGES in output
    assert output[TermDepositAgentStateFields.MESSAGES][0].content == "It's okay."
    assert TermDepositAgentStateFields.RESUME_NODE in output
    assert output[TermDepositAgentStateFields.RESUME_NODE] is None
    assert output[TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS] == {}
    assert output[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS] == {}
    assert output[TermDepositAgentStateFields.DEPOSIT_AMOUNT] is None
    assert output[TermDepositAgentStateFields.TERM_NUMBER] is None
    assert output[TermDepositAgentStateFields.TERM_UNIT] is None
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert (
        config_data[PENDING_RESPONSE_KEY][0].action == ChatRespAction.RENEW_TERM_DEPOSIT
    )
