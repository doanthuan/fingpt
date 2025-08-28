from langchain_core.pydantic_v1 import BaseModel


class ToMoneyTransferFlow(BaseModel):
    """
    Transfers work to a specialized money transfer assistant to handle money transfer.
    Call this tool whenever the user wants to transfer money to another.
    This tool does not require any further information,
     it will handle the rest of the conversation and process the transaction,
    so call it immediately every time the user wants to transfer money.
    Note that this tool can not handle the request related to sending money to saving account or term deposit account.
    """

    pass
