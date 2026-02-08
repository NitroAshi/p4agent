from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import main
from core.service import AgentService


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(main.app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_tasks(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def list_tasks(self) -> list[str]:
            return ["append_hello_agent_comment"]

    monkeypatch.setattr(main, "AgentService", FakeService)

    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == {"tasks": ["append_hello_agent_comment"]}


def test_run_task_success(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def run_task(self, task_id: str, payload: dict[str, object]) -> dict[str, object]:
            assert task_id == "append_hello_agent_comment"
            assert payload == {"target_file": "demo.py"}
            return {"status": "ok", "task_id": task_id}

    monkeypatch.setattr(main, "AgentService", FakeService)

    response = client.post(
        "/run",
        json={"task_id": "append_hello_agent_comment", "payload": {"target_file": "demo.py"}},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "task_id": "append_hello_agent_comment"}


def test_run_task_not_found(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def run_task(self, task_id: str, payload: dict[str, object]) -> dict[str, object]:
            raise KeyError("Unknown task_id")

    monkeypatch.setattr(main, "AgentService", FakeService)

    response = client.post("/run", json={"task_id": "unknown", "payload": {}})

    assert response.status_code == 404
    assert "Unknown task_id" in response.json()["detail"]


def test_service_provider() -> None:
    provider = main.service_provider()
    service = next(provider)

    assert isinstance(service, AgentService)
