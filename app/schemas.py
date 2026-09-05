from pydantic import BaseModel, ConfigDict, field_validator


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None


def _normalize_title(value: str) -> str:
    # Recorta y rechaza el resultado vacío (cadena vacía o solo espacios
    # ASCII). El caso de invisibles Unicode se trabaja en la sesión 7
    # (docs/contrato-api.md:30-31), no aquí.
    normalized = value.strip()
    if not normalized:
        raise ValueError("El título no puede quedar vacío")
    return normalized


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    project_id: int
    state_id: int

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        return _normalize_title(value)


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    project_id: int | None = None
    state_id: int | None = None

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_title(value)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    project_id: int
    state_id: int
