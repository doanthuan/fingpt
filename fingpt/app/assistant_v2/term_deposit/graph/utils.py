import json
from datetime import date, datetime, timedelta
from typing import Any, Dict

from langchain_core.messages import ToolMessage

from app.assistant_v2.term_deposit.constant import (
    GET_ACCOUNT_TOOL_NAME,
    GET_TERM_DEPOSIT_ACCOUNT_TOOL_NAME,
    GET_TERM_DEPOSIT_PRODUCT_TOOL_NAME,
    NOTICE_DEPOSIT_AMOUNT_TOOL_NAME,
    NOTICE_TERM_NUMBER_TOOL_NAME,
    NOTICE_TERM_UNIT_TOOL_NAME,
)
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.core.logging import Logger
from app.entity import (
    ActiveAccount,
    ChatRespMetadataForAccountChoice,
    ChatRespMetadataForChoices,
    TermDepositAccount,
    TermDepositProduct,
    TermUnit,
)
from app.entity.chat_response import (
    ChatRespMetadataForTermDepositProductChoice,
    ChatRespMetadataForTermDepositReviewChoice,
    ChatRespTermDepositLabel,
)


async def chain_ainvoke(chain, input_data: Dict[str, Any]):
    return await chain.ainvoke(input_data)


def extract_tool_messages(logger: Logger, messages) -> Dict[str, Any]:
    # get all recent tool messages
    logger.info("Extracting data from tool message...")
    output = {}
    for message in messages[::-1]:
        if not isinstance(message, ToolMessage):
            break
        logger.debug(f"Tool message: {message}")
        if message.name == GET_ACCOUNT_TOOL_NAME:
            output[TermDepositAgentStateFields.ACTIVE_ACCOUNTS] = {
                json.loads(account)["id"]: ActiveAccount(**json.loads(account))
                for account in eval(message.content)
            }
        elif message.name == GET_TERM_DEPOSIT_PRODUCT_TOOL_NAME:
            output[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS] = {
                json.loads(term_deposit_product)["id"]: TermDepositProduct(
                    **json.loads(term_deposit_product)
                )
                for term_deposit_product in eval(message.content)
            }
        elif message.name == GET_TERM_DEPOSIT_ACCOUNT_TOOL_NAME:
            output[TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS] = {
                json.loads(term_deposit_account)["id"]: TermDepositAccount(
                    **json.loads(term_deposit_account)
                )
                for term_deposit_account in eval(message.content)
            }
        elif message.name == NOTICE_DEPOSIT_AMOUNT_TOOL_NAME:
            output[TermDepositAgentStateFields.DEPOSIT_AMOUNT] = float(message.content)
        elif message.name == NOTICE_TERM_NUMBER_TOOL_NAME:
            output[TermDepositAgentStateFields.TERM_NUMBER] = int(message.content)
        elif message.name == NOTICE_TERM_UNIT_TOOL_NAME:
            output[TermDepositAgentStateFields.TERM_UNIT] = TermUnit(message.content)

    return output


def to_date(date_str: str) -> date:
    return datetime.fromisoformat(date_str).date()


def convert_to_day(term_unit: TermUnit, term_number: int) -> int:
    mapping_time = {
        TermUnit.D: 1,
        TermUnit.W: 7,
        TermUnit.M: 30,
        TermUnit.Y: 360,
    }
    days = mapping_time[term_unit] * term_number
    return days


def convert_to_time_string(term_unit: TermUnit) -> str:
    mapping_time = {
        TermUnit.D: "day(s)",
        TermUnit.W: "week(s)",
        TermUnit.M: "month(s)",
        TermUnit.Y: "year(s)",
    }

    time_string = mapping_time[term_unit]
    return time_string


def _compute_maturity_earn(
    deposit_amount: float,
    product: TermDepositProduct,
) -> float:
    mapping_time: dict[TermUnit, float] = {
        TermUnit.D: 1 / 360,
        TermUnit.W: 1 / 52,
        TermUnit.M: 1 / 12,
        TermUnit.Y: 1,
    }

    time_in_year = mapping_time[product.term_unit] * product.term_number
    maturity_earn = deposit_amount * product.interest_rate / 100 * time_in_year
    return maturity_earn


def update_term_deposit(
    deposit_amount: float,
    list_term_deposit: list[TermDepositProduct],
) -> dict[str, TermDepositProduct]:
    result: dict[str, TermDepositProduct] = {}
    for product in list_term_deposit:
        product.maturity_earn = _compute_maturity_earn(
            deposit_amount=deposit_amount, product=product
        )
        if (
            product.minimum_required_balance is None
            or product.minimum_required_balance <= deposit_amount
        ):
            product.is_available = True

        else:
            product.is_available = False

        result[product.id] = product

    return result


def _update_term_account(
    deposit_amount: float | None, list_term_deposit_account: list[TermDepositAccount]
) -> dict[str, TermDepositAccount]:
    result = {}
    for account in list_term_deposit_account:
        if to_date(account.maturity_date) - date.today() > timedelta(days=15):
            account.is_mature = False
            account.is_renewable = False
        elif (
            deposit_amount is not None
            and _compute_maturity_earn(
                deposit_amount=account.deposit_amount, product=account
            )
            + account.deposit_amount
            < deposit_amount
        ):
            account.is_renewable = False
            account.is_mature = True
        else:
            account.is_mature = True
            account.is_renewable = True

        result[account.id] = account
    return result


def _build_choices_from_term_deposit_accounts(
    term_deposit_accounts: Dict[str, TermDepositAccount]
) -> ChatRespMetadataForChoices:

    return ChatRespMetadataForChoices(
        choices=[
            ChatRespMetadataForTermDepositReviewChoice(
                id=term_deposit.id,
                name=term_deposit.name,
                interest_rate=term_deposit.interest_rate,
                term_number=term_deposit.term_number,
                term_unit=term_deposit.term_unit,
                deposit_amount=term_deposit.deposit_amount,
                maturity_date=term_deposit.maturity_date,
                is_enabled=(
                    True
                    if term_deposit.is_mature and term_deposit.is_renewable
                    else False
                ),
            )
            for term_deposit in term_deposit_accounts.values()
        ],
    )


def _build_choices_from_term_deposit_products(
    term_deposit_products: Dict[str, TermDepositProduct]
) -> ChatRespMetadataForChoices:
    ls_term_deposit = list(term_deposit_products.values())
    choices = []
    max_earn_idx = -1
    for idx, term_deposit in enumerate(ls_term_deposit):
        choice = ChatRespMetadataForTermDepositProductChoice(
            id=term_deposit.id,
            name=term_deposit.name,
            is_enabled=term_deposit.is_available,
            interest_rate=term_deposit.interest_rate,
            term_number=term_deposit.term_number,
            term_unit=term_deposit.term_unit,
            minimum_required_balance=term_deposit.minimum_required_balance,
            maturity_earn=term_deposit.maturity_earn,
        )
        if term_deposit.is_available and (
            max_earn_idx < 0
            or (
                term_deposit.maturity_earn > ls_term_deposit[max_earn_idx].maturity_earn
            )
        ):
            max_earn_idx = idx

        choices.append(choice)

    if max_earn_idx >= 0:
        choices[max_earn_idx].label = ChatRespTermDepositLabel.BEST_CHOICE

    # sort choices by available_balance
    choices = sorted(choices, key=lambda choice: choice.maturity_earn, reverse=True)
    return ChatRespMetadataForChoices(choices=choices)


def _build_choices_from_accounts(
    accounts: list[ActiveAccount],
    minimum_required_amount: float = 0,
) -> ChatRespMetadataForChoices:
    choices = [
        ChatRespMetadataForAccountChoice(
            id=account.id,
            name=account.name,
            available_balance=account.available_balance,
            currency=account.currency,
            is_enabled=account.available_balance >= minimum_required_amount
            and account.booked_balance >= 0,
            bban=account.identifications.bban if account.identifications else None,
            product_type=account.product_type,
        )
        for account in accounts.values()
    ]

    # sort choices by available_balance
    choices = sorted(choices, key=lambda choice: choice.available_balance, reverse=True)

    return ChatRespMetadataForChoices(choices=choices)
