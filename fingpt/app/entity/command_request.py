from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel


class CommandType(str, Enum):
    BASH_CMD = "BASH_CMD"
    REQUEST_CMD = "REQUEST_CMD"
    SERVICE_CALL = "SERVICE_CALL"


class BashCommandDto(BaseModel):
    command: str


class RequestCommandDto(BaseModel):
    method: str
    url: str
    headers: Optional[dict[str, str]] = None
    data: Optional[dict[str, str]] = None
    params: Optional[dict[str, str]] = None


class AvailableServiceName(str, Enum):
    CONTACT_SERVICE = "contact_service"
    PRODUCT_SUMMARY_SERVICE = "product_summary_service"
    TRANSACTION_SERVICE = "transaction_service"
    CARD_SERVICE = "card_service"


class ServiceCallDto(BaseModel):
    env: Optional[str] = None
    service_name: AvailableServiceName


class CommandDto(BaseModel):
    command_type: CommandType
    command: Union[
        BashCommandDto,
        RequestCommandDto,
        ServiceCallDto,
    ]
