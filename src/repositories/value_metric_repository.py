import uuid
from src.models.value_metric import ValueMetric
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.base_repository import BaseRepository
from src.repositories.query_extensions import QueryExtensions


class ValueMetricRepository(BaseRepository[ValueMetric, uuid.UUID]):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session,
            ValueMetric,
            query_extension_method=QueryExtensions.empty_load,
        )

    async def update(self, entities: list[ValueMetric]) -> list[ValueMetric]:
        entities_to_update = await self.get([value_metric.id for value_metric in entities])
        # sort the entity lists to share the same order according to the entity.id
        self.prepare_entities_for_update([entities, entities_to_update])

        for n, entity_to_update in enumerate(entities_to_update):
            entity = entities[n]
            entity_to_update.name = entity.name

        await self.session.flush()
        return entities_to_update
