from typing import Any, cast

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from core.settings import settings
from core.state import AgentState
from infra.fs import append_text
from infra.llm.chains import CommentNormChain
from infra.llm.factory import build_llm_adapter
from tasks.registry import TaskRegistry


class AgentOrchestrator:
    def __init__(self, task_registry: TaskRegistry):
        self._task_registry = task_registry
        self._comment_chain: CommentNormChain | None = None
        self._llm_bootstrap_error: str | None = None
        if settings.llm_enabled:
            try:
                adapter = build_llm_adapter(settings)
                self._comment_chain = CommentNormChain(adapter)
            except ValueError as exc:
                self._llm_bootstrap_error = str(exc)
        self._compiled = self._build()

    def invoke(self, task_id: str, payload: dict[str, Any]) -> AgentState:
        start_state: AgentState = {
            "task_id": task_id,
            "input_payload": payload,
            "plan": "",
            "llm_error": None,
            "tool_result": None,
            "response": None,
            "error": None,
        }
        result = self._compiled.invoke(start_state)
        return cast(AgentState, result)

    def _build(self) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
        graph: StateGraph[AgentState, Any, AgentState, AgentState] = StateGraph(AgentState)
        graph.add_node("planning", self._planning_node)
        graph.add_node("llm_generate", self._llm_generate_node)
        graph.add_node("tool_call", self._tool_node)
        graph.add_node("validation", self._validation_node)

        graph.set_entry_point("planning")
        graph.add_edge("planning", "llm_generate")
        graph.add_edge("llm_generate", "tool_call")
        graph.add_edge("tool_call", "validation")
        graph.add_edge("validation", END)

        return graph.compile()

    def _planning_node(self, state: AgentState) -> AgentState:
        task = self._task_registry.get(state["task_id"])
        state["plan"] = task.goal
        return state

    def _llm_generate_node(self, state: AgentState) -> AgentState:
        task = self._task_registry.get(state["task_id"])
        if task.id != "append_hello_agnet_comment" or not settings.llm_enabled:
            return state

        if self._comment_chain is None:
            error_message = self._llm_bootstrap_error or "LLM chain was not initialized"
            state["llm_error"] = error_message
            if not settings.llm_fallback_to_rules:
                state["error"] = error_message
            return state

        try:
            target_file = str(state["input_payload"]["target_file"])
            generated = self._comment_chain.run(task_goal=task.goal, target_file=target_file)
            state["input_payload"]["comment_text"] = generated.comment_text
        except Exception as exc:
            state["llm_error"] = f"LLM generation failed: {exc}"
            if not settings.llm_fallback_to_rules:
                state["error"] = state["llm_error"]

        return state

    def _tool_node(self, state: AgentState) -> AgentState:
        if state["error"] is not None:
            return state

        task = self._task_registry.get(state["task_id"])
        payload = state["input_payload"]

        if task.id == "append_hello_agnet_comment":
            target_file = str(payload["target_file"])
            comment_text = str(payload.get("comment_text", "# hello agnet"))
            state["tool_result"] = append_text(target_file=target_file, text=comment_text)
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

        response: dict[str, Any] = {
            "status": "ok",
            "task_id": state["task_id"],
            **state["tool_result"],
        }
        if state["llm_error"] is not None:
            response["llm_error"] = state["llm_error"]
        state["response"] = response
        return state
