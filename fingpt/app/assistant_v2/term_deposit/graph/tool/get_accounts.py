from typing import Annotated, Any

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.structured import StructuredTool
from langgraph.prebuilt import InjectedState

from app.assistant_v2.common.base_agent_config import extract_bb_retail_api_config
from app.assistant_v2.term_deposit.constant import GET_ACCOUNT_TOOL_NAME
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.bb_retail.request import list_accounts
from app.entity import ActiveAccount
from app.utils.modified_langfuse_decorator import observe


class AccountInput(BaseModel):
    state: Annotated[dict[str, Any], InjectedState] = Field(
        description="The state of the graph"
    )


@observe()
async def _get_account(
    state: Annotated[dict[str, Any], InjectedState],
    config: RunnableConfig,
):
    result: list[ActiveAccount] = []
    config_data, ctx, logger = extract_config(config)
    api_config = extract_bb_retail_api_config(config_data)
    logger.info("Retrieving account...")
    accounts = await list_accounts(ctx=ctx, config=api_config)
    deposit_amount = state.get(TermDepositAgentStateFields.DEPOSIT_AMOUNT, 0)
    for account in accounts:
        if account.available_balance >= deposit_amount and account.booked_balance >= 0:
            account.is_usable = True
        else:
            account.is_usable = False
        result.append(account)
    message = [entity.json() for entity in result]
    return str(message)


get_account_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_get_account,
    name=GET_ACCOUNT_TOOL_NAME,
    description="Get list of user accounts",
    error_on_invalid_docstring=True,
)
