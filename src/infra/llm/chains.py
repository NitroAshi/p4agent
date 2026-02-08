from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from infra.llm.base import LLMAdapter
from infra.llm.schema import CommentNormOutput

_PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
_PROMPT_ENV = Environment(
    loader=FileSystemLoader(_PROMPT_DIR),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


class CommentNormChain:
    """LCEL-style chain wrapper for comment normalization output."""

    def __init__(self, adapter: LLMAdapter):
        self._adapter = adapter

    def run(self, task_goal: str, target_file: str) -> CommentNormOutput:
        template = _PROMPT_ENV.get_template("comment_norm.j2")
        prompt = template.render(task_goal=task_goal, target_file=target_file)
        return self._adapter.invoke_structured(prompt=prompt, schema=CommentNormOutput)
