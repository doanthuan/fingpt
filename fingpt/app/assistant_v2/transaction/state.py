import operator
from typing import Annotated, Any, Sequence

from attr import dataclass

from app.assistant_v2.common.base_agent_config import BbRetailAgentConfig
from app.assistant_v2.common.base_agent_state import (
    BaseAgentState,
    BaseAgentStateFields,
)


class TransactionAgentState(BaseAgentState):
    user_messages: Annotated[
        Sequence[str],
        operator.add,
    ]

    search_term: str

    filtered_transactions: list[Any]
    processed_transactions: dict[str, list[Any]]
    confirmed_transactions: list[Any]


@dataclass
class TransactionAgentStateFields(BaseAgentStateFields):
    USER_MESSAGES = "user_messages"

    SEARCH_TERM = "search_term"

    FILTERED_TRANSACTIONS = "filtered_transactions"
    PROCESSED_TRANSACTIONS = "processed_transactions"
    CONFIRMED_TRANSACTIONS = "confirmed_transactions"


TransactionAgentStateFields.validate_agent_fields(TransactionAgentState)


class TransactionAgentConfig(BbRetailAgentConfig):
    pass
