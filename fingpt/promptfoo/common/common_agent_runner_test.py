from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from promptfoo.common.common_agent_runner import common_call_api, generic_agent_router


@pytest.mark.asyncio
async def test_generic_agent_router():
    # Mock dependencies
    mock_build_agent_func = AsyncMock()
    mock_agent = AsyncMock()
    mock_agent.ainvoke.return_value = MagicMock(
        content="Test response", tool_calls=["Tool call 1", "Tool call 2"]
    )
    mock_build_agent_func.return_value = mock_agent

    # Test input
    prompt = "test_prompt:test_label"
    options = {"config": {"model": "gpt-3.5-turbo"}}
    context = {"vars": {"messages": ["Hello", "World"]}}

    # Call the function
    result = await generic_agent_router(prompt, options, context, mock_build_agent_func)

    # Assertions
    mock_build_agent_func.assert_called_once()
    mock_agent.ainvoke.assert_called_once_with(
        {"messages": ["Hello", "World"]}, temperature=0.0
    )

    assert result == {
        "output": {
            "content": "Test response",
            "tool_calls": ["Tool call 1", "Tool call 2"],
        }
    }


@pytest.mark.asyncio
async def test_common_call_api():
    # Mock dependencies
    mock_state_class = MagicMock()
    mock_call_model_func = AsyncMock()
    mock_response = MagicMock(
        content="Test response", tool_calls=["Tool call 1", "Tool call 2"]
    )
    mock_call_model_func.return_value = {"messages": [mock_response]}

    # Test input
    prompt = "test_prompt:test_label"
    options = {"config": {"model": "gpt-3.5-turbo"}}
    context = {"vars": {"messages": ["Hello", "World"]}}

    # Patch dependencies
    with patch(
        "promptfoo.common.common_agent_runner.AzureChatOpenAI"
    ) as mock_azure_chat, patch(
        "promptfoo.common.common_agent_runner.RequestContext"
    ) as mock_request_context, patch(
        "promptfoo.common.common_agent_runner.uuid.uuid4"
    ) as mock_uuid4, patch(
        "promptfoo.common.common_agent_runner.module.prompt_srv"
    ) as mock_prompt_srv:

        mock_logger = MagicMock()
        mock_request_context.return_value.logger.return_value = mock_logger
        mock_uuid4.return_value = "test-uuid"
        mock_prompt_srv.return_value = MagicMock()

        # Call the function
        result = await common_call_api(
            prompt, options, context, mock_state_class, mock_call_model_func
        )

    # Assertions
    mock_azure_chat.assert_called_once_with(azure_deployment="gpt-3.5-turbo")
    mock_state_class.assert_called_once_with(messages=["Hello", "World"])
    mock_call_model_func.assert_called_once_with(
        state=mock_state_class.return_value,
        config={
            "configurable": {
                "ctx": mock_request_context.return_value,
                "llm_model": mock_azure_chat.return_value,
                "ps": mock_prompt_srv.return_value,
                "thread_id": "test-uuid",
                "pending_response": [],
            }
        },
        prompt_name="test_prompt",
        prompt_label="test_label",
    )

    assert result == {
        "output": {
            "content": "Test response",
            "tool_calls": ["Tool call 1", "Tool call 2"],
        }
    }

    mock_logger.info.assert_any_call("Prompt: test_prompt:test_label")
    mock_logger.info.assert_any_call(f"call model response {mock_response}")
    mock_logger.debug.assert_called_once()
