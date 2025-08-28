import os
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Response
from fastapi.testclient import TestClient

from app.auth.auth_controller import AuthController
from app.container import ServerContainer
from app.entity import AuthReqDto, AuthRespDto
from app.entity.api import AuthUserType
from app.routers.backbase_auth import auth_login, backbase_auth_router

# Create a TestClient for the FastAPI app
client = TestClient(backbase_auth_router)


@pytest.fixture
def mock_auth_controller():
    mock = AsyncMock(AuthController)
    mock.login.return_value = AuthRespDto(
        agreement_id="test_agreement_id",
        edge_domain="test_edge_domain",
        access_token="test_access_token",
        cookie="sessionid=test_session_id",
    )
    return mock


@pytest.fixture
def mock_env_vars():
    with patch.dict(
        os.environ,
        {
            "EBP_TEST_ACCOUNT_USERNAME": "test_username",
            "EBP_TEST_ACCOUNT_PASSWORD": "test_password",  # pragma: allowlist secret
        },
    ):
        yield


@pytest.fixture
def mock_server_container(mock_auth_controller):
    container = ServerContainer()
    container.auth_module().auth_ctrl.override(mock_auth_controller)
    return container


@pytest.mark.asyncio
async def test_auth_login(mock_env_vars, mock_server_container):
    req_data = {
        "username": "test_username",
        "password": "********",
        "user_type": AuthUserType.RETAIL,
    }
    response = Response()
    x_request_id = str(uuid.uuid4())

    with patch("app.routers.backbase_auth.RequestContext") as MockRequestContext:
        mock_ctx = MockRequestContext.return_value
        mock_ctx.logger.return_value.info = print

        with patch(
            "app.routers.backbase_auth.Provide",
            return_value=mock_server_container.auth_module().auth_ctrl,
        ):
            response = await auth_login(
                req=AuthReqDto(**req_data), response=response, x_request_id=x_request_id
            )

    assert response.agreement_id == "test_agreement_id"
    assert response.edge_domain == "test_edge_domain"
    assert response.access_token == "test_access_token"
    assert response.cookie == "sessionid=test_session_id"
