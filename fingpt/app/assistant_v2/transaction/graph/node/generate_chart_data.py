import datetime
from collections import defaultdict
from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.transaction.constant import (
    TRANSACTION_REVIEW_DESCRIPTION,
    TRANSACTION_REVIEW_NO_DATA_CONTENT,
)
from app.assistant_v2.transaction.state import (
    TransactionAgentState,
    TransactionAgentStateFields,
)
from app.assistant_v2.util.misc import extract_config
from app.entity import (
    ChatRespAction,
    ChatRespDto,
    ChatRespMetadataForTransaction,
    Transaction,
    TransactionChartData,
)
from app.utils.modified_langfuse_decorator import observe

generate_chart_data_node = NodeName("generate_chart_data")


@observe()
async def generate_chart_data_func(
    state: TransactionAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data, ctx, logger = extract_config(config)
    transactions = state[TransactionAgentStateFields.CONFIRMED_TRANSACTIONS]

    try:
        logger.info("Generating chart data...")
        trans_data = _create_transaction_report_data(transactions)
        num_month = len(trans_data)

        trans_chart_data: list[TransactionChartData] = []
        for month, values in trans_data.items():
            month_name = datetime.date(1900, int(month[5:]), 1).strftime("%B")[:3]

            chart_data_item = TransactionChartData(
                month=month_name,
                transaction_count=values["total"],
                income=values["pos"],
                outcome=values["neg"],
            )

            trans_chart_data.append(chart_data_item)

        if num_month > 0:
            description = TRANSACTION_REVIEW_DESCRIPTION.format(
                num_month=num_month,
            )

        else:
            description = TRANSACTION_REVIEW_NO_DATA_CONTENT
        content = state[TransactionAgentStateFields.MESSAGES][-1].content
        response = ChatRespDto(
            action=ChatRespAction.SHOW_REPLY,
            thread_id=config_data[THREAD_ID_KEY],
            response=content,
            metadata=ChatRespMetadataForTransaction(
                description=description, chart_data=trans_chart_data
            ),
        )
        logger.info("Returning chart data...")
        config_data[PENDING_RESPONSE_KEY].append(response)
        return {
            TransactionAgentStateFields.MESSAGES: [AIMessage(content=content)],
            TransactionAgentStateFields.CONFIRMED_TRANSACTIONS: [],
            TransactionAgentStateFields.PROCESSED_TRANSACTIONS: [],
        }
    except Exception as e:
        logger.error(f"Error generating chart data: {e}")
        raise e


@observe()
def _create_transaction_report_data(transactions: list[Transaction]):
    transactions_by_month: dict[str, list[Any]] = defaultdict(list)
    for trans in transactions:
        month = trans.execution_date[:7]
        transactions_by_month[month].append(trans)

    trans_data: dict[str, Any] = {}
    for month, transactions in transactions_by_month.items():
        pos = sum(
            float(tran.amount)
            for tran in transactions
            if tran.transaction_type == "Deposit"
        )
        neg = sum(
            -float(tran.amount)
            for tran in transactions
            if tran.transaction_type == "Withdrawal"
        )

        trans_data[month] = {
            "pos": round(pos, 3),
            "neg": round(neg, 3),
            "total": len(transactions),
        }

    return trans_data
