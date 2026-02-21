from core.settings import Settings
from infra.llm.base import LLMAdapter


def build_llm_adapter(cfg: Settings) -> LLMAdapter:
    provider = cfg.llm_provider.strip().lower()

    if provider == "openai":
        if not cfg.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when llm_provider=openai")
        from infra.llm.openai_adapter import OpenAIAdapter

        return OpenAIAdapter(
            model=cfg.llm_model,
            api_key=cfg.openai_api_key,
            base_url=cfg.openai_base_url,
            temperature=cfg.llm_temperature,
            timeout_seconds=cfg.llm_timeout_seconds,
        )

    if provider == "anthropic":
        if not cfg.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when llm_provider=anthropic")
        from infra.llm.anthropic_adapter import AnthropicAdapter

        return AnthropicAdapter(
            model=cfg.llm_model,
            api_key=cfg.anthropic_api_key,
            temperature=cfg.llm_temperature,
            timeout_seconds=cfg.llm_timeout_seconds,
        )

    if provider == "azure":
        if not cfg.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is required when llm_provider=azure")
        if not cfg.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required when llm_provider=azure")
        # if not cfg.azure_openai_deployment:
            # raise ValueError("AZURE_OPENAI_DEPLOYMENT is required when llm_provider=azure")
        # if deployment is not set, use llm_model as deployment name
        deployment = cfg.azure_openai_deployment or cfg.llm_model
        from infra.llm.azure_adapter import AzureOpenAIAdapter

        return AzureOpenAIAdapter(
            deployment=deployment,
            endpoint=cfg.azure_openai_endpoint,
            api_key=cfg.azure_openai_api_key,
            api_version=cfg.azure_openai_api_version,
            temperature=cfg.llm_temperature,
            timeout_seconds=cfg.llm_timeout_seconds,
        )

    raise ValueError(f"Unsupported llm_provider '{cfg.llm_provider}'")
