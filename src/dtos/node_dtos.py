import uuid
from pydantic import BaseModel, Field
from typing import Optional, Annotated, TYPE_CHECKING
from src.models.node import Node
from src.constants import DatabaseConstants

from src.dtos.node_style_dtos import (
    NodeStyleMapper,
    NodeStyleIncomingDto,
    NodeStyleOutgoingDto,
)

if TYPE_CHECKING:
    from src.dtos.issue_dtos import IssueViaNodeOutgoingDto


class NodeDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    project_id: uuid.UUID
    issue_id: uuid.UUID
    name: Annotated[str, Field(max_length=DatabaseConstants.MAX_SHORT_STRING_LENGTH.value)] = ""


class NodeIncomingDto(NodeDto):
    node_style: Optional[NodeStyleIncomingDto]


class NodeOutgoingDto(NodeDto):
    issue: "IssueViaNodeOutgoingDto"
    node_style: NodeStyleOutgoingDto


class NodeViaIssueOutgoingDto(NodeDto):
    node_style: NodeStyleOutgoingDto


class NodeMapper:
    @staticmethod
    def to_outgoing_dto(entity: Node) -> NodeOutgoingDto:
        from src.dtos.issue_dtos import IssueMapper

        return NodeOutgoingDto(
            id=entity.id,
            issue_id=entity.issue_id,
            project_id=entity.project_id,
            name=entity.name,
            issue=IssueMapper.to_outgoing_dto_via_node(entity.issue),
            node_style=NodeStyleMapper.to_outgoing_dto(entity.node_style),
        )

    @staticmethod
    def to_outgoing_dto_via_issue(entity: Node) -> NodeViaIssueOutgoingDto:
        return NodeViaIssueOutgoingDto(
            id=entity.id,
            issue_id=entity.issue_id,
            project_id=entity.project_id,
            name=entity.name,
            node_style=NodeStyleMapper.to_outgoing_dto(entity.node_style),
        )

    @staticmethod
    def to_entity(dto: NodeIncomingDto) -> Node:
        return Node(
            id=dto.id,
            issue_id=dto.issue_id,
            project_id=dto.project_id,
            name=dto.name,
            node_style=NodeStyleMapper.to_entity(dto.node_style) if dto.node_style else None,
        )

    @staticmethod
    def to_outgoing_dtos(entities: list[Node]) -> list[NodeOutgoingDto]:
        return [NodeMapper.to_outgoing_dto(entity) for entity in entities]

    @staticmethod
    def to_entities(dtos: list[NodeIncomingDto]) -> list[Node]:
        return [NodeMapper.to_entity(dto) for dto in dtos]
