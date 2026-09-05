from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Project, Task
from app.schemas import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


async def _get_project_or_404(project_id: int, session: AsyncSession) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"El proyecto {project_id} no existe")
    return project


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(
    payload: ProjectCreate, session: AsyncSession = Depends(get_session)
) -> Project:
    project = Project(name=payload.name, description=payload.description)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
async def list_projects(session: AsyncSession = Depends(get_session)) -> list[Project]:
    result = await session.execute(select(Project).order_by(Project.id))
    return list(result.scalars().all())


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int, session: AsyncSession = Depends(get_session)
) -> Project:
    return await _get_project_or_404(project_id, session)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
) -> Project:
    project = await _get_project_or_404(project_id, session)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await session.commit()
    await session.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, session: AsyncSession = Depends(get_session)) -> None:
    project = await _get_project_or_404(project_id, session)

    has_tasks = (
        await session.execute(select(Task.id).where(Task.project_id == project_id).limit(1))
    ).first() is not None
    if has_tasks:
        raise HTTPException(
            status_code=409, detail=f"El proyecto {project_id} tiene tareas asociadas"
        )

    await session.delete(project)
    await session.commit()
