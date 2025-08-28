from unittest.mock import AsyncMock

import pytest
from langchain_core.prompts import ChatPromptTemplate
from langfuse.model import ChatMessageDict

from app.entity import ChatPrompt
from app.prompt.prompt_service import PromptService


@pytest.fixture()
def langchain_mocker(mocker):
    mock_message = "Mock prompt for {user_query}"
    mock_response_for_prompt = ChatPrompt(
        name="mock_prompt",
        chat_messages=[ChatMessageDict(role="system", content=mock_message)],
        tmpl=ChatPromptTemplate.from_messages([("system", mock_message)]),
    )
    mock_response_for_ticker_ainvoke = "AAPL"
    mocker.patch.object(
        PromptService, "get_prompt", AsyncMock(return_value=mock_response_for_prompt)
    )
    mocker.patch(
        "app.assistant.ticker.nodes._invoke_chain",
        AsyncMock(return_value=mock_response_for_ticker_ainvoke),
    )
