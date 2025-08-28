import traceback
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from langgraph.graph import START
from langgraph.graph.state import CompiledStateGraph

from app.assistant_v2.common.base_agent_config import extract_bb_retail_api_config
from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    EBP_ACCESS_TOKEN_KEY,
    EBP_COOKIE_KEY,
    EBP_EDGE_DOMAIN_KEY,
    PENDING_RESPONSE_KEY,
    THREAD_ID_KEY,
    USER_CHOICE_ID_KEY,
    USER_QUERY_KEY,
)
from app.assistant_v2.primary.constant import GUARDRAIL_ERROR_CONTENT
from app.assistant_v2.primary.graph import AssistantGraph
from app.assistant_v2.term_deposit.graph.node import present_offer_node
from app.assistant_v2.term_deposit.graph.utils import update_term_deposit
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.bb_retail.request import list_td_products, list_term_deposit_accounts
from app.core.config import settings
from app.core.context import RequestContext
from app.entity import (
    ApiHeader,
    AssistantStatus,
    ChatReqAction,
    ChatReqDto,
    ChatReqMetadataForChoice,
    ChatReqMetadataForOffer,
    ChatReqMetadataForQuery,
    ChatRespAction,
    ChatRespDto,
    ChatRespMetadataForOffer,
    ChatRespMetadataType,
    OfferProduct,
    OfferReqDataForTermDeposit,
    OfferType,
)
from app.entity.error import GuardrailInputError, UnauthorizedError

# from app.nemo_config.guardrails import guardrails_input
from app.entity.offer import OfferReq, OfferResp, OfferRespDataForCard
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import observe  # type: ignore

from .state import AssistantConfig, AssistantStateFields


class AssistantController:
    def __init__(
        self,
        prompt_srv: PromptService,
        llm: AzureChatOpenAI,
        graph: AssistantGraph,
        debug: bool = False,
    ) -> None:
        self.llm = llm
        self.prompt_srv = prompt_srv
        self.debug = debug
        self.graph = graph

    async def _get_workflow(self):
        return await self.graph.get_graph()

    def _get_config(self) -> RunnableConfig:
        return RunnableConfig(
            configurable=dict(
                AssistantConfig(
                    thread_id=None,
                    ctx=RequestContext("PLACEHOLDER"),
                    llm_model=self.llm,
                    ps=self.prompt_srv,
                    pending_response=[],
                    user_query=None,
                    user_choice_id=None,
                    ebp_access_token=None,
                    ebp_cookie=None,
                    ebp_edge_domain=None,
                )
            )
        )

    @observe()
    async def chat(
        self,
        ctx: RequestContext,
        header: ApiHeader,
        req: ChatReqDto,
    ) -> ChatRespDto:
        logger = ctx.logger()
        logger.info(f'Received user input: "{req}"')
        state_storage = settings.assistant_state_path
        memory = AsyncSqliteSaver.from_conn_string(state_storage)
        agent: Optional[CompiledStateGraph] = None
        try:
            logger.debug("Compling agent with memory...")
            agent = (await self._get_workflow()).compile(
                checkpointer=memory,
            )
            if req.action == ChatReqAction.QUERY:
                return await self._query(
                    ctx,
                    agent,
                    header,
                    ChatReqMetadataForQuery.model_validate(req.metadata),
                )
            elif req.action == ChatReqAction.MAKE_CHOICE:
                return await self._make_choice(
                    ctx,
                    agent,
                    header,
                    ChatReqMetadataForChoice.model_validate(req.metadata),
                )
            elif req.action == ChatReqAction.GET_OFFER:
                return await self._get_offer(
                    ctx,
                    agent,
                    header,
                    ChatReqMetadataForOffer.model_validate(req.metadata),
                )

            else:
                raise HTTPException(
                    status_code=400,
                    detail=f'Invalid action "{req.action}"',
                )

        except GuardrailInputError as e:
            logger.error(f"Guardrail Input Error: {str(e)}, trace: {e.trace}")
            return ChatRespDto(
                thread_id=req.metadata.thread_id,
                action=ChatRespAction.SHOW_REPLY,
                response=GUARDRAIL_ERROR_CONTENT,
                metadata=None,
            )

        except HTTPException as e:
            logger.error(f"Http exception: {str(e)}")
            traceback.print_exc()
            raise e

        except UnauthorizedError:
            logger.error("Unauthorized access")
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials data",
                headers={"www-authenticate": 'Bearer error="invalid_token"'},
            )

        except Exception as e:
            logger.error(f"Assistant error: {e}")
            logger.error(traceback.format_exc())
            assert req.metadata.thread_id is not None
            traceback.print_exc()
            return await self._reset_state(
                ctx,
                agent,
                self._get_config(),
                req.metadata.thread_id,
            )

    # @guardrails_input("req_data.user_query")

    async def _query(
        self,
        ctx: RequestContext,
        agent: CompiledStateGraph,
        header: ApiHeader,
        req_data: ChatReqMetadataForQuery,
    ) -> ChatRespDto:
        logger = ctx.logger()
        logger.debug("Processing user query...")
        cfg = self._get_config()
        cfg[CONFIGURABLE_CONTEXT_KEY].update(  # type: ignore
            {
                THREAD_ID_KEY: req_data.thread_id,
                CONTEXT_KEY: ctx,
                EBP_ACCESS_TOKEN_KEY: header.token,
                EBP_COOKIE_KEY: header.cookie,
                EBP_EDGE_DOMAIN_KEY: settings.ebp_edge_domain,
                USER_QUERY_KEY: req_data.user_query,
            }
        )
        logger.debug("Clear WAIT_FOR_CHOICE state if it is set...")
        await agent.aupdate_state(
            config=cfg,
            values={
                AssistantStateFields.STATUS: AssistantStatus.WAIT_FOR_QUERY,
            },
            as_node=START,
        )
        logger.debug("Invoking agent...")
        await agent.ainvoke(
            input={
                AssistantStateFields.MESSAGES: [HumanMessage(req_data.user_query)],
            },
            config=cfg,
            stream_mode="values",
            debug=self.debug,
        )
        config_data: AssistantConfig = cfg.get(CONFIGURABLE_CONTEXT_KEY, {})
        response: ChatRespDto = config_data[PENDING_RESPONSE_KEY].pop()
        response.thread_id = req_data.thread_id
        logger.info("Returning response...")
        return response

    async def _make_choice(
        self,
        ctx: RequestContext,
        agent: CompiledStateGraph,
        header: ApiHeader,
        req_data: ChatReqMetadataForChoice,
    ) -> ChatRespDto:
        logger = ctx.logger()
        logger.debug("Processing user choice...")
        cfg = self._get_config()
        cfg[CONFIGURABLE_CONTEXT_KEY].update(  # type: ignore
            {
                THREAD_ID_KEY: req_data.thread_id,
                CONTEXT_KEY: ctx,
                EBP_ACCESS_TOKEN_KEY: header.token,
                EBP_COOKIE_KEY: header.cookie,
                EBP_EDGE_DOMAIN_KEY: settings.ebp_edge_domain,
                USER_CHOICE_ID_KEY: req_data.choice_id,
            }
        )
        choice_id = req_data.choice_id
        snapshot = await agent.aget_state(config=cfg)
        state = snapshot.values

        if (
            AssistantStateFields.STATUS not in state
            or state[AssistantStateFields.STATUS] != AssistantStatus.WAIT_FOR_CHOICE
        ):
            logger.error(f"Unexpected choice ID: {choice_id}")
            response = ChatRespDto(
                action=ChatRespAction.SHOW_REPLY,
                response=(
                    "I am not expecting a choice from you at this moment. "
                    "Please double-check your input."
                ),
                metadata=None,
            )

        logger.debug("Resuming assistant...")
        await agent.ainvoke(
            input={
                AssistantStateFields.MESSAGES: [
                    HumanMessage("Great!"),
                ],
            },
            config=cfg,
            stream_mode="values",
            debug=self.debug,
        )
        config_data: AssistantConfig = cfg.get(CONFIGURABLE_CONTEXT_KEY, {})
        response: ChatRespDto = config_data[PENDING_RESPONSE_KEY].pop()
        response.thread_id = req_data.thread_id
        logger.info("Returning response...")
        return response

    async def _get_offer(
        self,
        ctx: RequestContext,
        agent: CompiledStateGraph,
        header: ApiHeader,
        req_data: ChatReqMetadataForOffer,
    ) -> ChatRespDto:
        logger = ctx.logger()
        logger.debug("Processing get offer query...")
        if req_data.offer.product == OfferProduct.TERM_DEPOSIT:
            return await self._get_term_deposit_offer(ctx, agent, header, req_data)
        else:
            return await self._get_card_offer(ctx, agent, header, req_data)

    async def _get_card_offer(
        self,
        ctx: RequestContext,
        agent: CompiledStateGraph,
        header: ApiHeader,
        req_data: ChatReqMetadataForOffer,
    ) -> ChatRespDto:
        logger = ctx.logger()
        logger.debug("Getting card offer...")
        _ = OfferReq.model_validate(req_data.offer)
        next2weeks = datetime.now() + timedelta(days=14)
        exp_date = next2weeks.strftime("%b %d, %Y")

        message = f"""Your Credit Card is about to expire on {exp_date}.

Let's take a look at your current card's information and benefits.

**Benefits**
**Bills**
2% cash-back on utility and bill payments.

**Travel**
3x points on flights, hotels, and car rentals.

**Points**
Earn points on every purchase for great rewards.

**Plus**
- No annual fee
- 10,000 Bonus Points: Spend $1000 in first 3 months.
- Complementary Travel Insurance.
"""
        response = ChatRespDto(
            action=ChatRespAction.SHOW_OFFER,
            response=message,
            thread_id=req_data.thread_id,
            metadata=ChatRespMetadataForOffer(
                type=ChatRespMetadataType.OFFER_DATA,
                offer=OfferResp(
                    product=OfferProduct.CARD,
                    message="",
                    data=OfferRespDataForCard(
                        type=OfferType.RENEWAL,
                        card=None,
                    ),
                ),
            ),
        )

        logger.info("Returning card offer...")
        return response

    async def _get_term_deposit_offer(
        self,
        ctx: RequestContext,
        agent: CompiledStateGraph,
        header: ApiHeader,
        req_data: ChatReqMetadataForOffer,
    ) -> ChatRespDto:
        logger = ctx.logger()
        logger.debug("Processing user query...")
        cfg = self._get_config()
        cfg[CONFIGURABLE_CONTEXT_KEY].update(  # type: ignore
            {
                THREAD_ID_KEY: req_data.thread_id,
                CONTEXT_KEY: ctx,
                EBP_ACCESS_TOKEN_KEY: header.token,
                EBP_COOKIE_KEY: header.cookie,
                EBP_EDGE_DOMAIN_KEY: settings.ebp_edge_domain,
                USER_QUERY_KEY: "Renew my term deposit.",
            }
        )
        logger.debug("Update state with the offer info")
        config_data: AssistantConfig = cfg.get(CONFIGURABLE_CONTEXT_KEY, {})
        api_config = extract_bb_retail_api_config(config_data)

        accounts = await list_term_deposit_accounts(ctx, api_config)
        data = OfferReqDataForTermDeposit.model_validate(req_data.offer.data)
        account = list(filter(lambda a: a.id == data.deposit_id, accounts))[0]

        products = await list_td_products(ctx)
        product_dict = update_term_deposit(
            deposit_amount=account.deposit_amount,
            list_term_deposit=products,
        )

        logger.debug("Set the state at getting products...")
        await agent.aupdate_state(
            config=cfg,
            values={
                AssistantStateFields.TERM_DEPOSIT_AGENT_STATE: {
                    TermDepositAgentStateFields.ACTION: "get_offer",
                    TermDepositAgentStateFields.DEPOSIT_AMOUNT: account.deposit_amount,
                    TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: product_dict,
                    TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS: {
                        account.id: account
                    },
                    TermDepositAgentStateFields.RESUME_NODE: present_offer_node,
                }
            },
            as_node=START,
        )
        logger.debug("Invoking agent...")
        await agent.ainvoke(
            input={
                AssistantStateFields.MESSAGES: [
                    HumanMessage(str(config_data[USER_QUERY_KEY])),
                ],
            },
            config=cfg,
            stream_mode="values",
            debug=self.debug,
        )
        config_data: AssistantConfig = cfg.get(CONFIGURABLE_CONTEXT_KEY, {})
        response: ChatRespDto = config_data[PENDING_RESPONSE_KEY].pop()
        response.thread_id = req_data.thread_id
        logger.info("Returning term deposit offer...")
        return response

    async def _reset_state(
        self,
        ctx: RequestContext,
        agent: CompiledStateGraph,
        cfg: RunnableConfig,
        thread_id: str,
    ) -> ChatRespDto:
        logger = ctx.logger()
        logger.info("Resetting agent state...")
        current_state = await agent.aget_state(config=cfg)
        messages = current_state.values.get(AssistantStateFields.MESSAGES, [])
        await agent.aupdate_state(
            config=cfg,
            values={
                AssistantStateFields.MESSAGES: [
                    RemoveMessage(id=m.id) for m in messages
                ],
                AssistantStateFields.STATUS: AssistantStatus.WAIT_FOR_QUERY,
                AssistantStateFields.TERM_DEPOSIT_AGENT_STATE: {},
                AssistantStateFields.CARD_AGENT_STATE: {},
                AssistantStateFields.TRANSFER_AGENT_STATE: {},
                AssistantStateFields.TRANSACTION_REPORT_AGENT_STATE: {},
            },
            as_node=START,
        )
        response = ChatRespDto(
            action=ChatRespAction.SHOW_REPLY,
            thread_id=thread_id,
            response=(
                "There is a technical glitch and I couldn't complete your request. "
                "Let's try again!"
            ),
            metadata=None,
        )
        logger.info("Returning response...")
        return response
