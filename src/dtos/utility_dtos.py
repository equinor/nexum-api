import uuid
from pydantic import BaseModel, Field
from src.models.utility import Utility
from src.dtos.discrete_utility_dtos import (
    DiscreteUtilityIncomingDto,
    DiscreteUtilityOutgoingDto,
    DiscreteUtilityMapper,
)

class UtilityDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    issue_id: uuid.UUID


class UtilityIncomingDto(UtilityDto):
    discrete_utilities: list[DiscreteUtilityIncomingDto]


class UtilityOutgoingDto(UtilityDto):
    discrete_utilities: list[DiscreteUtilityOutgoingDto]


class UtilityMapper:
    @staticmethod
    def to_outgoing_dto(entity: Utility) -> UtilityOutgoingDto:
        return UtilityOutgoingDto(
            id=entity.id,
            issue_id=entity.issue_id,
            discrete_utilities=DiscreteUtilityMapper.to_outgoing_dtos(entity.discrete_utilities),
        )

    @staticmethod
    def to_entity(dto: UtilityIncomingDto) -> Utility:
        return Utility(
            id=dto.id,
            issue_id=dto.issue_id,
            discrete_utilities=DiscreteUtilityMapper.to_entities(dto.discrete_utilities),
        )

    @staticmethod
    def to_outgoing_dtos(entities: list[Utility]) -> list[UtilityOutgoingDto]:
        return [UtilityMapper.to_outgoing_dto(entity) for entity in entities]

    @staticmethod
    def to_entities(dtos: list[UtilityIncomingDto]) -> list[Utility]:
        return [UtilityMapper.to_entity(dto) for dto in dtos]
