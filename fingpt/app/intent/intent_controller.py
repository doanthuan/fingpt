from fastapi import HTTPException

from app.core.context import RequestContext
from app.core.logging import Logger
from app.entity import IntentReqDto, IntentRespDto
from app.entity.api import ApiHeader
from app.intent.intent_service import IntentService
from app.utils.modified_langfuse_decorator import observe  # type: ignore
from app.utils.modified_langfuse_decorator import langfuse_context


class IntentController:
    def __init__(self, intent_srv: IntentService):
        self.intent_srv = intent_srv

    @observe(name="Process Intent Controller")
    async def process_intent(
        self,
        ctx: RequestContext,
        header: ApiHeader,
        req: IntentReqDto,
    ) -> IntentRespDto:
        logger: Logger = ctx.logger()
        langfuse_context.update_current_trace(
            session_id=ctx.request_id(),
        )
        logger.info(f"Processing intent: {req.model_dump()}")

        try:
            return await self.intent_srv.analyze_intent(
                ctx=ctx,
                header=header,
                req=req,
            )

        except Exception as e:
            logger.error(f"Error processing intent: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error: " + str(e),
            )
        finally:
            logger.info("Intent Controller exiting...")
