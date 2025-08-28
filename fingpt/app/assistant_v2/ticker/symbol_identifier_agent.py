from typing import Any, Optional, no_type_check

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
)
from app.assistant_v2.util.complete_or_escalate import CompleteOrEscalateTool
from app.core.config import settings
from app.core.context import RequestContext
from app.entity.api import SupportedTicker
from app.entity.chat_response import (
    ChatRespAction,
    ChatRespDto,
    ChatRespMetadataForShowTickerReport,
)
from app.prompt.prompt_service import PromptService

from ..util.handle_ai_message import verify_ai_message
from .constant import (
    TICKER_AGENT_TOOLS,
    UNRECOGNIZED_SYMBOL_MESSAGE,
    UNSUPPORTED_SYMBOL_MESSAGE,
)
from .state import TickerAgentConfig, TickerAgentState, TickerAgentStateFields
from .tool.report_generator import report_generator_tool
from .tool.symbol_identifier import symbol_identifier_tool


class SymbolIdentifierAgent:
    def __init__(
        self,
        prompt_srv: PromptService,
        llm: AzureChatOpenAI,
    ):
        self.prompt_srv = prompt_srv
        self.llm = llm
        self.ready = False

    @staticmethod
    async def build_agent(  # type: ignore
        ctx: RequestContext,
        prompt_srv: PromptService,
        prompt_name: str,
        prompt_label: str,
    ):
        prompt = await prompt_srv.get_prompt(
            ctx,
            name=prompt_name,
            label=prompt_label,
            type="chat",
        )
        prompt_tmpl = prompt.tmpl + MessagesPlaceholder(variable_name="messages")
        prompt_with_tool = prompt_tmpl.partial(
            symbol_identifier_tool_name=symbol_identifier_tool.name,
            report_generator_tool_name=report_generator_tool.name,
            return_control_tool_name=CompleteOrEscalateTool.__name__,
        )

        agent = prompt_with_tool | prompt.llm_model.bind_tools(TICKER_AGENT_TOOLS)  # type: ignore
        return agent

    async def get_agent(  # type: ignore
        self,
        ctx: RequestContext,
    ):
        if not self.ready:
            self.agent = await self.build_agent(
                ctx,
                self.prompt_srv,
                settings.ticker_report_symbol_identifier_agent_prompt,
                settings.ticker_report_symbol_identifier_agent_label,
            )
            self.ready = True

        return self.agent  # type: ignore

    @no_type_check
    async def __call__(
        self,
        state: TickerAgentState,
        config: TickerAgentConfig,
    ) -> dict[str, Any]:
        config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
        ctx = config_data[CONTEXT_KEY]
        logger = ctx.logger()
        logger.info(f"{type(self).__name__} is running...")

        last_message = state[TickerAgentStateFields.MESSAGES][-1]
        logger.info(f"Last message: {last_message}")
        need_llm: bool = True
        resp: Optional[ChatRespDto] = None
        symbol: Optional[SupportedTicker] = None

        if isinstance(last_message, ToolMessage):
            if last_message.name == report_generator_tool.name and last_message.content:
                symbol = state[TickerAgentStateFields.SYMBOL]
                resp = ChatRespDto(
                    response=last_message.content,
                    action=ChatRespAction.SHOW_TICKER_REPORT,
                    metadata=ChatRespMetadataForShowTickerReport(
                        ticker=symbol,
                    ),
                )
                logger.info(f"Response prepared: {resp}")
                config_data[PENDING_RESPONSE_KEY].append(resp)
                need_llm = False

            elif last_message.name == symbol_identifier_tool.name:
                if last_message.content in ["", "UNKNOWN"]:
                    logger.debug("No symbol found, ask again for symbol...")
                    resp = ChatRespDto(
                        action=ChatRespAction.SHOW_REPLY,
                        response=UNRECOGNIZED_SYMBOL_MESSAGE,
                        metadata=None,
                    )
                    logger.info(f"Response prepared: {resp}")
                    config_data[PENDING_RESPONSE_KEY].append(resp)
                    need_llm = False

                elif not SupportedTicker.has_value(last_message.content):
                    logger.debug("Invalid symbol found, ask again for symbol...")
                    resp = ChatRespDto(
                        action=ChatRespAction.SHOW_REPLY,
                        response=UNSUPPORTED_SYMBOL_MESSAGE.format(
                            symbol=last_message.content
                        ),
                        metadata=None,
                    )
                    logger.info(f"Response prepared: {resp}")
                    config_data[PENDING_RESPONSE_KEY].append(resp)
                    need_llm = False

                else:
                    symbol = SupportedTicker[last_message.content]
                    logger.info(f"Symbol identified: {symbol}")

        logger.info(f"Enter {type(self).__name__} decision loop...")
        retry_counter = 0
        result = None
        while need_llm:
            logger.debug(f"Invoking {type(self).__name__}...")
            agent = await self.get_agent(ctx)
            result = await agent.ainvoke(  # type: ignore
                {
                    "messages": state[TickerAgentStateFields.MESSAGES],
                },
                RunnableConfig(configurable=dict(config)),
            )

            new_message = verify_ai_message(
                ctx, state, result, retry_counter, maximum_tool_calls=1
            )
            retry_counter += 1
            if new_message:
                state = {**state, TickerAgentStateFields.MESSAGES: new_message}
            else:
                logger.info(f"Valid output received: {result.content}")
                if isinstance(result, AIMessage) and result.content:
                    resp = ChatRespDto(
                        action=ChatRespAction.SHOW_REPLY,
                        response=result.content,
                        metadata=None,
                    )
                    config_data[PENDING_RESPONSE_KEY].append(resp)
                break

        return {
            TickerAgentStateFields.MESSAGES: ([result] if result else []),
            TickerAgentStateFields.SYMBOL: symbol,
        }
