from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import select
import uuid
from src.models import (
    Strategy,
    Option,
    StrategyOption,
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
            entity_to_update.project_id = entity.project_id
            entity_to_update.name = entity.name
            entity_to_update.description = entity.description
            entity_to_update.rationale = entity.rationale
            entity_to_update.updated_by_id = entity.updated_by_id

            # Clear existing strategy options and create new ones
            # This ensures we only manage the relationship without updating Option or Strategy entities
            await self._replace_strategy_options(entity_to_update, entity.strategy_options)
            

        await self.session.flush()
        return entities_to_update

    async def _replace_strategy_options(self, strategy_to_update: Strategy, new_strategy_options: list[StrategyOption]) -> None:
        """
        Safely replace strategy options by managing only the StrategyOption join table relationships.
        This approach prevents any updates to Option or Strategy entities themselves.
        """
        strategy_to_update.strategy_options.clear()
        
        for new_strategy_option in new_strategy_options:
            strategy_option_to_add = StrategyOption(
                strategy_id=strategy_to_update.id,
                option_id=new_strategy_option.option_id
            )
            self.session.add(strategy_option_to_add)
            strategy_to_update.strategy_options.append(strategy_option_to_add)

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

    