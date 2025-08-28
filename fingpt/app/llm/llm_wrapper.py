from typing import Any, Callable, Dict, List, Literal, Optional, Sequence, Type, Union

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool
from langchain_openai import AzureChatOpenAI

from app.core.config import settings
from app.utils.modified_langfuse_decorator import langfuse_context


class AzureChatOpenAIWrapper(AzureChatOpenAI):
    def _set_langfuse_callback(self):
        try:
            if self.callbacks:
                langfuse_type = type(langfuse_context.get_current_langchain_handler())
                for i, callback in enumerate(self.callbacks):
                    if isinstance(callback, langfuse_type):
                        self.callbacks[i] = (
                            langfuse_context.get_current_langchain_handler()
                        )
                        break
                else:
                    self.callbacks.append(
                        langfuse_context.get_current_langchain_handler()
                    )
            else:
                self.callbacks = [langfuse_context.get_current_langchain_handler()]
        except Exception as e:
            print(f"Error setting langfuse callback: {e}")

    async def ainvoke(
        self,
        input: LanguageModelInput,
        config: Optional[RunnableConfig] = None,
        *,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> BaseMessage:
        if settings.enable_langfuse_tracer:
            self._set_langfuse_callback()
        return await super().ainvoke(input, config, stop=stop, **kwargs)

    def invoke(
        self,
        input: LanguageModelInput,
        config: Optional[RunnableConfig] = None,
        *,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> BaseMessage:
        if settings.enable_langfuse_tracer:
            self._set_langfuse_callback()
        return super().invoke(input, config, stop=stop, **kwargs)

    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], Type, Callable, BaseTool]],
        *,
        tool_choice: Optional[
            Union[dict, str, Literal["auto", "none", "required", "any"], bool]
        ] = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        # check whether strict mode is enabled
        # if "strict" not in kwargs:
        #     return super().bind_tools(
        #         tools, tool_choice=tool_choice, strict=True, **kwargs
        #     )
        return super().bind_tools(tools, tool_choice=tool_choice, **kwargs)
