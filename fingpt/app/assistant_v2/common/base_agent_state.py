from typing import Annotated, Any, Optional, Sequence, TypedDict

from attr import dataclass
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class BaseAgentState(TypedDict):
    messages: Annotated[
        Sequence[AnyMessage],
        add_messages,
    ]
    resume_node: Optional[str]


@dataclass
class BaseAgentStateFields:
    MESSAGES = "messages"
    RESUME_NODE = "resume_node"

    @classmethod
    def validate(cls, field: str) -> None:
        class_attr_names = [
            n
            for n in dir(cls)
            if not n.startswith("__") and n.replace("_", "").isupper()
        ]
        class_fields = {getattr(cls, attr) for attr in class_attr_names}
        if field not in class_fields:
            raise ValueError(f"Invalid field: {field}")

    @classmethod
    def validate_agent_fields(cls, clazz: Any) -> None:
        """
        Validate fields for a given class. Should be called after defining a state class.
        Args:
            clazz: TypedDict: The class to validate

        Returns: Raises ValueError if any field is invalid

        """
        state_fields = clazz.__dict__["__annotations__"].keys()
        for field in state_fields:
            cls.validate(field)


BaseAgentStateFields.validate_agent_fields(BaseAgentState)
