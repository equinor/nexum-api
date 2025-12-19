import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, INT
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
from src.models.scenario import Scenario
from src.models.decision import Decision
from src.models.uncertainty import Uncertainty
from src.models.node import Node
from src.models.utility import Utility
from src.constants import (
    DatabaseConstants, 
    Type,
    Boundary,
)


class Issue(Base, BaseEntity, BaseAuditableEntity):
    __tablename__ = "issue"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(Scenario.id), index=True)

    type: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_SHORT_STRING_LENGTH.value),
        default=Type.UNASSIGNED.value,
    )
    boundary: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_SHORT_STRING_LENGTH.value), default=Boundary.OUT.value,
    )

    name: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_SHORT_STRING_LENGTH.value), index=True
    )
    description: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_LONG_STRING_LENGTH.value), default=""
    )
    order: Mapped[int] = mapped_column(INT, default=0)

    scenario: Mapped[Scenario] = relationship(
        Scenario, foreign_keys=[scenario_id], back_populates="issues"
    )

    node: Mapped[Node] = relationship(
        Node,
        back_populates="issue",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    decision: Mapped[Optional[Decision]] = relationship(
        Decision,
        back_populates="issue",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    uncertainty: Mapped[Optional[Uncertainty]] = relationship(
        Uncertainty,
        back_populates="issue",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    utility: Mapped[Optional[Utility]] = relationship(
        Utility,
        back_populates="issue",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    def __init__(
        self,
        id: uuid.UUID,
        scenario_id: uuid.UUID,
        type: str,
        name: str,
        description: str,
        boundary: str,
        order: int,
        user_id: int,
        node: Node,
        decision: Optional[Decision] = None,
        uncertainty: Optional[Uncertainty] = None,
        utility: Optional[Utility] = None,
    ):
        self.id = id
        self.scenario_id = scenario_id
        self.type = type
        self.name = name
        self.description = description
        self.boundary = boundary
        self.order = order
        self.updated_by_id = user_id
        self.node = node
        self.decision = decision
        self.uncertainty = uncertainty
        self.utility = utility


@listens_for(Issue, "before_insert")
def set_created_by_id(mapper, connection, target: Issue):  # type: ignore
    target.created_by_id = target.updated_by_id
