from unittest.mock import AsyncMock

import pytest
from fastapi import Request

from app.bb_retail.request import BbApiRequest
from app.command.command_controller import CommandController
from app.core import RequestContext
from app.entity import Contact
from app.entity.command_request import (
    AvailableServiceName,
    BashCommandDto,
    CommandDto,
    CommandType,
    RequestCommandDto,
    ServiceCallDto,
)


@pytest.fixture()
def controller():
    return CommandController()


@pytest.mark.asyncio
async def test_execute_bash_command(controller):
    command = CommandDto(
        command_type=CommandType.BASH_CMD,
        command=BashCommandDto(command="echo hello"),
    )
    ctx = RequestContext("test")
    result, error = await controller.execute(ctx, command)
    assert result == "hello\n"
    assert error == ""


@pytest.mark.asyncio
async def test_execute_request_post_command(mock_aioresponse, controller):
    mock_aioresponse.post("http://test_post.com", payload={"key": "value"})
    command = CommandDto(
        command_type=CommandType.REQUEST_CMD,
        command=RequestCommandDto(
            method="POST",
            url="http://test_post.com",
            headers={"Content-Type": "application/json"},
            data={"key": "value"},
        ),
    )
    ctx = RequestContext("test")
    result = await controller.execute(ctx, command)
    assert result == '{"key": "value"}'


@pytest.mark.asyncio
async def test_execute_request_get_command(mock_aioresponse, controller):
    mock_aioresponse.get("http://test.com", payload={"key": "value"})
    command = CommandDto(
        command_type=CommandType.REQUEST_CMD,
        command=RequestCommandDto(
            method="GET",
            url="http://test.com",
        ),
    )
    ctx = RequestContext("test")
    result = await controller.execute(ctx, command)
    assert result == '{"key": "value"}'


@pytest.mark.asyncio
async def test_execute_service_call(mocker, controller):
    mocker.patch.object(
        BbApiRequest,
        "list_contacts",
        AsyncMock(return_value=[Contact(id="1", name="John")]),
    )
    command = CommandDto(
        command_type=CommandType.SERVICE_CALL,
        command=ServiceCallDto(
            service_name=AvailableServiceName.CONTACT_SERVICE,
        ),
    )
    ctx = RequestContext("test")
    result = await controller.execute(
        ctx, command, Request(scope={"type": "http", "headers": {}})
    )
    assert result == [Contact(id="1", name="John")]
