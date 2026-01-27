from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import select
import uuid
from src.models import (
    Strategy,
    Option,
    Issue,
    Decision
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.base_repository import BaseRepository
from src.repositories.query_extensions import QueryExtensions


class StrategyRepository(BaseRepository[Strategy, uuid.UUID]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Strategy, query_extension_method=QueryExtensions.load_strategy)

    async def update(self, entities: list[Strategy]) -> list[Strategy]:
        entities_to_update = await self.get([strategy.id for strategy in entities])
        # sort the entity lists to share the same order according to the entity.id
        self.prepare_entities_for_update([entities, entities_to_update])


        for n, entity_to_update in enumerate(entities_to_update):
            entity = entities[n]
            await self._update_strategy(incoming_entity=entity, existing_entity=entity_to_update)

        await self.session.flush()
        return entities_to_update

def remove_options_out_of_scope(session: Session, issue_ids: set[uuid.UUID]):

    query = (
        select(Issue)
        .where(Issue.id.in_(issue_ids))
        .options(
            joinedload(Issue.decision).options(
                selectinload(Decision.options).options(
                    selectinload(Option.strategy_options)
                )
            )
        )
    )

    issues: list[Issue] = list((session.scalars(query)).unique().all())

    for issue in issues:
        if issue.decision and issue.decision.options:
            for option in issue.decision.options:
                for strategy_option in option.strategy_options:
                    session.delete(strategy_option)

    