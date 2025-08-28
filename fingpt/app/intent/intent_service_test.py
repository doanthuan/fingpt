from unittest import mock
from unittest.mock import AsyncMock, call, patch

import pytest

from app.core.context import RequestContext
from app.entity import (
    FieldStatus,
    Intent,
    IntentMetadataForMoneyTransfer,
    IntentMetadataType,
    IntentReqDto,
)
from app.entity.api import ApiHeader
from app.entity.intent import IntentMetadataForAbort
from app.entity.transfer import Currency
from app.intent.intent_service import IntentService
from app.prompt.prompt_module import PromptModule

prompt_module = PromptModule()


@pytest.mark.asyncio
async def test_analyze_single_intent_with_only_intention():
    # ARRANGE
    prompt_srv = prompt_module.prompt_srv()
    intent_srv = IntentService(prompt_srv)
    req = IntentReqDto(
        messages=["Make a transfer"],
    )
    ctx = RequestContext("test")
    header = ApiHeader(
        cookie="test",
        token="test",
    )

    # Mock the OpenAI response
    mock_response = {
        "intent": Intent.MONEY_TRANSFER.value,
        "metadata": {
            "type": IntentMetadataType.MONEY_TRANSFER_DATA,
            "amount": {"value": None, "status": FieldStatus.MISSING},
            "currency": {"value": None, "status": FieldStatus.MISSING},
            "recipient": {"value": None, "status": FieldStatus.MISSING},
            "account": {"value": None, "status": FieldStatus.MISSING},
        },
    }

    # ACT
    with patch(
        "app.intent.intent_service.IntentService.load_prompt"
    ) as mock_load_prompt:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_response
        mock_load_prompt.return_value = mock_chain
        resp = await intent_srv.analyze_intent(ctx, header, req)

    # ASSERT
    assert resp is not None
    assert resp.intent == Intent.MONEY_TRANSFER.value
    assert resp.metadata.type == IntentMetadataType.MONEY_TRANSFER_DATA

    metadata = IntentMetadataForMoneyTransfer.model_validate(resp.metadata)
    assert metadata.amount.value is None
    assert metadata.currency.value is None
    assert metadata.recipient.value is None
    assert metadata.account.value is None
    assert metadata.amount.status == FieldStatus.MISSING
    assert metadata.currency.status == FieldStatus.MISSING
    assert metadata.recipient.status == FieldStatus.MISSING
    assert metadata.account.status == FieldStatus.MISSING

    # Verify that the mock was called
    mock_chain.ainvoke.assert_called_once_with(
        input={
            "message_history": ["Make a transfer"],
            "current_payload": "{}",
        }
    )


@pytest.mark.asyncio
async def test_analyze_single_intent_with_amount():
    # ARRANGE
    prompt_srv = prompt_module.prompt_srv()
    intent_srv = IntentService(prompt_srv)
    req = IntentReqDto(
        messages=["Make a transfer of $1000"],
    )
    ctx = RequestContext("test")
    header = ApiHeader(
        cookie="test",
        token="test",
    )

    # Mock the OpenAI response
    mock_response = {
        "intent": Intent.MONEY_TRANSFER.value,
        "metadata": {
            "type": IntentMetadataType.MONEY_TRANSFER_DATA,
            "amount": {"value": 1000.0, "status": FieldStatus.AVAILABLE},
            "currency": {"value": Currency.USD.value, "status": FieldStatus.AVAILABLE},
            "recipient": {"value": None, "status": FieldStatus.MISSING},
            "account": {"value": None, "status": FieldStatus.MISSING},
        },
    }

    # ACT
    with patch(
        "app.intent.intent_service.IntentService.load_prompt"
    ) as mock_load_prompt:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_response
        mock_load_prompt.return_value = mock_chain
        resp = await intent_srv.analyze_intent(ctx, header, req)

    # ASSERT
    assert resp is not None
    assert resp.intent == Intent.MONEY_TRANSFER.value
    assert resp.metadata.type == IntentMetadataType.MONEY_TRANSFER_DATA

    metadata = IntentMetadataForMoneyTransfer.model_validate(resp.metadata)
    assert metadata.amount.value == 1000.0
    assert metadata.currency.value == Currency.USD.value
    assert metadata.recipient.value is None
    assert metadata.account.value is None
    assert metadata.amount.status == FieldStatus.AVAILABLE
    assert metadata.currency.status == FieldStatus.AVAILABLE
    assert metadata.recipient.status == FieldStatus.MISSING
    assert metadata.account.status == FieldStatus.MISSING

    # Verify that the mock was called
    mock_chain.ainvoke.assert_called_once_with(
        input={
            "message_history": ["Make a transfer of $1000"],
            "current_payload": "{}",
        }
    )


@pytest.mark.asyncio
async def test_analyze_multiple_queries_with_only_the_amount():
    # ARRANGE
    prompt_srv = prompt_module.prompt_srv()
    intent_srv = IntentService(prompt_srv)
    queries = [
        "Make a transfer",
        "$1000",
    ]
    ctx = RequestContext("test")
    header = ApiHeader(
        cookie="test",
        token="test",
    )

    # Mock the OpenAI responses
    mock_responses = [
        {
            "intent": Intent.MONEY_TRANSFER.value,
            "metadata": {
                "type": IntentMetadataType.MONEY_TRANSFER_DATA,
                "amount": {"value": None, "status": FieldStatus.MISSING},
                "currency": {"value": None, "status": FieldStatus.MISSING},
                "recipient": {"value": None, "status": FieldStatus.MISSING},
                "account": {"value": None, "status": FieldStatus.MISSING},
            },
        },
        {
            "intent": Intent.MONEY_TRANSFER.value,
            "metadata": {
                "type": IntentMetadataType.MONEY_TRANSFER_DATA,
                "amount": {"value": 1000.0, "status": FieldStatus.AVAILABLE},
                "currency": {
                    "value": Currency.USD.value,
                    "status": FieldStatus.AVAILABLE,
                },
                "recipient": {"value": None, "status": FieldStatus.MISSING},
                "account": {"value": None, "status": FieldStatus.MISSING},
            },
        },
    ]

    messages: list[str] = []
    resp = None

    with patch(
        "app.intent.intent_service.IntentService.load_prompt"
    ) as mock_load_prompt:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.side_effect = mock_responses
        mock_load_prompt.return_value = mock_chain

        for query in queries:
            messages.append(query)
            if not resp:
                req = IntentReqDto(
                    messages=messages,
                )
            else:
                req = IntentReqDto(
                    messages=messages,
                    metadata=resp,
                )

            # ACT
            resp = await intent_srv.analyze_intent(ctx, header, req)

    # ASSERT
    assert resp is not None
    assert resp.intent == Intent.MONEY_TRANSFER.value
    assert resp.metadata.type == IntentMetadataType.MONEY_TRANSFER_DATA

    metadata = IntentMetadataForMoneyTransfer.model_validate(resp.metadata)
    assert metadata.amount.value == 1000.0
    assert metadata.currency.value == Currency.USD.value
    assert metadata.recipient.value is None
    assert metadata.account.value is None
    assert metadata.amount.status == FieldStatus.AVAILABLE
    assert metadata.currency.status == FieldStatus.AVAILABLE
    assert metadata.recipient.status == FieldStatus.MISSING
    assert metadata.account.status == FieldStatus.MISSING

    # Verify that the mock was called twice
    assert mock_chain.ainvoke.call_count == 2
    mock_chain.ainvoke.assert_has_calls(
        [
            call(
                input={"message_history": ["Make a transfer"], "current_payload": "{}"}
            ),
            call(
                input={
                    "message_history": ["Make a transfer", "$1000"],
                    "current_payload": mock.ANY,
                }
            ),
        ]
    )


@pytest.mark.asyncio
async def test_analyze_multiple_queries_with_cancel():
    # ARRANGE
    prompt_srv = prompt_module.prompt_srv()
    intent_srv = IntentService(prompt_srv)
    queries = [
        "Make a transfer",
        "$1000",
        "Cancel the transfer",
    ]
    ctx = RequestContext("test")
    header = ApiHeader(
        cookie="test",
        token="test",
    )

    # Mock the OpenAI responses
    mock_responses = [
        {
            "intent": Intent.MONEY_TRANSFER.value,
            "metadata": {
                "type": IntentMetadataType.MONEY_TRANSFER_DATA,
                "amount": {"value": None, "status": FieldStatus.MISSING},
                "currency": {"value": None, "status": FieldStatus.MISSING},
                "recipient": {"value": None, "status": FieldStatus.MISSING},
                "account": {"value": None, "status": FieldStatus.MISSING},
            },
        },
        {
            "intent": Intent.MONEY_TRANSFER.value,
            "metadata": {
                "type": IntentMetadataType.MONEY_TRANSFER_DATA,
                "amount": {"value": 1000.0, "status": FieldStatus.AVAILABLE},
                "currency": {
                    "value": Currency.USD.value,
                    "status": FieldStatus.AVAILABLE,
                },
                "recipient": {"value": None, "status": FieldStatus.MISSING},
                "account": {"value": None, "status": FieldStatus.MISSING},
            },
        },
        {
            "intent": Intent.ABORT.value,
            "metadata": {
                "type": IntentMetadataType.ABORT_DATA,
                "reason": {
                    "value": "User requested cancellation",
                    "status": FieldStatus.AVAILABLE,
                },
            },
        },
    ]

    messages: list[str] = []
    resp = None

    with patch(
        "app.intent.intent_service.IntentService.load_prompt"
    ) as mock_load_prompt:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.side_effect = mock_responses
        mock_load_prompt.return_value = mock_chain

        for query in queries:
            messages.append(query)
            if not resp:
                req = IntentReqDto(
                    messages=messages,
                )
            else:
                req = IntentReqDto(
                    messages=messages,
                    metadata=resp,
                )

            # ACT
            resp = await intent_srv.analyze_intent(ctx, header, req)

    # ASSERT
    assert resp is not None
    assert resp.intent == Intent.ABORT.value
    assert resp.metadata.type == IntentMetadataType.ABORT_DATA

    metadata = IntentMetadataForAbort.model_validate(resp.metadata)
    assert metadata.reason.value == "User requested cancellation"
    assert metadata.reason.status == FieldStatus.AVAILABLE

    # Verify that the mock was called three times
    assert mock_chain.ainvoke.call_count == 3
    mock_chain.ainvoke.assert_has_calls(
        [
            call(
                input={"message_history": ["Make a transfer"], "current_payload": "{}"}
            ),
            call(
                input={
                    "message_history": ["Make a transfer", "$1000"],
                    "current_payload": mock.ANY,
                }
            ),
            call(
                input={
                    "message_history": [
                        "Make a transfer",
                        "$1000",
                        "Cancel the transfer",
                    ],
                    "current_payload": mock.ANY,
                }
            ),
        ]
    )


@pytest.mark.asyncio
async def test_analyze_single_intent_with_full_transfer_details():
    # ARRANGE
    prompt_srv = prompt_module.prompt_srv()
    intent_srv = IntentService(prompt_srv)
    messages = ["Transfer 500 euros to John Doe from my savings account"]
    ctx = RequestContext("test")
    header = ApiHeader(
        cookie="test",
        token="test",
    )
    req = IntentReqDto(
        messages=messages,
    )

    # Mock the OpenAI response
    mock_response = {
        "intent": Intent.MONEY_TRANSFER.value,
        "metadata": {
            "type": IntentMetadataType.MONEY_TRANSFER_DATA,
            "amount": {"value": 500.0, "status": FieldStatus.AVAILABLE},
            "currency": {"value": Currency.EUR.value, "status": FieldStatus.AVAILABLE},
            "recipient": {
                "value": {"name": "John Doe"},
                "status": FieldStatus.AVAILABLE,
            },
            "account": {
                "value": {"displayName": "Savings Account"},
                "status": FieldStatus.AVAILABLE,
            },
        },
    }

    # Mock the list_contacts function
    mock_contacts = [
        {
            "id": "1",
            "name": "John Doe",
            "accounts": [
                {
                    "accountNumber": "1234567890",
                    "phoneNumber": "+1234567890",
                    "emailId": "john.doe@example.com",
                    "iban": "DE89370400440532013000",
                }
            ],
        }
    ]
    # Mock the list_accounts function
    mock_accounts = {
        "currentAccounts": {
            "products": [
                {
                    "id": "1",
                    "displayName": "Savings Account",
                    "productType": "SAVINGS",
                    "productKindName": "Standard Savings",
                    "availableBalance": 1000.0,
                    "currency": "EUR",
                    "identifications": {"BBAN": "12345678", "BIC": "ABCDEFGH"},
                    "bookedBalance": 1000.0,
                    "isUsable": True,
                }
            ]
        }
    }

    # ACT
    with patch(
        "app.intent.intent_service.IntentService.load_prompt"
    ) as mock_load_prompt, patch(
        "app.bb_retail.request.BbApiRequest._make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_response
        mock_load_prompt.return_value = mock_chain
        mock_make_request.side_effect = [
            mock_contacts,  # For list_contacts
            mock_accounts,  # For list_accounts
        ]
        resp = await intent_srv.analyze_intent(ctx, header, req)

    # ASSERT
    assert resp is not None
    assert resp.intent == Intent.MONEY_TRANSFER.value
    assert resp.metadata.type == IntentMetadataType.MONEY_TRANSFER_DATA

    metadata = IntentMetadataForMoneyTransfer.model_validate(resp.metadata)
    assert metadata.amount.value == 500.0
    assert metadata.currency.value == Currency.EUR.value
    assert metadata.recipient.value is not None
    assert metadata.account.value is not None
    assert metadata.amount.status == FieldStatus.AVAILABLE
    assert metadata.currency.status == FieldStatus.AVAILABLE
    assert metadata.recipient.status == FieldStatus.AVAILABLE
    assert metadata.account.status == FieldStatus.AVAILABLE

    # Verify that the mock was called
    mock_chain.ainvoke.assert_called_once_with(
        input={
            "message_history": messages,
            "current_payload": "{}",
        }
    )


@pytest.mark.asyncio
async def test_analyze_multiple_queries_with_partial_information():
    # ARRANGE
    prompt_srv = prompt_module.prompt_srv()
    intent_srv = IntentService(prompt_srv)
    messages = [
        "I want to send money",
        "To Alice",
        "200 pounds",
        "From my checking account",
    ]
    ctx = RequestContext("test")
    header = ApiHeader(
        cookie="test",
        token="test",
    )
    req = IntentReqDto(
        messages=messages,
    )

    # Mock the OpenAI response
    mock_response = {
        "intent": Intent.MONEY_TRANSFER.value,
        "metadata": {
            "type": IntentMetadataType.MONEY_TRANSFER_DATA,
            "amount": {"value": 200.0, "status": FieldStatus.AVAILABLE},
            "currency": {"value": Currency.GBP.value, "status": FieldStatus.AVAILABLE},
            "recipient": {"value": {"name": "Alice"}, "status": FieldStatus.AVAILABLE},
            "account": {
                "value": {"displayName": "Checking Account"},
                "status": FieldStatus.AVAILABLE,
            },
        },
    }

    # Mock the list_contacts function
    mock_contacts = [
        {
            "id": "1",
            "name": "Alice",
            "accounts": [
                {
                    "accountNumber": "1234567890",
                    "phoneNumber": "+1234567890",
                    "emailId": "alice@example.com",
                    "iban": "GB29NWBK60161331926819",
                }
            ],
        }
    ]
    # Mock the list_accounts function
    mock_accounts = {
        "currentAccounts": {
            "products": [
                {
                    "id": "1",
                    "displayName": "Checking Account",
                    "productType": "CURRENT",
                    "productKindName": "Standard Checking",
                    "availableBalance": 1000.0,
                    "currency": "GBP",
                    "identifications": {"BBAN": "12345678", "BIC": "ABCDEFGH"},
                    "bookedBalance": 1000.0,
                    "isUsable": True,
                }
            ]
        }
    }

    # ACT
    with patch(
        "app.intent.intent_service.IntentService.load_prompt"
    ) as mock_load_prompt, patch(
        "app.bb_retail.request.BbApiRequest._make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_response
        mock_load_prompt.return_value = mock_chain
        mock_make_request.side_effect = [
            mock_contacts,  # For list_contacts
            mock_accounts,  # For list_accounts
        ]
        resp = await intent_srv.analyze_intent(ctx, header, req)

    # ASSERT
    assert resp is not None
    assert resp.intent == Intent.MONEY_TRANSFER.value
    assert resp.metadata.type == IntentMetadataType.MONEY_TRANSFER_DATA

    metadata = IntentMetadataForMoneyTransfer.model_validate(resp.metadata)
    assert metadata.amount.value == 200.0
    assert metadata.currency.value == Currency.GBP.value
    assert metadata.recipient.value is not None
    assert metadata.account.value is not None
    assert metadata.amount.status == FieldStatus.AVAILABLE
    assert metadata.currency.status == FieldStatus.AVAILABLE
    assert metadata.recipient.status == FieldStatus.AVAILABLE
    assert metadata.account.status == FieldStatus.AVAILABLE

    # Verify that the mock was called
    mock_chain.ainvoke.assert_called_once_with(
        input={
            "message_history": messages,
            "current_payload": "{}",
        }
    )


@pytest.mark.asyncio
async def test_analyze_multiple_queries_as_a_conversation_wrong_contact():
    # ARRANGE
    prompt_srv = prompt_module.prompt_srv()
    intent_srv = IntentService(prompt_srv)
    messages = [
        "I want to send money",
        "To Kevin",  # WRONG CONTACT
        "200 pounds",
        "From my checking account",
    ]
    ctx = RequestContext("test")
    header = ApiHeader(
        cookie="test",
        token="test",
    )
    req = IntentReqDto(
        messages=messages,
    )

    # Mock the OpenAI response
    mock_response = {
        "intent": Intent.MONEY_TRANSFER.value,
        "metadata": {
            "type": IntentMetadataType.MONEY_TRANSFER_DATA,
            "amount": {"value": 200.0, "status": FieldStatus.AVAILABLE},
            "currency": {"value": Currency.GBP.value, "status": FieldStatus.AVAILABLE},
            "recipient": {"value": {"name": "Kevin"}, "status": FieldStatus.AVAILABLE},
            "account": {"value": None, "status": FieldStatus.MISSING},
        },
    }

    # Mock the list_contacts function
    mock_contacts = []

    # Mock the list_accounts function
    mock_accounts = {
        "currentAccounts": {
            "products": [
                {
                    "id": "1",
                    "displayName": "Checking Account",
                    "productType": "CURRENT",
                    "productKindName": "Standard Checking",
                    "availableBalance": 1000.0,
                    "currency": "GBP",
                    "identifications": {"BBAN": "12345678", "BIC": "ABCDEFGH"},
                    "bookedBalance": 1000.0,
                    "isUsable": True,
                }
            ]
        }
    }

    # ACT
    with patch(
        "app.intent.intent_service.IntentService.load_prompt"
    ) as mock_load_prompt, patch(
        "app.bb_retail.request.BbApiRequest._make_request", new_callable=AsyncMock
    ) as mock_make_request:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_response
        mock_load_prompt.return_value = mock_chain
        mock_make_request.side_effect = [
            mock_contacts,  # For list_contacts
            mock_accounts,  # For list_accounts
        ]
        resp = await intent_srv.analyze_intent(ctx, header, req)

    # ASSERT
    assert resp is not None
    assert resp.intent == Intent.MONEY_TRANSFER.value
    assert resp.metadata.type == IntentMetadataType.MONEY_TRANSFER_DATA
    metadata = IntentMetadataForMoneyTransfer.model_validate(resp.metadata)
    assert metadata.amount.value == 200.0
    assert metadata.currency.value == Currency.GBP.value
    assert metadata.recipient.value is None
    assert metadata.account.value is None
    assert metadata.amount.status == FieldStatus.AVAILABLE
    assert metadata.currency.status == FieldStatus.AVAILABLE
    assert metadata.recipient.status == FieldStatus.NOT_FOUND
    assert metadata.account.status == FieldStatus.MISSING

    # Verify that the mock was called
    mock_chain.ainvoke.assert_called_once_with(
        input={
            "message_history": messages,
            "current_payload": "{}",
        }
    )


@pytest.mark.asyncio
async def test_analyze_intent_with_currency_change():
    # ARRANGE
    prompt_srv = prompt_module.prompt_srv()
    intent_srv = IntentService(prompt_srv)
    queries = [
        "Transfer 100 dollars to Bob",
        "Actually, make it 100 euros",
    ]
    ctx = RequestContext("test")
    header = ApiHeader(
        cookie="test",
        token="test",
    )
    req = IntentReqDto(
        messages=queries,
    )
    # Mock the list_contacts function
    mock_contacts = [
        {
            "id": "1",
            "name": "Bob",
            "accounts": [
                {
                    "accountNumber": "1234567890",
                    "phoneNumber": "+1234567890",
                    "emailId": "bob@example.com",
                    "iban": "DE89370400440532013000",
                }
            ],
        }
    ]
    # Mock the list_accounts function
    mock_accounts = {
        "currentAccounts": {
            "products": [
                {
                    "id": "1",
                    "displayName": "Checking Account",
                    "productType": "CURRENT",
                    "productKindName": "Standard Checking",
                    "availableBalance": 1000.0,
                    "currency": "EUR",
                    "identifications": {"BBAN": "12345678", "BIC": "ABCDEFGH"},
                    "bookedBalance": 1000.0,
                    "isUsable": True,
                }
            ]
        }
    }

    # Mock the OpenAI response
    mock_response = {
        "intent": Intent.MONEY_TRANSFER.value,
        "metadata": {
            "type": IntentMetadataType.MONEY_TRANSFER_DATA,
            "amount": {"value": 100.0, "status": FieldStatus.AVAILABLE},
            "currency": {"value": Currency.EUR.value, "status": FieldStatus.AVAILABLE},
            "recipient": {
                "value": {"name": "Bob", "account": "DE89370400440532013000"},
                "status": FieldStatus.AVAILABLE,
            },
            "account": {
                "value": {"id": "1", "name": "Checking Account"},
                "status": FieldStatus.AVAILABLE,
            },
        },
    }

    # ACT
    with patch(
        "app.bb_retail.request.BbApiRequest._make_request", new_callable=AsyncMock
    ) as mock_make_request, patch(
        "app.intent.intent_service.IntentService.load_prompt"
    ) as mock_load_prompt:
        mock_make_request.side_effect = [
            mock_contacts,  # For list_contacts
            mock_accounts,  # For list_accounts
        ]
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_response
        mock_load_prompt.return_value = mock_chain

        resp = await intent_srv.analyze_intent(ctx, header, req)

    # ASSERT
    assert resp is not None
    assert resp.intent == Intent.MONEY_TRANSFER.value
    assert resp.metadata.type == IntentMetadataType.MONEY_TRANSFER_DATA

    metadata = IntentMetadataForMoneyTransfer.model_validate(resp.metadata)
    assert metadata.amount.value == 100.0
    assert metadata.currency.value == Currency.EUR.value
    assert metadata.recipient.value is not None
    assert metadata.account.value is not None
    assert metadata.amount.status == FieldStatus.AVAILABLE
    assert metadata.currency.status == FieldStatus.AVAILABLE
    assert metadata.recipient.status == FieldStatus.AVAILABLE
    assert metadata.account.status == FieldStatus.AVAILABLE

    # Verify that the mock was called
    mock_chain.ainvoke.assert_called_once_with(
        input={
            "message_history": queries,
            "current_payload": "{}",
        }
    )


@pytest.mark.asyncio
async def test_analyze_intent_with_invalid_input():
    # ARRANGE
    prompt_srv = prompt_module.prompt_srv()
    intent_srv = IntentService(prompt_srv)
    req = IntentReqDto(
        messages=["What's the weather like today?"],
    )
    ctx = RequestContext("test")
    header = ApiHeader(
        cookie="test",
        token="test",
    )

    # Mock the OpenAI response
    mock_response = {
        "intent": Intent.UNKNOWN.value,
        "metadata": {
            "type": IntentMetadataType.UNKNOWN_DATA,
        },
    }

    # ACT
    with patch(
        "app.intent.intent_service.IntentService.load_prompt"
    ) as mock_load_prompt:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_response
        mock_load_prompt.return_value = mock_chain
        resp = await intent_srv.analyze_intent(ctx, header, req)

    # ASSERT
    assert resp is not None
    assert resp.intent == Intent.UNKNOWN.value
    assert resp.metadata.type == IntentMetadataType.UNKNOWN_DATA

    # Verify that the mock was called
    mock_chain.ainvoke.assert_called_once_with(
        input={
            "message_history": ["What's the weather like today?"],
            "current_payload": "{}",
        }
    )
