import pytest

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, USER_CHOICE_ID_KEY
from app.assistant_v2.transfer.graph.node.select_contact import select_contact_func
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.entity import Contact


@pytest.mark.asyncio
async def test_select_contact(agent_config):
    # Mock the state and config
    state = {
        TransferAgentStateFields.CONTACT_LIST: [
            Contact(
                id="contact_1",
                name="test contact 1",
                identifications=None,
            ),
            Contact(
                id="contact_2",
                name="test contact 2",
                identifications=None,
            ),
        ]
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = "contact_1"

    # Call the function
    output = await select_contact_func(state, agent_config)

    # Assertions
    assert TransferAgentStateFields.MESSAGES in output
    assert (
        output[TransferAgentStateFields.MESSAGES][0].content
        == "My selected contact is: test contact 1, id: contact_1"
    )
    assert TransferAgentStateFields.CONTACT_LIST in output
    assert output[TransferAgentStateFields.SELECTED_CONTACT].id == "contact_1"
    assert TransferAgentStateFields.RESUME_NODE in output
    assert output[TransferAgentStateFields.RESUME_NODE] is None

    # Stop patches


@pytest.mark.asyncio
async def test_select_contact_no_choice(agent_config):
    # Mock the state and config
    state = {
        TransferAgentStateFields.CONTACT_LIST: [
            Contact(
                id="contact_1",
                name="test contact 1",
                identifications=None,
            )
        ]
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = ""

    # Mock the extract_config function

    # Call the function and expect an assertion error
    with pytest.raises(AssertionError, match="User choice is empty"):
        await select_contact_func(state, agent_config)
