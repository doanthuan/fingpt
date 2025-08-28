from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import USER_CHOICE_ID_KEY
from app.assistant_v2.transfer.state import TransferAgentState, TransferAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.utils.modified_langfuse_decorator import observe

select_contact_node = NodeName("select_contact")


@observe()
async def select_contact_func(
    state: TransferAgentState, config: RunnableConfig
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info(f"Selecting contact... User choice: {config_data[USER_CHOICE_ID_KEY]}")
    try:
        choice_id: str = config_data[USER_CHOICE_ID_KEY] or ""
        assert choice_id != "", "User choice is empty"
        contacts = state[TransferAgentStateFields.CONTACT_LIST]
        contact = next(
            (contact for contact in contacts if contact.id == choice_id), None
        )
        return {
            TransferAgentStateFields.MESSAGES: [
                HumanMessage(
                    content=f"My selected contact is: {contact.name}, id: {contact.id}"
                )
            ],
            TransferAgentStateFields.CONTACT_LIST: [],
            TransferAgentStateFields.SELECTED_CONTACT: contact,
            TransferAgentStateFields.RESUME_NODE: None,
        }
    except Exception as e:
        logger.error(f"Failed to select contact: {e}")
        raise
