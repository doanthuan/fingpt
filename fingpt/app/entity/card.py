from pydantic.v1 import BaseModel  # type: ignore


class Card(BaseModel):
    id: str
    brand: str
    card_type: str
    status: str
    lock_status: str | None
    replacement_status: str | None
    holder_name: str | None
    currency: str
    expiry_date: str
