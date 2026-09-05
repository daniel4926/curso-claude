import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import text

from app.db import engine
from app.main import app
from app.schemas import TaskCreate, TaskUpdate


async def _client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seeded_state_id() -> int:
    async with engine.connect() as conn:
        result = await conn.execute(text("select id from states order by sort_order limit 1"))
        return result.scalar_one()


async def _task_count() -> int:
    async with engine.connect() as conn:
        result = await conn.execute(text("select count(*) from tasks"))
        return result.scalar_one()


def test_create_schema_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(title="", project_id=1, state_id=1)


def test_create_schema_rejects_ascii_whitespace_only_title() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(title="   ", project_id=1, state_id=1)


def test_create_schema_trims_title() -> None:
    task = TaskCreate(title="  Regar las plantas  ", project_id=1, state_id=1)
    assert task.title == "Regar las plantas"


def test_update_schema_allows_omitting_title() -> None:
    update = TaskUpdate(description="Nueva descripción")
    assert update.title is None


def test_update_schema_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        TaskUpdate(title="   ")


@pytest.mark.asyncio
async def test_create_task_returns_201_with_exact_schema() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project = await client.post("/projects", json={"name": "Casa"})
        project_id = project.json()["id"]

        response = await client.post(
            "/tasks",
            json={"title": "Regar las plantas", "project_id": project_id, "state_id": state_id},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Regar las plantas"
    assert body["description"] is None
    assert body["project_id"] == project_id
    assert body["state_id"] == state_id
    assert set(body.keys()) == {"id", "title", "description", "project_id", "state_id"}


@pytest.mark.asyncio
async def test_create_task_with_nonexistent_project_returns_422() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        response = await client.post(
            "/tasks",
            json={"title": "X", "project_id": 999999, "state_id": state_id},
        )

    assert response.status_code == 422
    assert "detail" in response.json()
    assert await _task_count() == 0


@pytest.mark.asyncio
async def test_create_task_with_nonexistent_state_returns_422() -> None:
    async with await _client() as client:
        project = await client.post("/projects", json={"name": "Casa"})
        project_id = project.json()["id"]

        response = await client.post(
            "/tasks",
            json={"title": "X", "project_id": project_id, "state_id": 999999},
        )

    assert response.status_code == 422
    assert "detail" in response.json()
    assert await _task_count() == 0
