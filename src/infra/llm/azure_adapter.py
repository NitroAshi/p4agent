from langchain_openai import AzureChatOpenAI
from pydantic import SecretStr

from infra.llm.base import ModelT, extract_text_content, parse_structured_result


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
        try:
            result = runner.invoke(prompt)
            return parse_structured_result(result, schema)
        except Exception:
            raw_result = self._model.invoke(prompt)
            raw_text = extract_text_content(raw_result)
            return parse_structured_result(raw_text, schema)
