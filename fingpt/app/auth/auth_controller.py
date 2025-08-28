from fastapi import HTTPException

from app.auth.auth_service import AuthService
from app.core.context import RequestContext
from app.entity import AuthReqDto, AuthRespDto
from app.entity.error import InvalidCredentialsError
from app.utils.modified_langfuse_decorator import (  # type: ignore
    langfuse_context,
    observe,
)


class AuthController:
    def __init__(
        self,
        auth_srv: AuthService,
    ):
        self.auth_srv = auth_srv

    @observe(name="Login", capture_input=False)
    async def login(
        self,
        ctx: RequestContext,
        req: AuthReqDto,
    ) -> AuthRespDto:
        logger = ctx.logger()
        langfuse_context.update_current_trace(
            session_id=ctx.request_id(),
        )
        logger.info(f"Logging in user: {req.username}")
        try:
            return await self.auth_srv.login(ctx, req)
        except InvalidCredentialsError:
            logger.error("Wrong username or password")
            raise HTTPException(
                status_code=401,
                detail="Wrong username or password",
            )
        except Exception as e:
            logger.error(f"Error logging in user: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error: " + str(e),
            )
        finally:
            logger.info("Controller exiting...")
