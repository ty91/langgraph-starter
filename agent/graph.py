import logging
from typing import Annotated, Any, Dict, List, Literal, Sequence, TypedDict

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from .prompt import SYSTEM_PROMPT
from .tools import tools

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    iteration: int
    max_iterations: int


class AgentGraph:
    def __init__(self, provider: str, model: str, api_key: str, max_tokens: int = 4096):
        self.llm = init_chat_model(
            model=f"{provider}:{model}",
            api_key=api_key,
            streaming=True,
            max_tokens=max_tokens,
        )
        self.tools = tools
        self.tool_node = ToolNode(tools)
        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(GraphState)
        workflow.add_node("chat", self._chat_node)
        workflow.add_node("tools", self._tools_node)
        workflow.set_entry_point("chat")
        workflow.add_conditional_edges(
            "chat",
            self._should_continue,
            {
                "continue": "tools",
                "end": END,
            },
        )
        workflow.add_edge("tools", "chat")
        return workflow

    async def _chat_node(self, state: GraphState) -> Dict[str, Any]:
        llm_with_tools = self.llm.bind_tools(self.tools)

        prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("placeholder", "{messages}")])

        chain = prompt | llm_with_tools

        response = await chain.ainvoke({"messages": state["messages"]})

        return {
            "messages": [response],
            "iteration": state["iteration"] + 1,
        }

    async def _tools_node(self, state: GraphState) -> Dict[str, Any]:
        tool_messages = await self.tool_node.ainvoke({"messages": state["messages"]})
        return {"messages": tool_messages["messages"]}

    def _should_continue(self, state: GraphState) -> Literal["continue", "end"]:
        messages = state["messages"]
        last_message = messages[-1]

        if state["iteration"] >= state["max_iterations"]:
            return "end"

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"

        return "end"

    async def astream(
        self,
        messages: List[BaseMessage],
        max_iterations: int = 10,
        stream_mode: str = "messages",
    ):
        initial_state = {
            "messages": messages,
            "iteration": 0,
            "max_iterations": max_iterations,
        }

        async for event in self.app.astream(
            initial_state,
            stream_mode=stream_mode,
        ):
            yield event
