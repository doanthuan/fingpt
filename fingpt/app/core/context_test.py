import pytest
from starlette.datastructures import URL

from app.core.context import RequestContext
from app.core.logging import Logger


@pytest.fixture
def ctx():
    req_id = "12345 67890"
    context = RequestContext(req_id)
    return context


@pytest.fixture
def url():
    url = URL("https://example.com/path?query=1")
    return url


def test_request_context_initialization(ctx):
    assert ctx.request_id() == "12345-67890"
    assert isinstance(ctx.logger(), Logger)
