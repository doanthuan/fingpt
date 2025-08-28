import pytest
from langchain_core.messages import HumanMessage

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.assistant_v2.transfer.graph.node.multiple_contact_match import (
    multiple_contact_match_func,
)
from app.assistant_v2.transfer.graph.node.select_contact import select_contact_node
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.entity import Contact


@pytest.mark.asyncio
async def test_multiple_contact_match(agent_config):
    # Mock the state and config
    state = {
        TransferAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
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
    }

    # Call the function
    output = await multiple_contact_match_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert TransferAgentStateFields.RESUME_NODE in output
    assert output[TransferAgentStateFields.RESUME_NODE] == select_contact_node
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].action == "SHOW_CHOICES"
    assert len(config_data[PENDING_RESPONSE_KEY][0].metadata.choices) == 2
    assert config_data[PENDING_RESPONSE_KEY][0].metadata.choices[0].is_enabled
    assert config_data[PENDING_RESPONSE_KEY][0].metadata.choices[1].is_enabled
