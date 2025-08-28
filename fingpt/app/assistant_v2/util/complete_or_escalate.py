from langchain_core.pydantic_v1 import BaseModel


class CompleteOrEscalateTool(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control
    of the dialog to the main assistant, who can re-route the dialog based on
    the user's needs."""

    exit: bool
    reason: str

    class Config:
        schema_extra = {
            "example": {
                "exit": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "exit": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "exit": False,
                "reason": "I need to search the transactions for more information.",
            },
        }
