from langchain_core.pydantic_v1 import BaseModel


class ToCardFlow(BaseModel):
    """
    Transfers work to a specialized Card assistant to help give information about car and handle renew a card.
    Call this flow every time user wants to do something related to card.
    This tool does not need any additional information to work, just call it, it will handle the rest.
    """

    pass
