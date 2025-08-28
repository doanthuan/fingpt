from typing import Any

from app.bb_retail.base_api_parser import BaseApiParser
from app.entity import ActiveAccount, Contact
from app.entity.term_deposit import AccountIdentification


class IstioApiParser(BaseApiParser):
    def parse_contacts(self, contacts: list[dict[str, Any]]) -> list[Contact]:
        return [
            Contact(
                id=item["id"],
                name=item["name"],
                account_number=item["accounts"][0].get("accountNumber"),
                phone_number=item.get("phoneNumber"),
                email_address=item.get("emailId"),
                iban=item["accounts"][0].get("IBAN"),
            )
            for item in contacts
        ]

    def parse_accounts(self, accounts: list[dict[str, Any]]) -> list[ActiveAccount]:
        return [
            ActiveAccount(
                id=account["id"],
                name=account.get("bankAlias", ""),
                product_type=account.get("productTypeName", ""),
                product_kind_name=account.get("productKindName", ""),
                identifications=AccountIdentification(
                    bban=account.get("BBAN", ""),
                    bic=account.get("BIC", ""),
                ),
                available_balance=float(account.get("availableBalance", 0.0)),
                booked_balance=float(account.get("bookedBalance", 0.0)),
                currency=account["currency"],
            )
            for account in accounts
        ]
