import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.command.command_controller import CommandController
from app.container import ServerContainer
from app.core import RequestContext
from app.entity.command_request import CommandDto

command_router = APIRouter()
auth_scheme = HTTPBearer()


@command_router.post("/v1/tools/command")
@inject
async def command(
    req: CommandDto,
    request: Request,
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    ctrl: CommandController = Depends(
        Provide[ServerContainer.command_module().command_ctrl]
    ),
):
    ctx = RequestContext(str(uuid.uuid4()))
    return await ctrl.execute(ctx, req, request, token)
