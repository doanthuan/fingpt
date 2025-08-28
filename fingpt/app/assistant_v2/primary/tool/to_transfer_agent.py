from langchain_core.pydantic_v1 import BaseModel


class ToTransferAgent(BaseModel):
    """
    Transfers work to a specialized transaction assistant to handle financial transactions.
    Call this tool whenever the user wants to transfer money to another account.
    This tool does not require any further information,
    it will handle the rest of the conversation and process the transaction.
    So call it immediately every time the user wants to transfer money.
    """

    pass
