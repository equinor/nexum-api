import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from src.models.discrete_probability import DiscreteProbability, DiscreteProbabilityParentOption, DiscreteProbabilityParentOutcome
from src.constants import DtoConstants

class DiscreteProbabilityDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    uncertainty_id: uuid.UUID
    outcome_id: uuid.UUID
    probability: Optional[float] = None
    parent_outcome_ids: List[uuid.UUID] = []
    parent_option_ids: List[uuid.UUID] = []

    @field_validator('probability')
    @classmethod
    def probability_validator(cls, value: Optional[float]) -> Optional[float]:
        """
        Ensures that the probability values fulfill the following conditions:
        1) Probabilities cannot be negative
        2) Probabilities have a decimal precision set by the global constant
        """
        if value is not None:
            return abs(round(value, DtoConstants.DECIMAL_PLACES.value))
        return value

class DiscreteProbabilityIncomingDto(DiscreteProbabilityDto):
    pass

class DiscreteProbabilityOutgoingDto(DiscreteProbabilityDto):
    pass

class DiscreteProbabilityMapper:
    @staticmethod
    def to_outgoing_dto(entity: DiscreteProbability) -> DiscreteProbabilityOutgoingDto:
        return DiscreteProbabilityOutgoingDto(
            id=entity.id,
            outcome_id=entity.outcome_id,
            uncertainty_id=entity.uncertainty_id,
            probability=entity.probability,
            parent_outcome_ids=[x.parent_outcome_id for x in entity.parent_outcomes] if entity.parent_outcomes else [],
            parent_option_ids=[x.parent_option_id for x in entity.parent_options] if entity.parent_options else [],
        )

    @staticmethod
    def to_entity(dto: DiscreteProbabilityIncomingDto) -> DiscreteProbability:
        return DiscreteProbability(
            id=dto.id,
            outcome_id=dto.outcome_id,
            uncertainty_id=dto.uncertainty_id,
            probability=dto.probability,
            parent_outcomes=[DiscreteProbabilityParentOutcome(discrete_probability_id=dto.id, parent_outcome_id=x) for x in dto.parent_outcome_ids],
            parent_options=[DiscreteProbabilityParentOption(discrete_probability_id=dto.id, parent_option_id=x) for x in dto.parent_option_ids]
        )

    @staticmethod
    def to_outgoing_dtos(entities: List[DiscreteProbability]) -> List[DiscreteProbabilityOutgoingDto]:
        return [DiscreteProbabilityMapper.to_outgoing_dto(entity) for entity in entities]

    @staticmethod
    def to_entities(dtos: List[DiscreteProbabilityIncomingDto]) -> List[DiscreteProbability]:
        return [DiscreteProbabilityMapper.to_entity(dto) for dto in dtos]