import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.auth_service import AuthService
from app.auth.constant import COOKIE_KEYS
from app.container import ServerContainer
from app.core import RequestContext
from app.entity.api import ApiHeader
from app.entity.profile import ProfileDataReq, ProfileDataResp
from app.profile.profile_controller import ProfileController

profile_router = APIRouter()
auth_scheme = HTTPBearer(auto_error=False)


@profile_router.post("/v1/profile")
@inject
async def update_profile(
    req: ProfileDataReq,
    request: Request,
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    ctrl: ProfileController = Depends(
        Provide[ServerContainer.profile_module().profile_ctrl]
    ),
    auth_srv: AuthService = Depends(
        Provide[ServerContainer.auth_module().auth_srv],
    ),
    x_request_id: Annotated[str, Header()] = str(uuid.uuid4()),
) -> ProfileDataResp:
    """
    LOGIN REQUIRED: Make sure you use login API first!
    Set user profile
    Headers:
    - x-request-id (str): (OPTIONAL) The request ID.
    Args:
        req (ProfileData): request json for user profile
        token (HTTPAuthorizationCredentials): authorization token
    """
    ctx = RequestContext(x_request_id)
    logger = ctx.logger()
    logger.debug(f'Request headers: "{request.headers}"')

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials data",
            headers={"www-authenticate": 'Bearer error="invalid_token"'},
        )

    cookie = ""
    for k, v in request.cookies.items():
        if k in COOKIE_KEYS:
            cookie += f"{k}={v}; "
    cookie = cookie.strip().strip(";")

    header = ApiHeader(
        cookie=cookie,
        token=token.credentials,
    )

    try:
        username = await auth_srv.get_username_from_token(token)
        ctx = RequestContext(x_request_id)
        return await ctrl.update_profile(ctx, header, username, req)

    except HTTPException as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise e

    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )


@profile_router.get("/v1/profile")
@inject
async def get_profile(
    request: Request,
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    ctrl: ProfileController = Depends(
        Provide[ServerContainer.profile_module().profile_ctrl]
    ),
    auth_srv: AuthService = Depends(
        Provide[ServerContainer.auth_module().auth_srv],
    ),
    x_request_id: Annotated[str, Header()] = str(uuid.uuid4()),
) -> ProfileDataResp:
    """
    LOGIN REQUIRED: Make sure you use login API first!
    Return user profile
    Headers:
    - x-request-id (str): (OPTIONAL) The request ID.
    Args:
        token (HTTPAuthorizationCredentials): authorization token

    Returns:
        ProfileData: user profile
    """

    ctx = RequestContext(x_request_id)
    logger = ctx.logger()
    logger.debug(f'Request headers: "{request.headers}"')

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials data",
            headers={"www-authenticate": 'Bearer error="invalid_token"'},
        )

    try:
        username = await auth_srv.get_username_from_token(token)
        return await ctrl.get_profile(ctx, username)

    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )
