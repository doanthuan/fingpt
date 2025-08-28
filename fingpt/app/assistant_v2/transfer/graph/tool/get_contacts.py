from typing import Annotated, Any

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.structured import StructuredTool
from langgraph.prebuilt import InjectedState

from app.assistant_v2.common.base_agent_config import extract_bb_retail_api_config
from app.assistant_v2.transfer.constant import GET_CONTACT_TOOL_NAME
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.bb_retail.request import list_contacts
from app.entity import BbQueryPaging, Contact
from app.utils.modified_langfuse_decorator import observe


class RecipientInput(BaseModel):
    recipient_name: str = Field(
        description="The name of the recipient to whom the money is to be transferred, the value must not be null",
    )
    state: Annotated[dict[str, Any], InjectedState] = Field(
        description="The state of the graph"
    )


def _filter_contact(
    filter_term: str,
    contacts: list[Contact],
) -> dict[str, Contact]:
    """
    Filter the contact list based on the matching the term with the contact name.
    """
    return {
        contact.id: contact
        for contact in contacts
        if filter_term.lower() in contact.name.lower()
    }


@observe()
async def _get_contacts(
    recipient_name: str,
    config: RunnableConfig,
    state: Annotated[dict[str, Any], InjectedState],
) -> str:
    selected_contact = state.get(TransferAgentStateFields.SELECTED_CONTACT)
    if selected_contact:
        message = [selected_contact.json()]
        return str(message)
    config_data, ctx, logger = extract_config(config)
    api_config = extract_bb_retail_api_config(config_data)
    logger.info(f"Retrieving contact list for {recipient_name}")
    contacts = await list_contacts(
        ctx=ctx, config=api_config, params=BbQueryPaging(fr0m=0, size=500)
    )
    filtered_contacts = _filter_contact(recipient_name, contacts)
    message = [entity.json() for entity in filtered_contacts.values()]
    logger.debug(f"Filtered contacts: {message}")
    return str(message)


get_contact_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_get_contacts,
    name=GET_CONTACT_TOOL_NAME,
    description="Get list of user contacts which have the same name as the recipient_name",
    args_schema=RecipientInput,
    error_on_invalid_docstring=True,
)
