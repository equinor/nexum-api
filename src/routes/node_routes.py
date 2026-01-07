import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession
from src.dtos.node_dtos import NodeIncomingDto, NodeOutgoingDto
from src.services.node_service import NodeService
from src.dependencies import get_node_service
from src.models.filters.node_filter import NodeFilter
from src.constants import SwaggerDocumentationConstants
from src.dependencies import get_db


router = APIRouter(tags=["nodes"])


@router.get("/nodes/{id}")
async def get_node(
    id: uuid.UUID,
    node_service: NodeService = Depends(get_node_service),
    session: AsyncSession = Depends(get_db),
) -> NodeOutgoingDto:
    try:
        nodes: list[NodeOutgoingDto] = await node_service.get(session, [id])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if len(nodes) > 0:
        return nodes[0]
    else:
        raise HTTPException(status_code=404)


@router.get("/nodes")
async def get_all_node(
    node_service: NodeService = Depends(get_node_service),
    filter: Optional[str] = Query(None, description=SwaggerDocumentationConstants.FILTER_DOC),
    session: AsyncSession = Depends(get_db),
) -> list[NodeOutgoingDto]:
    try:
        nodes: list[NodeOutgoingDto] = await node_service.get_all(session, odata_query=filter)
        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/nodes")
async def get_all_nodes_from_project(
    project_id: uuid.UUID,
    node_service: NodeService = Depends(get_node_service),
    filter: Optional[str] = Query(None, description=SwaggerDocumentationConstants.FILTER_DOC),
    session: AsyncSession = Depends(get_db),
) -> list[NodeOutgoingDto]:
    try:
        nodes: list[NodeOutgoingDto] = await node_service.get_all(
            session, NodeFilter(project_ids=[project_id]), odata_query=filter
        )
        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/nodes/{id}")
async def delete_node(
    id: uuid.UUID,
    node_service: NodeService = Depends(get_node_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        await node_service.delete(session, [id])
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/nodes")
async def delete_nodes(
    ids: list[uuid.UUID] = Query([]),
    node_service: NodeService = Depends(get_node_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        await node_service.delete(session, ids)
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/nodes")
async def update_nodes(
    dtos: list[NodeIncomingDto],
    node_service: NodeService = Depends(get_node_service),
    session: AsyncSession = Depends(get_db),
) -> list[NodeOutgoingDto]:
    try:
        result = list(await node_service.update(session, dtos))
        await session.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
