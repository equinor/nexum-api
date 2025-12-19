import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base
from src.constants import DatabaseConstants
from src.models.base_entity import BaseEntity
from src.models.guid import GUID
if TYPE_CHECKING:
    from src.models.outcome import Outcome
    from src.models.option import Option
    from src.models.utility import Utility
    from src.models.value_metric import ValueMetric

class DiscreteUtilityParentOutcome(Base):
    __tablename__ = "discrete_utility_parent_outcome"
    discrete_utility_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("discrete_utility.id"), primary_key=True)
    parent_outcome_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("outcome.id", ondelete="CASCADE"), primary_key=True)

    discrete_utility: Mapped["DiscreteUtility"] = relationship("DiscreteUtility", back_populates="parent_outcomes")
    parent_outcome: Mapped["Outcome"] = relationship("Outcome")

    def __init__(self, discrete_utility_id: uuid.UUID, parent_outcome_id: uuid.UUID):
        self.discrete_utility_id = discrete_utility_id
        self.parent_outcome_id = parent_outcome_id

class DiscreteUtilityParentOption(Base):
    __tablename__ = "discrete_utility_parent_option"
    discrete_utility_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("discrete_utility.id"), primary_key=True)
    parent_option_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("option.id", ondelete="CASCADE"), primary_key=True)

    discrete_utility: Mapped["DiscreteUtility"] = relationship("DiscreteUtility", back_populates="parent_options")
    parent_option: Mapped["Option"] = relationship("Option")

    def __init__(self, discrete_utility_id: uuid.UUID, parent_option_id: uuid.UUID):
        self.discrete_utility_id = discrete_utility_id
        self.parent_option_id = parent_option_id

class DiscreteUtility(Base, BaseEntity):
    __tablename__ = "discrete_utility"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)

    value_metric_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("value_metric.id", ondelete="CASCADE"), index=True)
    utility_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("utility.id"), index=True) # cascade delete handled in utility model
    utility_value: Mapped[Optional[float]] = mapped_column(Float(precision=DatabaseConstants.FLOAT_PRECISION.value), default=None, nullable=True)

    value_metric: Mapped["ValueMetric"] = relationship("ValueMetric", foreign_keys=[value_metric_id])
    utility: Mapped["Utility"] = relationship("Utility", back_populates="discrete_utilities", foreign_keys=[utility_id])

    parent_outcomes: Mapped[list["DiscreteUtilityParentOutcome"]] = relationship(
        "DiscreteUtilityParentOutcome",
        back_populates="discrete_utility",
        cascade="all, delete-orphan"
    )

    parent_options: Mapped[list["DiscreteUtilityParentOption"]] = relationship(
        "DiscreteUtilityParentOption",
        back_populates="discrete_utility",
        cascade="all, delete-orphan"
    )

    def __init__(
        self,
        id: uuid.UUID,
        utility_id: uuid.UUID,
        value_metric_id: uuid.UUID,  
        utility_value: Optional[float] = None,
        parent_outcomes: Optional[list["DiscreteUtilityParentOutcome"]] = None,
        parent_options: Optional[list["DiscreteUtilityParentOption"]] = None,
    ):
        self.id = id
        self.utility_id = utility_id
        self.value_metric_id = value_metric_id  
        self.utility_value = utility_value
        self.parent_outcomes = parent_outcomes or []
        self.parent_options = parent_options or []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DiscreteUtility):
            return False
        return (
            self.id == other.id and
            self.utility_id == other.utility_id and
            self.value_metric_id == other.value_metric_id and 
            self.utility_value == other.utility_value and
            len(self.parent_outcomes) == len(other.parent_outcomes) and
            len(self.parent_options) == len(other.parent_options) and
            all(po1.parent_outcome_id == po2.parent_outcome_id for po1, po2 in zip(
                sorted(self.parent_outcomes, key=lambda x: x.parent_outcome_id), 
                sorted(other.parent_outcomes, key=lambda x: x.parent_outcome_id)
            )) and
            all(po1.parent_option_id == po2.parent_option_id for po1, po2 in zip(
                sorted(self.parent_options, key=lambda x: x.parent_option_id), 
                sorted(other.parent_options, key=lambda x: x.parent_option_id)
            ))
        )

    def __hash__(self) -> int:
        return hash(uuid.uuid4())
