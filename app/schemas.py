from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


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


def _normalize_due_at(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("due_at debe incluir zona horaria")
    return value.astimezone(UTC)


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
    due_at: datetime | None = None
    priority: int | None = Field(default=None, ge=1, le=5)

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        return _normalize_title(value)

    @field_validator("due_at")
    @classmethod
    def _validate_due_at(cls, value: datetime | None) -> datetime | None:
        return _normalize_due_at(value)


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    project_id: int | None = None
    state_id: int | None = None
    due_at: datetime | None = None
    priority: int | None = Field(default=None, ge=1, le=5)

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_title(value)

    @field_validator("due_at")
    @classmethod
    def _validate_due_at(cls, value: datetime | None) -> datetime | None:
        return _normalize_due_at(value)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    project_id: int
    state_id: int
    due_at: datetime | None
    priority: int | None

    @field_serializer("due_at")
    def _serialize_due_at(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        utc_value = value.astimezone(UTC).replace(microsecond=0)
        return utc_value.isoformat().replace("+00:00", "Z")
