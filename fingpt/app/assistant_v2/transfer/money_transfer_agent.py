from typing import Any, no_type_check

from langchain_core.messages import AIMessage, ToolCall
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
    USER_CHOICE_ID_KEY,
)
from app.assistant_v2.transfer.constant import TRANSFER_AGENT_TOOLS
from app.assistant_v2.transfer.state import (
    TransferAgentConfig,
    TransferAgentState,
    TransferAgentStateFields,
)
from app.assistant_v2.transfer.tool.to_transfer_money_flow import ToMoneyTransferFlow
from app.assistant_v2.util.complete_or_escalate import CompleteOrEscalateTool
from app.assistant_v2.util.handle_ai_message import verify_ai_message
from app.core.config import settings
from app.core.context import RequestContext
from app.entity import ChatRespAction, ChatRespDto
from app.prompt.prompt_service import PromptService


class MoneyTransferAgent:
    def __init__(
        self,
        prompt_srv: PromptService,
        llm: AzureChatOpenAI,
    ):
        self.prompt_srv = prompt_srv
        self.llm = llm
        self.ready = False
        self.agent = None
        # # TODO: inject this dependency

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
        system_prompt = prompt.tmpl + MessagesPlaceholder(variable_name="messages")
        prompt_with_tool = system_prompt.partial(
            to_money_transfer_flow_tool_name=ToMoneyTransferFlow.__name__,
            return_control_tool_name=CompleteOrEscalateTool.__name__,
        )
        agent = prompt_with_tool | prompt.llm_model.bind_tools(TRANSFER_AGENT_TOOLS)  # type: ignore
        return agent

    async def get_agent(  # type: ignore
        self,
        ctx: RequestContext,
    ):
        if not self.ready:
            self.agent = await self.build_agent(
                ctx,
                self.prompt_srv,
                settings.money_transfer_agent_prompt,
                settings.money_transfer_agent_label,
            )
            self.ready = True

        return self.agent  # type: ignore

    @no_type_check
    async def __call__(
        self,
        state: TransferAgentState,
        config: TransferAgentConfig,
    ) -> dict[str, Any]:
        config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
        ctx: RequestContext = config_data[CONTEXT_KEY]
        logger = ctx.logger()
        logger.info(f"{type(self).__name__} is running...")

        last_message = state[TransferAgentStateFields.MESSAGES][-1]
        logger.info(f"Last message: {last_message}")
        need_llm: bool = True

        if config_data.get(PENDING_RESPONSE_KEY):
            logger.info("There is a response to be sent. Skip LLM.")
            return {
                TransferAgentStateFields.MESSAGES: [],
            }

        if (
            config_data.get(USER_CHOICE_ID_KEY)
            and len(config_data[USER_CHOICE_ID_KEY]) > 0
        ):
            logger.info("User choice is available. Skip LLM.")
            tool = ToolCall(
                name=ToMoneyTransferFlow.__name__,
                id=ctx.request_id(),
                args={},
            )
            msg = AIMessage(content="Resume with user choice.", tool_calls=[tool])
            return {
                TransferAgentStateFields.MESSAGES: [msg],
            }

        logger.info(f"Enter {type(self).__name__} decision loop...")
        retry_counter = 0
        result = None
        while need_llm:
            logger.debug(f"Invoking {type(self).__name__}...")
            agent = await self.get_agent(ctx)
            result = await agent.ainvoke(  # type: ignore
                {
                    "messages": state[TransferAgentStateFields.MESSAGES],
                },
                RunnableConfig(configurable=dict(config)),
            )

            new_message = verify_ai_message(
                ctx, state, result, retry_counter, minimum_tool_calls=1
            )
            retry_counter += 1
            if new_message:
                state = {**state, TransferAgentStateFields.MESSAGES: new_message}

            else:
                logger.info("Valid output received.")
                if (
                    isinstance(result, AIMessage)
                    and not result.tool_calls
                    and result.content
                ):
                    resp = ChatRespDto(
                        action=ChatRespAction.SHOW_REPLY,
                        response=result.content,
                        metadata=None,
                    )
                    config_data[PENDING_RESPONSE_KEY].append(resp)
                break

        return {
            TransferAgentStateFields.MESSAGES: [result] if result else [],
        }
