from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from infra.llm.base import LLMAdapter
from infra.llm.news_schema import NewsExtractOutput, NewsTranslateOutput

_PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
_PROMPT_ENV = Environment(
    loader=FileSystemLoader(_PROMPT_DIR),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


class NewsExtractChain:
    def __init__(self, adapter: LLMAdapter):
        self._adapter = adapter

    def run(self, *, raw_cards: list[dict[str, str]], top_k: int) -> NewsExtractOutput:
        template = _PROMPT_ENV.get_template("news_extract.j2")
        prompt = template.render(
            raw_cards_json=json.dumps(raw_cards, ensure_ascii=True),
            top_k=top_k,
        )
        return self._adapter.invoke_structured(prompt=prompt, schema=NewsExtractOutput)


class NewsTranslateChain:
    def __init__(self, adapter: LLMAdapter):
        self._adapter = adapter

    def run(self, *, items_en: list[dict[str, str]], date: str) -> NewsTranslateOutput:
        template = _PROMPT_ENV.get_template("news_translate.j2")
        prompt = template.render(items_en_json=json.dumps(items_en, ensure_ascii=True), date=date)
        return self._adapter.invoke_structured(prompt=prompt, schema=NewsTranslateOutput)
