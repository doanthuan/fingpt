from unittest.mock import MagicMock, Mock

import pytest

from app.core.context import RequestContext
from app.utils.semantic_cache import SemanticCache


@pytest.fixture
def mock_vector_store():
    return Mock()


@pytest.fixture
def mock_emb_srv():
    return Mock()


@pytest.fixture
def semantic_cache(mock_vector_store, mock_emb_srv):
    return SemanticCache(mock_vector_store, mock_emb_srv)


def test_init(semantic_cache):
    assert semantic_cache._vector_store is not None
    assert semantic_cache._emb_srv is not None
    assert semantic_cache._score_threshold == 0.5
    assert isinstance(semantic_cache._ctx, RequestContext)
    assert semantic_cache._logger is not None


def test_update_sigma(semantic_cache):
    semantic_cache._update_sigma(0.3)
    assert semantic_cache.min_score == 0.3
    assert semantic_cache.max_score == 0.3

    semantic_cache._update_sigma(0.7)
    assert semantic_cache.min_score == 0.3
    assert semantic_cache.max_score == 0.7
    assert semantic_cache.sigma == pytest.approx(0.2)


def test_distance_to_confidence(semantic_cache):
    confidence = semantic_cache._distance_to_confidence(0.5)
    assert 0 <= confidence <= 1


@pytest.mark.asyncio
async def test_clear(semantic_cache):
    await semantic_cache.aclear()
    semantic_cache._vector_store.delete_collection.assert_called_once()


def test_conversation(semantic_cache):
    prompt = (
        '[{"lc": 1, "type": "constructor", "id": ["langchain", "schema", "messages", "SystemMessage"], '
        '"kwargs": {"content": "test prompt", "type": "system"}},'
        '{"lc": 1, "type": "constructor", "id": ["langchain", "schema", "messages", "HumanMessage"], '
        '"kwargs": {"content": "test question", "type": "human"}},'
        '{"lc": 1, "type": "constructor", "id": ["langchain", "schema", "messages", "SystemMessage"], '
        '"kwargs": {"content": "test answer", "type": "system"}}]'
    )

    result = semantic_cache._conversation(prompt)
    assert result == "\n- HUMAN: test question\n- SYSTEM: test answer"


@pytest.fixture
def setup_semantic_cache():
    vector_store_mock = MagicMock()
    emb_srv_mock = MagicMock()
    instance = SemanticCache(vector_store_srv=vector_store_mock, emb_srv=emb_srv_mock)
    instance._vector_store._collection_metadata = {"hnsw:space": "l2"}
    instance._conversation = MagicMock(return_value="mocked_conversation")
    return instance, vector_store_mock


@pytest.mark.asyncio
async def test_alookup(setup_semantic_cache):
    instance, mock_vector_store = setup_semantic_cache

    # Mock the similarity search results
    mock_document = MagicMock()
    mock_document.metadata = {
        "conversation": "mocked_conversation",
        "return_val": (
            '[{"message": {"content": "value", '
            '"response_metadata": {"token_usage": {"total_tokens": 10}}, '
            '"usage_metadata": {"total_tokens": 10}}}]'
        ),
    }
    mock_vector_store.similarity_search_with_score.return_value = [(mock_document, 0.3)]

    # Mock the _distance_to_confidence method to return a value above the threshold
    instance._distance_to_confidence = MagicMock(return_value=0.6)

    # Call the async method
    result = await instance.alookup("test prompt", "llm_string")
    # Assertions
    assert result is not None
    assert len(result) == 1
    assert result[0]["message"]["content"] == "value"
    assert result[0]["message"]["response_metadata"]["token_usage"]["total_tokens"] == 0
    assert result[0]["message"]["usage_metadata"]["total_tokens"] == 0


class MockGeneration:
    def __init__(self, message_content, tool_calls=None):
        self.message = MagicMock()
        self.message.content = message_content
        self.message.tool_calls = tool_calls if tool_calls is not None else []


@pytest.mark.asyncio
async def test_update_with_tool_calls(setup_semantic_cache):
    instance, mock_vector_store = setup_semantic_cache
    return_val = [
        MockGeneration(message_content="test message", tool_calls=["tool name"])
    ]

    instance.update("test prompt", "llm_string", return_val)

    # Assertions
    mock_vector_store.add_texts.assert_called_once()


@pytest.mark.asyncio
async def test_update_without_tool_calls(setup_semantic_cache):
    instance, mock_vector_store = setup_semantic_cache
    return_val = [MockGeneration(message_content="test message", tool_calls=[])]

    instance.update("test prompt", "llm_string", return_val)

    # Assertions
    mock_vector_store.add_texts.assert_called_once()


def test_check_if_list(semantic_cache):
    assert semantic_cache._check_if_list('["item1", "item2"]')
    assert semantic_cache._check_if_list('{"key": ["item1", "item2"]}')
    assert not semantic_cache._check_if_list("not a list")
