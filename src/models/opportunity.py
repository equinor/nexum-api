from typing import TYPE_CHECKING
import uuid
from sqlalchemy import String, ForeignKey
from src.models.guid import GUID
from sqlalchemy.orm import (
    Mapped,
    relationship,
    mapped_column,
)
from src.models.base import Base
from sqlalchemy.event import listens_for
from src.models.base_entity import BaseEntity
from src.models.base_auditable_entity import BaseAuditableEntity
from src.constants import DatabaseConstants

if TYPE_CHECKING:
    from src.models import Project


class Opportunity(Base, BaseEntity, BaseAuditableEntity):
    __tablename__ = "opportunity"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("project.id"), index=True)

    description: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_LONG_STRING_LENGTH.value), default=""
    )

    project: Mapped["Project"] = relationship(
        "Project",
        foreign_keys=[project_id],
        back_populates="opportunities",
    )

    def __init__(
        self,
        id: uuid.UUID,
        project_id: uuid.UUID,
        description: str,
        user_id: int,
    ):
        self.id = id

        self.project_id = project_id
        self.description = description
        self.updated_by_id = user_id

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


@listens_for(Opportunity, "before_insert")
def set_created_by_id(mapper, connection, target: Opportunity):  # type: ignore
    target.created_by_id = target.updated_by_id
