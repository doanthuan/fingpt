import asyncio
from contextvars import ContextVar
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    ParamSpec,
    Tuple,
    cast,
)

from black.nodes import TypeVar
from langchain_openai import AzureChatOpenAI
from langfuse.decorators import LangfuseDecorator
from langfuse.decorators.langfuse_decorator import F, R

from app.core import RequestContext
from app.core.config import settings
from app.prompt import prompt_service_name

P = ParamSpec("P")
T = TypeVar("T")
FN = Callable[[T], Dict[str, str]]
_session_id_context_var: ContextVar[Optional[str]] = ContextVar(
    "session_id", default=None
)


class ModifiedLangfuseDecorator(LangfuseDecorator):
    """
    Modify Langfuse decorator to support fields selecting
    """

    @staticmethod
    def _handle_context_request(input_data: RequestContext) -> Dict[str, str]:
        current_session_id = _session_id_context_var.get()
        if not current_session_id:
            _session_id_context_var.set(input_data.request_id())
        return {}

    @staticmethod
    def _handle_prompt_service(_) -> Dict[str, str]:
        return {}

    @staticmethod
    def _handle_azure_chat_openai(model: AzureChatOpenAI) -> Dict[str, str]:
        return {"model": model.model_name, "model_temperature": model.temperature}

    IGNORE_TYPES: Dict[str, FN] = {
        RequestContext.__name__: _handle_context_request,
        prompt_service_name: _handle_prompt_service,
        AzureChatOpenAI.__name__: _handle_azure_chat_openai,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def observe(
        self,
        *,
        name: Optional[str] = None,
        as_type: Optional[Literal["generation"]] = None,
        capture_input: bool = True,
        capture_output: bool = True,
        transform_to_string: Optional[Callable[[Iterable], str]] = None,
        excluded_args: Optional[Iterable[int]] = None,
        excluded_kwargs: Optional[Iterable[str]] = None,
        included_args: Optional[Iterable[Any]] = None,
        included_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            return (
                self._async_observe(
                    func,
                    name=name,
                    as_type=as_type,
                    capture_input=capture_input,
                    capture_output=capture_output,
                    transform_to_string=transform_to_string,
                    excluded_args=excluded_args,
                    excluded_kwargs=excluded_kwargs,
                    included_kwargs=included_kwargs,
                    included_args=included_args,
                )
                if asyncio.iscoroutinefunction(func)
                else self._sync_observe(
                    func,
                    name=name,
                    as_type=as_type,
                    capture_input=capture_input,
                    capture_output=capture_output,
                    transform_to_string=transform_to_string,
                    excluded_args=excluded_args,
                    excluded_kwargs=excluded_kwargs,
                    included_kwargs=included_kwargs,
                    included_args=included_args,
                )
            )

        return decorator

    def _remove_ignored_args(self, args) -> Tuple[List, Dict]:
        remain_args = []
        remain_kwargs = {}
        for arg in args:
            if type(arg).__name__ in self.IGNORE_TYPES:
                remain_kwargs.update(self.IGNORE_TYPES[type(arg).__name__](arg))
            else:
                if isinstance(arg, dict):
                    remain_args.append(self._remove_ignored_types_recursive((), arg)[1])
                elif isinstance(arg, list):
                    remain_args += self._remove_ignored_types_recursive(arg, {})[0]
                    remain_kwargs.update(
                        self._remove_ignored_types_recursive(arg, {})[1]
                    )
                else:
                    remain_args.append(arg)
        return remain_args, remain_kwargs

    def _remove_ignored_kwargs(self, kwargs) -> Dict:
        remain_kwargs = {}
        for key, value in kwargs.items():
            if type(value).__name__ in self.IGNORE_TYPES:
                remain_kwargs.update(self.IGNORE_TYPES[type(value).__name__](value))
            else:
                if isinstance(value, dict):
                    remain_kwargs[key] = self._remove_ignored_types_recursive(
                        (), value
                    )[1]
                elif (
                    isinstance(value, list)
                    or isinstance(value, tuple)
                    or isinstance(value, set)
                ):
                    remain_kwargs[key] = self._remove_ignored_types_recursive(value, {})
                else:
                    remain_kwargs[key] = value
        return remain_kwargs

    def _remove_ignored_types_recursive(self, args, kwargs) -> Tuple[Tuple, Dict]:
        remain_args = []
        remain_kwargs = {}
        a, k = self._remove_ignored_args(args)
        remain_args += a
        remain_kwargs.update(k)
        k = self._remove_ignored_kwargs(kwargs)
        remain_kwargs.update(k)

        return tuple(remain_args), remain_kwargs

    @staticmethod
    def _extract_args(args, included_args):
        result = []
        for value in included_args:
            try:
                if isinstance(value, str) and "." in value:
                    parts = value.split(".")
                    assert len(parts) == 2, "Only one level of nesting is supported"
                    if not str.isdigit(parts[0]) or int(parts[0]) >= len(args):
                        result.append(value)
                    elif str.isdigit(parts[0]) and isinstance(
                        args[int(parts[0])], dict
                    ):
                        result.append(args[int(parts[0])].get(parts[1]))
                    else:
                        result.append(getattr(args[int(parts[0])], parts[1]))
                else:
                    result.append(value)
            except AttributeError as _:  # noqa
                continue
        return result

    @staticmethod
    def _filter_args(args, excluded_args, included_args):
        result = args
        if excluded_args is not None:
            result = [arg for i, arg in enumerate(args) if i not in excluded_args]
        if included_args is not None:
            result += ModifiedLangfuseDecorator._extract_args(args, included_args)
        return tuple(result)

    @staticmethod
    def _extract_kwargs(kwargs, included_kwargs):
        result = {}
        for key, value in included_kwargs.items():
            try:
                if isinstance(value, str) and "." in value:
                    parts = value.split(".")
                    assert len(parts) == 2, "Only one level of nesting is supported"

                    if parts[0] not in kwargs:
                        result[key] = value
                        continue
                    if isinstance(kwargs[parts[0]], dict):
                        result[key] = kwargs[parts[0]].get(parts[1])
                    else:
                        result[key] = getattr(kwargs[parts[0]], parts[1])
                else:
                    result[key] = value
            except AttributeError as _:  # noqa
                continue
        return result

    def _filter_kwargs(self, kwargs, excluded_kwargs, included_kwargs):
        result = kwargs.copy()
        if excluded_kwargs is not None:
            for key in excluded_kwargs:
                result.pop(key, None)
        if included_kwargs is not None:
            result.update(self._extract_kwargs(kwargs, included_kwargs))

        return result

    def _modify_arguments(
        self,
        included_args,
        included_kwargs,
        excluded_args,
        excluded_kwargs,
        *args,
        **kwargs,
    ):

        modified_args = self._filter_args(args, excluded_args, included_args)
        modified_kwargs = self._filter_kwargs(kwargs, excluded_kwargs, included_kwargs)
        modified_args, modified_kwargs = self._remove_ignored_types_recursive(
            modified_args, modified_kwargs
        )
        return modified_args, modified_kwargs

    def _async_observe(
        self,
        func: F,
        *,
        name: Optional[str],
        as_type: Optional[Literal["generation"]],
        capture_input: bool,
        capture_output: bool,
        transform_to_string: Optional[Callable[[Iterable], str]] = None,
        excluded_args: Optional[Iterable[int]] = None,
        excluded_kwargs: Optional[Iterable[str]] = None,
        included_args: Optional[Iterable[Any]] = None,
        included_kwargs: Optional[Dict[str, Any]] = None,
    ) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not settings.enable_langfuse_tracer:
                return await func(*args, **kwargs)

            modified_args, modified_kwargs = self._modify_arguments(
                included_args,
                included_kwargs,
                excluded_args,
                excluded_kwargs,
                *args,
                **kwargs,
            )
            observation = self._prepare_call(
                name=name or func.__name__,
                as_type=as_type,
                capture_input=capture_input,
                is_method=self._is_method(func),
                func_args=modified_args,
                func_kwargs=modified_kwargs,
            )
            result = None

            try:
                self.update_current_trace(
                    session_id=_session_id_context_var.get(), tags=[settings.runtime]
                )
                result = await func(*args, **kwargs)
            except Exception as e:
                self._handle_exception(observation, e)
            finally:
                result = self._finalize_call(
                    observation, result, capture_output, transform_to_string
                )

            if result is not None:
                return result

        return cast(F, async_wrapper)

    def _sync_observe(
        self,
        func: F,
        *,
        name: Optional[str],
        as_type: Optional[Literal["generation"]],
        capture_input: bool,
        capture_output: bool,
        transform_to_string: Optional[Callable[[Iterable], str]] = None,
        excluded_args: Optional[Iterable[int]] = None,
        excluded_kwargs: Optional[Iterable[str]] = None,
        included_args: Optional[Iterable[Any]] = None,
        included_kwargs: Optional[Dict[str, Any]] = None,
    ) -> F:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not settings.enable_langfuse_tracer:
                return func(*args, **kwargs)
            modified_args, modified_kwargs = self._modify_arguments(
                included_args,
                included_kwargs,
                excluded_args,
                excluded_kwargs,
                *args,
                **kwargs,
            )
            observation = self._prepare_call(
                name=name or func.__name__,
                as_type=as_type,
                capture_input=capture_input,
                is_method=self._is_method(func),
                func_args=modified_args,
                func_kwargs=modified_kwargs,
            )
            result = None
            try:
                self.update_current_trace(
                    session_id=_session_id_context_var.get(), tags=[settings.runtime]
                )
                result = func(*args, **kwargs)
            except Exception as e:
                self._handle_exception(observation, e)
            finally:
                result = self._finalize_call(
                    observation, result, capture_output, transform_to_string
                )

            if result is not None:
                return result

        return cast(F, sync_wrapper)


langfuse_context = ModifiedLangfuseDecorator()
observe = langfuse_context.observe
