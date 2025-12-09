import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, FLOAT
from src.constants import DatabaseConstants
from src.models.guid import GUID
from sqlalchemy.orm import (
    Mapped,
    relationship,
    mapped_column,
)
from src.models.base import Base
from src.models.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.models import Node


class NodeStyle(Base, BaseEntity):
    __tablename__ = "node_style"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    node_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("node.id"), index=True)

    x_position: Mapped[float] = mapped_column(FLOAT(precision=DatabaseConstants.FLOAT_PRECISION.value))
    y_position: Mapped[float] = mapped_column(FLOAT(precision=DatabaseConstants.FLOAT_PRECISION.value))

    node: Mapped["Node"] = relationship("Node", back_populates="node_style")

    def __init__(
        self,
        id: uuid.UUID,
        node_id: Optional[uuid.UUID],
        x_position: float = 0.,
        y_position: float = 0.,
    ):
        self.id = id
        if node_id:
            self.node_id = node_id
        self.x_position = x_position
        self.y_position = y_position

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NodeStyle):
            return False
        return (
            self.id == other.id and
            self.node_id == other.node_id and
            self.x_position == other.x_position and
            self.y_position == other.y_position
        )

    def __hash__(self) -> int:
        return hash(uuid.uuid4())
