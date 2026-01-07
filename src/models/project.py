import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean
from src.models.guid import GUID
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy.event import listens_for
from typing import Optional, TYPE_CHECKING
from src.models.base import Base
from src.models.base_entity import BaseEntity
from src.models.base_auditable_entity import BaseAuditableEntity
from src.constants import DatabaseConstants

if TYPE_CHECKING:
    from src.models.project_role import ProjectRole
    from src.models.issue import Issue
    from src.models.node import Node
    from src.models.objective import Objective
    from src.models.opportunity import Opportunity
    from src.models.edge import Edge

from sqlalchemy import DateTime
from datetime import timedelta


def default_endtime() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=30)


class Project(Base, BaseEntity, BaseAuditableEntity):
    __tablename__ = "project"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    name: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_SHORT_STRING_LENGTH.value), index=True
    )
    parent_project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), nullable=True, index=True
    )
    parent_project_name: Mapped[Optional[str]] = mapped_column(
        String(DatabaseConstants.MAX_SHORT_STRING_LENGTH.value), default=""
    )
    opportunityStatement: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_LONG_STRING_LENGTH.value)
    )

    public: Mapped[bool] = mapped_column(Boolean, default=False)

    project_role: Mapped[list["ProjectRole"]] = relationship(
        "ProjectRole",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    opportunities: Mapped[list["Opportunity"]] = relationship(
        "Opportunity",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    objectives: Mapped[list["Objective"]] = relationship(
        "Objective",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    issues: Mapped[list["Issue"]] = relationship(
        "Issue",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    nodes: Mapped[list["Node"]] = relationship("Node", back_populates="project")

    edges: Mapped[list["Edge"]] = relationship(
        "Edge",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=default_endtime)

    def __init__(
        self,
        id: uuid.UUID,
        parent_project_id: Optional[uuid.UUID],
        parent_project_name: Optional[str],
        opportunityStatement: str,
        name: str,
        project_role: list["ProjectRole"],
        user_id: int,
        public: bool = False,
        end_date: datetime = default_endtime(),
    ):
        self.id = id
        self.parent_project_id = parent_project_id
        self.parent_project_name = parent_project_name
        self.project_role = project_role
        self.name = name
        self.opportunityStatement = opportunityStatement
        self.updated_by_id = user_id
        self.public = public
        self.end_date = end_date

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


@listens_for(Project, "before_insert")
def set_created_by_id(mapper, connection, target: Project):  # type: ignore
    target.created_by_id = target.updated_by_id
