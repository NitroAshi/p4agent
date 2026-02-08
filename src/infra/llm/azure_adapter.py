from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, SecretStr

from infra.llm.base import ModelT


class AzureOpenAIAdapter:
    def __init__(
        self,
        *,
        deployment: str,
        endpoint: str,
        api_key: str,
        api_version: str,
        temperature: float,
        timeout_seconds: int,
    ) -> None:
        self._model = AzureChatOpenAI(
            azure_deployment=deployment,
            azure_endpoint=endpoint,
            api_key=SecretStr(api_key),
            api_version=api_version,
            temperature=temperature,
            timeout=timeout_seconds,
        )

    def invoke_structured(self, prompt: str, schema: type[ModelT]) -> ModelT:
        runner = self._model.with_structured_output(schema)
        result: BaseModel | dict[str, object] = runner.invoke(prompt)
        if isinstance(result, schema):
            return result
        return schema.model_validate(result)
