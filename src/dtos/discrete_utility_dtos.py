import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from src.models import DiscreteUtility, DiscreteUtilityParentOption, DiscreteUtilityParentOutcome
from src.constants import default_value_metric_id

class DiscreteUtilityDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    utility_id: uuid.UUID
    value_metric_id: uuid.UUID = default_value_metric_id
    utility_value: Optional[float] = None
    parent_outcome_ids: List[uuid.UUID] = []
    parent_option_ids: List[uuid.UUID] = []

class DiscreteUtilityIncomingDto(DiscreteUtilityDto):
    pass

class DiscreteUtilityOutgoingDto(DiscreteUtilityDto):
    pass

class DiscreteUtilityMapper:
    @staticmethod
    def to_outgoing_dto(entity: DiscreteUtility) -> DiscreteUtilityOutgoingDto:
        return DiscreteUtilityOutgoingDto(
            id=entity.id,
            value_metric_id=default_value_metric_id,
            utility_id=entity.utility_id,
            utility_value=entity.utility_value,
            parent_outcome_ids=[x.parent_outcome_id for x in entity.parent_outcomes] if entity.parent_outcomes else [],
            parent_option_ids=[x.parent_option_id for x in entity.parent_options] if entity.parent_options else [],
        )

    @staticmethod
    def to_entity(dto: DiscreteUtilityIncomingDto) -> DiscreteUtility:
        return DiscreteUtility(
            id=dto.id,
            value_metric_id=default_value_metric_id,
            utility_id=dto.utility_id,
            utility_value=dto.utility_value,
            parent_outcomes=[DiscreteUtilityParentOutcome(discrete_utility_id=dto.id, parent_outcome_id=x) for x in dto.parent_outcome_ids],
            parent_options=[DiscreteUtilityParentOption(discrete_utility_id=dto.id, parent_option_id=x) for x in dto.parent_option_ids]
        )

    @staticmethod
    def to_outgoing_dtos(entities: List[DiscreteUtility]) -> List[DiscreteUtilityOutgoingDto]:
        return [DiscreteUtilityMapper.to_outgoing_dto(entity) for entity in entities]

    @staticmethod
    def to_entities(dtos: List[DiscreteUtilityIncomingDto]) -> List[DiscreteUtility]:
        return [DiscreteUtilityMapper.to_entity(dto) for dto in dtos]