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
from app.assistant_v2.primary.constant import TERM_DEPOSIT_CONTROLLER_TOOLS
from app.assistant_v2.primary.state import (
    AssistantConfig,
    AssistantState,
    AssistantStateFields,
)
from app.assistant_v2.primary.tool.to_term_deposit_flow import ToTermDepositFlow
from app.assistant_v2.util.complete_or_escalate import CompleteOrEscalateTool
from app.assistant_v2.util.handle_ai_message import verify_ai_message
from app.core.config import settings
from app.core.context import RequestContext
from app.entity import ChatRespAction, ChatRespDto
from app.prompt.prompt_service import PromptService


class TermDepositController:
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
            to_term_deposit_flow_tool_name=ToTermDepositFlow.__name__,
            return_control_tool_name=CompleteOrEscalateTool.__name__,
        )

        agent = prompt_with_tool | prompt.llm_model.bind_tools(TERM_DEPOSIT_CONTROLLER_TOOLS)  # type: ignore
        return agent

    async def get_agent(  # type: ignore
        self,
        ctx: RequestContext,
    ):
        if not self.ready:
            self.agent = await self.build_agent(
                ctx,
                self.prompt_srv,
                settings.term_deposit_controller_prompt,
                settings.term_deposit_controller_label,
            )
            self.ready = True

        return self.agent  # type: ignore

    @no_type_check
    async def __call__(
        self,
        state: AssistantState,
        config: AssistantConfig,
    ) -> dict[str, Any]:
        config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
        ctx = config_data[CONTEXT_KEY]
        logger = ctx.logger()
        logger.info(f"{type(self).__name__} is running...")

        last_message = state[AssistantStateFields.MESSAGES][-1]
        logger.info(f"Last message: {last_message}")
        need_llm: bool = True

        if config_data.get(PENDING_RESPONSE_KEY):
            logger.info("There is a response to be sent. Skip LLM.")
            return {
                AssistantStateFields.MESSAGES: [],
            }

        if (
            config_data.get(USER_CHOICE_ID_KEY)
            and len(config_data[USER_CHOICE_ID_KEY]) > 0
        ):
            logger.info("User choice is available. Skip LLM.")
            tool = ToolCall(
                name=ToTermDepositFlow.__name__,
                id=ctx.request_id(),
                args={},
            )
            msg = AIMessage(content="Resume with user choice.", tool_calls=[tool])
            return {
                AssistantStateFields.MESSAGES: [msg],
            }

        logger.info(f"Enter {type(self).__name__} decision loop...")
        retry_counter = 0
        result = None
        while need_llm:
            logger.debug(f"Invoking {type(self).__name__}...")
            agent = await self.get_agent(ctx)
            result = await agent.ainvoke(  # type: ignore
                {
                    "messages": state[AssistantStateFields.MESSAGES],
                },
                RunnableConfig(configurable=dict(config)),
            )
            new_message = verify_ai_message(
                ctx, state, result, retry_counter, minimum_tool_calls=1
            )
            retry_counter += 1
            if new_message:
                state = {**state, AssistantStateFields.MESSAGES: new_message}

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
            AssistantStateFields.MESSAGES: [result] if result else [],
        }
