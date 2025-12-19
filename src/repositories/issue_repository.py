import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import select
from src.models import (
    Issue,
    Edge,
    Node,
)
from src.repositories.query_extensions import QueryExtensions
from src.repositories.base_repository import BaseRepository
from src.constants import Type
from src.utils.session_info_handler import SessionInfo

class IssueRepository(BaseRepository[Issue, uuid.UUID]):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session,
            Issue,
            query_extension_method=QueryExtensions.load_issue_with_relationships,
        )

    async def update(self, entities: list[Issue]) -> list[Issue]:
        entities_to_update = await self.get([decision.id for decision in entities])
        # sort the entity lists to share the same order according to the entity.id
        self.prepare_entities_for_update([entities, entities_to_update])

        for n, entity_to_update in enumerate(entities_to_update):
            entity = entities[n]
            
            if entity_to_update.scenario_id != entity.scenario_id:
                entity_to_update.scenario_id = entity.scenario_id

            if entity_to_update.type != entity.type:
                entity_to_update.type = entity.type

            if entity_to_update.boundary != entity.boundary:
                entity_to_update.boundary = entity.boundary

            if entity_to_update.name != entity.name:
                entity_to_update.name = entity.name

            if entity_to_update.description != entity.description:
                entity_to_update.description = entity.description

            if entity_to_update.order != entity.order:
                entity_to_update.order = entity.order

            if entity.node and (entity_to_update.node != entity.node):
                entity_to_update.node = self._update_node(entity.node, entity_to_update.node)

            if entity.decision and (entity_to_update.decision != entity.decision):
                entity_to_update.decision = await self._update_decision(entity.decision, entity_to_update.decision)

            if entity.uncertainty and entity_to_update.uncertainty and (entity_to_update.uncertainty != entity.uncertainty):
                entity_to_update.uncertainty = await self._update_uncertainty(entity.uncertainty, entity_to_update.uncertainty)

            if entity.utility and (entity_to_update.utility != entity.utility):
                entity_to_update.utility = await self._update_utility(entity.utility, entity_to_update.utility)

        await self.session.flush()
            
        return entities_to_update
    
    async def clear_discrete_probability_tables(self, ids: list[uuid.UUID]):
        
        entities = await self.get(ids)

        for entity in entities:
            if entity.uncertainty is None: continue
            entity.uncertainty.discrete_probabilities = []

        await self.session.flush()


def find_effected_session_entities(session: Session, issue_ids: set[uuid.UUID]) -> SessionInfo:
    session_info = SessionInfo()

    query = select(Issue).where(Issue.id.in_(issue_ids)).options(
        joinedload(Issue.node).options(
            selectinload(Node.tail_edges).options(
                joinedload(Edge.head_node).options(
                    joinedload(Node.issue).options(
                        joinedload(Issue.utility),
                        joinedload(Issue.uncertainty),
                    )
                )
            )
        )
    )

    issues: list[Issue] = list((session.scalars(query)).unique().all())

    for issue in issues:
        for edge in issue.node.tail_edges:
            if edge.head_node.issue.type == Type.UNCERTAINTY.value and edge.head_node.issue.uncertainty:
                session_info.affected_uncertainties.add(edge.head_node.issue.uncertainty.id)
            if edge.head_node.issue.type == Type.UTILITY.value and edge.head_node.issue.utility:
                session_info.affected_utilities.add(edge.head_node.issue.utility.id)

    return session_info