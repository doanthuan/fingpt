import asyncio
import subprocess
import uuid

from aiohttp import ClientSession
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials

from app.bb_retail.request import BbApiRequest
from app.core import RequestContext
from app.core.config import settings
from app.entity import BbQueryPaging
from app.entity.bb_api import BbApiConfig, BBRuntime
from app.entity.command_request import (
    AvailableServiceName,
    BashCommandDto,
    CommandDto,
    CommandType,
    RequestCommandDto,
    ServiceCallDto,
)


class CommandController:
    def __init__(self):
        pass

    @staticmethod
    async def _execute_bash_command(command: BashCommandDto):
        process = await asyncio.create_subprocess_shell(
            command.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return stdout.decode(), stderr.decode()

    @staticmethod
    async def _execute_request_command(
        command: RequestCommandDto,
        request: Request,
        token: HTTPAuthorizationCredentials,
    ):
        headers = command.headers or {}
        cookies = None
        if request:
            headers["authorization"] = token.credentials
            headers.update(request.headers)
            cookies = request.cookies

        async with ClientSession() as session:
            async with session.request(
                method=command.method,
                url=command.url,
                headers=headers,
                cookies=cookies,
                data=command.data,
                params=command.params,
            ) as response:
                return await response.text()

    @staticmethod
    async def _execute_call_service(
        command: ServiceCallDto, request: Request, token: HTTPAuthorizationCredentials
    ):
        ctx = RequestContext(request.headers.get("x-request-id") or str(uuid.uuid4()))
        config = BbApiConfig(
            ebp_access_token=token.credentials if token is not None else "",
            ebp_cookie=request.headers.get("cookie") or "",
            ebp_edge_domain=settings.ebp_edge_domain,
        )
        bb_api_request = BbApiRequest(BBRuntime(command.env) if command.env else None)
        service_mapping = {
            AvailableServiceName.CONTACT_SERVICE: (
                bb_api_request.list_contacts,
                (ctx, config, BbQueryPaging()),
            ),
            AvailableServiceName.PRODUCT_SUMMARY_SERVICE: (
                bb_api_request.list_accounts,
                (ctx, config),
            ),
            AvailableServiceName.TRANSACTION_SERVICE: (
                bb_api_request.filter_transactions,
                (ctx, config),
            ),
            AvailableServiceName.CARD_SERVICE: (
                bb_api_request.list_cards,
                (ctx, config),
            ),
        }
        service, args = service_mapping.get(command.service_name)
        return await service(*args)

    async def execute(
        self,
        ctx: RequestContext,
        req: CommandDto,
        request: Request = None,
        token: HTTPAuthorizationCredentials = None,
    ):
        logger = ctx.logger()
        logger.info(f"Received command: {req.command}")
        if req.command_type == CommandType.BASH_CMD:
            return await self._execute_bash_command(req.command)
        elif req.command_type == CommandType.REQUEST_CMD:
            return await self._execute_request_command(req.command, request, token)
        elif req.command_type == CommandType.SERVICE_CALL:
            return await self._execute_call_service(req.command, request, token)
        else:
            return "Command type not supported"
