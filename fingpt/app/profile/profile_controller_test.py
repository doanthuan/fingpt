import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.context import RequestContext
from app.entity.api import ApiHeader
from app.entity.offer import OfferReq
from app.entity.profile import ProfileDataReq, ProfileDataResp
from app.profile.profile_controller import ProfileController


@pytest.mark.asyncio
async def test_update_profile():
    # Arrange
    controller = ProfileController()
    ctx = MagicMock(spec=RequestContext)
    ctx.logger.return_value = MagicMock()
    ctx.request_id.return_value = "test_request_id"
    username = "test_user"
    header = ApiHeader(
        token="mocked_token",
        cookie="mocked_cookie",
    )

    req = ProfileDataReq(
        renewals=[
            OfferReq.model_validate(
                {
                    "product": "TERM_DEPOSIT",
                    "message": "happy renew",
                    "data": {
                        "type": "RENEWAL",
                        "deposit_id": "d1e2f3a4-b5c6-7d8e-9f0a-b1c2d3e4f5a6",
                    },
                }
            )
        ],
    )

    mock_account_response: Any = {
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

    mock_file_content: Any = {
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
    ):
        mock_make_request.return_value = mock_account_response

        # Act
        result = await controller.update_profile(ctx, header, username, req)

    # Assert
    assert result.renewals[0].data.deposit_id == req.renewals[0].data.deposit_id
    ctx.logger().info.assert_any_call(f'Updating user profile with input: "{req}"')
    ctx.logger().info.assert_any_call("Controller exiting...")


@pytest.mark.asyncio
async def test_update_profile_with_card():
    # Arrange
    controller = ProfileController()
    ctx = MagicMock(spec=RequestContext)
    ctx.logger.return_value = MagicMock()
    ctx.request_id.return_value = "test_request_id"
    username = "test_user"
    header = ApiHeader(
        token="mocked_token",
        cookie="mocked_cookie",
    )

    req = ProfileDataReq(
        renewals=[
            OfferReq.model_validate(
                {
                    "product": "CARD",
                    "message": "happy renew",
                    "data": {
                        "type": "RENEWAL",
                        "card_id": "edd1e126-1f3f-458b-9f7a-fd143c9cfcc9",
                    },
                }
            )
        ],
    )

    mock_card_list = [
        {
            "id": "edd1e126-1f3f-458b-9f7a-fd143c9cfcc9",
            "brand": "mastercard",
            "type": "Debit",
            "status": "Active",
            "lockStatus": "UNLOCKED",
            "replacement": {"status": "NotUnderReplacement", "additions": {}},
            "holder": {"name": "Sara Williams", "additions": {}},
            "expiryDate": {"year": "2028", "month": "09", "additions": {}},
            "currency": "USD",
            "maskedNumber": "1659",
            "limits": [
                {
                    "id": "2e4d6c19-d9bf-4ff3-a2ce-3d90a95af43b",
                    "channel": "online",
                    "frequency": "DAILY",
                    "amount": 5000,
                    "maxAmount": 10000,
                    "minAmount": 0,
                    "additions": {},
                },
                {
                    "id": "73a96466-0a21-46fd-a3dc-7ba7b3aaeb61",
                    "channel": "atm",
                    "frequency": "DAILY",
                    "amount": 5000,
                    "maxAmount": 10000,
                    "minAmount": 0,
                    "additions": {},
                },
                {
                    "id": "9d69f05d-2e5c-486a-936e-1ee3419f121b",
                    "channel": "atm",
                    "frequency": "DAILY",
                    "amount": 5000,
                    "maxAmount": 10000,
                    "minAmount": 0,
                    "additions": {},
                },
                {
                    "id": "1edf9e52-039d-4713-b669-f2a9179ca585",
                    "channel": "online",
                    "frequency": "DAILY",
                    "amount": 5000,
                    "maxAmount": 10000,
                    "minAmount": 0,
                    "additions": {},
                },
                {
                    "id": "b80c26f1-0e4e-4271-89b5-8d82011fab5f",
                    "channel": "online",
                    "frequency": "DAILY",
                    "amount": 5000,
                    "maxAmount": 10000,
                    "minAmount": 0,
                    "additions": {},
                },
            ],
            "cardVisual": {
                "frontImageURL": "https://cards-assets.stg.sdbxaz.azure.backbaseservices.com/assets/Multi-Use.png"
            },
            "instrument": "VIRTUAL",
            "additions": {},
        }
    ]

    # with patch(
    #     "app.bb_retail.request.list_cards", new_callable=AsyncMock
    # ) as mock_make_request:
    with patch(
        "app.bb_retail.request.BbApiRequest._make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_make_request.return_value = mock_card_list

        # Act
        await controller.update_profile(ctx, header, username, req)

    # Assert
    ctx.logger().info.assert_any_call(f'Updating user profile with input: "{req}"')
    ctx.logger().info.assert_any_call("Controller exiting...")


@pytest.mark.asyncio
async def test_get_profile():
    # Arrange
    controller = ProfileController()
    ctx = MagicMock(spec=RequestContext)
    ctx.logger.return_value = MagicMock()
    ctx.request_id.return_value = "test_request_id"
    username = "test_user"

    # Act
    result = await controller.get_profile(ctx, username)

    # Assert
    assert isinstance(result, ProfileDataResp)
    ctx.logger().info.assert_any_call(
        f'Getting user profile with username: "{username}"'
    )
    ctx.logger().info.assert_any_call("Controller exiting...")
