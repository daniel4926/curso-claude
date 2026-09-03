from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    sort_order: Mapped[int]
