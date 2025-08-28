from langchain_core.pydantic_v1 import BaseModel


class ToTermDepositAgent(BaseModel):
    """
    Transfers work to a specialized Term-Deposit assistant to handle everything related to term deposits
    or user's term deposit accounts.
    This tool can handle multiple tasks related to term deposit at a time, DO NOT spawning multiple tools.
    Call this tool whenever the user want to interact with term deposits or get information about term deposits.
    This tool does not require any further information,
    it will handle the rest of the conversation and process the term deposit.
    So call it immediately every time the user wants to interact with term deposits.
    Some examples requests that could trigger this tool:
        * I want to create a term deposit.
        * I want to renew my term deposit.
        * I want to know more about term deposits.
        * How can I close my term deposit account?
        * List out all my term deposit accounts.
        * Deposit $1000

    """

    pass
