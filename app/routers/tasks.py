from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Project, State, Task
from app.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _ensure_project_exists(project_id: int, session: AsyncSession) -> None:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=422, detail=f"El proyecto {project_id} no existe")


async def _ensure_state_exists(state_id: int, session: AsyncSession) -> None:
    state = await session.get(State, state_id)
    if state is None:
        raise HTTPException(status_code=422, detail=f"El estado {state_id} no existe")


async def _get_task_or_404(task_id: int, session: AsyncSession) -> Task:
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"La tarea {task_id} no existe")
    return task


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(payload: TaskCreate, session: AsyncSession = Depends(get_session)) -> Task:
    await _ensure_project_exists(payload.project_id, session)
    await _ensure_state_exists(payload.state_id, session)

    task = Task(
        title=payload.title,
        description=payload.description,
        project_id=payload.project_id,
        state_id=payload.state_id,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    project_id: int | None = None,
    state_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Task]:
    query = select(Task).order_by(Task.id)
    if project_id is not None:
        query = query.where(Task.project_id == project_id)
    if state_id is not None:
        query = query.where(Task.state_id == state_id)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)) -> Task:
    return await _get_task_or_404(task_id, session)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int, payload: TaskUpdate, session: AsyncSession = Depends(get_session)
) -> Task:
    task = await _get_task_or_404(task_id, session)
    updates = payload.model_dump(exclude_unset=True)

    if "project_id" in updates:
        await _ensure_project_exists(updates["project_id"], session)
    if "state_id" in updates:
        await _ensure_state_exists(updates["state_id"], session)

    for field, value in updates.items():
        setattr(task, field, value)
    await session.commit()
    await session.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)) -> None:
    task = await _get_task_or_404(task_id, session)
    await session.delete(task)
    await session.commit()
