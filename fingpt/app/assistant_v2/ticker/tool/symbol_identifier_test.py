from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate

from app.assistant.constant import CONTEXT_KEY
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PROMPT_SERVICE_KEY
from app.assistant_v2.ticker.tool.symbol_identifier import symbol_identifier


@pytest.mark.asyncio
async def test_symbol_identifier_success():
    mock_prompt_service = AsyncMock()
    dummy_tmpl = ChatPromptTemplate.from_messages([("system", "test_prompt")])
    mock_prompt_service.get_prompt.return_value = AsyncMock(
        tmpl=dummy_tmpl, llm_model=FakeListChatModel(responses=["AAPL"])
    )
    with patch(
        "app.assistant_v2.ticker.tool.symbol_identifier.PromptService",
        return_value=mock_prompt_service,
    ):
        config = {
            CONFIGURABLE_CONTEXT_KEY: {
                PROMPT_SERVICE_KEY: mock_prompt_service,
                CONTEXT_KEY: AsyncMock(logger=MagicMock()),
            }
        }
        result = await symbol_identifier("What is the ticker symbol for Apple?", config)
        assert result == "AAPL"


@pytest.mark.asyncio
async def test_symbol_identifier_failure():
    mock_prompt_service = AsyncMock()
    mock_prompt_service.get_prompt.side_effect = Exception("Prompt service error")

    with patch(
        "app.assistant_v2.ticker.tool.symbol_identifier.PromptService",
        return_value=mock_prompt_service,
    ):
        config = {
            CONFIGURABLE_CONTEXT_KEY: {
                PROMPT_SERVICE_KEY: mock_prompt_service,
                CONTEXT_KEY: AsyncMock(logger=MagicMock()),
            }
        }
        with pytest.raises(Exception, match="Prompt service error"):
            await symbol_identifier("What is the ticker symbol for Apple?", config)
