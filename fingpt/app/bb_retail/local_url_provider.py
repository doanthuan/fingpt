from app.auth.constant import (
    CARD_LIST_URL,
    CONTACT_LIST_URL,
    PAYMENT_MANAGER_URL,
    PRODUCT_SUMMARY_URL,
    TRANSACTION_MANAGER_URL,
)
from app.bb_retail.base_url_provider import BaseUrlProvider


class LocalUrlProvider(BaseUrlProvider):
    def product_summary_url(self) -> str:
        return PRODUCT_SUMMARY_URL

    def contact_list_url(self) -> str:
        return CONTACT_LIST_URL

    def card_list_url(self, **kwargs: str) -> str:
        return CARD_LIST_URL

    def transaction_url(self) -> str:
        return TRANSACTION_MANAGER_URL

    def payment_url(self) -> str:
        return PAYMENT_MANAGER_URL
