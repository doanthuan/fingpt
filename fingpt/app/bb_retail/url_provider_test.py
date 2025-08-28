from app.auth.constant import (
    CARD_LIST_URL,
    CONTACT_LIST_URL,
    PAYMENT_MANAGER_URL,
    PRODUCT_SUMMARY_URL,
    TRANSACTION_MANAGER_URL,
)
from app.bb_retail.api_parser_factory import ApiParserFactory
from app.bb_retail.url_provider_factory import UrlProviderFactory
from app.entity import ActiveAccount, Card, Contact, Transaction
from app.entity.bb_api import BBRuntime
from app.entity.term_deposit import AccountIdentification

local_url_provider = UrlProviderFactory.get_url_provider(BBRuntime.LOCAL)
stg_url_provider = UrlProviderFactory.get_url_provider(BBRuntime.STAGING)
api_parser = ApiParserFactory.get_api_parser()


def test_get_product_summary_url():
    assert local_url_provider.product_summary_url() == PRODUCT_SUMMARY_URL
    assert stg_url_provider.product_summary_url() != PRODUCT_SUMMARY_URL


def test_parse_product_summary_to_account():
    local_data = [
        {
            "id": "1",
            "displayName": "Test Account",
            "productTypeName": "Test Product",
            "currency": "USD",
            "BBAN": "123456",
            "BIC": "654321",
            "availableBalance": 100.0,
            "bookedBalance": 100.0,
        }
    ]

    local_accounts = api_parser.parse_accounts(local_data)
    expected_account = ActiveAccount(
        id="1",
        name="Test Account",
        product_type="Test Product",
        currency="USD",
        identifications=AccountIdentification(
            bban="123456",
            bic="654321",
        ),
        available_balance=100.0,
        booked_balance=100.0,
    )
    assert local_accounts == [expected_account]


def test_get_contact_list_url():
    assert local_url_provider.contact_list_url() == CONTACT_LIST_URL
    assert stg_url_provider.contact_list_url() != CONTACT_LIST_URL


def test_parse_contact_list_to_contacts():
    local_data = [
        {
            "id": "1",
            "activeStatus": "ACTIVE",
            "name": "Test Contact",
            "accounts": [
                {
                    "accountNumber": "123456",
                    "phoneNumber": "654321",
                    "emailId": "mail@bb.com",
                    "iban": "xxx.yyy.zzz",
                }
            ],
        }
    ]
    local_contacts = api_parser.parse_contacts(local_data)
    expected_contact = Contact(
        id="1",
        name="Test Contact",
        account_number="123456",
        phone_number="654321",
        email_address="mail@bb.com",
        iban="xxx.yyy.zzz",
    )
    assert local_contacts == [expected_contact]


def test_get_card_list_api():
    token = (
        "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJLRUxUODRf"  # pragma: allowlist secret
        "bFJ3QTdqSklFRnFBcEJPTVI4MnBkdF9QLUxoZy1mWlo4"  # pragma: allowlist secret
        "cGlrIn0.eyJleHAiOjE3MjYxMzIzNjAsImlhdCI6MTcyNjEzMjA2MCwianRpI"  # pragma: allowlist secret
        "joiMTAxYjQ1MTAtZGM5YS00MTE4LTliMGQtMzVlOGE3"  # pragma: allowlist secret
        "ZGExNmZmIiwiaXNzIjoiaHR0cHM6Ly9pZGVudGl0eS5zdGcuc2RieGF6LmF6dX"  # pragma: allowlist secret
        "JlLmJhY2tiYXNlc2VydmljZXMuY29tL2F1dGgvcmVh"  # pragma: allowlist secret
        "bG1zL2N1c3RvbWVyIiwic3ViIjoiYmY4YzlkZjQtMzViMC00ODUyLWIxZjAtOTd"  # pragma: allowlist secret
        "lMjVjYjg3ODJhIiwidHlwIjoiQmVhcmVyIiwiYXpwI"  # pragma: allowlist secret
        "joibW9iaWxlLWNsaWVudCIsInNlc3Npb25fc3RhdGUiOiI4ODY4MzJkMS1hOTcy"  # pragma: allowlist secret
        "LTQ4N2MtYTk5NC01ZThkYWZiZTAxZDgiLCJhY3IiOi"  # pragma: allowlist secret
        "IxIiwic2NvcGUiOiJlbWFpbCBwcm9maWxlIiwic2lkIjoiODg2ODMyZDEtYTk3M"  # pragma: allowlist secret
        "i00ODdjLWE5OTQtNWU4ZGFmYmUwMWQ4IiwiaW51aWQ"  # pragma: allowlist secret
        "iOiJiZjhjOWRmNC0zNWIwLTQ4NTItYjFmMC05N2UyNWNiODc4MmEiLCJlbWFpbF"  # pragma: allowlist secret
        "92ZXJpZmllZCI6dHJ1ZSwibGVpZCI6IjhhODI4MTFm"  # pragma: allowlist secret
        "OTBkYTM3MjQwMTkwZGE0MDM1MzQwMDUwIiwibmFtZSI6Ikxpc2EgQ2FydGVyI"  # pragma: allowlist secret
        "iwicHJlZmVycmVkX3VzZXJuYW1lIjoic2RieGF6LXN0Z"  # pragma: allowlist secret
        "y1saXNhIiwiZ2l2ZW5fbmFtZSI6Ikxpc2EiLCJmYW1pbHlfbmFtZSI6IkNhcnR"  # pragma: allowlist secret
        "lciIsImludGVybmFsX3Njb3BlIjpbImJiLXN1OmNhcm"  # pragma: allowlist secret
        "RzIiwiYmI6c3RlcC11cCJdLCJlbWFpbCI6Imxpc2EuY2FydGVyQGJhY2tiYXNl"  # pragma: allowlist secret
        "Y2xvdWQuY29tIn0.Kk7kBOCnSFCvGigPeY4dNHubMCI"  # pragma: allowlist secret
        "nKE_e9k7s6oqNtQ-ZcXhyW7AuJ0PLGSIt5X3RMvqzxl--qkPVcRybjXTHP9M5z"  # pragma: allowlist secret
        "E7g5kJ5WA4UktQIqfhVxdojaSyEpwK4P4b3r9jBq8G"  # pragma: allowlist secret
        "KbcJdKPXpdGDcXVeyd3XE5vqvjo8lMooLon4merLK21aI9rskp-SFGqxyFafS"  # pragma: allowlist secret
        "lWIk_FtaEIMPmNdLZ0CASFMBu5TuJJjJJqdn9vAiwDdC"  # pragma: allowlist secret
        "gxsPghOk56tSbD5sGQ-NXXQMKm3W64opG8Ri1rLXjoaOGqt_eIq3F0VIcsRFs"  # pragma: allowlist secret
        "daMBZ1ZP3RByo8t3pRaliXfsoyU3LopWZq0I11gY4QAdg"  # pragma: allowlist secret
    )

    assert local_url_provider.card_list_url() == CARD_LIST_URL
    assert stg_url_provider.card_list_url(token=token) != CARD_LIST_URL


def test_parse_card_list_to_cards():
    data = [
        {
            "id": "card1",
            "brand": "Visa",
            "type": "Credit",
            "status": "Active",
            "lockStatus": "Unlocked",
            "holder": {"name": "John Doe"},
            "currency": "USD",
            "expiryDate": {
                "year": 2023,
                "month": 12,
            },
        }
    ]
    expected_card = Card(
        id="card1",
        brand="Visa",
        card_type="Credit",
        status="Active",
        lock_status="Unlocked",
        replacement_status=None,
        holder_name="John Doe",
        currency="USD",
        expiry_date="2023-12-31",
    )
    assert api_parser.parse_cards(data) == [expected_card]


def test_get_transaction_url():
    assert local_url_provider.transaction_url() == TRANSACTION_MANAGER_URL
    assert stg_url_provider.transaction_url() != TRANSACTION_MANAGER_URL


def test_get_payment_url():
    assert local_url_provider.payment_url() == PAYMENT_MANAGER_URL
    assert stg_url_provider.payment_url() != PAYMENT_MANAGER_URL


# account_id=item.get("arrangementId", ""),
# execution_date=item.get("bookingDate", ""),
# transaction_type="Deposit",
# amount=item.get("transactionAmountCurrency", {"amount": None}).get(
#     "amount"
# ),
# currency=item.get(
#     "transactionAmountCurrency", {"currencyCode": None}
# ).get("currencyCode"),
# counterparty_name=item.get("counterPartyName", ""),
# counterparty_account=item.get("counterPartyAccountNumber", ""),


def test_parse_transactions():
    local_data = [
        {
            "arrangementId": "1",
            "bookingDate": "1000-01-01",
            "type": "Deposit",
            "transactionAmountCurrency": {"amount": 1000, "currencyCode": "USD"},
            "counterPartyName": "name",
            "counterPartyAccountNumber": "123456789",
        }
    ]

    local_transaction = api_parser.parse_transactions(
        transactions=local_data, search_term="name"
    )

    expected_transaction = Transaction(
        account_id="1",
        execution_date="1000-01-01",
        transaction_type="Deposit",
        amount=1000.0,
        currency="USD",
        counterparty_name="name",
        counterparty_account="123456789",
    )
    assert local_transaction == [expected_transaction]
