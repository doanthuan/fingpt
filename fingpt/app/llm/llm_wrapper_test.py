# test_llm_wrapper.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI

from app.core.config import settings
from app.llm.llm_wrapper import AzureChatOpenAIWrapper


@pytest.fixture
def mock_langfuse_context(mocker):
    mocker.patch.object(settings, "enable_langfuse_tracer", "true")
    with patch(
        "app.utils.modified_langfuse_decorator.langfuse_context.get_current_langchain_handler"
    ) as mock_handler:
        yield mock_handler


@pytest.fixture
def azure_chat_openai_wrapper(mock_langfuse_context):
    return AzureChatOpenAIWrapper(azure_deployment="test_deployment", temperature=0.7)


@pytest.mark.asyncio
async def test_ainvoke_sets_callback(mock_langfuse_context, azure_chat_openai_wrapper):
    mock_langfuse_context.return_value = MagicMock()
    azure_chat_openai_wrapper.callbacks = []

    mock_input = MagicMock(spec=LanguageModelInput)
    mock_config = MagicMock(spec=RunnableConfig)
    mock_response = MagicMock(spec=BaseMessage)

    with patch.object(
        AzureChatOpenAI, "ainvoke", new=AsyncMock(return_value=mock_response)
    ) as _:
        response = await azure_chat_openai_wrapper.ainvoke(mock_input, mock_config)

    assert mock_langfuse_context.called
    assert len(azure_chat_openai_wrapper.callbacks) == 1
    assert azure_chat_openai_wrapper.callbacks[0] == mock_langfuse_context.return_value
    assert response == mock_response


@pytest.mark.asyncio
async def test_ainvoke_sets_callback_2_times(
    mock_langfuse_context, azure_chat_openai_wrapper
):
    mock_langfuse_context.return_value = MagicMock()
    azure_chat_openai_wrapper.callbacks = []

    mock_input = MagicMock(spec=LanguageModelInput)
    mock_config = MagicMock(spec=RunnableConfig)
    mock_response = MagicMock(spec=BaseMessage)

    with patch.object(
        AzureChatOpenAI, "ainvoke", new=AsyncMock(return_value=mock_response)
    ) as _:
        response = await azure_chat_openai_wrapper.ainvoke(mock_input, mock_config)
        response_2 = await azure_chat_openai_wrapper.ainvoke(mock_input, mock_config)

    assert mock_langfuse_context.called
    assert mock_langfuse_context.call_count == 3
    assert len(azure_chat_openai_wrapper.callbacks) == 1
    assert azure_chat_openai_wrapper.callbacks[0] == mock_langfuse_context.return_value
    assert response == mock_response
    assert response_2 == mock_response


@pytest.mark.asyncio
async def test_ainvoke_sets_callback_2_times_different_context(
    mock_langfuse_context, azure_chat_openai_wrapper
):
    mock_langfuse_context.return_value = MagicMock()
    azure_chat_openai_wrapper.callbacks = []

    mock_input = MagicMock(spec=LanguageModelInput)
    mock_config = MagicMock(spec=RunnableConfig)
    mock_response = MagicMock(spec=BaseMessage)
    azure_chat_openai_wrapper.callbacks = [BaseCallbackHandler()]

    with patch.object(
        AzureChatOpenAI, "ainvoke", new=AsyncMock(return_value=mock_response)
    ) as _:
        response = await azure_chat_openai_wrapper.ainvoke(mock_input, mock_config)

    assert mock_langfuse_context.called
    assert mock_langfuse_context.call_count == 2
    assert len(azure_chat_openai_wrapper.callbacks) == 2
    assert azure_chat_openai_wrapper.callbacks[1] == mock_langfuse_context.return_value
    assert response == mock_response


def test_invoke_sets_callback(mock_langfuse_context, azure_chat_openai_wrapper):
    mock_langfuse_context.return_value = MagicMock()
    azure_chat_openai_wrapper.callbacks = []

    mock_input = MagicMock(spec=LanguageModelInput)
    mock_config = MagicMock(spec=RunnableConfig)
    mock_response = MagicMock(spec=BaseMessage)

    with patch.object(AzureChatOpenAI, "invoke", return_value=mock_response) as _:
        response = azure_chat_openai_wrapper.invoke(mock_input, mock_config)

    assert mock_langfuse_context.called
    assert len(azure_chat_openai_wrapper.callbacks) == 1
    assert azure_chat_openai_wrapper.callbacks[0] == mock_langfuse_context.return_value
    assert response == mock_response
