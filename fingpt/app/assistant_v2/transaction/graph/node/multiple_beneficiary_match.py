from typing import Any, Dict

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.transaction.graph.node.select_beneficiary import (
    select_beneficiary_node,
)
from app.assistant_v2.transaction.state import (
    TransactionAgentState,
    TransactionAgentStateFields,
)
from app.assistant_v2.util.misc import extract_config
from app.entity import (
    ChatRespAction,
    ChatRespChoiceMetadataType,
    ChatRespDto,
    ChatRespMetadataForBeneficiaryChoice,
    ChatRespMetadataForChoices,
    MissingStateDataError,
)
from app.utils.modified_langfuse_decorator import observe

multiple_beneficiary_match_node = NodeName("multiple_beneficiary_match")


@observe()
async def multiple_beneficiary_match_func(
    state: TransactionAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data, ctx, logger = extract_config(config)
    logger.info("Multiple matched beneficiaries found...")
    processed = state[TransactionAgentStateFields.PROCESSED_TRANSACTIONS]
    thread_id = config_data[THREAD_ID_KEY]
    assert processed is not None, MissingStateDataError(
        "Processed transactions not found in state"
    )
    logger.info("Building up choices...")

    choices = ChatRespMetadataForChoices(choices=[])
    for key, value in processed.items():
        choice1 = ChatRespMetadataForBeneficiaryChoice(
            id=key,
            name=value[0].counterparty_name,
            account_number=key,
            type=ChatRespChoiceMetadataType.BENEFICIARY_CHOICE,
        )
        choice2 = ChatRespMetadataForBeneficiaryChoice(
            id=key,
            name=value[0].counterparty_name,
            account_number=key,
            type=ChatRespChoiceMetadataType.BENIFICIARY_TYPO_CHOICE,
        )
        choices.choices.append(choice1)
        choices.choices.append(choice2)

    last_messages = state[TransactionAgentStateFields.MESSAGES][-1]
    response = ChatRespDto(
        action=ChatRespAction.SHOW_CHOICES,
        thread_id=thread_id,
        response=last_messages.content,
        metadata=choices,
    )
    logger.info("Saving response...")
    config_data[PENDING_RESPONSE_KEY].append(response)
    if len(choices.choices) > 1:
        logger.info("Multiple choices found...")
        return {
            TransactionAgentStateFields.RESUME_NODE: select_beneficiary_node,
        }
    return {TransactionAgentStateFields.MESSAGES: []}
