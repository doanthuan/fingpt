import ast
import hashlib
import json
import math
from typing import Any, List, Optional

from langchain_chroma.vectorstores import Chroma
from langchain_core.caches import RETURN_VAL_TYPE, BaseCache
from langchain_core.load.dump import dumps
from langchain_core.load.load import loads
from langchain_core.messages import ToolMessage
from langchain_core.outputs import Generation
from langchain_core.runnables.config import run_in_executor
from langchain_openai.embeddings import AzureOpenAIEmbeddings

from app.core.context import RequestContext


def _hash(_input: str) -> str:
    """Use a deterministic hashing approach."""
    return hashlib.md5(_input.encode()).hexdigest()


class SemanticCache(BaseCache):
    def __init__(
        self,
        vector_store_srv: Chroma,
        emb_srv: AzureOpenAIEmbeddings,
        cache_type: List[str] = ["message", "tool_call", "tool_message"],
        score_threshold: float = 0.5,
    ) -> None:
        self._vector_store = vector_store_srv
        self._emb_srv = emb_srv
        self._score_threshold = score_threshold
        self._ctx = RequestContext("SemanticCache")
        self._logger = self._ctx.logger()
        self.min_score = float("inf")
        self.max_score = 0
        self.sigma = 1.0
        self.epsilon = 1e-10
        self.cache_type = cache_type

    def _update_sigma(self, score: float):
        self.min_score = min(self.min_score, score)
        self.max_score = max(self.max_score, score)
        range_distance = self.max_score - self.min_score
        if range_distance > self.epsilon:
            self.sigma = range_distance / 2

    def _distance_to_confidence(self, score: float) -> float:
        self._update_sigma(score)
        return math.exp(-score / (2 * self.sigma**2 + self.epsilon))

    def lookup(
        self,
        prompt: str,
        llm_string: str,
    ) -> Optional[RETURN_VAL_TYPE]:

        results = self._vector_store.similarity_search_with_score(
            query=self._conversation(prompt),
            k=1,
        )
        generations: list[Generation] = []
        generation = None
        for document, score in results:
            if list(self._vector_store._collection_metadata.values())[0] == "l2":
                confidence_score = self._distance_to_confidence(score)
            else:
                confidence_score = 1 - score
            if confidence_score >= self._score_threshold:
                self._logger.debug(
                    f"Cached return val: {document.metadata['return_val']}"
                )
                self._logger.debug(f"Confidence score: {confidence_score}")

                generation = loads(document.metadata["return_val"])
                generation[0]["message"]["response_metadata"]["token_usage"][
                    "total_tokens"
                ] = 0
                generation[0]["message"]["usage_metadata"]["total_tokens"] = 0
            if generation:
                generations.extend(generation)

        return generations if generations else None

    async def alookup(self, prompt: str, llm_string: str):
        return await run_in_executor(None, self.lookup, prompt, llm_string)

    def clear(self, **kwargs: Any) -> None:
        return self._vector_store.delete_collection()

    async def aclear(self, **kwargs: Any) -> None:
        return await run_in_executor(None, self.clear, **kwargs)

    def update(
        self,
        prompt: str,
        llm_string: str,
        return_val: RETURN_VAL_TYPE,
    ) -> None:
        for gen in return_val:
            if len(gen.message.tool_calls) > 0 and "tool_call" not in self.cache_type:
                self._logger.info("Not caching tool calls")
            elif (
                isinstance(gen.message, ToolMessage)
                and "tool_message" not in self.cache_type
            ):
                self._logger.info("Not caching tool messages")
            else:
                conversation = self._conversation(prompt)
                if len(conversation) != 0:
                    metadata = {
                        "llm_string": llm_string,
                        "conversation": conversation,
                        "return_val": dumps([g for g in return_val]),
                    }
                    self._logger.info("Adding text ....")
                    self._vector_store.add_texts(  # type: ignore
                        texts=[conversation],
                        metadatas=[metadata],
                        ids=[_hash(conversation)],
                    )
                else:
                    self._logger.info("Not cache empty conversation")
                    pass

    async def aupdate(
        self,
        prompt: str,
        llm_string: str,
        return_val: RETURN_VAL_TYPE,
    ) -> None:
        await run_in_executor(None, self.update, prompt, llm_string, return_val)

    def _conversation(self, prompt: str) -> str:
        conversation = ""
        load_prompt = loads(prompt)
        if len(load_prompt) > 10:
            input = load_prompt[-10:]
        else:
            input = load_prompt
        for index, msg in enumerate(input):
            if len(msg.content) > 0 and index != 0:
                is_list = self._check_if_list(msg.content)
                if is_list:
                    conversation += f"\n- {msg.type.upper()}: A list of choices"
                else:
                    conversation += f"\n- {msg.type.upper()}: {msg.content}"
        return conversation

    def _check_if_list(self, content):
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return True
            if isinstance(parsed, dict):
                return any(isinstance(v, list) for v in parsed.values())
            return False
        except json.JSONDecodeError:
            try:
                return (
                    content.strip().startswith("[")
                    and content.strip().endswith("]")
                    and isinstance(ast.literal_eval(content), list)
                )
            except (ValueError, SyntaxError):
                return False
