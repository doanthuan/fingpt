from enum import Enum
from typing import Any

from pydantic import BaseModel


class BBRuntime(str, Enum):
    LOCAL = "local"
    EXP = "exp"
    STAGING = "stg"


class BbHeader(BaseModel):
    authorization: str
    cookie: str

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, str]:
        d = super().model_dump(*args, **kwargs)
        if "authorization" in d and not d["authorization"].startswith("Bearer "):
            d["authorization"] = "Bearer " + d["authorization"]
        return d


class BbQueryPaging(BaseModel):
    fr0m: int = 0
    size: int = 100

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        d["from"] = d.pop("fr0m")
        return d


class BbQueryParams(BbQueryPaging):
    query: str = ""
    orderBy: str = "bookingDate"
    direction: str = "ASC"


class BbApiConfig(BaseModel):
    ebp_access_token: str
    ebp_cookie: str
    ebp_edge_domain: str
