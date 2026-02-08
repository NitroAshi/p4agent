from typing import Any

import pytest

import infra.llm.anthropic_adapter as anthropic_module
import infra.llm.azure_adapter as azure_module
import infra.llm.openai_adapter as openai_module
from infra.llm.schema import CommentNormOutput


class FakeRunner:
    def __init__(self, payload: dict[str, str]):
        self._payload = payload

    def invoke(self, prompt: str) -> dict[str, str]:
        assert isinstance(prompt, str)
        return self._payload


class FakeModel:
    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs

    def with_structured_output(self, schema: type[CommentNormOutput]) -> FakeRunner:
        assert schema is CommentNormOutput
        return FakeRunner({"comment_text": "# from fake model"})


def test_openai_adapter_invokes_structured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(openai_module, "ChatOpenAI", FakeModel)

    adapter = openai_module.OpenAIAdapter(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url=None,
        temperature=0.0,
        timeout_seconds=5,
    )
    result = adapter.invoke_structured("hi", CommentNormOutput)

    assert result.comment_text == "# from fake model"


def test_anthropic_adapter_invokes_structured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(anthropic_module, "ChatAnthropic", FakeModel)

    adapter = anthropic_module.AnthropicAdapter(
        model="claude-3-5-haiku-latest",
        api_key="test-key",
        temperature=0.0,
        timeout_seconds=5,
    )
    result = adapter.invoke_structured("hi", CommentNormOutput)

    assert result.comment_text == "# from fake model"


def test_azure_adapter_invokes_structured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(azure_module, "AzureChatOpenAI", FakeModel)

    adapter = azure_module.AzureOpenAIAdapter(
        deployment="my-deployment",
        endpoint="https://example.openai.azure.com",
        api_key="test-key",
        api_version="2024-02-15-preview",
        temperature=0.0,
        timeout_seconds=5,
    )
    result = adapter.invoke_structured("hi", CommentNormOutput)

    assert result.comment_text == "# from fake model"
