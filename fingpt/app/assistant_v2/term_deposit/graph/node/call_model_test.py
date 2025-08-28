import math
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.assistant_v2.term_deposit.constant import (
    GET_ACCOUNT_TOOL_NAME,
    GET_TERM_DEPOSIT_ACCOUNT_TOOL_NAME,
    GET_TERM_DEPOSIT_PRODUCT_TOOL_NAME,
    NOTICE_DEPOSIT_AMOUNT_TOOL_NAME,
    NOTICE_TERM_NUMBER_TOOL_NAME,
    NOTICE_TERM_UNIT_TOOL_NAME,
)
from app.assistant_v2.term_deposit.graph.node.call_model import call_model_func
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import (
    AccountIdentification,
    ActiveAccount,
    TermDepositAccount,
    TermDepositProduct,
    TermUnit,
)


@pytest.mark.asyncio
async def test_call_model(agent_config):
    get_term_deposit_account_message = ToolMessage(
        name=GET_TERM_DEPOSIT_ACCOUNT_TOOL_NAME,
        content=str(
            [
                TermDepositAccount(
                    id="td_account_1",
                    name="test term deposit account",
                    interest_rate=1.25,
                    term_number=6,
                    term_unit=TermUnit("M"),
                    maturity_date="test_maturity_date",
                    start_date="test_start_date",
                    bban="test_bban",
                    deposit_amount=6000,
                    maturity_earn=0.0,
                    is_renewable=True,
                    is_mature=True,
                ).json()
            ]
        ),
        tool_call_id="1",
    )
    get_account_message = ToolMessage(
        name=GET_ACCOUNT_TOOL_NAME,
        content=str(
            [
                ActiveAccount(
                    id="ac_1",
                    name="test account",
                    product_type="test product",
                    available_balance=1000,
                    identifications=AccountIdentification(),
                    currency="USD",
                ).json()
            ]
        ),
        tool_call_id="2",
    )
    get_term_deposit_product_message = ToolMessage(
        name=GET_TERM_DEPOSIT_PRODUCT_TOOL_NAME,
        content=str(
            [
                TermDepositProduct(
                    id="td_product_1",
                    name="test term deposit product",
                    interest_rate=1.25,
                    term_number=6,
                    term_unit=TermUnit("M"),
                    minimum_required_balance=0,
                    is_available=False,
                    maturity_earn=0,
                ).json()
            ]
        ),
        tool_call_id="3",
    )
    notice_deposit_amount_message = ToolMessage(
        name=NOTICE_DEPOSIT_AMOUNT_TOOL_NAME, content="5000", tool_call_id="4"
    )
    notice_term_number_message = ToolMessage(
        name=NOTICE_TERM_NUMBER_TOOL_NAME, content="6", tool_call_id="5"
    )
    notice_term_unit_message = ToolMessage(
        name=NOTICE_TERM_UNIT_TOOL_NAME, content="M", tool_call_id="6"
    )

    human_message = HumanMessage(content="test message")
    messages = [
        human_message,
        get_term_deposit_account_message,
        get_account_message,
        get_term_deposit_product_message,
        notice_deposit_amount_message,
        notice_term_number_message,
        notice_term_unit_message,
    ]
    # Mock the state and config
    state = {TermDepositAgentStateFields.MESSAGES: messages}

    mock_chain_ainvoke = patch(
        "app.assistant_v2.term_deposit.graph.node.call_model.chain_ainvoke",
        AsyncMock(return_value=AIMessage(content="response content")),
    ).start()

    # Call the function
    output = await call_model_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    print(output)
    # Assertions
    assert TermDepositAgentStateFields.MESSAGES in output
    assert output[TermDepositAgentStateFields.MESSAGES][0].content == "response content"
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].response == "response content"
    assert math.isclose(output[TermDepositAgentStateFields.DEPOSIT_AMOUNT], 5000)
    assert math.isclose(output[TermDepositAgentStateFields.TERM_NUMBER], 6)
    assert output[TermDepositAgentStateFields.TERM_UNIT] == "M"
    assert (
        list(output[TermDepositAgentStateFields.ACTIVE_ACCOUNTS].values())[0].id
        == "ac_1"
    )
    assert (
        list(output[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS].values())[0].id
        == "td_product_1"
    )
    assert (
        list(output[TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS].values())[0].id
        == "td_account_1"
    )

    # Stop patches
    mock_chain_ainvoke.stop()
