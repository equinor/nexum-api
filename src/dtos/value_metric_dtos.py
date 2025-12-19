import uuid
from pydantic import BaseModel, Field
from src.models.value_metric import ValueMetric


class ValueMetricDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str


class ValueMetricIncomingDto(ValueMetricDto):
    pass


class ValueMetricOutgoingDto(ValueMetricDto):
    pass


class ValueMetricMapper:
    @staticmethod
    def to_outgoing_dto(entity: ValueMetric) -> ValueMetricOutgoingDto:
        return ValueMetricOutgoingDto(id=entity.id, name=entity.name)

    @staticmethod
    def to_entity(dto: ValueMetricIncomingDto) -> ValueMetric:
        return ValueMetric(
            id=dto.id,
            name=dto.name,
        )

    @staticmethod
    def to_outgoing_dtos(
        entities: list[ValueMetric],
    ) -> list[ValueMetricOutgoingDto]:
        return [ValueMetricMapper.to_outgoing_dto(entity) for entity in entities]

    @staticmethod
    def to_entities(dtos: list[ValueMetricIncomingDto]) -> list[ValueMetric]:
        return [ValueMetricMapper.to_entity(dto) for dto in dtos]
