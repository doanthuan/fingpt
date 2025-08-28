import os
import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, Response

from app.auth.auth_controller import AuthController
from app.container import ServerContainer
from app.core import RequestContext
from app.entity import AuthReqDto, AuthRespDto
from app.utils.modified_langfuse_decorator import observe  # type: ignore

backbase_auth_router = APIRouter()


@observe()
@backbase_auth_router.post(
    "/v1/auth/login",
    summary="Login to Backbase API",
    response_description="The full user profile with token",
)
@inject
async def auth_login(
    req: AuthReqDto,
    response: Response,
    auth_ctrl: AuthController = Depends(
        Provide[ServerContainer.auth_module().auth_ctrl],
    ),
    x_request_id: Annotated[str, Header()] = str(uuid.uuid4()),
) -> AuthRespDto:
    """
    Login to Backbase EBP API

    This endpoint accepts a username and password to authenticate the user and return a token.

    Headers:
    - x-request-id (str): (OPTIONAL) The request ID.

    Args:
    - username: str - The username of our test account. Example: "sdbxaz-stg-sara"
    - password: str - The password
    - user_type: AuthUserType - The user type. Example: "retail"

    Returns:
    - JSON response containing the user profile and token.
    """
    ctx = RequestContext(x_request_id)
    logger = ctx.logger()
    logger.info(f"Received login request for user: {req.username}")
    default_username = os.getenv("EBP_TEST_ACCOUNT_USERNAME")
    default_password = os.getenv("EBP_TEST_ACCOUNT_PASSWORD") or ""
    if req.username == default_username and req.password == "********":
        req.password = default_password

    creds = await auth_ctrl.login(ctx, req)
    for morsel in creds.cookie.split(";"):
        key, value = morsel.strip().split("=")
        response.set_cookie(key, value)

    return creds
