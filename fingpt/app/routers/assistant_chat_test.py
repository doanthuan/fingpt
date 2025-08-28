from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.entity import (
    ChatReqAction,
    ChatReqDto,
    ChatReqMetadataForQuery,
    ChatRespAction,
    ChatRespDto,
)
from app.entity.error import EbpInternalError
from app.routers.assistant_chat import assistant_chat


@pytest.mark.asyncio
async def test_assistant_chat(mock_http_request: Request, mock_token):
    # Mock dependencies
    mock_assistant_ctrl = AsyncMock()

    # Mock ChatReqDto
    mock_req = ChatReqDto(
        action=ChatReqAction.QUERY,
        metadata=ChatReqMetadataForQuery(
            thread_id="test_thread", user_query="Test query"
        ),
    )

    # Mock ChatRespDto
    mock_chat_resp = ChatRespDto(
        response="Test response", action=ChatRespAction.SHOW_REPLY, metadata=None
    )
    mock_assistant_ctrl.chat.return_value = mock_chat_resp

    # Call the function
    with patch("app.routers.assistant_chat.RequestContext") as _:
        result = await assistant_chat(
            req=mock_req,
            request=mock_http_request,
            token=mock_token,
            ctrl=mock_assistant_ctrl,
            x_request_id="test_request_id",
        )

    # Assertions
    assert isinstance(result, ChatRespDto)
    assert result.response == "Test response"

    mock_assistant_ctrl.chat.assert_called_once()


@pytest.mark.asyncio
async def test_assistant_chat_no_token(mock_http_request: Request):
    # Mock dependencies
    mock_assistant_ctrl = AsyncMock()

    # Mock ChatReqDto
    mock_req = ChatReqDto(
        action=ChatReqAction.QUERY,
        metadata=ChatReqMetadataForQuery(
            thread_id="test_thread", user_query="Test query"
        ),
    )

    # Call the function and expect an HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await assistant_chat(
            req=mock_req,
            request=mock_http_request,
            token=None,  # type: ignore
            ctrl=mock_assistant_ctrl,
            x_request_id="test_request_id",
        )

    # Assertions
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid credentials data"


@pytest.mark.asyncio
async def test_assistant_chat_ebp_internal_error(mock_http_request: Request):
    # Mock dependencies
    mock_assistant_ctrl = AsyncMock()

    # Mock ChatReqDto
    mock_req = ChatReqDto(
        action=ChatReqAction.QUERY,
        metadata=ChatReqMetadataForQuery(
            thread_id="test_thread", user_query="Test query"
        ),
    )

    # Simulate EbpInternalError
    mock_assistant_ctrl.chat.side_effect = EbpInternalError("Test EbpInternalError")

    # Call the function and expect an HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await assistant_chat(
            req=mock_req,
            request=mock_http_request,
            token=HTTPAuthorizationCredentials(
                scheme="Bearer", credentials="test_token"
            ),
            ctrl=mock_assistant_ctrl,
            x_request_id="test_request_id",
        )

    # Assertions
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Test EbpInternalError"

    mock_assistant_ctrl.chat.assert_called_once()
