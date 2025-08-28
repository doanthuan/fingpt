import base64
import json

from .base_url_provider import BaseUrlProvider
from .constants import (
    DEFAULT_CARD_LIST_URL,
    DEFAULT_CONTACT_LIST_URL,
    DEFAULT_PAYMENT_URL,
    DEFAULT_PRODUCT_SUMMARY_URL,
    DEFAULT_TRANSACTION_URL,
)


class IstioUrlProvider(BaseUrlProvider):
    def contact_list_url(self) -> str:
        return DEFAULT_CONTACT_LIST_URL

    def card_list_url(self, **kwargs: str):
        if "token" not in kwargs:
            raise ValueError("Token is required for non-local environment")
        token = str(kwargs["token"])
        # parse user_id from jwt token
        _, payload, _ = token.split(".")
        if len(payload) % 4:
            payload += "=" * (4 - len(payload) % 4)
        payload = base64.urlsafe_b64decode(payload).decode("utf-8")
        payload = json.loads(payload)
        in_uid = payload.get("inuid")
        return DEFAULT_CARD_LIST_URL.format(userId=in_uid)

    def transaction_url(self) -> str:
        return DEFAULT_TRANSACTION_URL

    def product_summary_url(self) -> str:
        return DEFAULT_PRODUCT_SUMMARY_URL

    def payment_url(self) -> str:
        return DEFAULT_PAYMENT_URL
