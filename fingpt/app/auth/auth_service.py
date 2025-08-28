import base64
import json
import os
import time

from aiohttp import ClientSession
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.constant import (
    AUTH_TIMEOUT,
    CLIENT_ID,
    COOKIE_KEYS,
    GRANT_TYPE,
    SERVICE_URL,
    TOKEN_URL,
    USER_CONTEXT_URL,
)
from app.auth.user_info import UserInfo
from app.core.config import settings
from app.core.context import RequestContext
from app.entity import AuthReqDto, AuthRespDto
from app.entity.api import ApiHeader, AuthUserType
from app.entity.error import InvalidCredentialsError
from app.utils.modified_langfuse_decorator import observe

# TODO Clean up this service, many overlapping methods


class AuthService:

    def __init__(
        self,
    ):
        self.auth_info = None
        self.last_login = int(time.time())

    @observe(capture_input=False)
    async def login(
        self,
        ctx: RequestContext,
        req: AuthReqDto,
    ) -> AuthRespDto:
        user_info = UserInfo.from_auth_req(req)
        access_token = await self._access_token(ctx, user_info)
        agreement_id = await self._get_service_agreements(ctx, user_info, access_token)
        cookie = await self._set_user_context(
            ctx, user_info, access_token, agreement_id
        )

        auth_info = AuthRespDto(
            access_token=access_token,
            agreement_id=agreement_id,
            cookie=cookie,
            edge_domain=user_info.edge_domain,
        )
        self.auth_info = auth_info
        self.last_login = int(time.time())
        return auth_info

    async def check_auth(
        self,
        ctx: RequestContext,
        req: AuthReqDto,
    ) -> AuthRespDto:
        if self.auth_info and (int(time.time()) - self.last_login) < AUTH_TIMEOUT:
            return self.auth_info
        return await self.login(ctx, req)

    async def get_auth_header(
        self, request: Request, token: HTTPAuthorizationCredentials
    ) -> ApiHeader:
        cookie = ""
        for k, v in request.cookies.items():
            if k in COOKIE_KEYS:
                cookie += f"{k}={v}; "
        cookie = cookie.strip().strip(";")

        header = ApiHeader(
            cookie=cookie,
            token=token.credentials,
        )
        return header

    async def get_username_from_token(self, token: HTTPAuthorizationCredentials) -> str:
        token = token.credentials  # type: ignore
        coded_string = token.split(".")[1]  # type: ignore
        b64decode_str = base64.b64decode(coded_string.encode("utf-8") + b"==")
        data = json.loads(b64decode_str)
        username = data["preferred_username"]
        return username

    async def auto_auth(
        self,
        ctx: RequestContext,
    ):
        if (
            self.auth_info is None
            or (int(time.time()) - self.last_login) > AUTH_TIMEOUT
        ):
            return await self.reauth(ctx)

        return ApiHeader(
            cookie=self.auth_info.cookie,
            token=self.auth_info.access_token,
        )

    async def reauth(
        self,
        ctx: RequestContext,
    ):
        req = AuthReqDto(
            username=settings.ebp_test_account_username,
            password=settings.ebp_test_account_password,
            user_type=AuthUserType.RETAIL,
        )
        self.auth_info = await self.login(ctx, req)
        self.last_login = int(time.time())
        return ApiHeader(
            cookie=self.auth_info.cookie,
            token=self.auth_info.access_token,
        )

    @observe(capture_input=False)
    async def _access_token(
        self,
        ctx: RequestContext,
        user_info: UserInfo,
    ):
        logger = ctx.logger()
        url = TOKEN_URL.format(identity_domain=user_info.identity_domain)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-SDBXAZ-API-KEY": str(os.getenv("X_SDBXAZ_API_KEY")),
        }
        body = {
            "grant_type": GRANT_TYPE,
            "username": user_info.username,
            "password": user_info.password,
            "client_id": CLIENT_ID,
        }

        logger.debug(f"Getting token from: {url}")
        async with ClientSession() as session:
            async with session.post(url, data=body, headers=headers) as resp:
                if resp.status == 401:
                    raise InvalidCredentialsError("Invalid credentials!")
                if resp.status != 200:
                    raise Exception(f"Failed to get token. Response: {resp}")

                response = await resp.json()
                if "access_token" not in response:
                    raise ValueError("Access token not found in response")

        logger.info("Returning token...")

        return response["access_token"]

    @observe(capture_input=False)
    async def _get_service_agreements(
        self,
        ctx: RequestContext,
        user_info: UserInfo,
        access_token: str,
    ):
        logger = ctx.logger()
        url = SERVICE_URL.format(edge_domain=user_info.edge_domain)
        headers = {
            "Content-Type": "application/json",
            "X-SDBXAZ-API-KEY": str(os.getenv("X_SDBXAZ_API_KEY")),
            "Authorization": f"Bearer {access_token}",
        }

        logger.debug(f"Getting service agreements from: {url}")
        async with ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(
                        f"Failed to get service agreements. Response: {text}"
                    )

                response = await resp.json()
                if len(response) < 1 or "id" not in response[0]:
                    raise ValueError("Service agreements not found in response")

        logger.info("Returning service agreement id...")
        return response[0]["id"]

    @observe(capture_input=False)
    async def _set_user_context(
        self,
        ctx: RequestContext,
        user_info: UserInfo,
        access_token: str,
        service_agreement_id: str,
    ):
        logger = ctx.logger()
        url = USER_CONTEXT_URL.format(edge_domain=user_info.edge_domain)
        headers = {
            "Content-Type": "application/json",
            "X-SDBXAZ-API-KEY": str(os.getenv("X_SDBXAZ_API_KEY")),
            "Authorization": f"Bearer {access_token}",
        }
        body = {
            "serviceAgreementId": service_agreement_id,
        }

        logger.debug(f"Setting user context at: {url}")
        async with ClientSession() as session:
            async with session.post(url, json=body, headers=headers) as resp:
                if resp.status != 204:
                    text = await resp.text()
                    raise Exception(f"Failed to set user context. Response: {text}")

                cookie = ""
                for k, v in resp.cookies.items():
                    if k in COOKIE_KEYS:
                        cookie += f"{k}={v.value}; "

        logger.info("Returning cookie...")
        return cookie.strip().strip(";")
