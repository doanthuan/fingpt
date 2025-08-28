import json
from typing import Annotated, Any, Dict, List

from black.trans import defaultdict
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.structured import StructuredTool
from langgraph.prebuilt import InjectedState

from app.assistant_v2.common.base_agent_config import extract_bb_retail_api_config
from app.assistant_v2.transaction.constant import FILTER_TRANSACTION_TOOL_NAME
from app.assistant_v2.transaction.state import TransactionAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.bb_retail.request import filter_transactions
from app.entity import BbQueryParams
from app.utils.modified_langfuse_decorator import observe


class FilterTransactionInput(BaseModel):
    search_term: str = Field(
        description="The search phrase extracted from the user query"
        " which will be used to retrieve the relevant transaction data"
        "Example of the search term from the user query: \n"
        "User: Show me all transactions for Uber\n"
        "Search term: Uber"
        "User: How many times have I eaten out lately?\n"
        "Search term: food",
    )

    state: Annotated[Dict[str, Any], InjectedState] = Field(
        description="The state of the graph"
    )


@observe()
async def _filter_transaction(
    search_term: str,
    config: RunnableConfig,
    state: Annotated[Dict[str, Any], InjectedState],
) -> str:
    if (
        TransactionAgentStateFields.CONFIRMED_TRANSACTIONS in state
        and state[TransactionAgentStateFields.CONFIRMED_TRANSACTIONS]
    ):
        confirmed_transactions = state[
            TransactionAgentStateFields.CONFIRMED_TRANSACTIONS
        ]
        return json.dumps(
            {"selected_beneficiary": [item.dict() for item in confirmed_transactions]}
        )

    config_data, ctx, logger = extract_config(config)
    if len(search_term) < 3:
        search_term += "   "
    api_config = extract_bb_retail_api_config(config_data)
    transactions = await filter_transactions(
        ctx, api_config, BbQueryParams(query=search_term, fr0m=0, size=100)
    )
    processed_transactions: Dict[str, List[Dict]] = defaultdict(list)
    for trans in transactions:
        account_key = f"{trans.counterparty_account}-{trans.counterparty_name}"
        processed_transactions[account_key].append(trans.dict())

    logger.info(f"Returning filtered transactions for search term: {search_term}")
    return json.dumps(processed_transactions)


filter_transaction_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_filter_transaction,
    name=FILTER_TRANSACTION_TOOL_NAME,
    description="This tool is used to get the transactions report for a given search term. \n"
    "It also uses to get the beneficiary report. \n"
    "When to call: When the user asks for transactions for a specific entity. "
    "Also when user change or update the search term\n"
    "Without calling this tool, the transactions information will not be available\n"
    "Example: User: Show me all transactions for Uber\n"
    "This tool will be used to get the transactions for Uber",
    args_schema=FilterTransactionInput,
    error_on_invalid_docstring=True,
)
