import json
from typing import Any, Dict

from langchain_core.messages import ToolMessage

from app.assistant_v2.transfer.constant import (
    GET_ACCOUNT_TOOL_NAME,
    GET_CONTACT_TOOL_NAME,
    NOTICE_TRANSFER_AMOUNT_TOOL_NAME,
)
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.entity import ActiveAccount, Contact


async def chain_ainvoke(chain, input_data: Dict[str, Any]):
    return await chain.ainvoke(input_data)


def extract_tool_messages(logger, messages) -> Dict[str, Any]:
    # get all recent tool messages
    logger.info("Extracting data from tool message...")
    output = {}
    for message in messages[::-1]:
        if not isinstance(message, ToolMessage):
            break
        logger.debug(f"Tool message: {message}")
        if message.name == GET_ACCOUNT_TOOL_NAME:
            output[TransferAgentStateFields.ACTIVE_ACCOUNTS] = [
                ActiveAccount(**json.loads(account))
                for account in eval(message.content)
            ]
        elif message.name == GET_CONTACT_TOOL_NAME:
            output[TransferAgentStateFields.CONTACT_LIST] = [
                Contact(**json.loads(contact)) for contact in eval(message.content)
            ]
        elif (
            message.name == NOTICE_TRANSFER_AMOUNT_TOOL_NAME
            and message.content is not None
        ):
            output[TransferAgentStateFields.TRANSFER_AMOUNT] = float(message.content)
    if (
        TransferAgentStateFields.ACTIVE_ACCOUNTS in output
        and len(output[TransferAgentStateFields.ACTIVE_ACCOUNTS]) == 1
    ):
        output[TransferAgentStateFields.SELECTED_ACCOUNT] = output[
            TransferAgentStateFields.ACTIVE_ACCOUNTS
        ][0]
    if (
        TransferAgentStateFields.CONTACT_LIST in output
        and len(output[TransferAgentStateFields.CONTACT_LIST]) == 1
    ):
        output[TransferAgentStateFields.SELECTED_CONTACT] = output[
            TransferAgentStateFields.CONTACT_LIST
        ][0]
    return output
