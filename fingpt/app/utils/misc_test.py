import json
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request
from pydantic import BaseModel

from app.entity import ChatRespAction, ChatRespDto, ChatRespMetadataForChoices
from app.entity.chat_response import (
    ChatRespChoiceMetadataType,
    ChatRespMetadataForChoiceBaseType,
)
from app.utils.misc import ResponseSortingMiddleware, read_yaml


def test_read_yaml():
    class TestModel(BaseModel):
        first: str
        second: dict
        third: list

    content = """
first: hello
second:
    key: value
    another_dict:
        sub_key: sub_value
third:
    - 1
    - 2
    """
    test_file = "test.yaml"
    with open(test_file, "w") as f:
        f.write(content)

    model = read_yaml(TestModel, "test.yaml")
    assert model.first == "hello"
    assert model.second == {"key": "value", "another_dict": {"sub_key": "sub_value"}}
    assert model.third == [1, 2]
    os.remove(test_file)


@pytest.mark.asyncio
async def test_response_sorting_middleware():
    # Create a mock request
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }
    )

    # Create a mock response
    response_data = ChatRespDto(
        action=ChatRespAction.SHOW_CHOICES,
        thread_id="123",
        response="Hello",
        metadata=ChatRespMetadataForChoices(
            choices=[
                ChatRespMetadataForChoiceBaseType(
                    type=ChatRespChoiceMetadataType.ACCOUNT_CHOICE,
                    id="1",
                    is_enabled=False,
                ),
                ChatRespMetadataForChoiceBaseType(
                    type=ChatRespChoiceMetadataType.ACCOUNT_CHOICE,
                    id="2",
                    is_enabled=True,
                ),
            ]
        ),
    )
    # Create an instance of the middleware
    middleware = ResponseSortingMiddleware(app=None)

    # Create a mock call_next function

    async def body_stream():
        yield response_data.model_dump_json().encode("utf-8")

    mock_response = MagicMock()
    mock_response.body_iterator = body_stream()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.media_type = "application/json"
    # Create a mock call_next function
    call_next = AsyncMock(return_value=mock_response)
    response = await middleware.dispatch(request, call_next)

    # Check that the response is modified
    json_body = json.loads(response.body.decode("utf-8"))
    reverted_body = ChatRespDto(**json_body)
    assert reverted_body.metadata.choices[0].id == "2"


@pytest.mark.asyncio
async def test_response_sorting_no_change_middleware():
    # Create a mock request
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }
    )

    # Create a mock response
    response_data = ChatRespDto(
        action=ChatRespAction.SHOW_REPLY,
        thread_id="123",
        response="Hello",
        metadata=None,
    )
    # Create an instance of the middleware
    middleware = ResponseSortingMiddleware(app=None)

    # Create a mock call_next function

    async def body_stream():
        yield response_data.model_dump_json().encode("utf-8")

    mock_response = MagicMock()
    mock_response.body_iterator = body_stream()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.media_type = "application/json"
    # Create a mock call_next function
    call_next = AsyncMock(return_value=mock_response)
    response = await middleware.dispatch(request, call_next)

    # Check that the response is modified
    json_body = json.loads(response.body.decode("utf-8"))
    reverted_body = ChatRespDto(**json_body)
    assert reverted_body.action == ChatRespAction.SHOW_REPLY


@pytest.mark.asyncio
async def test_response_sorting_html_middleware():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }
    )
    response_data = """
    <html>
        <head>
            <title>Test</title>
        </head>
        <body>
            <h1>Hello</h1>
        </body>
    </html>
    """
    middleware = ResponseSortingMiddleware(app=None)

    async def body_stream():
        yield response_data.encode("utf-8")

    mock_response = MagicMock()
    mock_response.body_iterator = body_stream()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.media_type = "text/html"
    # Create a mock call_next function
    call_next = AsyncMock(return_value=mock_response)
    response = await middleware.dispatch(request, call_next)

    # Check that the response is modified
    assert response.body.decode("utf-8") == response_data
