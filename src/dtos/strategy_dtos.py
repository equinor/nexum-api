import uuid
from typing import Annotated
from pydantic import BaseModel, Field
from src.models import Strategy
from src.models import StrategyOption
from src.constants import DatabaseConstants
from src.dtos.option_dtos import OptionOutgoingDto, OptionIncomingDto, OptionMapper


class StrategyDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: Annotated[str, Field(max_length=DatabaseConstants.MAX_SHORT_STRING_LENGTH.value)] = ""
    description: Annotated[str, Field(max_length=DatabaseConstants.MAX_LONG_STRING_LENGTH.value)] = ""
    rationale: Annotated[str, Field(max_length=DatabaseConstants.MAX_LONG_STRING_LENGTH.value)] = ""
    
class StrategyIncomingDto(StrategyDto):
    project_id: uuid.UUID
    options: list[OptionIncomingDto] = []


class StrategyOutgoingDto(StrategyDto):
    project_id: uuid.UUID
    options: list[OptionOutgoingDto] = []


class StrategyMapper:
    @staticmethod
    def to_outgoing_dto(entity: Strategy) -> StrategyOutgoingDto:
        # Convert strategy_options to option DTOs through the relationship
        return StrategyOutgoingDto(
            id=entity.id,
            project_id=entity.project_id,
            name=entity.name,
            description=entity.description,
            rationale=entity.rationale,
            options=[
                OptionMapper.to_outgoing_dto(strategy_option.option) 
                for strategy_option in entity.strategy_options
            ] if entity.strategy_options else [],
        )

    @staticmethod
    def to_entity(dto: StrategyIncomingDto, user_id: int) -> Strategy:
        res = Strategy(
            id=dto.id,
            project_id=dto.project_id,
            name=dto.name,
            description=dto.description,
            rationale=dto.rationale,
            user_id=user_id,
            strategy_options = [
                StrategyOption(option_id=option.id, strategy_id=dto.id) 
                for option in dto.options
            ] 
        )
        return res

    @staticmethod
    def to_outgoing_dtos(entities: list[Strategy]) -> list[StrategyOutgoingDto]:
        return [StrategyMapper.to_outgoing_dto(entity) for entity in entities]

    @staticmethod
    def to_entities(dtos: list[StrategyIncomingDto], user_id: int) -> list[Strategy]:
        return [StrategyMapper.to_entity(dto, user_id) for dto in dtos]
