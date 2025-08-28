import json
from unittest.mock import AsyncMock, patch

import pytest

# Import the functions you want to test
from app.bb_retail.request import (
    BbApiRequest,
    get_balance,
    list_accounts,
    list_contacts,
    list_td_products,
    list_term_deposit_accounts,
)
from app.core.context import RequestContext
from app.entity import UnauthorizedError
from app.entity.bb_api import BbApiConfig, BbHeader, BbQueryPaging
from app.entity.term_deposit import (
    AccountIdentification,
    ActiveAccount,
    TermDepositAccount,
    TermDepositProduct,
    TermUnit,
)
from app.entity.transfer import Contact


@pytest.fixture
def mock_context():
    return AsyncMock(spec=RequestContext)


@pytest.fixture
def mock_config():
    return BbApiConfig(
        ebp_access_token="mock_token",
        ebp_cookie="mock_cookie",
        ebp_edge_domain="mock_domain",
    )


@pytest.mark.asyncio
async def test_get_balance(mock_context, mock_config):
    mock_response = {
        "currentAccounts": {
            "products": [{"availableBalance": "100.50"}, {"availableBalance": "200.75"}]
        }
    }

    with patch(
        "app.bb_retail.request.BbApiRequest._make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_make_request.return_value = mock_response
        balance = await get_balance(ctx=mock_context, config=mock_config)

    assert balance == 100.50
    mock_make_request.assert_called_once()


@pytest.mark.asyncio
async def test_list_contacts(mock_context, mock_config):
    mock_response = [
        {
            "id": "1",
            "name": "John Doe",
            "accounts": [{"accountNumber": "123456"}],
            "activeStatus": "ACTIVE",
        },
        {
            "id": "2",
            "name": "Jane Smith",
            "accounts": [{"accountNumber": "789012"}],
            "activeStatus": "ACTIVE",
        },
    ]

    with patch(
        "app.bb_retail.request.BbApiRequest._make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_make_request.return_value = mock_response
        contacts = await list_contacts(
            ctx=mock_context, config=mock_config, params=BbQueryPaging(fr0m=0, size=10)
        )

    assert len(contacts) == 2
    assert contacts[0] == Contact(id="1", name="John Doe", account_number="123456")
    assert contacts[1] == Contact(id="2", name="Jane Smith", account_number="789012")


@pytest.mark.asyncio
async def test_list_accounts(mock_context, mock_config):
    mock_response = {
        "currentAccounts": {
            "products": [
                {
                    "id": "1",
                    "name": "Account 1",
                    "displayName": "Account 1",
                    "availableBalance": "100.50",
                    "currency": "USD",
                    "productTypeName": "Current Account",
                },
                {
                    "id": "2",
                    "name": "Account 2",
                    "displayName": "Account 2",
                    "availableBalance": "200.75",
                    "currency": "USD",
                    "productTypeName": "Current Account",
                },
            ]
        }
    }

    with patch(
        "app.bb_retail.request.BbApiRequest._make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_make_request.return_value = mock_response
        accounts = await list_accounts(ctx=mock_context, config=mock_config)

    assert len(accounts) == 2
    print(f"Type of accounts[0]: {type(accounts[0])}")
    print(f"accounts[0]: {accounts[0]}")

    expected_account = ActiveAccount(
        id="1",
        name="Account 1",
        available_balance=100.50,
        currency="USD",
        product_type="Current Account",
        identifications=AccountIdentification(bban="", bic=""),
        booked_balance=0.0,
    )
    print(f"Type of expected_account: {type(expected_account)}")
    print(f"expected_account: {expected_account}")

    assert accounts[0] == expected_account
    assert accounts[1] == ActiveAccount(
        id="2",
        name="Account 2",
        available_balance=200.75,
        currency="USD",
        product_type="Current Account",
        identifications=AccountIdentification(bban="", bic=""),
        booked_balance=0.0,
    )


@pytest.mark.asyncio
async def test_make_request_unauthorized(mock_context):
    mock_response = AsyncMock()
    mock_response.status = 401

    with patch(
        "aiohttp.ClientSession.get",
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)),
    ):
        with pytest.raises(UnauthorizedError):
            await BbApiRequest()._make_request(
                mock_context, "http://test.com", AsyncMock()
            )


@pytest.mark.asyncio
async def test_make_request_error(mock_context):
    mock_response = AsyncMock()
    mock_response.status = 500

    with patch(
        "aiohttp.ClientSession.get",
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)),
    ):
        with pytest.raises(Exception):
            await BbApiRequest()._make_request(
                mock_context, "http://test.com", AsyncMock()
            )


@pytest.mark.asyncio
async def test_list_td_products():
    mock_json_data = """
    [
        {
            "id": "TD001",
            "displayName": "3 Month Term Deposit",
            "accountInterestRate": 2.5,
            "termNumber": 3,
            "termUnit": "M",
            "minimumRequiredBalance": 1000
        },
        {
            "id": "TD002",
            "displayName": "1 Year Term Deposit",
            "accountInterestRate": 3.0,
            "termNumber": 12,
            "termUnit": "M",
            "minimumRequiredBalance": 5000
        }
    ]
    """

    mock_file = AsyncMock()
    mock_file.read.return_value = mock_json_data
    mock_aiofiles = AsyncMock()
    mock_aiofiles.__aenter__.return_value = mock_file

    with patch("aiofiles.open", return_value=mock_aiofiles):
        mock_context = RequestContext("123")
        result = await list_td_products(ctx=mock_context)

    assert len(result) == 2
    assert isinstance(result[0], TermDepositProduct)
    assert isinstance(result[1], TermDepositProduct)

    assert result[0].id == "TD001"
    assert result[0].name == "3 Month Term Deposit"
    assert result[0].interest_rate == 2.5
    assert result[0].term_number == 3
    assert result[0].term_unit == TermUnit.M
    assert result[0].minimum_required_balance == 1000

    assert result[1].id == "TD002"
    assert result[1].name == "1 Year Term Deposit"
    assert result[1].interest_rate == 3.0
    assert result[1].term_number == 12
    assert result[1].term_unit == TermUnit.M
    assert result[1].minimum_required_balance == 5000


@pytest.mark.asyncio
async def test_list_term_deposit_accounts(mock_context, mock_config):
    mock_account_response = {
        "currentAccounts": {
            "products": [
                {
                    "id": "1",
                    "name": "Account 1",
                    "availableBalance": "1000.00",
                    "currency": "USD",
                    "accountHolderNames": "Sara Williams",
                }
            ]
        }
    }

    mock_file_content = {
        "termDeposits": {
            "products": [
                {
                    "id": "d1e2f3a4-b5c6-7d8e-9f0a-b1c2d3e4f5a6",
                    "name": "Short-term Deposit",
                    "interestRate": "2.50",
                    "termNumber": 6,
                    "termUnit": "M",
                    "maturityDate": "2025-03-01T00:00:00Z",
                    "bban": "**************1234",
                    "bookedBalance": "10000.00",
                }
            ]
        }
    }

    mock_file = AsyncMock()
    mock_file.read.return_value = json.dumps(mock_file_content)

    with patch(
        "app.bb_retail.request.BbApiRequest._make_request", new_callable=AsyncMock
    ) as mock_make_request, patch(
        "aiofiles.open",
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_file)),
    ) as mock_aiofiles_open:

        mock_make_request.return_value = mock_account_response
        term_deposit_accounts = await list_term_deposit_accounts(
            ctx=mock_context, config=mock_config
        )

    assert len(term_deposit_accounts) == 1
    assert term_deposit_accounts[0] == TermDepositAccount(
        id="d1e2f3a4-b5c6-7d8e-9f0a-b1c2d3e4f5a6",
        name="Short-term Deposit",
        interest_rate=2.5,
        term_number=6,
        term_unit=TermUnit("M"),
        maturity_date="2025-03-01T00:00:00Z",
        bban="**************1234",
        deposit_amount=10000,
        start_date="",
        maturity_earn=0,
        is_mature=False,
        is_renewable=False,
    )

    # Verify that _make_request was called with the correct arguments
    mock_make_request.assert_called_once_with(
        mock_context,
        f"https://{mock_config.ebp_edge_domain}/api/arrangement-manager/client-api/v2/productsummary",
        BbHeader(
            authorization=f"Bearer {mock_config.ebp_access_token}",
            cookie=mock_config.ebp_cookie,
        ),
    )

    # Verify that aiofiles.open was called with the correct arguments
    mock_aiofiles_open.assert_called_once_with(
        "./app/bb_retail/mock_data/sara_account_info.json", "r"
    )
