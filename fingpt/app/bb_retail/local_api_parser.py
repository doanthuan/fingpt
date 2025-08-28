from typing import Any

from app.bb_retail.base_api_parser import BaseApiParser
from app.entity import AccountIdentification, ActiveAccount, Contact


class LocalApiParser(BaseApiParser):
    def parse_contacts(
        self,
        contacts: list[dict[str, Any]],
    ) -> list[Contact]:
        out: list[Contact] = []
        for item in contacts:
            contact = Contact(
                id=item["id"],
                name=item["name"],
                account_number=item["accounts"][0].get("accountNumber"),
                phone_number=item["accounts"][0].get("phoneNumber"),
                email_address=item["accounts"][0].get("emailId"),
                iban=item["accounts"][0].get("iban"),
            )
            out.append(contact)
        return out

    def parse_accounts(
        self,
        accounts: list[dict[str, Any]],
    ) -> list[Any]:
        out: list[ActiveAccount] = []
        for item in accounts:
            account = ActiveAccount(
                id=item["id"],
                name=item["displayName"],
                product_type=item.get("productTypeName", ""),
                product_kind_name=item.get("productKindName", ""),
                currency=item["currency"],
                identifications=AccountIdentification(
                    bban=item.get("BBAN", ""),
                    bic=item.get("BIC", ""),
                ),
                available_balance=float(item.get("availableBalance", 0.0)),
                booked_balance=float(item.get("bookedBalance", 0.0)),
            )
            out.append(account)
        return out
