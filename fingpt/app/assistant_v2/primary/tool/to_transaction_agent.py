from langchain_core.pydantic_v1 import BaseModel


class ToTransactionAgent(BaseModel):
    """
    Transfers work to a specialized analyst to perform analysis on personal transaction history.
    This tool should be called when:
        * User's query mentions a transaction history related to themselves.
        * User ask for analysis on personal transaction history.
        * User want to know their spending habits.
    Some keywords that could trigger this tool:
        * My transaction.
        * Recent transaction.
    This tool do not require any further information,
    it will handle the rest of the conversation and produce the analysis on personal transaction history.
    """

    pass
