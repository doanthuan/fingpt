import uuid
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.assistant_v2.primary.controller import AssistantController
from app.auth.constant import COOKIE_KEYS
from app.container import ServerContainer
from app.core import RequestContext
from app.entity.api import ApiHeader
from app.entity.chat_request import ChatReqDto
from app.entity.chat_response import ChatRespDto
from app.entity.error import EbpInternalError
from app.utils.modified_langfuse_decorator import observe  # type: ignore

assistant_chat_router = APIRouter()
auth_scheme = HTTPBearer(auto_error=False)


@observe()
@assistant_chat_router.post(
    "/v1/assistant/chat",
    summary="Use this API to converse with the Backbase intelligent assistant",
    response_description="The ChatRespDto object to the frontend client",
)
@inject
async def assistant_chat(
    req: ChatReqDto,
    request: Request,
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    ctrl: AssistantController = Depends(
        Provide[ServerContainer.assistant_module().controller],
    ),
    x_request_id: Annotated[str, Header()] = str(uuid.uuid4()),
) -> Optional[ChatRespDto]:
    """
    LOGIN REQUIRED: Make sure you use login API first!

    Our all-in-one intelligent assistant to support all of your needs.

    Headers:
    - x-request-id (str): (OPTIONAL) The request ID.

    Args:
    - request (ChatReqDto): The user request object

    Returns:
    - JSON response from the assistant

    """
    ctx = RequestContext(x_request_id)
    logger = ctx.logger()

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

    req.metadata.thread_id = req.metadata.thread_id or x_request_id
    logger.info(f'Received request for: "{req.model_dump()}"')
    try:
        return await ctrl.chat(ctx, header, req)

    except EbpInternalError as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise e
