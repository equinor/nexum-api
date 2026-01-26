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
from datetime import datetime, timezone

if TYPE_CHECKING:
    from src.models import Project
    from src.models.stragegy_option import StrategyOption


class Strategy(Base, BaseEntity, BaseAuditableEntity):
    __tablename__ = "strategy"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("project.id"), index=True)

    name: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_SHORT_STRING_LENGTH.value),
        index=True,
        default="",
    )

    description: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_LONG_STRING_LENGTH.value), default=""
    )

    rationale: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_LONG_STRING_LENGTH.value), default=""
    )

    project: Mapped["Project"] = relationship(
        "Project",
        foreign_keys=[project_id],
        back_populates="strategies",
    )

    strategy_options: Mapped[list["StrategyOption"]] = relationship(
        "StrategyOption",
        back_populates="strategy",
        cascade="all, delete-orphan",
    )

    def __init__(
        self,
        id: uuid.UUID,
        project_id: uuid.UUID,
        description: str,
        rationale: str,
        name: str,
        user_id: int,
        strategy_options: list["StrategyOption"],
    ):
        self.id = id
        self.project_id = project_id
        self.name = name
        self.description = description
        self.rationale = rationale
        self.updated_by_id = user_id

        self.strategy_options = strategy_options

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


@listens_for(Strategy, "before_insert")
def set_created_by_id(mapper, connection, target: Strategy):  # type: ignore
    target.created_by_id = target.updated_by_id


@listens_for(Strategy, "before_update")
def receive_before_update(mapper, connection, target: Strategy):  # type: ignore
    target.updated_at = datetime.now(timezone.utc)  # Automatically update the timestamp
