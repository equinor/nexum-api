import uuid
from sqlalchemy.orm import joinedload, Session
from sqlalchemy.sql import select 
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.query_extensions import QueryExtensions
from src.repositories.base_repository import BaseRepository
from src.constants import Type
from src.models import (
    Node, 
    Issue,
)
from src.utils.session_info_handler import SessionInfo

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
            entity_to_update.scenario_id = entity.scenario_id
            if entity.issue_id:
                entity_to_update.issue_id = entity.issue_id
            if entity.node_style and (entity.node_style != entity_to_update.node_style):
                entity_to_update.node_style = self._update_node_style(entity.node_style, entity_to_update.node_style)

        await self.session.flush()
        return entities_to_update
    
    async def clear_discrete_probability_tables(self, ids: list[uuid.UUID]):
        
        entities = await self.get(ids)

        for entity in entities:
            if entity.issue.uncertainty is None: continue
            entity.issue.uncertainty.discrete_probabilities = []

        await self.session.flush()

def add_effected_session_enities_by_nodes(session: Session, head_ids: set[uuid.UUID], edge_tail_to_head_mapping: dict[uuid.UUID, uuid.UUID]) -> SessionInfo:
    """
    Adds affected session entities based on node relationships and edge mappings.
    This function analyzes nodes and their relationships to determine which entities
    should be included in the session info. It processes both direct head nodes and
    nodes connected through edge relationships, checking for valid tail nodes that
    might cause table resets.
    Args:
        session (Session): The database session for querying nodes.
        head_ids (set[uuid.UUID]): Set of head node IDs to process directly.
        edge_tail_to_head_mapping (dict[uuid.UUID, uuid.UUID]): Mapping of tail node IDs 
            to their corresponding head node IDs representing edge relationships.
    Returns:
        SessionInfo: Object containing the affected entities that should be included
            in the session based on the node analysis.
    """

    session_info = SessionInfo()
    
    # Collect all node IDs to query
    nodes_to_get: set[uuid.UUID] = set()
    nodes_to_get.update(head_ids)
    nodes_to_get.update(edge_tail_to_head_mapping.keys())
    nodes_to_get.update(edge_tail_to_head_mapping.values())

    query = select(Node).where(Node.id.in_(nodes_to_get)).options(
        joinedload(Node.issue).options(
            joinedload(Issue.utility),
            joinedload(Issue.decision),
            joinedload(Issue.uncertainty),
        )
    )

    entities = list((session.scalars(query)).unique().all())
    
    # Create a lookup map for quick access
    node_map = {entity.id: entity for entity in entities}

    # Check edge tails if they would cause table reset
    for tail_id, head_id in edge_tail_to_head_mapping.items():
        tail_node = node_map.get(tail_id)
        head_node = node_map.get(head_id)
        
        if tail_node and _is_valid_tail_node(tail_node):
            # If tail would cause reset, check if head is affected in the next loop
            if head_node:
                head_ids.add(head_node.id)

    # Check direct head IDs
    for head_id in head_ids:
        head_node = node_map.get(head_id)
        if head_node:
            # Add edge head if they can contain table that should be reset
            _add_affected_entity(session_info, head_node)

    return session_info

def _is_valid_tail_node(node: Node) -> bool:
    """Check if a node is a valid parent to a table"""
    if node.issue.type == Type.UNCERTAINTY.value and node.issue.uncertainty:
        return True
    elif node.issue.type == Type.DECISION.value and node.issue.decision:
        return True
    return False

def _add_affected_entity(session_info: SessionInfo, node: Node) -> None:
    """Add node if it is of a type that has a table"""
    if node.issue.type == Type.UNCERTAINTY.value and node.issue.uncertainty:
        session_info.affected_uncertainties.add(node.issue.uncertainty.id)
    elif node.issue.type == Type.UTILITY.value and node.issue.utility:
        session_info.affected_utilities.add(node.issue.utility.id)
