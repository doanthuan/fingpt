from enum import Enum


class AssistantStatus(str, Enum):
    WAIT_FOR_QUERY = "WAIT_FOR_QUERY"
    WAIT_FOR_CHOICE = "WAIT_FOR_CHOICE"
