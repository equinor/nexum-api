import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from sqlalchemy.ext.asyncio import AsyncSession
from src.dtos.uncertainty_dtos import (
    UncertaintyIncomingDto,
    UncertaintyOutgoingDto,
)
from src.services.uncertainty_service import UncertaintyService
from src.dependencies import get_uncertainty_service
from src.constants import SwaggerDocumentationConstants
from src.dependencies import get_db


router = APIRouter(tags=["uncertainties"])


@router.get("/uncertainties/{id}")
async def get_uncertainty(
    id: uuid.UUID,
    uncertainty_service: UncertaintyService = Depends(get_uncertainty_service),
    session: AsyncSession = Depends(get_db),
) -> UncertaintyOutgoingDto:
    try:
        uncertainties: list[UncertaintyOutgoingDto] = await uncertainty_service.get(session, [id])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if len(uncertainties) > 0:
        return uncertainties[0]
    else:
        raise HTTPException(status_code=404)


@router.get("/uncertainties")
async def get_all_uncertainty(
    uncertainty_service: UncertaintyService = Depends(get_uncertainty_service),
    filter: Optional[str] = Query(None, description=SwaggerDocumentationConstants.FILTER_DOC),
    session: AsyncSession = Depends(get_db),
) -> list[UncertaintyOutgoingDto]:
    try:
        uncertainties: list[UncertaintyOutgoingDto] = await uncertainty_service.get_all(
            session, odata_query=filter
        )
        return uncertainties
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/uncertainties/{id}")
async def delete_uncertainty(
    id: uuid.UUID,
    uncertainty_service: UncertaintyService = Depends(get_uncertainty_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        await uncertainty_service.delete(session, [id])
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/uncertainties")
async def delete_uncertainties(
    ids: list[uuid.UUID] = Query([]),
    uncertainty_service: UncertaintyService = Depends(get_uncertainty_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        await uncertainty_service.delete(session, ids)
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/uncertainties")
async def update_uncertainties(
    dtos: list[UncertaintyIncomingDto],
    uncertainty_service: UncertaintyService = Depends(get_uncertainty_service),
    session: AsyncSession = Depends(get_db),
) -> list[UncertaintyOutgoingDto]:
    try:
        result = list(await uncertainty_service.update(session, dtos))
        await session.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/uncertainties/{id}/remake-probability-table")
async def remake_probability_table(
    id: uuid.UUID,
    uncertainty_service: UncertaintyService = Depends(get_uncertainty_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        dto = await uncertainty_service.recalculate_discrete_probability_table_async(session, id)
        await session.commit()
        if dto is None:
            return HTTPException(status_code=404)
        return Response(status_code=204)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))