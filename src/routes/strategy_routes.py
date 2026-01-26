import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.filters.strategy_filter import StrategyFilter
from src.dtos.strategy_dtos import StrategyIncomingDto, StrategyOutgoingDto
from src.dtos.user_dtos import UserIncomingDto
from src.services.strategy_service import StrategyService
from src.services.user_service import get_current_user
from src.dependencies import get_strategy_service
from src.constants import SwaggerDocumentationConstants
from src.dependencies import get_db


router = APIRouter(tags=["strategies"])


@router.post("/strategies")
async def create_strategies(
    dtos: list[StrategyIncomingDto],
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: UserIncomingDto = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[StrategyOutgoingDto]:
    try:
        await strategy_service.create(session, dtos, current_user)
        await session.commit()
        return await strategy_service.get(session, ids = [dto.id for dto in dtos])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/strategies")
async def update_strategies(
    dtos: list[StrategyIncomingDto],
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: UserIncomingDto = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[StrategyOutgoingDto]:
    try:
        await strategy_service.update(session, dtos, current_user)
        await session.commit()
        return await strategy_service.get(session, ids = [dto.id for dto in dtos])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies/{id}")
async def get_strategy(
    id: uuid.UUID,
    strategy_service: StrategyService = Depends(get_strategy_service),
    session: AsyncSession = Depends(get_db),
) -> StrategyOutgoingDto:
    try:
        strategies: list[StrategyOutgoingDto] = await strategy_service.get(session, [id])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if len(strategies) > 0:
        return strategies[0]
    else:
        raise HTTPException(status_code=404)


@router.get("/strategies")
async def get_all_strategies(
    strategy_service: StrategyService = Depends(get_strategy_service),
    filter: Optional[str] = Query(None, description=SwaggerDocumentationConstants.FILTER_DOC),
    session: AsyncSession = Depends(get_db),
) -> list[StrategyOutgoingDto]:
    try:
        strategies: list[StrategyOutgoingDto] = await strategy_service.get_all(
            session, odata_query=filter
        )
        return strategies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/strategies/{project_id}")
async def get_strategies_by_project(
    project_id: uuid.UUID,
    strategy_service: StrategyService = Depends(get_strategy_service),
    filter: Optional[str] = Query(None, description=SwaggerDocumentationConstants.FILTER_DOC),
    session: AsyncSession = Depends(get_db),
) -> list[StrategyOutgoingDto]:
    try:
        strategies: list[StrategyOutgoingDto] = await strategy_service.get_all(
            session, odata_query=filter, filter=StrategyFilter(project_ids=[project_id])
        )
        return strategies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/strategies/{id}")
async def delete_strategy(
    id: uuid.UUID,
    strategy_service: StrategyService = Depends(get_strategy_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        await strategy_service.delete(session, [id])
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/strategies")
async def delete_strategies(
    ids: list[uuid.UUID] = Query([]),
    strategy_service: StrategyService = Depends(get_strategy_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        await strategy_service.delete(session, ids)
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))