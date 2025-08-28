from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.structured import StructuredTool

from app.assistant_v2.common.base_agent_config import extract_bb_retail_api_config
from app.assistant_v2.term_deposit.constant import GET_TERM_DEPOSIT_ACCOUNT_TOOL_NAME
from app.assistant_v2.term_deposit.graph.utils import _update_term_account
from app.assistant_v2.util.misc import extract_config
from app.bb_retail.request import list_term_deposit_accounts
from app.utils.modified_langfuse_decorator import observe


class DepositAmountInput(BaseModel):
    deposit_amount: str = Field(
        description="The deposit amount for renewing term deposit. Can be empty string",
    )


@observe()
async def _get_term_deposit_accounts(
    deposit_amount: str,
    config: RunnableConfig,
):
    if deposit_amount.strip() == "":
        deposit_amount = None
    elif deposit_amount.strip() != "":
        deposit_amount = float(deposit_amount)

    config_data, ctx, logger = extract_config(config)
    api_config = extract_bb_retail_api_config(config_data=config_data)
    logger.debug("Retrieving all term deposit accounts ...")

    term_deposit_accounts = await list_term_deposit_accounts(ctx=ctx, config=api_config)

    logger.info("Filtering term deposit accounts ...")

    filtered_accounts = _update_term_account(
        deposit_amount=deposit_amount,
        list_term_deposit_account=term_deposit_accounts,
    )
    logger.info(f"Filtered accounts: {filtered_accounts}")
    message = [entity.json() for entity in filtered_accounts.values()]

    return str(message)


get_term_deposit_account_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_get_term_deposit_accounts,
    name=GET_TERM_DEPOSIT_ACCOUNT_TOOL_NAME,
    description="Get list of term deposit accounts",
    args_schema=DepositAmountInput,
    error_on_invalid_docstring=True,
)
