from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, ValidationError, create_model

from tasks.registry import TaskSpec

_TYPE_MAP: dict[str, type[Any]] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict[str, Any],
    "array": list[Any],
}


def validate_task_payload(spec: TaskSpec, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate payload strictly from the task input schema."""
    fields: dict[str, tuple[type[Any], Any]] = {}
    required = set(spec.inputs.required)

    for field_name, property_schema in spec.inputs.properties.items():
        field_type = _TYPE_MAP.get(property_schema.get("type", "string"), Any)
        default = ... if field_name in required else None
        fields[field_name] = (field_type, default)

    model = create_model(  # type: ignore[call-overload]
        f"Payload_{spec.id}",
        __config__=ConfigDict(extra="forbid"),
        **fields,
    )
    validated = model.model_validate(payload)
    return dict(validated)


__all__ = ["ValidationError", "validate_task_payload"]
