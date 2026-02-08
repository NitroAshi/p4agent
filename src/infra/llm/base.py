import re
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class LLMAdapter(Protocol):
    """Adapter contract for provider-specific structured generation."""

    def invoke_structured(self, prompt: str, schema: type[ModelT]) -> ModelT: ...


def parse_structured_result[T: BaseModel](result: Any, schema: type[T]) -> T:
    """Normalize provider outputs into a validated schema object."""
    if isinstance(result, schema):
        return result

    if isinstance(result, BaseModel):
        return schema.model_validate(result.model_dump())

    if isinstance(result, dict):
        return schema.model_validate(result)

    if isinstance(result, str):
        normalized_json = _extract_json_payload(result)
        return schema.model_validate_json(normalized_json)

    return schema.model_validate(result)


def extract_text_content(message: Any) -> str:
    """Extract text payload from chat model responses."""
    if isinstance(message, str):
        return message

    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        return "\n".join(chunks).strip()

    return str(message)


def _extract_json_payload(raw_text: str) -> str:
    text = raw_text.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        return fenced.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        return text[start : end + 1]

    return text
