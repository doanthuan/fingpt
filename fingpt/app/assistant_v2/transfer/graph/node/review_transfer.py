from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.transfer.state import TransferAgentState, TransferAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.entity import ActiveAccount, ChatRespAction, ChatRespDto, Contact
from app.entity.chat_response import ChatRespMetadataForTransfer
from app.utils.modified_langfuse_decorator import observe

review_transfer_node = NodeName("review_transfer")


@observe()
async def review_transfer_func(
    state: TransferAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info("Reviewing transfer...")
    contact: Contact = state[TransferAgentStateFields.SELECTED_CONTACT]
    account: ActiveAccount = state[TransferAgentStateFields.SELECTED_ACCOUNT]
    amount = state[TransferAgentStateFields.TRANSFER_AMOUNT]
    if not amount:
        return {
            TransferAgentStateFields.MESSAGES: [
                HumanMessage(
                    content="Please call tool to notify me about the transfer amount."
                )
            ],
        }
    last_message = state[TransferAgentStateFields.MESSAGES][-1]

    output = {}
    if account.available_balance < state[TransferAgentStateFields.TRANSFER_AMOUNT]:
        response = ChatRespDto(
            action=ChatRespAction.SHOW_REPLY,
            thread_id=config_data[THREAD_ID_KEY],
            response=last_message.content,
            metadata=None,
        )
    else:
        response = ChatRespDto(
            action=ChatRespAction.MAKE_TRANSFER,
            thread_id=config_data[THREAD_ID_KEY],
            response=last_message.content,
            metadata=ChatRespMetadataForTransfer(
                account=account.dict(),
                recipient=contact.dict(),
                transfer_amount=state[TransferAgentStateFields.TRANSFER_AMOUNT],
            ),
        )
        output[TransferAgentStateFields.MESSAGES] = [HumanMessage(content="It's okay.")]
    # show response to user
    config_data[PENDING_RESPONSE_KEY].append(response)
    # reset state
    output[TransferAgentStateFields.RESUME_NODE] = None
    output[TransferAgentStateFields.SELECTED_ACCOUNT] = None
    output[TransferAgentStateFields.SELECTED_CONTACT] = None
    return output
