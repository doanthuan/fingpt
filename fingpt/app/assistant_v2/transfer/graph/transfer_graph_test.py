from unittest.mock import MagicMock

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    USER_CHOICE_ID_KEY,
)
from app.assistant_v2.transfer.graph.transfer_graph import TransferGraph
from app.assistant_v2.transfer.state import TransferAgentState, TransferAgentStateFields
from app.core import RequestContext


def setUp():
    global state
    state = TransferAgentState(
        {
            TransferAgentStateFields.MESSAGES: ["message1", "message2"],
            TransferAgentStateFields.TRANSFER_AMOUNT: 100,
            TransferAgentStateFields.ACTIVE_ACCOUNTS: ["account1"],
            TransferAgentStateFields.CONTACT_LIST: ["contact1"],
            TransferAgentStateFields.SELECTED_ACCOUNT: "account1",
            TransferAgentStateFields.SELECTED_CONTACT: "contact1",
            "other_field": "some_value",
            "list_field": [1, 2, 3],
            "dict_field": {"key": "value"},
        }
    )


def test_clear_state_except_messages():
    setUp()
    cleared_state = TransferGraph.clear_state_except_messages(state)
    assert cleared_state[TransferAgentStateFields.MESSAGES] == ["message1", "message2"]
    assert cleared_state[TransferAgentStateFields.TRANSFER_AMOUNT] == 100
    assert cleared_state[TransferAgentStateFields.ACTIVE_ACCOUNTS] == ["account1"]
    assert cleared_state[TransferAgentStateFields.CONTACT_LIST] == ["contact1"]
    assert cleared_state[TransferAgentStateFields.SELECTED_ACCOUNT] == "account1"
    assert cleared_state[TransferAgentStateFields.SELECTED_CONTACT] == "contact1"
    assert cleared_state["other_field"] is None
    assert cleared_state["list_field"] == []
    assert cleared_state["dict_field"] == {}


async def test_start_node_fnc_resume_node_no_user_choice_id():
    state = TransferAgentState(
        {
            TransferAgentStateFields.RESUME_NODE: "some_node",
            TransferAgentStateFields.MESSAGES: ["message1", "message2"],
        }
    )
    config = RunnableConfig(
        {CONFIGURABLE_CONTEXT_KEY: {CONTEXT_KEY: MagicMock(RequestContext)}}
    )
    config.get(CONFIGURABLE_CONTEXT_KEY)[CONTEXT_KEY].logger = MagicMock()

    result = await TransferGraph.start_node_fnc(state, config)

    assert result[TransferAgentStateFields.MESSAGES] == ["message1", "message2"]
    assert result.get(TransferAgentStateFields.RESUME_NODE) is None


async def test_start_node_fnc_no_resume_node_user_choice_id():
    state = TransferAgentState(
        {TransferAgentStateFields.MESSAGES: ["message1", "message2"]}
    )
    config = RunnableConfig(
        {
            CONFIGURABLE_CONTEXT_KEY: {
                CONTEXT_KEY: MagicMock(RequestContext),
                USER_CHOICE_ID_KEY: "some_choice_id",
            }
        }
    )
    config.get(CONFIGURABLE_CONTEXT_KEY)[CONTEXT_KEY].logger = MagicMock()

    result = await TransferGraph.start_node_fnc(state, config)

    assert result == {TransferAgentStateFields.MESSAGES: []}
    assert config.get(CONFIGURABLE_CONTEXT_KEY).get(USER_CHOICE_ID_KEY) is None
