from datetime import UTC, datetime, timedelta, timezone

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


async def _seeded_state_ids(count: int) -> list[int]:
    async with engine.connect() as conn:
        result = await conn.execute(
            text("select id from states order by sort_order limit :count"), {"count": count}
        )
        return [row.id for row in result.all()]


async def _state_id_by_code(code: str) -> int:
    async with engine.connect() as conn:
        result = await conn.execute(
            text("select id from states where code = :code"), {"code": code}
        )
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


def test_create_schema_rejects_due_at_without_timezone() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(
            title="X",
            project_id=1,
            state_id=1,
            due_at=datetime(2026, 3, 1, 9, 0, 0),
        )


def test_create_schema_normalizes_due_at_to_utc() -> None:
    tz_minus_3 = timezone(timedelta(hours=-3))
    task = TaskCreate(
        title="X",
        project_id=1,
        state_id=1,
        due_at=datetime(2026, 3, 1, 6, 0, 0, tzinfo=tz_minus_3),
    )
    assert task.due_at == datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC)


def test_update_schema_rejects_due_at_without_timezone() -> None:
    with pytest.raises(ValidationError):
        TaskUpdate(due_at=datetime(2026, 3, 1, 9, 0, 0))


def test_create_schema_rejects_priority_out_of_range() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(title="X", project_id=1, state_id=1, priority=6)
    with pytest.raises(ValidationError):
        TaskCreate(title="X", project_id=1, state_id=1, priority=0)


def test_update_schema_rejects_priority_out_of_range() -> None:
    with pytest.raises(ValidationError):
        TaskUpdate(priority=6)


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
    assert body["due_at"] is None
    assert body["priority"] is None
    assert set(body.keys()) == {
        "id",
        "title",
        "description",
        "project_id",
        "state_id",
        "due_at",
        "priority",
    }


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
async def test_get_task_by_id() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]
        created = await client.post(
            "/tasks", json={"title": "Regar", "project_id": project_id, "state_id": state_id}
        )
        task_id = created.json()["id"]

        response = await client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id


@pytest.mark.asyncio
async def test_get_nonexistent_task_returns_404() -> None:
    async with await _client() as client:
        response = await client.get("/tasks/999999")

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_patch_task_updates_only_given_fields_and_normalizes_title() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]
        created = await client.post(
            "/tasks",
            json={
                "title": "Regar",
                "description": "Original",
                "project_id": project_id,
                "state_id": state_id,
            },
        )
        task_id = created.json()["id"]

        response = await client.patch(f"/tasks/{task_id}", json={"title": "  Regar todo  "})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Regar todo"
    assert body["description"] == "Original"


@pytest.mark.asyncio
async def test_patch_task_with_nonexistent_project_returns_422_and_does_not_change_task() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]
        created = await client.post(
            "/tasks", json={"title": "Regar", "project_id": project_id, "state_id": state_id}
        )
        task_id = created.json()["id"]

        response = await client.patch(f"/tasks/{task_id}", json={"project_id": 999999})
        unchanged = await client.get(f"/tasks/{task_id}")

    assert response.status_code == 422
    assert unchanged.json()["project_id"] == project_id


@pytest.mark.asyncio
async def test_patch_nonexistent_task_returns_404() -> None:
    async with await _client() as client:
        response = await client.patch("/tasks/999999", json={"title": "X"})

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_delete_task_returns_204_without_body() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]
        created = await client.post(
            "/tasks", json={"title": "Regar", "project_id": project_id, "state_id": state_id}
        )
        task_id = created.json()["id"]

        response = await client.delete(f"/tasks/{task_id}")
        after = await client.get(f"/tasks/{task_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert after.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_task_returns_404() -> None:
    async with await _client() as client:
        response = await client.delete("/tasks/999999")

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_list_tasks_without_filters_is_ordered_by_id_and_stable() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]

        first = await client.post(
            "/tasks", json={"title": "Uno", "project_id": project_id, "state_id": state_id}
        )
        second = await client.post(
            "/tasks", json={"title": "Dos", "project_id": project_id, "state_id": state_id}
        )

        response_a = await client.get("/tasks")
        response_b = await client.get("/tasks")

    ids_a = [task["id"] for task in response_a.json()]
    ids_b = [task["id"] for task in response_b.json()]
    assert ids_a == [first.json()["id"], second.json()["id"]]
    assert ids_a == ids_b


@pytest.mark.asyncio
async def test_list_tasks_filters_by_project_and_state_without_validating_existence() -> None:
    state_ids = await _seeded_state_ids(2)
    async with await _client() as client:
        project_a = (await client.post("/projects", json={"name": "A"})).json()["id"]
        project_b = (await client.post("/projects", json={"name": "B"})).json()["id"]

        a1 = await client.post(
            "/tasks", json={"title": "A1", "project_id": project_a, "state_id": state_ids[0]}
        )
        a2 = await client.post(
            "/tasks", json={"title": "A2", "project_id": project_a, "state_id": state_ids[1]}
        )
        await client.post(
            "/tasks", json={"title": "B1", "project_id": project_b, "state_id": state_ids[0]}
        )

        by_project = await client.get("/tasks", params={"project_id": project_a})
        by_state = await client.get("/tasks", params={"state_id": state_ids[1]})
        combined = await client.get(
            "/tasks", params={"project_id": project_a, "state_id": state_ids[0]}
        )
        empty = await client.get("/tasks", params={"project_id": 999999})

    assert {t["id"] for t in by_project.json()} == {a1.json()["id"], a2.json()["id"]}
    assert {t["id"] for t in by_state.json()} == {a2.json()["id"]}
    assert [t["id"] for t in combined.json()] == [a1.json()["id"]]
    assert empty.status_code == 200
    assert empty.json() == []


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


@pytest.mark.asyncio
async def test_create_task_with_due_at_serializes_as_utc_z_without_microseconds() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]

        response = await client.post(
            "/tasks",
            json={
                "title": "Pagar impuestos",
                "project_id": project_id,
                "state_id": state_id,
                "due_at": "2026-03-01T06:00:00.123456-03:00",
            },
        )

    assert response.status_code == 201
    assert response.json()["due_at"] == "2026-03-01T09:00:00Z"


@pytest.mark.asyncio
async def test_create_task_with_due_at_without_timezone_returns_422() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]

        response = await client.post(
            "/tasks",
            json={
                "title": "X",
                "project_id": project_id,
                "state_id": state_id,
                "due_at": "2026-03-01T09:00:00",
            },
        )

    assert response.status_code == 422
    assert "detail" in response.json()
    assert await _task_count() == 0


@pytest.mark.asyncio
async def test_patch_task_can_set_and_clear_due_at() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]
        created = await client.post(
            "/tasks", json={"title": "Regar", "project_id": project_id, "state_id": state_id}
        )
        task_id = created.json()["id"]

        set_response = await client.patch(
            f"/tasks/{task_id}", json={"due_at": "2026-03-01T09:00:00Z"}
        )
        clear_response = await client.patch(f"/tasks/{task_id}", json={"due_at": None})

    assert set_response.json()["due_at"] == "2026-03-01T09:00:00Z"
    assert clear_response.json()["due_at"] is None


@pytest.mark.asyncio
async def test_list_tasks_overdue_filter() -> None:
    pending_state_id = await _state_id_by_code("PENDIENTE")
    done_state_id = await _state_id_by_code("HECHA")
    now = datetime.now(UTC)
    past = (now - timedelta(days=1)).isoformat()
    future = (now + timedelta(days=1)).isoformat()

    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]

        overdue_task = await client.post(
            "/tasks",
            json={
                "title": "Vencida",
                "project_id": project_id,
                "state_id": pending_state_id,
                "due_at": past,
            },
        )
        await client.post(
            "/tasks",
            json={
                "title": "Futura",
                "project_id": project_id,
                "state_id": pending_state_id,
                "due_at": future,
            },
        )
        await client.post(
            "/tasks",
            json={
                "title": "Sin fecha",
                "project_id": project_id,
                "state_id": pending_state_id,
            },
        )
        await client.post(
            "/tasks",
            json={
                "title": "Vencida pero hecha",
                "project_id": project_id,
                "state_id": done_state_id,
                "due_at": past,
            },
        )

        response = await client.get("/tasks", params={"overdue": "true"})

    assert [t["id"] for t in response.json()] == [overdue_task.json()["id"]]


@pytest.mark.asyncio
async def test_create_task_with_priority_in_range() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]

        response = await client.post(
            "/tasks",
            json={
                "title": "Pagar impuestos",
                "project_id": project_id,
                "state_id": state_id,
                "priority": 5,
            },
        )

    assert response.status_code == 201
    assert response.json()["priority"] == 5


@pytest.mark.asyncio
async def test_create_task_with_priority_out_of_range_returns_422() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]

        response = await client.post(
            "/tasks",
            json={
                "title": "X",
                "project_id": project_id,
                "state_id": state_id,
                "priority": 6,
            },
        )

    assert response.status_code == 422
    assert "detail" in response.json()
    assert await _task_count() == 0


@pytest.mark.asyncio
async def test_patch_task_can_set_and_clear_priority() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]
        created = await client.post(
            "/tasks", json={"title": "Regar", "project_id": project_id, "state_id": state_id}
        )
        task_id = created.json()["id"]

        set_response = await client.patch(f"/tasks/{task_id}", json={"priority": 3})
        clear_response = await client.patch(f"/tasks/{task_id}", json={"priority": None})

    assert set_response.json()["priority"] == 3
    assert clear_response.json()["priority"] is None
