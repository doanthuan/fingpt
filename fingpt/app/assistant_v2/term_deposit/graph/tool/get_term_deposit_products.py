from typing import Annotated, Any

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.structured import StructuredTool
from langgraph.prebuilt import InjectedState

from app.assistant_v2.term_deposit.constant import GET_TERM_DEPOSIT_PRODUCT_TOOL_NAME
from app.assistant_v2.term_deposit.graph.utils import update_term_deposit
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.bb_retail.request import list_td_products
from app.utils.modified_langfuse_decorator import observe


class DepositAmountInput(BaseModel):
    deposit_amount: float = Field(
        description="The deposit amount for creating term deposit or renew term deposit",
    )
    state: Annotated[dict[str, Any], InjectedState] = Field(
        description="The state of the graph"
    )


@observe()
async def _get_term_deposit_products(
    deposit_amount: float,
    config: RunnableConfig,
    state: Annotated[dict[str, Any], InjectedState],
):
    config_data, ctx, logger = extract_config(config)
    logger.debug("Retrieving all term deposit products ...")

    term_deposit_products = await list_td_products(ctx=ctx)

    logger.debug(
        f"Retrieving {len(term_deposit_products)} term deposit products"  # type: ignore
    )

    updated_term_deposit_products = update_term_deposit(
        deposit_amount=float(deposit_amount),
        list_term_deposit=term_deposit_products,
    )

    term_unit = state.get(TermDepositAgentStateFields.TERM_UNIT)
    term_number = state.get(TermDepositAgentStateFields.TERM_NUMBER)
    if term_unit and term_number:
        updated_term_deposit_products = {
            key: value
            for key, value in updated_term_deposit_products.items()
            if value.term_unit == term_unit and value.term_number == term_number
        }

    logger.info("Returning TD products list...")

    message = [entity.json() for entity in updated_term_deposit_products.values()]
    return str(message)


get_term_deposit_product_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_get_term_deposit_products,
    name=GET_TERM_DEPOSIT_PRODUCT_TOOL_NAME,
    description="Get list of term deposit products",
    args_schema=DepositAmountInput,
    error_on_invalid_docstring=True,
)
