import random
import uuid
from typing import Annotated

from dependency_injector.wiring import inject
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core import RequestContext
from app.entity.suggestion import Platform, Suggestion, SuggestionResp, SuggestionType

suggestion_router = APIRouter()
auth_scheme = HTTPBearer(auto_error=False)

FIRST_SAMPLE = "What services can you do for me?"


@suggestion_router.get("/v1/suggestions")
@inject
async def get_suggestions(
    request: Request,
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    x_request_id: Annotated[str, Header()] = str(uuid.uuid4()),
    platform: Platform = Platform.WEB,
) -> SuggestionResp:
    """
    Get suggestions
    Headers:
    - x-request-id (str): (OPTIONAL) The request ID.
    Args:
        req (SuggestionReq): request json for suggestions
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

    suggestions: dict[Platform, list[str]] = {
        Platform.MOBILE: [
            "Show me recent transactions related to food",
            "Show me Apple stock report",
            "I want to make a bank transfer",
            "How many cards do I have?",
            "Show me recent transactions related to Uber",
            "How is Tesla doing recently?",
            "Create a new term deposit of $10,000",
            "Renew my term deposit",
            "Renew my card",
        ],
        Platform.WEB: [
            "Show me recent transactions related to food",
            "Show me Apple stock report",
            "I want to make a bank transfer",
            "Show me recent transactions related to Uber",
            "How is Tesla doing recently?",
        ],
    }

    # @SONAR_STOP@
    samples = [FIRST_SAMPLE] + random.sample(suggestions[platform], 3)
    # @SONAR_START@

    return SuggestionResp(
        type=SuggestionType.WELCOME,
        thread_id=x_request_id,
        platform=platform,
        suggestions=[
            Suggestion(
                content=content,
                is_highlighted=True if content == FIRST_SAMPLE else False,
            )
            for content in samples
        ],
    )
