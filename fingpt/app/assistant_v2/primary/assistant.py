from typing import Any, Optional, no_type_check

from langchain_core.messages import AIMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI
from openai import BadRequestError

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
)
from app.assistant_v2.primary.constant import (
    AGAINST_POLICY_CONTENT,
    PRIMARY_ASSISTANT_TOOLS,
)
from app.core.config import settings
from app.core.context import RequestContext
from app.entity.chat_response import ChatRespAction, ChatRespDto
from app.prompt.prompt_service import PromptService

from ...assistant.base_agent_state import BaseAgentStateFields
from ..util.handle_ai_message import verify_ai_message
from .state import AssistantConfig, AssistantState, AssistantStateFields


class Assistant:
    def __init__(
        self,
        prompt_srv: PromptService,
        llm: AzureChatOpenAI,
    ) -> None:
        self.prompt_srv = prompt_srv
        self.llm = llm
        self.ready = False
        self.agent = None

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
        agent = prompt_tmpl | prompt.llm_model.bind_tools(PRIMARY_ASSISTANT_TOOLS)  # type: ignore
        return agent

    async def get_agent(  # type: ignore
        self,
        ctx: RequestContext,
    ):
        if not self.ready:
            self.agent = await self.build_agent(
                ctx,
                self.prompt_srv,
                settings.assistant_primary_prompt,
                settings.assistant_primary_label,
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
        resp: Optional[ChatRespDto] = None

        if config_data[PENDING_RESPONSE_KEY]:
            logger.info("There is a response to be sent. Skip LLM.")
            need_llm = False

        logger.info(f"Enter {type(self).__name__} decision loop...")
        retry_counter = 0
        result = None
        while need_llm:
            logger.debug(f"Invoking {type(self).__name__}...")
            agent = await self.get_agent(ctx)
            try:
                result = await agent.ainvoke(  # type: ignore
                    {
                        "messages": state[AssistantStateFields.MESSAGES],
                    },
                    RunnableConfig(configurable=dict(config)),
                )
            except BadRequestError as e:
                if e.code == "content_filter":
                    result = AIMessage(
                        content=AGAINST_POLICY_CONTENT,
                    )
                    logger.info(f"Content filter error: {e}")
                else:
                    logger.error(f"Error running assistant{type(e)}: {e}")
                    raise e

            except Exception as e:
                logger.error(f"Error running assistant{type(e)}: {e}")
                raise e

            new_message = verify_ai_message(
                ctx, state, result, retry_counter, maximum_tool_calls=1
            )
            retry_counter += 1

            if new_message:
                state = {**state, BaseAgentStateFields.MESSAGES: new_message}

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
