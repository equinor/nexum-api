import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.query_extensions import QueryExtensions
from src.repositories.base_repository import BaseRepository
from src.models import (
    Node,
)


class NodeRepository(BaseRepository[Node, uuid.UUID]):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session,
            Node,
            query_extension_method=QueryExtensions.load_node_with_relationships,
        )

    async def update(self, entities: list[Node]) -> list[Node]:
        entities_to_update = await self.get([node.id for node in entities])
        # sort the entity lists to share the same order according to the entity.id
        self.prepare_entities_for_update([entities, entities_to_update])

        for n, entity_to_update in enumerate(entities_to_update):
            entity = entities[n]
            entity_to_update.project_id = entity.project_id
            if entity.issue_id:
                entity_to_update.issue_id = entity.issue_id
            if entity.node_style and (entity.node_style != entity_to_update.node_style):
                entity_to_update.node_style = self._update_node_style(
                    entity.node_style, entity_to_update.node_style
                )

        await self.session.flush()
        return entities_to_update

    async def clear_discrete_probability_tables(self, ids: list[uuid.UUID]):

        entities = await self.get(ids)

        for entity in entities:
            if entity.issue.uncertainty is None:
                continue
            entity.issue.uncertainty.discrete_probabilities = []

        await self.session.flush()
