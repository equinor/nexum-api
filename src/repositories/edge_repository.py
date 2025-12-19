from sqlalchemy.orm import joinedload, Session
from sqlalchemy.sql import select 
import uuid
from src.models.edge import Edge
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.base_repository import BaseRepository
from src.repositories.query_extensions import QueryExtensions
from src.constants import Type
from src.models import Issue, Node
from src.utils.session_info_handler import SessionInfo

class EdgeRepository(BaseRepository[Edge, uuid.UUID]):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session,
            Edge,
            query_extension_method=QueryExtensions.load_edge_with_relationships,
        )

    async def update(self, entities: list[Edge]) -> list[Edge]:
        entities_to_update = await self.get([edge.id for edge in entities])
        # sort the entity lists to share the same order according to the entity.id
        self.prepare_entities_for_update([entities, entities_to_update])

        for n, edge_to_update in enumerate(entities_to_update):
            edge = entities[n]
            if edge_to_update.tail_id != edge.tail_id:
                edge_to_update.tail_id = edge.tail_id
            if edge_to_update.head_id != edge.head_id:
                edge_to_update.head_id = edge.head_id
            if edge_to_update.scenario_id != edge.scenario_id:
                edge_to_update.scenario_id = edge.scenario_id
        await self.session.flush()
        return entities_to_update

def find_effected_session_entities(session: Session, ids: set[uuid.UUID]) -> SessionInfo:
    session_info = SessionInfo()
    query = select(Edge).where(Edge.id.in_(ids)).options(
        joinedload(Edge.tail_node),
        joinedload(Edge.head_node).options(
            joinedload(Node.issue).options(
                joinedload(Issue.uncertainty),
                joinedload(Issue.utility),
            )
        )
    )
    entities = list((session.scalars(query)).unique().all())

    for entity in entities:
        if (entity.head_node.issue.type == Type.UNCERTAINTY.value and entity.head_node.issue.uncertainty):
            session_info.affected_uncertainties.add(entity.head_node.issue.uncertainty.id)

        if (entity.head_node.issue.type == Type.UTILITY.value and entity.head_node.issue.utility):
            session_info.affected_utilities.add(entity.head_node.issue.utility.id)


    return session_info
