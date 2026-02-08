from typing import Protocol, TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class LLMAdapter(Protocol):
    """Adapter contract for provider-specific structured generation."""

    def invoke_structured(self, prompt: str, schema: type[ModelT]) -> ModelT: ...
