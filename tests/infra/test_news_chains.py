from typing import TypeVar

from pydantic import BaseModel

from infra.llm.news_chains import NewsExtractChain, NewsTranslateChain

ModelT = TypeVar("ModelT", bound=BaseModel)


class FakeAdapter:
    def __init__(self) -> None:
        self.last_prompt = ""

    def invoke_structured(self, prompt: str, schema: type[ModelT]) -> ModelT:
        self.last_prompt = prompt
        if schema.__name__ == "NewsExtractOutput":
            return schema.model_validate(
                {
                    "items_en": [
                        {
                            "rank": 1,
                            "title_en": "T1",
                            "summary_en": "S1",
                            "source": "SRC",
                            "url": "https://example.com/1",
                        }
                    ],
                    "selection_notes": "ok",
                }
            )

        return schema.model_validate(
            {
                "items": [
                    {
                        "rank": 1,
                        "title_en": "T1",
                        "summary_en": "S1",
                        "title_zh": "ZH1",
                        "summary_zh": "ZHS1",
                        "title_ja": "JA1",
                        "summary_ja": "JAS1",
                        "source": "SRC",
                        "url": "https://example.com/1",
                    }
                ]
            }
        )


def test_news_extract_chain_renders_prompt() -> None:
    adapter = FakeAdapter()
    chain = NewsExtractChain(adapter)

    output = chain.run(
        raw_cards=[{"title": "A", "url": "u", "snippet": "s", "source": "x"}],
        top_k=10,
    )

    assert len(output.items_en) == 1
    assert "top 10" in adapter.last_prompt.lower()


def test_news_translate_chain_renders_prompt() -> None:
    adapter = FakeAdapter()
    chain = NewsTranslateChain(adapter)

    output = chain.run(
        items_en=[
            {
                "rank": "1",
                "title_en": "A",
                "summary_en": "B",
                "source": "X",
                "url": "https://example.com",
            }
        ],
        date="2026-02-18",
    )

    assert len(output.items) == 1
    assert "2026-02-18" in adapter.last_prompt
