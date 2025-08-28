from typing import Annotated, Any

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.structured import StructuredTool
from langgraph.prebuilt import InjectedState

from app.assistant_v2.common.base_agent_config import extract_bb_retail_api_config
from app.assistant_v2.transfer.constant import GET_ACCOUNT_TOOL_NAME
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.bb_retail.request import list_accounts
from app.utils.modified_langfuse_decorator import observe


class GetAccountInput(BaseModel):
    transfer_amount: float = Field(
        description="The amount to be transferred, the value must not be null",
    )
    state: Annotated[dict[str, Any], InjectedState] = Field(
        description="The state of the graph"
    )


@observe()
async def _get_account(
    transfer_amount: float,
    config: RunnableConfig,
    state: Annotated[dict[str, Any], InjectedState],
):
    selected_account = state.get(TransferAgentStateFields.SELECTED_ACCOUNT)
    if selected_account:
        message = [selected_account.json()]
        return str(message)

    config_data, ctx, logger = extract_config(config)
    api_config = extract_bb_retail_api_config(config_data)
    logger.info("Retrieving account...")
    accounts = await list_accounts(ctx=ctx, config=api_config)
    for account in accounts:
        if account.available_balance < transfer_amount or account.booked_balance < 0:
            account.is_usable = False
    message = [entity.json() for entity in accounts]
    return str(message)


get_account_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_get_account,
    name=GET_ACCOUNT_TOOL_NAME,
    description="Get list of user accounts",
    args_schema=GetAccountInput,
    error_on_invalid_docstring=True,
)
