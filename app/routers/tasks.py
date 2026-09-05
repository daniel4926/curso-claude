from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Project, State, Task
from app.schemas import TaskCreate, TaskRead

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _ensure_project_exists(project_id: int, session: AsyncSession) -> None:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=422, detail=f"El proyecto {project_id} no existe")


async def _ensure_state_exists(state_id: int, session: AsyncSession) -> None:
    state = await session.get(State, state_id)
    if state is None:
        raise HTTPException(status_code=422, detail=f"El estado {state_id} no existe")


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
