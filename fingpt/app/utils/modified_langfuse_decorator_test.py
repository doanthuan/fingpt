from typing import Any, Dict

import pytest
from langfuse.decorators import LangfuseDecorator

from app.core import RequestContext
from app.core.config import settings
from app.utils.modified_langfuse_decorator import ModifiedLangfuseDecorator


class TestClass:
    def __init__(self, t, k):
        self.t = t
        self.k = k


@pytest.fixture()
def prepare_call(mocker):
    mocker.patch.object(settings, "enable_langfuse_tracer", "true")
    mocker.patch.object(LangfuseDecorator, "_finalize_call", lambda x, y, z, t, w: z)
    return mocker.patch.object(LangfuseDecorator, "_prepare_call", return_value=None)


def test_langfuse_decorator_normal(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe()
    def func_test(x, y, *, s):
        print(s)
        return x + y

    assert func_test(1, 2, s="bye, test") == 3
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=(1, 2),
        func_kwargs={"s": "bye, test"},
    )


@pytest.mark.asyncio
async def test_langfuse_decorator_async(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe()
    async def func_test(x, y, *, s):
        print(s)
        return x + y

    assert await func_test(1, 2, s="hello, test") == 3
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=(1, 2),
        func_kwargs={"s": "hello, test"},
    )


@pytest.mark.asyncio
async def test_langfuse_decorator_async_kwargs_ex(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe(excluded_kwargs=["s"], included_kwargs={"t": "s.t"})
    async def func_test(x, y, *, s):
        print(s)
        return x + y + s["k"]

    assert await func_test(1, 2, s={"t": 1, "k": 2}) == 5
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=(1, 2),
        func_kwargs={"t": 1},
    )


@pytest.mark.asyncio
async def test_langfuse_decorator_async_kwargs_ex_class(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe(excluded_kwargs=["s"], included_kwargs={"t": "s.t"})
    async def func_test(x, y, *, s):
        print(s)
        return x + y + s.k

    assert await func_test(1, 2, s=TestClass(1, 2)) == 5
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=(1, 2),
        func_kwargs={"t": 1},
    )


def test_langfuse_decorator_kwargs_ex(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe(excluded_kwargs=["s"], included_kwargs={"t": "s.t"})
    def func_test(x, y, *, s):
        print(s)
        return x + y + s["k"]

    assert func_test(1, 2, s={"t": 1, "k": 2}) == 5
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=(1, 2),
        func_kwargs={"t": 1},
    )


def test_langfuse_decorator_kwargs_ex_class(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe(excluded_kwargs=["s"], included_kwargs={"t": "s.t"})
    def func_test(x, y, *, s):
        print(s)
        return x + y + s.k

    assert func_test(1, 2, s=TestClass(1, 2)) == 5
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=(1, 2),
        func_kwargs={"t": 1},
    )


def test_langfuse_decorator_args_ex(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe(excluded_args=[0], included_args=["1.t"])
    def func_test(x, y, *, s):
        return x + y["t"] + s["k"]

    assert func_test(1, {"t": 2}, s={"t": 1, "k": 2}) == 5
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=({"t": 2}, 2),
        func_kwargs={"s": {"t": 1, "k": 2}},
    )


def test_langfuse_decorator_args_ex_class(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe(excluded_args=[1], included_args=["1.t"])
    def func_test(x, y, *, s):
        return x + y.t + s["k"]

    assert func_test(1, TestClass(2, 3), s={"t": 1, "k": 2}) == 5
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=(1, 2),
        func_kwargs={"s": {"t": 1, "k": 2}},
    )


@pytest.mark.asyncio
async def test_langfuse_decorator_async_args_ex(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe(excluded_args=[1], included_args=["1.v"])
    async def func_test(x, y, *, s):
        return x + y["v"] + s["k"]

    assert await func_test(1, {"v": 2}, s={"t": 1, "k": 2}) == 5
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=(1, 2),
        func_kwargs={"s": {"t": 1, "k": 2}},
    )


@pytest.mark.asyncio
async def test_langfuse_decorator_async_args_ex_class(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe(excluded_args=[1], included_args=["1.t"])
    async def func_test(x, y, *, s):
        return x + y.t + s["k"]

    assert await func_test(1, TestClass(2, 3), s={"t": 1, "k": 2}) == 5
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=(1, 2),
        func_kwargs={"s": {"t": 1, "k": 2}},
    )


@pytest.mark.asyncio
async def test_langfuse_decorator_async_request_context(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe()
    async def func_test(x: RequestContext, y: str):
        return x.request_id() + y

    assert await func_test(RequestContext("test_id"), "_x") == "test_id_x"
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=("_x",),
        func_kwargs={},
    )


def test_langfuse_decorator_request_context_recursive(prepare_call):
    decorator = ModifiedLangfuseDecorator()
    observe = decorator.observe

    @observe()
    def func_test(x: Dict[str, Any], y: str):
        return x["ctx"].request_id() + y

    assert func_test({"ctx": RequestContext("test_id")}, "_x") == "test_id_x"
    prepare_call.assert_called_once_with(
        name="func_test",
        as_type=None,
        capture_input=True,
        is_method=False,
        func_args=(
            {},
            "_x",
        ),
        func_kwargs={},
    )
