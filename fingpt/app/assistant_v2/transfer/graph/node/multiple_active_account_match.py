from typing import Any, Dict

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.transfer.graph.node.select_account import select_account_node
from app.assistant_v2.transfer.state import TransferAgentState, TransferAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.entity import (
    ActiveAccount,
    ChatRespAction,
    ChatRespDto,
    ChatRespMetadataForAccountChoice,
    ChatRespMetadataForChoices,
)
from app.utils.modified_langfuse_decorator import observe

multiple_active_account_match_node = NodeName("multiple_active_account_match")


def _build_choices_from_accounts(
    accounts: list[ActiveAccount],
    minimum_required_amount: float = 0,
) -> ChatRespMetadataForChoices:
    return ChatRespMetadataForChoices(
        choices=[
            ChatRespMetadataForAccountChoice(
                id=account.id,
                name=account.name,
                available_balance=account.available_balance,
                currency=account.currency,
                is_enabled=account.available_balance >= minimum_required_amount
                and account.booked_balance >= 0,
                bban=account.identifications.bban if account.identifications else None,
                product_type=account.product_type,
            )
            for account in accounts
        ]
    )


@observe()
async def multiple_active_account_match_func(
    state: TransferAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info("Multiple matched accounts found...")
    last_message = state[TransferAgentStateFields.MESSAGES][-1]
    response = ChatRespDto(
        action=ChatRespAction.SHOW_CHOICES,
        thread_id=config_data[THREAD_ID_KEY],
        response=last_message.content,
        metadata=_build_choices_from_accounts(
            state[TransferAgentStateFields.ACTIVE_ACCOUNTS],
            state[TransferAgentStateFields.TRANSFER_AMOUNT] or 0.0,
        ),
    )
    config_data[PENDING_RESPONSE_KEY].append(response)
    if any([c.is_enabled for c in response.metadata.choices]):
        return {
            TransferAgentStateFields.RESUME_NODE: select_account_node,
        }
    return {TransferAgentStateFields.MESSAGES: []}
