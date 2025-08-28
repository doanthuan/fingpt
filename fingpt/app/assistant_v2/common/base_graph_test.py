import unittest
from unittest.mock import MagicMock

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import BaseGraph
from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    USER_CHOICE_ID_KEY,
)
from app.assistant_v2.transaction.state import BaseAgentState, BaseAgentStateFields


class TestStartNodeFnc(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.state = BaseAgentState()
        self.config = RunnableConfig()
        self.ctx = MagicMock()
        self.logger = MagicMock()
        self.ctx.logger.return_value = self.logger
        self.config[CONFIGURABLE_CONTEXT_KEY] = {CONTEXT_KEY: self.ctx}

    async def test_start_node_fnc_no_resume_no_user_choice(self):
        self.state[BaseAgentStateFields.RESUME_NODE] = ""
        self.state[BaseAgentStateFields.MESSAGES] = [HumanMessage(content="test")]
        self.config[CONFIGURABLE_CONTEXT_KEY][USER_CHOICE_ID_KEY] = None
        result = await BaseGraph.start_node_fnc(self.state, self.config)
        self.assertEqual(result, {BaseAgentStateFields.MESSAGES: []})  # no update state

    async def test_start_node_fnc_with_resume_no_user_choice(self):
        self.state[BaseAgentStateFields.RESUME_NODE] = "some_node"
        self.state[BaseAgentStateFields.MESSAGES] = [HumanMessage(content="test")]
        self.state["some_other_field"] = "some_other_value"
        self.config[CONFIGURABLE_CONTEXT_KEY][USER_CHOICE_ID_KEY] = None
        new_state = await BaseGraph.start_node_fnc(self.state, self.config)
        self.logger.warn.assert_called_once()
        self.assertEqual(new_state[BaseAgentStateFields.RESUME_NODE], None)

    async def test_start_node_fnc_no_resume_with_user_choice(self):
        self.state[BaseAgentStateFields.RESUME_NODE] = ""
        self.state[BaseAgentStateFields.MESSAGES] = [HumanMessage(content="test")]
        self.config[CONFIGURABLE_CONTEXT_KEY][USER_CHOICE_ID_KEY] = "user_choice"
        result = await BaseGraph.start_node_fnc(self.state, self.config)
        self.logger.warn.assert_called_once()
        self.assertEqual(result, {BaseAgentStateFields.MESSAGES: []})  # no update state
        self.assertIsNone(
            self.config[CONFIGURABLE_CONTEXT_KEY][USER_CHOICE_ID_KEY]
        )  # but user_choice_id is None


if __name__ == "__main__":
    unittest.main()
