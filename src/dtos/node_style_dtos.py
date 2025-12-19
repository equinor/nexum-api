import uuid
from pydantic import BaseModel, Field, field_validator

from src.models import NodeStyle
from src.constants import DtoConstants

class NodeStyleDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    node_id: uuid.UUID
    x_position: float = 0.
    y_position: float = 0.

    @field_validator('x_position')
    @classmethod
    def x_position_validator(cls, value: float) -> float:
        return round(value, DtoConstants.DECIMAL_PLACES.value)
    
    @field_validator('y_position')
    @classmethod
    def y_position_validator(cls, value: float) -> float:
        return round(value, DtoConstants.DECIMAL_PLACES.value)


class NodeStyleIncomingDto(NodeStyleDto):
    pass


class NodeStyleOutgoingDto(NodeStyleDto):
    pass


class NodeStyleMapper:
    @staticmethod
    def to_outgoing_dto(entity: NodeStyle) -> NodeStyleOutgoingDto:
        return NodeStyleOutgoingDto(
            id=entity.id,
            node_id=entity.node_id,
            x_position=entity.x_position,
            y_position=entity.y_position,
        )

    @staticmethod
    def to_entity(dto: NodeStyleIncomingDto) -> NodeStyle:
        return NodeStyle(
            id=dto.id,
            node_id=dto.node_id if dto.node_id else None,
            x_position=dto.x_position,
            y_position=dto.y_position,
        )

    @staticmethod
    def to_outgoing_dtos(
        entities: list[NodeStyle],
    ) -> list[NodeStyleOutgoingDto]:
        return [NodeStyleMapper.to_outgoing_dto(entity) for entity in entities]

    @staticmethod
    def to_entities(dtos: list[NodeStyleIncomingDto]) -> list[NodeStyle]:
        return [NodeStyleMapper.to_entity(dto) for dto in dtos]
