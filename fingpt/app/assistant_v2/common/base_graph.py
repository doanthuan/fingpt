import abc
from typing import Any, Awaitable, Callable, Generic, Type, TypeVar, Union

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.graph import Graph
from langgraph.graph import END, START, StateGraph

from ...assistant.constant import CONFIGURABLE_CONTEXT_KEY, CONTEXT_KEY
from ...core import RequestContext
from ..constant import USER_CHOICE_ID_KEY
from .base_agent_config import BaseAgentConfig
from .base_agent_state import BaseAgentState, BaseAgentStateFields


class NodeName(str):
    pass


class EdgeName(str):
    pass


S = TypeVar("S", bound=BaseAgentState)
START_NODE = NodeName(START)
END_NODE = NodeName(END)


class BaseGraph(Generic[S]):
    def __init__(self, state: Type[S], config_class: Type[BaseAgentConfig]):
        self.workflow = StateGraph(
            state_schema=state,
            config_schema=config_class,
        )
        self.initialized = False
        self.start_node = NodeName("internal_start")
        self.workflow.add_node(self.start_node, self.start_node_fnc)
        self.workflow.add_edge(START, self.start_node)

    @staticmethod
    def clear_state_except_messages(state: S) -> dict[str, Any]:
        for k, v in state.items():
            if k == BaseAgentStateFields.MESSAGES:
                continue
            elif isinstance(v, list):
                state[k] = []
            elif isinstance(v, dict):
                state[k] = {}
            else:
                state[k] = None
        return dict(state)

    @staticmethod
    async def start_node_fnc(state: S, config: RunnableConfig) -> dict[str, Any]:
        """
        Check the state and config before running into the user-defined graph.
        Args:
            state:
            config:

        Returns: the verified state and config
        """
        config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
        ctx: RequestContext = config_data.get(CONTEXT_KEY)
        logger = ctx.logger()
        resume_node = state.get(BaseAgentStateFields.RESUME_NODE)
        user_choice_id = config.get(CONFIGURABLE_CONTEXT_KEY, {}).get(
            USER_CHOICE_ID_KEY
        )
        if resume_node and not user_choice_id:
            logger.warn(
                f"Request to resume at node {resume_node} but no user choice id, "
                f"clear RESUME_NODE. If you to clear the other state, write a custom start node."
            )
            return {BaseAgentStateFields.RESUME_NODE: None}
        if not resume_node and user_choice_id:
            logger.warn(
                f"Request to resume with user choice id {user_choice_id} but no resume node, clear user choice id"
            )
            config_data[USER_CHOICE_ID_KEY] = None
        return {BaseAgentStateFields.MESSAGES: []}  # nothing to update

    @abc.abstractmethod
    async def initialize(self) -> None:
        raise NotImplementedError

    def add_start_router(
        self,
        router: Union[
            Callable[[S], EdgeName],
            Callable[[S], Awaitable[EdgeName]],
            Callable[[S, RunnableConfig], EdgeName],
            Callable[[S, RunnableConfig], Awaitable[EdgeName]],
        ],
        path_map: dict[EdgeName, NodeName],
    ) -> None:
        self.workflow.add_conditional_edges(
            self.start_node, router, {k: v for k, v in path_map.items()}
        )

    def add_node(
        self,
        name: NodeName,
        func: Union[
            Callable[[S, RunnableConfig], dict[str, Any]],
            Callable[[S, RunnableConfig], Awaitable[dict[str, Any]]],
        ],
    ) -> None:
        self.workflow.add_node(name, func)  # type: ignore

    def add_edge(
        self,
        start: NodeName,
        end: NodeName,
    ) -> None:
        self.workflow.add_edge(start, end)

    def add_conditional_edges(
        self,
        start: NodeName,
        router: Union[
            Callable[[S], EdgeName],
            Callable[[S], Awaitable[EdgeName]],
            Callable[[S, RunnableConfig], EdgeName],
            Callable[[S, RunnableConfig], Awaitable[EdgeName]],
        ],
        path_map: dict[EdgeName, NodeName],
    ) -> None:
        self.workflow.add_conditional_edges(
            start, router, {k: v for k, v in path_map.items()}
        )

    def route_to_end(
        self,
        node: NodeName,
    ) -> None:
        self.workflow.add_edge(node, END)

    async def get_workflow(self) -> StateGraph:
        if not self.initialized:
            await self.initialize()
            self.initialized = True
        return self.workflow

    async def get_graph(self) -> Graph:
        workflow = await self.get_workflow()
        return workflow.compile().get_graph(xray=1)
