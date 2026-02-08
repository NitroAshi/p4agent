from typing import Protocol


class Task(Protocol):
    """Common interface for workflow tasks."""

    def plan(self) -> str: ...

    def run(self) -> dict[str, object]: ...

    def validate(self) -> bool: ...
