import abc
from calendar import monthrange
from datetime import date
from typing import Any

from app.entity import ActiveAccount, Card, Contact, Transaction


class BaseApiParser:
    def parse_cards(self, data: list[dict[str, Any]]) -> list[Card]:
        return [
            Card(
                id=item["id"],
                brand=item["brand"],
                card_type=item["type"],
                status=item["status"],
                lock_status=item.get("lockStatus"),
                replacement_status=item.get("replacement", {"status": None}).get(
                    "status"
                ),
                holder_name=item.get("holder", {"name": None}).get("name"),
                currency=item["currency"],
                expiry_date=self._expiry_date(item),
            )
            for item in data
        ]

    @abc.abstractmethod
    def parse_contacts(
        self,
        contacts: list[dict[str, Any]],
    ) -> list[Contact]:
        raise NotImplementedError

    @abc.abstractmethod
    def parse_accounts(
        self,
        accounts: list[dict[str, Any]],
    ) -> list[ActiveAccount]:
        raise NotImplementedError

    @staticmethod
    def _expiry_date(
        card: dict[str, Any],
    ) -> str:
        return date(
            year=int(card["expiryDate"]["year"]),
            month=int(card["expiryDate"]["month"]),
            day=monthrange(
                int(card["expiryDate"]["year"]),
                int(card["expiryDate"]["month"]),
            )[1],
        ).strftime("%Y-%m-%d")

    @abc.abstractmethod
    def parse_transactions(
        self, transactions: list[dict[str, Any]], search_term: str
    ) -> list[Transaction]:
        parsed_trans = []
        for item in transactions:
            trans = Transaction(
                account_id=item.get("arrangementId", ""),
                execution_date=item.get("bookingDate", ""),
                transaction_type=item.get("type", ""),
                amount=item.get("transactionAmountCurrency", {"amount": None}).get(
                    "amount"
                ),
                currency=item.get(
                    "transactionAmountCurrency", {"currencyCode": None}
                ).get("currencyCode"),
                counterparty_name=item.get("counterPartyName", ""),
                counterparty_account=item.get("counterPartyAccountNumber", ""),
            )
            merchant = item.get("merchant")
            if merchant:
                merchant_name = merchant.get("name", "")
                if search_term in merchant_name:
                    trans.counterparty_name = merchant_name

            parsed_trans.append(trans)
        return parsed_trans

    @abc.abstractmethod
    def parse_payment(self, payments: list[dict[str, Any]]) -> list[Transaction]:
        return [
            Transaction(
                account_id=item.get("originatorAccount", {"arrangementId": None}).get(
                    "arrangementId"
                ),
                execution_date=item.get("requestedExecutionDate", ""),
                transaction_type="Withdrawal",
                amount=item.get("totalAmount", {"amount": None}).get("amount"),
                currency=item.get("totalAmount", {"currencyCode": None}).get(
                    "currencyCode"
                ),
                counterparty_name=item.get(
                    "transferTransactionInformation", {"counterparty": {"name": None}}
                )
                .get("counterparty")
                .get("name"),
                counterparty_account=item.get(
                    "transferTransactionInformation",
                    {
                        "counterpartyAccount": {
                            "identification": {"identification": None}
                        }
                    },
                )
                .get("counterpartyAccount")
                .get("identification")
                .get("identification"),
            )
            for item in payments
            if item.get("permissibleActions").get("cancel") is False
        ]
