import math
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.assistant_v2.transfer.constant import (
    GET_ACCOUNT_TOOL_NAME,
    GET_CONTACT_TOOL_NAME,
    NOTICE_TRANSFER_AMOUNT_TOOL_NAME,
)
from app.assistant_v2.transfer.graph.node.call_model import call_model_func
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.entity import AccountIdentification, ActiveAccount, Contact


@pytest.mark.asyncio
async def test_call_model(agent_config):
    get_contact_message = ToolMessage(
        name=GET_CONTACT_TOOL_NAME,
        content=str(
            [
                Contact(
                    id="1",
                    name="test contact",
                ).model_dump_json()
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
    notice_amount_message = ToolMessage(
        name=NOTICE_TRANSFER_AMOUNT_TOOL_NAME, content="1000", tool_call_id="3"
    )
    human_message = HumanMessage(content="test message")
    messages = [
        human_message,
        get_contact_message,
        get_account_message,
        notice_amount_message,
    ]
    # Mock the state and config
    state = {TransferAgentStateFields.MESSAGES: messages}

    mock_chain_ainvoke = patch(
        "app.assistant_v2.transfer.graph.node.call_model.chain_ainvoke",
        AsyncMock(return_value=AIMessage(content="response content")),
    ).start()

    # Call the function
    output = await call_model_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert TransferAgentStateFields.MESSAGES in output
    assert output[TransferAgentStateFields.MESSAGES][0].content == "response content"
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].response == "response content"
    assert math.isclose(output[TransferAgentStateFields.TRANSFER_AMOUNT], 1000.0)
    assert output[TransferAgentStateFields.ACTIVE_ACCOUNTS][0].id == "ac_1"
    assert output[TransferAgentStateFields.CONTACT_LIST][0].id == "1"

    # Stop patches
    mock_chain_ainvoke.stop()
