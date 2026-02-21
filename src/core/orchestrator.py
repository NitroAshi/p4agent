from typing import Any, cast

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import ValidationError

from core.routing import RouteNotFoundError, TaskRouter
from core.settings import settings
from core.state import AgentState
from infra.llm.chains import CommentNormChain
from infra.llm.factory import build_llm_adapter
from tasks.registry import TaskRegistry


class AgentOrchestrator:
    def __init__(self, task_registry: TaskRegistry, task_router: TaskRouter):
        self._task_registry = task_registry
        self._task_router = task_router
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
            "task_spec": None,
            "handler": None,
            "validated_payload": None,
            "plan": "",
            "llm_error": None,
            "execution_result": None,
            "response": None,
            "error_code": None,
            "error_message": None,
        }
        result = self._compiled.invoke(start_state)
        return cast(AgentState, result)

    def _build(self) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
        graph: StateGraph[AgentState, Any, AgentState, AgentState] = StateGraph(AgentState)
        graph.add_node("planning", self._planning_node)
        graph.add_node("validation", self._validation_node)
        graph.add_node("llm_generate", self._llm_generate_node)
        graph.add_node("execute", self._execute_node)
        graph.add_node("response", self._response_node)

        graph.set_entry_point("planning")
        graph.add_edge("planning", "validation")
        graph.add_edge("validation", "llm_generate")
        graph.add_edge("llm_generate", "execute")
        graph.add_edge("execute", "response")
        graph.add_edge("response", END)

        return graph.compile()

    def _planning_node(self, state: AgentState) -> AgentState:
        try:
            task_spec = self._task_registry.get(state["task_id"])
            handler = self._task_router.route(state["task_id"])
        except RouteNotFoundError as exc:
            state["error_code"] = "TASK_NOT_ROUTED"
            state["error_message"] = str(exc)
            return state
        except KeyError as exc:
            state["error_code"] = "TASK_NOT_FOUND"
            state["error_message"] = str(exc)
            return state

        state["task_spec"] = task_spec
        state["handler"] = handler
        state["plan"] = handler.plan(state["input_payload"], task_spec)
        return state

    def _validation_node(self, state: AgentState) -> AgentState:
        if state["error_code"] is not None:
            return state

        handler = state["handler"]
        task_spec = state["task_spec"]
        if handler is None or task_spec is None:
            state["error_code"] = "INTERNAL_ERROR"
            state["error_message"] = "Planner did not initialize handler and task spec"
            return state

        try:
            state["validated_payload"] = handler.validate_payload(state["input_payload"], task_spec)
        except ValidationError as exc:
            state["error_code"] = "INVALID_PAYLOAD"
            state["error_message"] = str(exc)

        return state

    def _llm_generate_node(self, state: AgentState) -> AgentState:
        if state["error_code"] is not None:
            return state

        handler = state["handler"]
        task_spec = state["task_spec"]
        payload = state["validated_payload"]
        if handler is None or task_spec is None or payload is None:
            state["error_code"] = "INTERNAL_ERROR"
            state["error_message"] = "Validator did not initialize execution context"
            return state

        if not handler.requires_llm:
            return state

        chain = self._comment_chain
        if chain is None and self._llm_bootstrap_error is not None:
            # Surface bootstrap errors in handler-level semantics.
            state["llm_error"] = self._llm_bootstrap_error

        next_payload, llm_error, fatal_error = handler.preprocess_with_llm(
            payload=payload,
            spec=task_spec,
            llm_enabled=settings.llm_enabled,
            llm_fallback_to_rules=settings.llm_fallback_to_rules,
            comment_chain=chain,
        )
        state["validated_payload"] = next_payload
        if llm_error is not None:
            state["llm_error"] = llm_error
        if fatal_error is not None:
            state["error_code"] = "LLM_PREPROCESS_FAILED"
            state["error_message"] = fatal_error

        return state

    def _execute_node(self, state: AgentState) -> AgentState:
        if state["error_code"] is not None:
            return state

        handler = state["handler"]
        task_spec = state["task_spec"]
        payload = state["validated_payload"]
        if handler is None or task_spec is None or payload is None:
            state["error_code"] = "INTERNAL_ERROR"
            state["error_message"] = "Execution context is incomplete"
            return state

        try:
            state["execution_result"] = handler.execute(payload, task_spec)
        except Exception as exc:
            state["error_code"] = "EXECUTION_ERROR"
            state["error_message"] = str(exc)

        return state

    def _response_node(self, state: AgentState) -> AgentState:
        if state["error_code"] is not None:
            state["response"] = {
                "status": "failed",
                "task_id": state["task_id"],
                "error": {
                    "code": state["error_code"],
                    "message": state["error_message"] or "Unknown error",
                },
            }
            return state

        handler = state["handler"]
        task_spec = state["task_spec"]
        result = state["execution_result"]
        if handler is None or task_spec is None or result is None:
            state["response"] = {
                "status": "failed",
                "task_id": state["task_id"],
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Task completed without output",
                },
            }
            return state

        state["response"] = handler.format_response(
            spec=task_spec,
            result=result,
            llm_error=state["llm_error"],
        )
        return state
