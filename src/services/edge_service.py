import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import (
    Edge,
    Node,
)
from src.dtos.edge_dtos import (
    EdgeMapper,
    EdgeIncomingDto,
    EdgeOutgoingDto,
)
from src.models.filters.edge_filter import EdgeFilter
from src.repositories.edge_repository import EdgeRepository
from src.repositories.node_repository import NodeRepository


class EdgeService:
    @staticmethod
    def _connect_nodes_to_edge(edge: Edge, tail_node: Node, head_node: Node):
        edge.tail_node, edge.head_node = tail_node, head_node
        return edge

    async def create(
        self, session: AsyncSession, dtos: list[EdgeIncomingDto]
    ) -> list[EdgeOutgoingDto]:
        entities: list[Edge] = await EdgeRepository(session).create(EdgeMapper.to_entities(dtos))
        # Get all unique node IDs (handles duplicates)
        all_node_ids = list({dto.tail_id for dto in dtos} | {dto.head_id for dto in dtos})
        nodes = await NodeRepository(session).get(all_node_ids)
        node_lookup: dict[uuid.UUID, Node] = {node.id: node for node in nodes}

        # Connect nodes using lookup (works with duplicate tail/head IDs)
        for edge in entities:
            tail_node = node_lookup.get(edge.tail_id)
            head_node = node_lookup.get(edge.head_id)
            if tail_node and head_node:
                self._connect_nodes_to_edge(edge, tail_node, head_node)

        result: list[EdgeOutgoingDto] = EdgeMapper.to_outgoing_dtos(entities)
        return result

    async def update(
        self, session: AsyncSession, dtos: list[EdgeIncomingDto]
    ) -> list[EdgeOutgoingDto]:
        entities: list[Edge] = await EdgeRepository(session).update(EdgeMapper.to_entities(dtos))
        # get the dtos while the entities are still connected to the session
        result: list[EdgeOutgoingDto] = EdgeMapper.to_outgoing_dtos(entities)
        return result

    async def delete(self, session: AsyncSession, ids: list[uuid.UUID]):
        await EdgeRepository(session).delete(ids)

    async def get(self, session: AsyncSession, ids: list[uuid.UUID]) -> list[EdgeOutgoingDto]:
        edges: list[Edge] = await EdgeRepository(session).get(ids)
        result = EdgeMapper.to_outgoing_dtos(edges)
        return result

    async def get_all(
        self,
        session: AsyncSession,
        odata_query: Optional[str] = None,
        filter: Optional[EdgeFilter] = None,
    ) -> list[EdgeOutgoingDto]:
        model_filter = filter.construct_filters() if filter else []
        edges: list[Edge] = await EdgeRepository(session).get_all(
            odata_query=odata_query, model_filter=model_filter
        )
        result = EdgeMapper.to_outgoing_dtos(edges)
        return result
