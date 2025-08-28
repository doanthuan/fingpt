import abc


class BaseUrlProvider:

    @abc.abstractmethod
    def product_summary_url(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def contact_list_url(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def card_list_url(self, **kwargs: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def transaction_url(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def payment_url(self) -> str:
        raise NotImplementedError
