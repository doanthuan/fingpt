import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.constant import COOKIE_KEYS
from app.container import ServerContainer
from app.core.context import RequestContext
from app.entity.api import ApiHeader
from app.entity.error import EbpInternalError
from app.entity.intent import IntentReqDto, IntentRespDto
from app.intent.intent_controller import IntentController
from app.utils.modified_langfuse_decorator import observe  # type: ignore

intent_router = APIRouter()
auth_scheme = HTTPBearer(auto_error=False)


@observe(name="/v1/intent/analyze")
@intent_router.post(
    "/v1/intent/analyze",
    summary="Analyze the user's intent and build up the intent object",
    response_description="The Intent object",
    response_model=IntentRespDto,
)
@inject
async def analyze_intent(
    req: IntentReqDto,
    request: Request,
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    ctrl: IntentController = Depends(
        Provide[ServerContainer.intent_module().controller],
    ),
    x_request_id: Annotated[str, Header()] = str(uuid.uuid4()),
) -> IntentRespDto:
    """
    LOGIN REQUIRED: Make sure you use login API first!

    Analyze the user's intent based on the provided request.

    This endpoint processes the user's intent and returns the analyzed Intent object.

    Headers:
    - x-request-id (str): (OPTIONAL) The request ID.

    Args:
    - req (IntentReqDto): The intent request object containing user query and other relevant information.

    Returns:
    - IntentRespDto: The analyzed Intent object.

    Raises:
    - HTTPException: If there's an error during the API call or processing.

    """
    ctx = RequestContext(x_request_id)
    logger = ctx.logger()
    logger.info(f'Received request for: "{req.model_dump()}"')

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

    header = ApiHeader(
        cookie=cookie,
        token=token.credentials,
    )

    try:
        return await ctrl.process_intent(ctx, header, req)

    except EbpInternalError as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise e
