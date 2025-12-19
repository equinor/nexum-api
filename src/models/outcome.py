import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Float
from src.models.guid import GUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from src.models.base import Base
from src.models.base_entity import BaseEntity
from src.constants import DatabaseConstants

if TYPE_CHECKING:
    from src.models.discrete_probability import DiscreteProbabilityParentOutcome
    from src.models.discrete_utility import DiscreteUtilityParentOutcome

class Outcome(Base, BaseEntity):
    __tablename__ = "outcome"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    uncertainty_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("uncertainty.id"), index=True
    )

    name: Mapped[str] = mapped_column(
        String(DatabaseConstants.MAX_SHORT_STRING_LENGTH.value), default=""
    )

    utility: Mapped[float] = mapped_column(Float(), default=0.0)

    discrete_probability_parent_outcomes: Mapped[list["DiscreteProbabilityParentOutcome"]] = relationship(
        "DiscreteProbabilityParentOutcome",
        back_populates="parent_outcome",
        cascade="all, delete-orphan",
    )

    discrete_utility_parent_outcomes: Mapped[list["DiscreteUtilityParentOutcome"]] = relationship(
        "DiscreteUtilityParentOutcome",
        back_populates="parent_outcome",
        cascade="all, delete-orphan",
    )

    def __init__(
        self,
        id: uuid.UUID,
        uncertainty_id: uuid.UUID,
        name: str,
        utility: float,
    ):
        self.id = id
        self.uncertainty_id = uncertainty_id
        self.name = name
        self.utility = utility

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Outcome):
            return False
        return (
            self.id == other.id and
            self.uncertainty_id == other.uncertainty_id and
            self.name == other.name and
            self.utility == other.utility
        )

    def __hash__(self) -> int:
        return hash(uuid.uuid4())
