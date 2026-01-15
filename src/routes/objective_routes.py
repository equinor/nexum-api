import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.filters.objective_filter import ObjectiveFilter
from src.dtos.objective_dtos import ObjectiveIncomingDto, ObjectiveOutgoingDto
from src.services.objective_service import ObjectiveService
from src.dependencies import get_objective_service
from src.services.user_service import get_current_user
from src.dtos.user_dtos import UserIncomingDto
from src.constants import SwaggerDocumentationConstants
from src.dependencies import get_db


router = APIRouter(tags=["objectives"])


@router.post("/objectives")
async def create_objectives(
    dtos: list[ObjectiveIncomingDto],
    objective_service: ObjectiveService = Depends(get_objective_service),
    current_user: UserIncomingDto = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ObjectiveOutgoingDto]:
    try:
        result = list(await objective_service.create(session, dtos, current_user))
        await session.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/objectives/{id}")
async def get_objective(
    id: uuid.UUID,
    objective_service: ObjectiveService = Depends(get_objective_service),
    session: AsyncSession = Depends(get_db),
) -> ObjectiveOutgoingDto:
    try:
        objectives: list[ObjectiveOutgoingDto] = await objective_service.get(session, [id])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if len(objectives) > 0:
        return objectives[0]
    else:
        raise HTTPException(status_code=404)


@router.get("/objectives")
async def get_all_objective(
    objective_service: ObjectiveService = Depends(get_objective_service),
    filter: Optional[str] = Query(None, description=SwaggerDocumentationConstants.FILTER_DOC),
    session: AsyncSession = Depends(get_db),
) -> list[ObjectiveOutgoingDto]:
    try:
        objectives: list[ObjectiveOutgoingDto] = await objective_service.get_all(
            session, odata_query=filter
        )
        return objectives
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/objectives")
async def get_project_objective(
    project_id: uuid.UUID,
    objective_service: ObjectiveService = Depends(get_objective_service),
    filter: Optional[str] = Query(None, description=SwaggerDocumentationConstants.FILTER_DOC),
    session: AsyncSession = Depends(get_db),
) -> list[ObjectiveOutgoingDto]:
    try:
        objectives: list[ObjectiveOutgoingDto] = await objective_service.get_all(
            session, filter=ObjectiveFilter(project_ids=[project_id]), odata_query=filter
        )
        return objectives
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/objectives/{id}")
async def delete_objective(
    id: uuid.UUID,
    objective_service: ObjectiveService = Depends(get_objective_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        await objective_service.delete(session, [id])
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/objectives")
async def delete_objectives(
    ids: list[uuid.UUID] = Query([]),
    objective_service: ObjectiveService = Depends(get_objective_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        await objective_service.delete(session, ids)
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/objectives")
async def update_objectives(
    dtos: list[ObjectiveIncomingDto],
    objective_service: ObjectiveService = Depends(get_objective_service),
    current_user: UserIncomingDto = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ObjectiveOutgoingDto]:
    try:
        result = list(await objective_service.update(session, dtos, current_user))
        await session.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
