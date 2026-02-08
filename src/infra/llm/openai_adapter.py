from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

from infra.llm.base import ModelT


class OpenAIAdapter:
    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        base_url: str | None,
        temperature: float,
        timeout_seconds: int,
    ) -> None:
        self._model = ChatOpenAI(
            model=model,
            api_key=SecretStr(api_key),
            base_url=base_url,
            temperature=temperature,
            timeout=timeout_seconds,
        )

    def invoke_structured(self, prompt: str, schema: type[ModelT]) -> ModelT:
        runner = self._model.with_structured_output(schema)
        result: BaseModel | dict[str, object] = runner.invoke(prompt)
        if isinstance(result, schema):
            return result
        return schema.model_validate(result)
