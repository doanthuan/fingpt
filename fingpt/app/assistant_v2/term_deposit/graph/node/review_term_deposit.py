from datetime import date, timedelta
from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.term_deposit.graph.utils import convert_to_day, to_date
from app.assistant_v2.term_deposit.state import (
    TermDepositAgentState,
    TermDepositAgentStateFields,
)
from app.assistant_v2.util.misc import extract_config
from app.entity import (
    ActiveAccount,
    ChatRespAction,
    ChatRespDto,
    TermDepositAccount,
    TermDepositProduct,
)
from app.entity.chat_response import ChatRespMetadataForTermDeposit
from app.utils.modified_langfuse_decorator import observe

review_term_deposit_node = NodeName("review_term_deposit")


@observe()
async def review_term_deposit_func(
    state: TermDepositAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info("Reviewing term deposit...")
    term_deposit_product: TermDepositProduct = list(
        state[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS].values()
    )[0]
    deposit_amount = state[TermDepositAgentStateFields.DEPOSIT_AMOUNT]
    last_message = state[TermDepositAgentStateFields.MESSAGES][-1]

    output = {}
    if state[TermDepositAgentStateFields.ACTIVE_ACCOUNTS]:
        if deposit_amount < term_deposit_product.minimum_required_balance:
            response = ChatRespDto(
                action=ChatRespAction.SHOW_REPLY,
                thread_id=config_data[THREAD_ID_KEY],
                response=last_message.content,
                metadata=None,
            )
        else:
            accounts = list(state[TermDepositAgentStateFields.ACTIVE_ACCOUNTS].values())
            active_account: ActiveAccount = accounts[0]
            maturity_date = date.today() + timedelta(
                days=convert_to_day(
                    term_deposit_product.term_unit, term_deposit_product.term_number
                )
            )
            response = ChatRespDto(
                action=ChatRespAction.MAKE_TERM_DEPOSIT,
                thread_id=config_data[THREAD_ID_KEY],
                response=last_message.content,
                metadata=ChatRespMetadataForTermDeposit(
                    id=term_deposit_product.id,
                    deposit_amount=deposit_amount,
                    interest_rate=term_deposit_product.interest_rate,
                    term_number=term_deposit_product.term_number,
                    term_unit=term_deposit_product.term_unit,
                    maturity_earn=term_deposit_product.maturity_earn,
                    start_date=date.today().isoformat(),
                    maturity_date=maturity_date.isoformat(),
                    active_account=active_account.dict(),
                    renewal_account={},
                    date_of_renewal=None,
                ),
            )
            output[TermDepositAgentStateFields.MESSAGES] = [
                HumanMessage(content="It's okay.")
            ]
    elif state[TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS]:
        # if deposit_amount < term_deposit_product.minimum_required_balance:
        #     response = ChatRespDto(
        #         action=ChatRespAction.SHOW_REPLY,
        #         thread_id=config_data[THREAD_ID_KEY],
        #         response=last_message.content,
        #         metadata=None,
        #     )
        # else:
        term_deposit_accounts = list(
            state[TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS].values()
        )
        renewal_account: TermDepositAccount = term_deposit_accounts[0]
        delta = timedelta(
            days=convert_to_day(
                term_deposit_product.term_unit, term_deposit_product.term_number
            )
        )
        maturity_date = to_date(renewal_account.maturity_date) + delta
        response = ChatRespDto(
            action=ChatRespAction.RENEW_TERM_DEPOSIT,
            thread_id=config_data[THREAD_ID_KEY],
            response=last_message.content,
            metadata=ChatRespMetadataForTermDeposit(
                id=renewal_account.id,
                deposit_amount=renewal_account.deposit_amount,
                interest_rate=term_deposit_product.interest_rate,
                term_number=term_deposit_product.term_number,
                term_unit=term_deposit_product.term_unit,
                maturity_earn=term_deposit_product.maturity_earn,
                date_of_renewal=renewal_account.maturity_date,
                maturity_date=maturity_date.isoformat(),
                renewal_account=renewal_account.dict(),
                active_account={},
                start_date=None,
            ),
        )
        output[TermDepositAgentStateFields.MESSAGES] = [
            HumanMessage(content="It's okay.")
        ]
    config_data[PENDING_RESPONSE_KEY].append(response)
    # reset state
    output[TermDepositAgentStateFields.RESUME_NODE] = None
    output[TermDepositAgentStateFields.DEPOSIT_AMOUNT] = None
    output[TermDepositAgentStateFields.TERM_NUMBER] = None
    output[TermDepositAgentStateFields.TERM_UNIT] = None
    output[TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS] = {}
    output[TermDepositAgentStateFields.ACTIVE_ACCOUNTS] = {}
    output[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS] = {}
    output[TermDepositAgentStateFields.HUMAN_APPROVAL_ACTIVE_ACCOUNT] = False
    output[TermDepositAgentStateFields.HUMAN_APPROVAL_TERM_DEPOSIT_ACCOUNT] = False
    output[TermDepositAgentStateFields.HUMAN_APPROVAL_TERM_DEPOSIT_PRODUCT] = False
    output[TermDepositAgentStateFields.HUMAN_APPROVAL_PRESENT_OFFER] = False
    return output
