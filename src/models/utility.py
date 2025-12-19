import uuid
from typing import TYPE_CHECKING, Optional
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
    from src.models.issue import Issue
    from src.models.discrete_utility import DiscreteUtility


class Utility(Base, BaseEntity):
    __tablename__ = "utility"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    issue_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("issue.id"), index=True)

    issue: Mapped["Issue"] = relationship("Issue", back_populates="utility")
    discrete_utilities: Mapped[list["DiscreteUtility"]] = relationship(
        "DiscreteUtility",
        back_populates="utility",
        cascade="all, delete-orphan",
        foreign_keys="[DiscreteUtility.utility_id]"
    )

    def __init__(self, id: uuid.UUID, issue_id: uuid.UUID, discrete_utilities: Optional[list["DiscreteUtility"]] = None):
        self.id = id
        self.issue_id = issue_id
        if discrete_utilities is not None:
            self.discrete_utilities=discrete_utilities

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Utility):
            return False
        return (
            self.id == other.id and
            self.issue_id == other.issue_id and 
            len(self.discrete_utilities) == len(other.discrete_utilities) and
            all(dp1 == dp2 for dp1, dp2 in zip(sorted(self.discrete_utilities, key=lambda x: x.id), sorted(other.discrete_utilities, key=lambda x: x.id)))
        )

    def __hash__(self) -> int:
        return hash(uuid.uuid4())
