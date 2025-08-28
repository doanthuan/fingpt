from langchain_core.pydantic_v1 import BaseModel


class ToCardAgent(BaseModel):
    """
    Transfers work to a specialized Card assistant to help user everything related to card.
    This tool does not require any further information,
     it will handle the rest of the conversation and process the card.
    So call it immediately every time the user wants to do something related to the card.
    """

    pass
