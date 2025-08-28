from typing import List, Literal

from langchain_core.prompts import ChatPromptTemplate
from langfuse.model import ChatMessageDict
from langfuse.utils.langfuse_singleton import LangfuseSingleton

from app.core.context import RequestContext
from app.entity import ChatPrompt
from app.utils.modified_langfuse_decorator import langfuse_context, observe


class PromptService:
    def __init__(
        self,
    ):
        self._lf = LangfuseSingleton().get()

    @staticmethod
    def _convert_raw_to_langchain_template(raw_prompt: str):
        text = raw_prompt.replace("{{", "$open_curly$").replace("}}", "$close_curly$")
        text = text.replace("{", "{{").replace("}", "}}")
        text = text.replace("$open_curly$", "{").replace("$close_curly$", "}")
        return text

    @observe(as_type="generation")
    async def get_prompt(
        self,
        ctx: RequestContext,
        name: str,
        label: str,
        type: Literal["chat"],
    ) -> ChatPrompt:
        logger = ctx.logger()
        tmpl = self._lf.get_prompt(name=name, type=type, label=label)
        langfuse_context.update_current_observation(prompt=tmpl)
        logger.info(f"Returning prompt {name}...")
        raw_prompt: List[ChatMessageDict] = tmpl.compile()
        langchain_tmpl = ChatPromptTemplate.from_messages(
            [
                (
                    message["role"],
                    self._convert_raw_to_langchain_template(message["content"]),
                )
                for message in raw_prompt
            ]
        )

        return ChatPrompt(
            name=name,
            chat_messages=tmpl.compile(),
            tmpl=langchain_tmpl,
            config=tmpl.config,
        )
