from langchain_core.pydantic_v1 import BaseModel


class ToTickerAgent(BaseModel):
    """
    Transfers work to a specialized analyst to produce financial report of public companies based on user query.
    This tool should be called when:
        * User's query mentions a ticker symbol directly.
        * User ask for financial report of a public company.
        * User want to know the performance of a public company.

    This tool do not require any further information,
    it  will handle the rest of the conversation and produce the financial report of the public company.
    """

    pass
