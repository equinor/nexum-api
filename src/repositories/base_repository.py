import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import ColumnElement, Select, select, desc
from sqlalchemy.orm.strategy_options import _AbstractLoad  # type: ignore
from typing import (
    Type,
    TypeVar,
    Generic,
    List,
    Protocol,
    Callable,
    Union,
    Optional,
    Tuple,
    cast,
)
from odata_query.sqlalchemy.shorthand import apply_odata_query
from src.constants import PageSize
from src.models import (
    Uncertainty,
    Utility,
    Decision,
    Node,
    NodeStyle,
    StrategyOption,
    Strategy,
    Outcome,
    Option,
    DiscreteProbability,
    ProjectRole,
)

LoadOptions = List[_AbstractLoad]


class AlchemyModel(Protocol):
    id: InstrumentedAttribute[Union[int, uuid.UUID]]
    created_at: InstrumentedAttribute[datetime]
    updated_at: InstrumentedAttribute[datetime]


T = TypeVar("T", bound=AlchemyModel)
IDType = TypeVar("IDType", int, uuid.UUID)


class BaseRepository(Generic[T, IDType]):
    def __init__(
        self,
        session: AsyncSession,
        model: Type[T],
        query_extension_method: Callable[[], LoadOptions],
    ):
        self.session = session
        self.model = model
        self.query_extension_method = query_extension_method

    async def create(self, entities: List[T]) -> List[T]:
        self.session.add_all(entities)
        await self.session.flush()
        return entities

    async def create_single(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get(self, ids: List[IDType]) -> List[T]:
        query = (
            select(self.model).where(self.model.id.in_(ids)).options(*self.query_extension_method())
        )
        return list((await self.session.scalars(query)).unique().all())

    async def get_all(
        self,
        model_filter: List[ColumnElement[bool]] = [],
        odata_query: Optional[str] = None,
        skip: int = 0,
        take: int = PageSize.DEFAULT,
    ) -> List[T]:
        query = select(self.model).options(*self.query_extension_method())
        if len(model_filter) != 0:
            query = query.filter(*model_filter)
        if odata_query is not None:
            query = cast(Select[Tuple[T]], apply_odata_query(query, odata_query))
        query = query.order_by(desc(self.model.created_at)).offset(skip).limit(take)
        return list((await self.session.scalars(query)).unique().all())

    async def delete(self, ids: List[IDType]) -> None:
        entities = await self.get(ids)
        for entity in entities:
            await self.session.delete(entity)

        await self.session.flush()

    async def update(self, entities: List[T]) -> List[T]:
        raise NotImplementedError("Subclasses must implement update_entity method.")

    @staticmethod
    def _check_update_entity_ids_match(entity_lists: List[List[T]]):
        """
        For update operations: checks that all entity lists have the same ids in the same order.
        Raises ValueError if not. Only intended for use in update methods.
        """
        if len(entity_lists) < 2:
            return
        ids_list = [[entity.id for entity in entity_list] for entity_list in entity_lists]
        if not all(ids == ids_list[0] for ids in ids_list):
            raise ValueError(
                "Entity lists do not have matching ids. Possible missing or extra entities during update."
            )

    @classmethod
    def prepare_entities_for_update(cls, entity_lists: List[List[T]]):
        """
        For update operations: sorts all entity lists by id and checks that their ids match.
        Only intended for use in update methods.
        """
        cls.sort_entity_collections_by_id(entity_lists)
        cls._check_update_entity_ids_match(entity_lists)

    @staticmethod
    def sort_entity_collections_by_id(entity_lists: List[List[T]]):
        for entity_list in entity_lists:
            entity_list.sort(key=lambda entity: entity.id)

    async def _update_uncertainty(
        self, incoming_entity: Uncertainty, existing_entity: Uncertainty
    ) -> Uncertainty:
        """
        Selective update of an existing Uncertainty entity with data from an incoming Uncertainty entity.
        """

        existing_entity.is_key = incoming_entity.is_key
        if incoming_entity.issue_id:
            existing_entity.issue_id = incoming_entity.issue_id

        if existing_entity.outcomes != incoming_entity.outcomes:
            existing_entity.outcomes = await self._update_outcomes(
                incoming_entity.outcomes, existing_entity.outcomes
            )

        # Create a map of incoming discrete probabilities by ID for efficient lookup
        incoming_dps_by_id = {dp.id: dp for dp in incoming_entity.discrete_probabilities}
        if (
            existing_entity.discrete_probabilities.__len__()
            != incoming_entity.discrete_probabilities.__len__()
        ):
            existing_entity.discrete_probabilities = incoming_entity.discrete_probabilities
        else:
            for existing_dp in existing_entity.discrete_probabilities:
                if existing_dp.id in incoming_dps_by_id:
                    incoming_dp = incoming_dps_by_id[existing_dp.id]
                    # Only update the probability field
                    if existing_dp.probability != incoming_dp.probability:
                        existing_dp.probability = incoming_dp.probability
            # If no match, ignore and leave existing discrete probability unchanged

        return existing_entity

    async def _update_utility(self, incoming_entity: Utility, existing_entity: Utility) -> Utility:
        """
        Selective update of an existing Utility entity with data from an incoming Utility entity.
        """

        if incoming_entity.issue_id:
            existing_entity.issue_id = incoming_entity.issue_id

        # Create a map of incoming discrete utilities by ID for efficient lookup
        incoming_dps_by_id = {dp.id: dp for dp in incoming_entity.discrete_utilities}

        for existing_dp in existing_entity.discrete_utilities:
            if existing_dp.id in incoming_dps_by_id:
                incoming_dp = incoming_dps_by_id[existing_dp.id]
                # Only update the utility_value field
                if existing_dp.utility_value != incoming_dp.utility_value:
                    existing_dp.utility_value = incoming_dp.utility_value
            # If no match, ignore and leave existing discrete utility unchanged

        return existing_entity

    async def _update_outcome(self, incoming_entity: Outcome, existing_entity: Outcome) -> Outcome:
        existing_entity.name = incoming_entity.name
        existing_entity.utility = incoming_entity.utility
        return existing_entity

    async def _update_option(self, incoming_entity: Option, existing_entity: Option) -> Option:
        existing_entity.name = incoming_entity.name
        existing_entity.utility = incoming_entity.utility
        return existing_entity

    async def _update_outcomes(
        self, incoming_entities: List[Outcome], existing_entities: List[Outcome]
    ):
        """
        Updates existing_entities to match incoming_entities by:
        - Updating outcomes that exist in both lists (matched by id)
        - Creating new outcomes from incoming that don't exist in existing
        - Deleting outcomes from existing that aren't in incoming
        """
        incoming_by_id = {outcome.id: outcome for outcome in incoming_entities}
        existing_by_id = {outcome.id: outcome for outcome in existing_entities}

        # Update existing outcomes that are in incoming
        common_ids = set(existing_by_id.keys()) & set(incoming_by_id.keys())
        await asyncio.gather(
            *[
                self._update_outcome(incoming_by_id[outcome_id], existing_by_id[outcome_id])
                for outcome_id in common_ids
            ]
        )

        # Delete outcomes that are in existing but not in incoming
        outcomes_to_delete = [
            outcome for outcome in existing_entities if outcome.id not in incoming_by_id
        ]
        if outcomes_to_delete:
            # delete discrete probabilities using ORM to trigger cascade delete operation
            outcome_ids_to_delete = [outcome.id for outcome in outcomes_to_delete]
            discrete_probs = await self.session.scalars(
                select(DiscreteProbability).where(
                    DiscreteProbability.outcome_id.in_(outcome_ids_to_delete)
                )
            )
            await asyncio.gather(*[self.session.delete(dp) for dp in discrete_probs])

            # Remove outcomes from existing_entities list and delete from session
            [existing_entities.remove(outcome) for outcome in outcomes_to_delete]
            await asyncio.gather(*[self.session.delete(outcome) for outcome in outcomes_to_delete])

        # Create new outcomes that are in incoming but not in existing
        new_outcomes = [
            outcome for outcome in incoming_entities if outcome.id not in existing_by_id
        ]
        if new_outcomes:
            existing_entities.extend(new_outcomes)
            [self.session.add(outcome) for outcome in new_outcomes]

        return existing_entities

    async def _update_options(
        self, incoming_entities: List[Option], existing_entities: List[Option]
    ):
        """
        Updates existing_entities to match incoming_entities by:
        - Updating options that exist in both lists (matched by id)
        - Creating new options from incoming that don't exist in existing
        - Deleting options from existing that aren't in incoming
        """
        incoming_by_id = {option.id: option for option in incoming_entities}
        existing_by_id = {option.id: option for option in existing_entities}

        # Update existing options that are in incoming
        common_ids = set(existing_by_id.keys()) & set(incoming_by_id.keys())
        await asyncio.gather(
            *[
                self._update_option(incoming_by_id[option_id], existing_by_id[option_id])
                for option_id in common_ids
            ]
        )

        # Delete options that are in existing but not in incoming
        options_to_delete = [
            option for option in existing_entities if option.id not in incoming_by_id
        ]
        if options_to_delete:
            # Remove options from existing_entities list and delete from session
            [existing_entities.remove(option) for option in options_to_delete]
            await asyncio.gather(*[self.session.delete(option) for option in options_to_delete])

        # Create new options that are in incoming but not in existing
        new_options = [option for option in incoming_entities if option.id not in existing_by_id]
        if new_options:
            existing_entities.extend(new_options)
            [self.session.add(option) for option in new_options]

        return existing_entities

    async def _update_decision(
        self, incoming_entity: Decision, existing_entity: Decision
    ) -> Decision:
        existing_entity.type = incoming_entity.type
        if existing_entity.options != incoming_entity.options:
            existing_entity.options = await self._update_options(
                incoming_entity.options, existing_entity.options
            )
        return existing_entity
    
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
    
    async def _update_strategy(self, incoming_entity: Strategy, existing_entity: Strategy):
        existing_entity.project_id = incoming_entity.project_id
        existing_entity.name = incoming_entity.name
        existing_entity.description = incoming_entity.description
        existing_entity.rationale = incoming_entity.rationale
        existing_entity.updated_by_id = incoming_entity.updated_by_id

        # Clear existing strategy options and create new ones
        # This ensures we only manage the relationship without updating Option or Strategy entities
        await self._replace_strategy_options(existing_entity, incoming_entity.strategy_options)
    
    async def _update_strategies(
        self, incoming_entities: list[Strategy], existing_entities: list[Strategy]
    ):
        """
        Updates existing_entities to match incoming_entities by:
        - Updating strategies that exist in both lists (matched by id)
        - Creating new strategies from incoming that don't exist in existing
        - Deleting strategies from existing that aren't in incoming
        """
        incoming_by_id = {strategy.id: strategy for strategy in incoming_entities}
        existing_by_id = {strategy.id: strategy for strategy in existing_entities}

        # Update existing strategies that are in incoming
        common_ids = set(existing_by_id.keys()) & set(incoming_by_id.keys())
        await asyncio.gather(
            *[
                self._update_strategy(
                    incoming_entity=incoming_by_id[strategy_id], 
                    existing_entity=existing_by_id[strategy_id],
                )
                for strategy_id in common_ids
            ]
        )

        # Delete strategies that are in existing but not in incoming
        strategies_to_delete = [
            strategy for strategy in existing_entities if strategy.id not in incoming_by_id
        ]
        if strategies_to_delete:

            # Remove strategies from existing_entities list and delete from session
            [existing_entities.remove(strategy) for strategy in strategies_to_delete]
            await asyncio.gather(*[self.session.delete(strategy) for strategy in strategies_to_delete])

        # Create new strategies that are in incoming but not in existing
        new_strategies = [
            strategy for strategy in incoming_entities if strategy.id not in existing_by_id
        ]
        if new_strategies:
            existing_entities.extend(new_strategies)
            [self.session.add(strategy) for strategy in new_strategies]

        return existing_entities

    def _update_node(self, incoming_entity: Node, existing_entity: Node):
        existing_entity.name = incoming_entity.name
        if incoming_entity.node_style and (
            existing_entity.node_style != incoming_entity.node_style
        ):
            existing_entity.node_style = self._update_node_style(
                incoming_entity.node_style, existing_entity.node_style
            )
        return existing_entity

    
    async def _update_project_roles(
        self, incoming_entities: list[ProjectRole], existing_entities: list[ProjectRole]
    ):
        """
        Updates existing_entities to match incoming_entities by:
        - Updating project roles that exist in both lists (matched by id)
        - Creating new project roles from incoming that don't exist in existing
        - Deleting project roles from existing that aren't in incoming
        """
        
        incoming_by_id = {role.id: role for role in incoming_entities}
        existing_by_id = {role.id: role for role in existing_entities}

        # Update existing project roles that are in incoming
        common_ids = set(existing_by_id.keys()) & set(incoming_by_id.keys())
        for role_id in common_ids:
            existing_role = existing_by_id[role_id]
            incoming_role = incoming_by_id[role_id]
            existing_role.role = incoming_role.role
            existing_role.user_id = incoming_role.user_id

        # Delete project roles that are in existing but not in incoming
        roles_to_delete = [
            role for role in existing_entities if role.id not in incoming_by_id
        ]
        if roles_to_delete:
            for role in roles_to_delete:
                existing_entities.remove(role)
                await self.session.delete(role)

        # Create new project roles that are in incoming but not in existing
        new_roles = [
            role for role in incoming_entities if role.id not in existing_by_id
        ]
        if new_roles:
            existing_entities.extend(new_roles)
            for role in new_roles:
                self.session.add(role)
                # ensure that the user is not updated or created while updating the role assignment
                self.session.expunge(role.user)

        return existing_entities


    @staticmethod
    def _update_node_style(incoming_entity: NodeStyle, existing_entity: NodeStyle):
        existing_entity.x_position = incoming_entity.x_position
        existing_entity.y_position = incoming_entity.y_position
        return existing_entity
