from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedNewsItem(BaseModel):
    rank: int = Field(ge=1)
    title_en: str = Field(min_length=1)
    summary_en: str = Field(min_length=1)
    source: str = Field(default="")
    url: str = Field(min_length=1)


class NewsExtractOutput(BaseModel):
    items_en: list[ExtractedNewsItem]
    selection_notes: str | None = None


class TranslatedNewsItem(BaseModel):
    rank: int = Field(ge=1)
    title_en: str = Field(min_length=1)
    summary_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    title_ja: str = Field(min_length=1)
    summary_ja: str = Field(min_length=1)
    source: str = Field(default="")
    url: str = Field(min_length=1)


class NewsTranslateOutput(BaseModel):
    items: list[TranslatedNewsItem]
