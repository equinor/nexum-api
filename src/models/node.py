import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from src.models.guid import GUID
from sqlalchemy.orm import (
    Mapped,
    relationship,
    mapped_column,
)
from src.models.base import Base
from src.models.base_entity import BaseEntity
from src.constants import DatabaseConstants

if TYPE_CHECKING:
    from src.models import Edge
    from src.models import Issue
    from src.models import NodeStyle
    from src.models import Project


class Node(Base, BaseEntity):
    __tablename__ = "node"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("project.id"), index=True)
    issue_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("issue.id"), index=True)

    name: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_SHORT_STRING_LENGTH.value), index=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="nodes")
    issue: Mapped["Issue"] = relationship(
        "Issue", back_populates="node", cascade="all, delete-orphan", single_parent=True
    )

    head_edges: Mapped[list["Edge"]] = relationship(
        "Edge",
        foreign_keys="[Edge.head_id]",
        back_populates="head_node",
        cascade="all, delete-orphan",
    )
    tail_edges: Mapped[list["Edge"]] = relationship(
        "Edge",
        foreign_keys="[Edge.tail_id]",
        back_populates="tail_node",
        cascade="all, delete-orphan",
    )

    node_style: Mapped["NodeStyle"] = relationship(
        "NodeStyle",
        back_populates="node",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    def __init__(
        self,
        id: uuid.UUID,
        project_id: uuid.UUID,
        name: str,
        issue_id: Optional[uuid.UUID],
        node_style: Optional["NodeStyle"],
    ):
        self.id = id

        self.project_id = project_id
        self.name = name

        if issue_id:
            self.issue_id = issue_id

        if node_style:
            self.node_style = node_style

    def head_neighbors(self) -> list["Node"]:
        try:
            return [x.head_node for x in self.head_edges]
        except Exception:
            return []

    def tail_neighbors(self) -> list["Node"]:
        try:
            return [x.tail_node for x in self.tail_edges]
        except Exception:
            return []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return False
        return (
            self.id == other.id
            and self.issue_id == other.issue_id
            and self.name == other.name
            and (
                self.node_style == other.node_style
                if self.node_style and other.node_style
                else self.node_style is other.node_style
            )
        )

    def __hash__(self) -> int:
        return hash(uuid.uuid4())
