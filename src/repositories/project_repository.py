import uuid
from src.models.project import Project
from src.repositories.query_extensions import QueryExtensions
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.base_repository import BaseRepository
from src.repositories.strategy_repository import StrategyRepository
from src.repositories.objective_repository import ObjectiveRepository


class ProjectRepository(BaseRepository[Project, uuid.UUID]):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session,
            Project,
            query_extension_method=QueryExtensions.load_project_with_relationships,
        )

    async def update(self, entities: list[Project]) -> list[Project]:
        entities_to_update = await self.get([entity.id for entity in entities])
        # sort the entity lists to share the same order according to the entity.id
        self.prepare_entities_for_update([entities, entities_to_update])

        for n, entity_to_update in enumerate(entities_to_update):
            entity = entities[n]
            entity_to_update.name = entity.name
            entity_to_update.opportunityStatement = entity.opportunityStatement
            entity_to_update.project_role = await self._update_project_roles(
                entity.project_role, entity_to_update.project_role
            )
            entity_to_update.public = entity.public
            entity_to_update.end_date = entity.end_date
            await StrategyRepository(session=self.session).update(entity.strategies)
            await ObjectiveRepository(session=self.session).update(entity.objectives)
            
        await self.session.flush()
        return entities_to_update

    