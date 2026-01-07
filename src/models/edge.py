from typing import TYPE_CHECKING
import uuid
from sqlalchemy import ForeignKey
from src.models.guid import GUID
from sqlalchemy.orm import (
    Mapped,
    relationship,
    mapped_column,
)
from src.models.base import Base
from src.models.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.models.project import Project
    from src.models.node import Node


class Edge(Base, BaseEntity):
    __tablename__ = "edge"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)

    tail_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("node.id"), index=True)
    head_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("node.id"), index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("project.id"), index=True)

    project: Mapped["Project"] = relationship(
        "Project", foreign_keys=[project_id], back_populates="edges"
    )

    tail_node: Mapped["Node"] = relationship(
        "Node",
        foreign_keys=[tail_id],
        back_populates="tail_edges",
    )

    head_node: Mapped["Node"] = relationship(
        "Node",
        foreign_keys=[head_id],
        back_populates="head_edges",
    )

    def __init__(
        self,
        id: uuid.UUID,
        tail_node_id: uuid.UUID,
        head_node_id: uuid.UUID,
        project_id: uuid.UUID,
    ):
        self.id = id
        self.tail_id = tail_node_id
        self.head_id = head_node_id
        self.project_id = project_id
