import pytest
from pydantic import ValidationError

from app.schemas import TaskCreate, TaskUpdate


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
