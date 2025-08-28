from typing import Any

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.transfer.graph.node.select_contact import select_contact_node
from app.assistant_v2.transfer.state import TransferAgentState, TransferAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.entity import (
    ChatRespAction,
    ChatRespDto,
    ChatRespMetadataForChoices,
    ChatRespMetadataForContactChoice,
    Contact,
)
from app.utils.modified_langfuse_decorator import observe

multiple_contact_match_node = NodeName("multiple_contact_match")


def _build_choices_from_contact_list(
    contact_list: list[Contact],
) -> ChatRespMetadataForChoices:
    return ChatRespMetadataForChoices(
        choices=[
            ChatRespMetadataForContactChoice(
                id=contact.id,
                name=contact.name,
                account_number=contact.account_number
                or contact.phone_number
                or contact.iban
                or "",
            )
            for contact in contact_list
        ],
    )


@observe()
async def multiple_contact_match_func(
    state: TransferAgentState,
    config: RunnableConfig,
) -> dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info("Multiple matched contacts found...")
    last_message = state[TransferAgentStateFields.MESSAGES][-1]
    response = ChatRespDto(
        action=ChatRespAction.SHOW_CHOICES,
        thread_id=config_data[THREAD_ID_KEY],
        response=last_message.content,
        metadata=_build_choices_from_contact_list(
            state[TransferAgentStateFields.CONTACT_LIST],
        ),
    )
    config_data[PENDING_RESPONSE_KEY].append(response)
    return {
        TransferAgentStateFields.RESUME_NODE: select_contact_node,
    }
