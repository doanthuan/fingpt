from langchain_core.pydantic_v1 import BaseModel


class ToTermDepositFlow(BaseModel):
    """
    Transfers work to a specialized Term-Deposit assistant to handle create a new or renew a term deposit.
    Call this flow every time user wants to do something related to term deposit.
    This tool does not need any additional information to work, just call it, it will handle the rest.
    """

    pass
