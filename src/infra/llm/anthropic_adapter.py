from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr

from infra.llm.base import ModelT, extract_text_content, parse_structured_result


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
        try:
            result = runner.invoke(prompt)
            return parse_structured_result(result, schema)
        except Exception:
            raw_result = self._model.invoke(prompt)
            raw_text = extract_text_content(raw_result)
            return parse_structured_result(raw_text, schema)
