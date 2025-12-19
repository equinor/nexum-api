import uuid
from sqlalchemy import String
from src.models.guid import GUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from src.models.base_entity import BaseEntity
from src.models.base import Base

class ValueMetric(Base, BaseEntity):
    __tablename__ = "value_metric"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)

    name: Mapped[str] = mapped_column(String, default="")

    def __init__(self, id: uuid.UUID, name: str):
        self.id = id
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ValueMetric):
            return False
        return (
            self.id == other.id and
            self.name == other.name
        )

    def __hash__(self) -> int:
        return hash(uuid.uuid4())
