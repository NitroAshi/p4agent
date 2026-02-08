from typing import Any

from langgraph.graph import END, StateGraph

from agent_core.state import AgentState
from agent_core.tasks import TaskRegistry
from agent_core.tools import append_text


class AgentGraph:
    def __init__(self, task_registry: TaskRegistry):
        self._task_registry = task_registry
        self._compiled = self._build()

    def invoke(self, task_id: str, payload: dict[str, Any]) -> AgentState:
        start_state: AgentState = {
            "task_id": task_id,
            "input_payload": payload,
            "plan": "",
            "tool_result": None,
            "response": None,
            "error": None,
        }
        return self._compiled.invoke(start_state)

    def _build(self):
        graph: StateGraph = StateGraph(AgentState)
        graph.add_node("planning", self._planning_node)
        graph.add_node("tool_call", self._tool_node)
        graph.add_node("validation", self._validation_node)

        graph.set_entry_point("planning")
        graph.add_edge("planning", "tool_call")
        graph.add_edge("tool_call", "validation")
        graph.add_edge("validation", END)

        return graph.compile()

    def _planning_node(self, state: AgentState) -> AgentState:
        task = self._task_registry.get(state["task_id"])
        state["plan"] = task.goal
        return state

    def _tool_node(self, state: AgentState) -> AgentState:
        task = self._task_registry.get(state["task_id"])
        payload = state["input_payload"]

        if task.id == "append_hello_agnet_comment":
            target_file = str(payload["target_file"])
            state["tool_result"] = append_text(target_file=target_file, text="# hello agnet")
            return state

        state["error"] = f"No tool execution mapping for task '{task.id}'"
        return state

    def _validation_node(self, state: AgentState) -> AgentState:
        if state["error"] is not None:
            state["response"] = {
                "status": "failed",
                "error": state["error"],
            }
            return state

        if state["tool_result"] is None:
            state["response"] = {
                "status": "failed",
                "error": "Tool execution produced no result",
            }
            return state

        state["response"] = {
            "status": "ok",
            "task_id": state["task_id"],
            **state["tool_result"],
        }
        return state
