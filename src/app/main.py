from collections.abc import Generator

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent_core.service import AgentService


class RunTaskRequest(BaseModel):
    task_id: str = Field(min_length=1)
    payload: dict[str, object]


def service_provider() -> Generator[AgentService, None, None]:
    yield AgentService()


app = FastAPI(title="p4agent-demo", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> dict[str, list[str]]:
    service = AgentService()
    return {"tasks": service.list_tasks()}


@app.post("/run")
def run_task(req: RunTaskRequest) -> dict[str, object]:
    service = AgentService()
    try:
        return service.run_task(task_id=req.task_id, payload=req.payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def run() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)


# hello agnet
