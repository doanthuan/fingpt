from datetime import date, datetime, timedelta

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.structured import StructuredTool

from app.assistant_v2.card.constant import GET_RENEWABLE_CARD_TOOL_NAME
from app.assistant_v2.common.base_agent_config import extract_bb_retail_api_config
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, CONTEXT_KEY
from app.bb_retail.request import list_cards
from app.core import RequestContext
from app.utils.modified_langfuse_decorator import observe


class RenewableCardInput(BaseModel):
    expired_days: int = Field(
        description="Number of days before expiry. Input only an integer number without any operator",
    )


@observe()
async def _get_renewable_card(
    config: RunnableConfig,
    expired_days: int,
):
    if expired_days is None:
        expired_days = 30
    config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    api_config = extract_bb_retail_api_config(config_data)
    logger.info("Retrieving renewable card...")
    cards = await list_cards(ctx=ctx, config=api_config)
    renewable_cards = [
        card
        for card in cards
        if datetime.strptime(card.expiry_date, "%Y-%m-%d").date()
        <= date.today() + timedelta(days=expired_days)
    ]

    message = [entity.json() for entity in renewable_cards]
    return str(message)


get_renewable_card_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_get_renewable_card,
    name=GET_RENEWABLE_CARD_TOOL_NAME,
    description="Get list of user renewable cards",
    error_on_invalid_docstring=True,
)
