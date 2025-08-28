import pytest
from langchain_core.messages import HumanMessage

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.assistant_v2.transfer.graph.node.review_transfer import review_transfer_func
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.entity import ActiveAccount, ChatRespAction, Contact


@pytest.mark.asyncio
async def test_review_transfer(agent_config):
    # Mock the state and config
    state = {
        TransferAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        TransferAgentStateFields.SELECTED_CONTACT: Contact(
            id="contact_1",
            name="test contact",
            identifications=None,
        ),
        TransferAgentStateFields.SELECTED_ACCOUNT: ActiveAccount(
            id="account_1",
            name="test account",
            product_type="test product",
            available_balance=1000,
            identifications=None,
            currency="USD",
        ),
        TransferAgentStateFields.TRANSFER_AMOUNT: 600,
    }

    # Mock the extract_config function

    # Call the function
    output = await review_transfer_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert TransferAgentStateFields.MESSAGES in output
    assert output[TransferAgentStateFields.MESSAGES][0].content == "It's okay."
    assert TransferAgentStateFields.RESUME_NODE in output
    assert output[TransferAgentStateFields.RESUME_NODE] is None
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].action == ChatRespAction.MAKE_TRANSFER


@pytest.mark.asyncio
async def test_review_transfer_not_sufficient_funds(agent_config):
    # Mock the state and config
    state = {
        TransferAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        TransferAgentStateFields.SELECTED_CONTACT: Contact(
            id="contact_1",
            name="test contact",
            identifications=None,
        ),
        TransferAgentStateFields.SELECTED_ACCOUNT: ActiveAccount(
            id="account_1",
            name="test account",
            product_type="test product",
            available_balance=500,
            identifications=None,
            currency="USD",
        ),
        TransferAgentStateFields.TRANSFER_AMOUNT: 600,
    }

    # Call the function
    output = await review_transfer_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert output[TransferAgentStateFields.RESUME_NODE] is None
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].action == ChatRespAction.SHOW_REPLY

    # Stop patches
