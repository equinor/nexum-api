import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession
from src.dtos.discrete_utility_dtos import (
    DiscreteUtilityIncomingDto,
    DiscreteUtilityOutgoingDto,
)
from src.services.discrete_utility_service import DiscreteUtilityService
from src.dependencies import get_discrete_utility_service
from src.constants import SwaggerDocumentationConstants
from src.dependencies import get_db


router = APIRouter(tags=["discrete_utilities"])


@router.get("/discrete_utilities/{id}")
async def get_discrete_utility(
    id: uuid.UUID,
    discrete_utility_service: DiscreteUtilityService = Depends(get_discrete_utility_service),
    session: AsyncSession = Depends(get_db),
) -> DiscreteUtilityOutgoingDto:
    try:
        discrete_utilities: list[DiscreteUtilityOutgoingDto] = await discrete_utility_service.get(session, [id])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if len(discrete_utilities) > 0:
        return discrete_utilities[0]
    else:
        raise HTTPException(status_code=404)


@router.get("/discrete_utilities")
async def get_all_discrete_utility(
    discrete_utility_service: DiscreteUtilityService = Depends(get_discrete_utility_service),
    filter: Optional[str] = Query(None, description=SwaggerDocumentationConstants.FILTER_DOC),
    session: AsyncSession = Depends(get_db),
) -> list[DiscreteUtilityOutgoingDto]:
    try:
        discrete_utilities: list[DiscreteUtilityOutgoingDto] = await discrete_utility_service.get_all(
            session, odata_query=filter
        )
        return discrete_utilities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/discrete_utilities")
async def update_discrete_utilities(
    dtos: list[DiscreteUtilityIncomingDto],
    discrete_utility_service: DiscreteUtilityService = Depends(get_discrete_utility_service),
    session: AsyncSession = Depends(get_db),
) -> list[DiscreteUtilityOutgoingDto]:
    try:
        result = list(await discrete_utility_service.update(session, dtos))
        await session.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))