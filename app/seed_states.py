from sqlalchemy import Connection
from sqlalchemy.dialects.postgresql import insert

from app.models import State

STATE_CODES = ("PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA")


def seed_states(connection: Connection) -> None:
    rows = [
        {"code": code, "sort_order": order} for order, code in enumerate(STATE_CODES, start=1)
    ]
    stmt = insert(State).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=[State.code])
    connection.execute(stmt)
