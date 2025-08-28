from unittest.mock import MagicMock, patch

import pytest
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, CONTEXT_KEY
from app.assistant_v2.util.misc import build_chain, extract_config
from app.core import RequestContext
from app.prompt.prompt_service import PromptService


def test_extract_config():
    mock_logger = MagicMock()
    mock_ctx = MagicMock(spec=RequestContext)
    mock_ctx.logger.return_value = mock_logger

    config = {
        CONFIGURABLE_CONTEXT_KEY: {CONTEXT_KEY: mock_ctx, "other_key": "other_value"}
    }

    config_data, ctx, logger = extract_config(config)

    assert config_data == {CONTEXT_KEY: mock_ctx, "other_key": "other_value"}
    assert ctx == mock_ctx
    assert logger == mock_logger


@pytest.mark.asyncio
async def test_build_chain():
    mock_ctx = MagicMock(spec=RequestContext)
    mock_prompt_srv = MagicMock(spec=PromptService)
    # Create a real ChatPromptTemplate instead of a mock
    mock_prompt = MagicMock()
    mock_prompt.tmpl = ChatPromptTemplate.from_messages(
        [("human", "Test template"), MessagesPlaceholder(variable_name="messages")]
    )
    mock_prompt.llm_model = MagicMock(spec=AzureChatOpenAI)
    mock_prompt_srv.get_prompt.return_value = mock_prompt

    mock_tool = MagicMock()
    mock_tool.name = "TestTool"
    tool_list = [mock_tool]

    with patch("app.assistant_v2.util.misc.MessagesPlaceholder", MessagesPlaceholder):
        result = await build_chain(
            mock_ctx,
            mock_prompt_srv,
            "test_prompt",
            "test_label",
            tool_list,
        )

    mock_prompt_srv.get_prompt.assert_called_once_with(
        mock_ctx, name="test_prompt", label="test_label", type="chat"
    )

    mock_prompt.llm_model.bind_tools.assert_called_once_with(tool_list)
    assert result is not None
