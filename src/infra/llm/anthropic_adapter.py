from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, SecretStr

from infra.llm.base import ModelT


class AnthropicAdapter:
    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        temperature: float,
        timeout_seconds: int,
    ) -> None:
        self._model = ChatAnthropic(
            model_name=model,
            api_key=SecretStr(api_key),
            temperature=temperature,
            timeout=timeout_seconds,
            stop=None,
        )

    def invoke_structured(self, prompt: str, schema: type[ModelT]) -> ModelT:
        runner = self._model.with_structured_output(schema)
        result: BaseModel | dict[str, object] = runner.invoke(prompt)
        if isinstance(result, schema):
            return result
        return schema.model_validate(result)
