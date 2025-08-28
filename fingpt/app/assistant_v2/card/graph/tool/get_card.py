from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.structured import StructuredTool

from app.assistant_v2.card.constant import GET_CARD_TOOL_NAME
from app.assistant_v2.common.base_agent_config import extract_bb_retail_api_config
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, CONTEXT_KEY
from app.bb_retail.request import list_cards
from app.core import RequestContext
from app.utils.modified_langfuse_decorator import observe


@observe()
async def _get_card(
    config: RunnableConfig,
):
    config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    api_config = extract_bb_retail_api_config(config_data)
    logger.info("Retrieving card...")
    cards = await list_cards(ctx=ctx, config=api_config)
    message = [entity.json() for entity in cards]
    return str(message)


get_card_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_get_card,
    name=GET_CARD_TOOL_NAME,
    description="Get list of user cards",
    error_on_invalid_docstring=True,
)
