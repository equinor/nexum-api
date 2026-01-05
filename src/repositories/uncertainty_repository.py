import uuid
from typing import List, Optional
from itertools import product, chain
from src.models import Uncertainty, DiscreteProbability, DiscreteProbabilityParentOption, DiscreteProbabilityParentOutcome
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, Session
from sqlalchemy.sql import select
from src.repositories.base_repository import BaseRepository
from src.repositories.query_extensions import QueryExtensions
from src.constants import Type, DecisionHierarchy, Boundary

from src.models import Issue, Node, Edge, Decision, Uncertainty


def uncertainty_table_load_query(id: uuid.UUID):
    return select(Uncertainty).where(Uncertainty.id == id).options(
        selectinload(Uncertainty.outcomes),
        selectinload(Uncertainty.discrete_probabilities).options(
            selectinload(DiscreteProbability.parent_options),
            selectinload(DiscreteProbability.parent_outcomes),
        ),
        joinedload(Uncertainty.issue).options(
            joinedload(Issue.node).options(
                selectinload(Node.head_edges).options(
                    joinedload(Edge.tail_node).options(
                        joinedload(Node.issue)
                    )
                ),
            ),
            joinedload(Issue.uncertainty).options(
                selectinload(Uncertainty.outcomes)
            ),                    
            joinedload(Issue.decision).options(
                selectinload(Decision.options)
            ),            
        )
    )
    
def perform_recalc(entity: Uncertainty) -> Uncertainty:
    entity.discrete_probabilities = []

    parent_outcomes_list: List[List[uuid.UUID]] = []
    parent_options_list: List[List[uuid.UUID]] = []

    # filter out duplicate edges (fix later)
    edges = list({(edge.tail_id, edge.head_id): edge for edge in entity.issue.node.head_edges}.values())
    for edge in edges:
        issue = edge.tail_node.issue
        if not issue.boundary in [Boundary.IN.value, Boundary.ON.value]: continue

        if issue.type == Type.UNCERTAINTY:
            # check that this is a key uncertainty
            if not issue.uncertainty or not issue.uncertainty.is_key: continue
            parent_outcomes_list.append([x.id for x in issue.uncertainty.outcomes])

        elif issue.type == Type.DECISION:
            # check that the decision is in focus
            if not issue.decision or issue.decision.type != DecisionHierarchy.FOCUS.value: continue
            parent_options_list.append([x.id for x in issue.decision.options])

    # check if no valid edges and thus cannot be empty, but should be 1 row
    if len(parent_outcomes_list) == 0 and len(parent_options_list) == 0:
        entity.discrete_probabilities = [DiscreteProbability(id = uuid.uuid4(), uncertainty_id=entity.id, outcome_id=x.id, probability=0) for x in entity.outcomes]
        return entity
    
    parent_combinations = list(product(*parent_outcomes_list, *parent_options_list))
    # get all options and outcomes to filter on later
    all_options: List[uuid.UUID] = list(chain(*parent_options_list))
    all_outcomes: List[uuid.UUID] = list(chain(*parent_outcomes_list))

    for outcome in entity.outcomes:
        for parent_combination in parent_combinations:
            parent_option_ids = filter(lambda x: x in all_options, parent_combination)
            parent_outcome_ids = filter(lambda x: x in all_outcomes, parent_combination)
            probability_id = uuid.uuid4() 
            entity.discrete_probabilities.append(
                DiscreteProbability(
                    id = probability_id,
                    uncertainty_id=entity.id,
                    outcome_id=outcome.id,
                    probability=0,
                    parent_outcomes=[DiscreteProbabilityParentOutcome(discrete_probability_id=probability_id, parent_outcome_id=x) for x in parent_outcome_ids],
                    parent_options=[DiscreteProbabilityParentOption(discrete_probability_id=probability_id, parent_option_id=x) for x in parent_option_ids],
                )
            )

    return entity


class UncertaintyRepository(BaseRepository[Uncertainty, uuid.UUID]):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session,
            Uncertainty,
            query_extension_method=QueryExtensions.load_uncertainty_with_relationships,
        )

    async def update(self, entities: list[Uncertainty]) -> list[Uncertainty]:
        entities_to_update = await self.get([entity.id for entity in entities])
        # sort the entity lists to share the same order according to the entity.id
        self.prepare_entities_for_update([entities, entities_to_update])

        for n, entity_to_update in enumerate(entities_to_update):
            entity = entities[n]
            entity_to_update = await self._update_uncertainty(entity, entity_to_update)
            if entity.issue_id:
                entity_to_update.issue_id = entity.issue_id

        await self.session.flush()
        return entities_to_update

    async def clear_discrete_probability_tables(self, ids: list[uuid.UUID]):
        
        entities = await self.get(ids)

        for entity in entities:
            entity.discrete_probabilities = []

        await self.session.flush()

    async def recalculate_discrete_probability_table_async(self, id: uuid.UUID):
        query = uncertainty_table_load_query(id)
        entity: Uncertainty = (await self.session.scalars(query)).unique().first()
        if entity is None:
            return
        perform_recalc(entity)    
        await self.session.flush()

def recalculate_discrete_probability_table(session: Session, id: uuid.UUID) -> Optional[Uncertainty]:

    query = uncertainty_table_load_query(id)

    entity: Uncertainty = (session.scalars(query)).unique().first()
    if entity is not None:
        entity = perform_recalc(entity)
    return entity
