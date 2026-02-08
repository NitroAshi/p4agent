from pathlib import Path
from typing import Any, cast

import pytest

import infra.llm.anthropic_adapter as anthropic_module
import infra.llm.azure_adapter as azure_module
import infra.llm.openai_adapter as openai_module
from core.settings import Settings
from infra.llm.factory import build_llm_adapter


def _make_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    **kwargs: Any,
) -> Settings:
    monkeypatch.chdir(tmp_path)
    return Settings(**kwargs)


def test_factory_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = _make_settings(monkeypatch, tmp_path, llm_provider="unknown")

    with pytest.raises(ValueError, match="Unsupported llm_provider"):
        build_llm_adapter(cfg)


def test_factory_validates_openai_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = _make_settings(monkeypatch, tmp_path, llm_provider="openai", openai_api_key=None)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_llm_adapter(cfg)


def test_factory_validates_anthropic_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg = _make_settings(monkeypatch, tmp_path, llm_provider="anthropic", anthropic_api_key=None)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        build_llm_adapter(cfg)


def test_factory_validates_azure_required_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)
    cfg = _make_settings(
        monkeypatch,
        tmp_path,
        llm_provider="azure",
        azure_openai_api_key=None,
        azure_openai_endpoint=None,
        azure_openai_deployment=None,
    )

    with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY"):
        build_llm_adapter(cfg)


def test_factory_builds_openai_adapter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        openai_module, "OpenAIAdapter", lambda **kwargs: {"provider": "openai", **kwargs}
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    cfg = _make_settings(
        monkeypatch,
        tmp_path,
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        openai_base_url=None,
    )

    adapter = cast(dict[str, Any], build_llm_adapter(cfg))

    assert adapter["provider"] == "openai"


def test_factory_builds_anthropic_adapter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        anthropic_module,
        "AnthropicAdapter",
        lambda **kwargs: {"provider": "anthropic", **kwargs},
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    cfg = _make_settings(
        monkeypatch,
        tmp_path,
        llm_provider="anthropic",
        llm_model="claude-3-5-haiku-latest",
    )

    adapter = cast(dict[str, Any], build_llm_adapter(cfg))

    assert adapter["provider"] == "anthropic"


def test_factory_builds_azure_adapter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        azure_module, "AzureOpenAIAdapter", lambda **kwargs: {"provider": "azure", **kwargs}
    )
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "my-deployment")
    cfg = _make_settings(
        monkeypatch,
        tmp_path,
        llm_provider="azure",
    )

    adapter = cast(dict[str, Any], build_llm_adapter(cfg))

    assert adapter["provider"] == "azure"
