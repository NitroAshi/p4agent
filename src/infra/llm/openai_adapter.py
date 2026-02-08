from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from infra.llm.base import ModelT, extract_text_content, parse_structured_result


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
        try:
            result = runner.invoke(prompt)
            return parse_structured_result(result, schema)
        except Exception:
            raw_result = self._model.invoke(prompt)
            raw_text = extract_text_content(raw_result)
            return parse_structured_result(raw_text, schema)
