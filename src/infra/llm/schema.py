from pydantic import BaseModel, Field


class CommentNormOutput(BaseModel):
    """Structured output for comment generation."""

    comment_text: str = Field(min_length=1, max_length=200)
