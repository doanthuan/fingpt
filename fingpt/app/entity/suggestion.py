from enum import Enum

from pydantic import BaseModel


class SuggestionType(str, Enum):
    WELCOME = "WELCOME"


class Platform(str, Enum):
    WEB = "WEB"
    MOBILE = "MOBILE"


class Suggestion(BaseModel):
    content: str
    is_highlighted: bool = False


class SuggestionResp(BaseModel):
    type: SuggestionType = SuggestionType.WELCOME
    thread_id: str
    platform: Platform
    suggestions: list[Suggestion]
