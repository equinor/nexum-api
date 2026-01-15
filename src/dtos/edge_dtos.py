import uuid
from pydantic import BaseModel, Field
from src.models.edge import Edge
from src.dtos.node_dtos import NodeMapper, NodeOutgoingDto


class EdgeDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    tail_id: uuid.UUID
    head_id: uuid.UUID
    project_id: uuid.UUID


class EdgeIncomingDto(EdgeDto):
    pass


class EdgeOutgoingDto(EdgeDto):
    head_node: NodeOutgoingDto
    tail_node: NodeOutgoingDto
    head_issue_id: uuid.UUID
    tail_issue_id: uuid.UUID


class EdgeMapper:
    @staticmethod
    def to_outgoing_dto(entity: Edge) -> EdgeOutgoingDto:
        return EdgeOutgoingDto(
            id=entity.id,
            tail_id=entity.tail_id,
            head_id=entity.head_id,
            project_id=entity.project_id,
            head_issue_id=entity.head_node.issue_id,
            tail_issue_id=entity.tail_node.issue_id,
            head_node=NodeMapper.to_outgoing_dto(entity.head_node),
            tail_node=NodeMapper.to_outgoing_dto(entity.tail_node),
        )

    @staticmethod
    def to_entity(dto: EdgeIncomingDto) -> Edge:
        return Edge(
            id=dto.id,
            tail_node_id=dto.tail_id,
            head_node_id=dto.head_id,
            project_id=dto.project_id,
        )

    @staticmethod
    def to_outgoing_dtos(entities: list[Edge]) -> list[EdgeOutgoingDto]:
        return [EdgeMapper.to_outgoing_dto(entity) for entity in entities]

    @staticmethod
    def to_entities(dtos: list[EdgeIncomingDto]) -> list[Edge]:
        return [EdgeMapper.to_entity(dto) for dto in dtos]
