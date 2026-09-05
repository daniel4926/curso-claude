import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db import engine
from app.main import app


async def _client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_create_project_without_description_returns_null() -> None:
    async with await _client() as client:
        response = await client.post("/projects", json={"name": "Casa"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Casa"
    assert body["description"] is None
    assert set(body.keys()) == {"id", "name", "description"}


@pytest.mark.asyncio
async def test_create_project_with_description() -> None:
    async with await _client() as client:
        response = await client.post(
            "/projects", json={"name": "Casa", "description": "Tareas del hogar"}
        )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Casa"
    assert body["description"] == "Tareas del hogar"


@pytest.mark.asyncio
async def test_list_projects_is_ordered_by_id_and_stable_across_calls() -> None:
    async with await _client() as client:
        first = await client.post("/projects", json={"name": "Primero"})
        second = await client.post("/projects", json={"name": "Segundo"})
        third = await client.post("/projects", json={"name": "Tercero"})

        expected_ids = [first.json()["id"], second.json()["id"], third.json()["id"]]

        response_a = await client.get("/projects")
        response_b = await client.get("/projects")

    assert response_a.status_code == 200
    ids_a = [project["id"] for project in response_a.json()]
    ids_b = [project["id"] for project in response_b.json()]

    assert ids_a == sorted(expected_ids)
    assert ids_a == ids_b


@pytest.mark.asyncio
async def test_get_project_by_id() -> None:
    async with await _client() as client:
        created = await client.post("/projects", json={"name": "Casa"})
        project_id = created.json()["id"]

        response = await client.get(f"/projects/{project_id}")

    assert response.status_code == 200
    assert response.json()["id"] == project_id


@pytest.mark.asyncio
async def test_get_nonexistent_project_returns_404() -> None:
    async with await _client() as client:
        response = await client.get("/projects/999999")

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_patch_project_updates_only_given_fields() -> None:
    async with await _client() as client:
        created = await client.post(
            "/projects", json={"name": "Casa", "description": "Original"}
        )
        project_id = created.json()["id"]

        response = await client.patch(
            f"/projects/{project_id}", json={"description": "Actualizada"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Casa"
    assert body["description"] == "Actualizada"


@pytest.mark.asyncio
async def test_patch_project_can_clear_description_with_null() -> None:
    async with await _client() as client:
        created = await client.post(
            "/projects", json={"name": "Casa", "description": "Original"}
        )
        project_id = created.json()["id"]

        response = await client.patch(f"/projects/{project_id}", json={"description": None})

    assert response.status_code == 200
    assert response.json()["description"] is None


@pytest.mark.asyncio
async def test_patch_nonexistent_project_returns_404() -> None:
    async with await _client() as client:
        response = await client.patch("/projects/999999", json={"name": "X"})

    assert response.status_code == 404
    assert "detail" in response.json()


async def _seeded_state_id() -> int:
    async with engine.connect() as conn:
        result = await conn.execute(text("select id from states order by sort_order limit 1"))
        return result.scalar_one()


@pytest.mark.asyncio
async def test_delete_project_without_tasks_returns_204() -> None:
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]

        response = await client.delete(f"/projects/{project_id}")
        after = await client.get(f"/projects/{project_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert after.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_with_tasks_returns_409_and_keeps_both() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]
        task_id = (
            await client.post(
                "/tasks",
                json={"title": "Regar", "project_id": project_id, "state_id": state_id},
            )
        ).json()["id"]

        response = await client.delete(f"/projects/{project_id}")
        project_after = await client.get(f"/projects/{project_id}")
        task_after = await client.get(f"/tasks/{task_id}")

    assert response.status_code == 409
    assert "detail" in response.json()
    assert project_after.status_code == 200
    assert task_after.status_code == 200


@pytest.mark.asyncio
async def test_delete_project_succeeds_after_deleting_its_task() -> None:
    state_id = await _seeded_state_id()
    async with await _client() as client:
        project_id = (await client.post("/projects", json={"name": "Casa"})).json()["id"]
        task_id = (
            await client.post(
                "/tasks",
                json={"title": "Regar", "project_id": project_id, "state_id": state_id},
            )
        ).json()["id"]

        await client.delete(f"/tasks/{task_id}")
        response = await client.delete(f"/projects/{project_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_project_returns_404() -> None:
    async with await _client() as client:
        response = await client.delete("/projects/999999")

    assert response.status_code == 404
    assert "detail" in response.json()
