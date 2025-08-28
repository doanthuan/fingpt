import time
from unittest.mock import AsyncMock, patch

import pytest
from aioresponses import aioresponses
from fastapi import Request

from app.auth.auth_service import AuthService
from app.auth.constant import COOKIE_KEYS
from app.auth.user_info import UserInfo
from app.core.context import RequestContext
from app.entity import ApiHeader, AuthReqDto, AuthRespDto, AuthUserType


@pytest.fixture
def auth_service():
    return AuthService()


@pytest.fixture
def mock_request_context():
    return AsyncMock(spec=RequestContext)


@pytest.fixture
def mock_auth_req():
    return AuthReqDto(
        username="sdbxaz-stg-test_user",
        password="test_pass",  # pragma: allowlist secret
        user_type=AuthUserType.RETAIL,
    )


@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m


@pytest.mark.asyncio
async def test_login(auth_service, mock_request_context, mock_auth_req):
    with patch.object(
        auth_service, "_access_token", return_value="mock_token"
    ), patch.object(
        auth_service, "_get_service_agreements", return_value="mock_agreement_id"
    ), patch.object(
        auth_service, "_set_user_context", return_value="mock_cookie"
    ):

        result = await auth_service.login(mock_request_context, mock_auth_req)

        assert isinstance(result, AuthRespDto)
        assert result.access_token == "mock_token"
        assert result.agreement_id == "mock_agreement_id"
        assert result.cookie == "mock_cookie"


@pytest.mark.asyncio
async def test_check_auth_cached(auth_service, mock_request_context, mock_auth_req):
    mock_auth_resp = AuthRespDto(
        access_token="cached_token",
        agreement_id="cached_id",
        cookie="cached_cookie",
        edge_domain="cached.com",
    )
    auth_service.auth_info = mock_auth_resp
    auth_service.last_login = int(time.time())

    result = await auth_service.check_auth(mock_request_context, mock_auth_req)

    assert result == mock_auth_resp


@pytest.mark.asyncio
async def test_check_auth_expired(auth_service, mock_request_context, mock_auth_req):
    mock_auth_resp = AuthRespDto(
        access_token="new_token",
        agreement_id="new_id",
        cookie="new_cookie",
        edge_domain="new.com",
    )
    auth_service.auth_info = AuthRespDto(
        access_token="old_token",
        agreement_id="old_id",
        cookie="old_cookie",
        edge_domain="old.com",
    )
    auth_service.last_login = int(time.time()) - 3601  # Expired

    with patch.object(auth_service, "login", return_value=mock_auth_resp):
        result = await auth_service.check_auth(mock_request_context, mock_auth_req)

    assert result == mock_auth_resp


# class MockResponse:
#     def __init__(self, json_data, status_code):
#         self.json_data = json_data
#         self.status_code = status_code

#     def json(self):
#         return self.json_data


@pytest.mark.asyncio
async def test_access_token(auth_service, mock_request_context, mock_aioresponse):
    mock_user_info = UserInfo(
        username="test_user",
        password="test_pass",  # pragma: allowlist secret
        edge_domain="test.com",
        identity_domain="id.test.com",
        installation_name="test_installation",
        runtime_name="test_runtime",
    )

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"access_token": "mock_token"}

    with patch(
        "aiohttp.ClientSession.post",
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)),
    ):
        result = await auth_service._access_token(mock_request_context, mock_user_info)

    assert result == "mock_token"


@pytest.mark.asyncio
async def test_get_service_agreements(auth_service, mock_request_context):
    mock_user_info = UserInfo(
        username="test_user",
        password="test_pass",  # pragma: allowlist secret
        edge_domain="test.com",
        identity_domain="id.test.com",
        installation_name="test_installation",
        runtime_name="test_runtime",
    )
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = [{"id": "mock_agreement_id"}]

    with patch(
        "aiohttp.ClientSession.get",
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)),
    ):
        result = await auth_service._get_service_agreements(
            mock_request_context, mock_user_info, "mock_token"
        )

    assert result == "mock_agreement_id"


@pytest.mark.asyncio
async def test_get_auth_header(mock_token):
    # Arrange
    auth_service = AuthService()
    mock_request = Request({"type": "http", "headers": []})
    mock_request.cookies.__setitem__("USER_CONTEXT", "session_value")
    mock_request.cookies.__setitem__("ASLBSA", "value1")
    mock_request.cookies.__setitem__("ASLBSACORS", "value2")
    mock_request.cookies.__setitem__("XSRF-TOKEN", "xsrf_value")

    # Act
    result = await auth_service.get_auth_header(mock_request, mock_token)

    # Assert
    assert isinstance(result, ApiHeader)
    assert result.token == "mock_credentials"

    expected_cookie = "USER_CONTEXT=session_value; ASLBSA=value1; ASLBSACORS=value2; XSRF-TOKEN=xsrf_value"
    assert result.cookie == expected_cookie

    # Check that only cookies in COOKIE_KEYS are included
    for cookie in COOKIE_KEYS:
        assert cookie in result.cookie
    assert "cookie1" not in result.cookie
    assert "cookie2" not in result.cookie
