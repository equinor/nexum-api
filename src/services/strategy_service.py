import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.filters.strategy_filter import StrategyFilter
from src.models.strategy import Strategy
from src.dtos.strategy_dtos import (
    StrategyIncomingDto,
    StrategyOutgoingDto,
    StrategyMapper,
)
from src.dtos.user_dtos import (
    UserIncomingDto,
    UserMapper,
)
from src.repositories.strategy_repository import StrategyRepository
from src.repositories.user_repository import UserRepository


class StrategyService:
    async def create(
        self,
        session: AsyncSession,
        dtos: list[StrategyIncomingDto],
        user_dto: UserIncomingDto,
    ):
        user = await UserRepository(session).get_or_create(UserMapper.to_entity(user_dto))
        await StrategyRepository(session).create(
            StrategyMapper.to_entities(dtos, user.id)
        )

    async def update(
        self,
        session: AsyncSession,
        dtos: list[StrategyIncomingDto],
        user_dto: UserIncomingDto,
    ):
        user = await UserRepository(session).get_or_create(UserMapper.to_entity(user_dto))
        await StrategyRepository(session).update(
            StrategyMapper.to_entities(dtos, user.id)
        )

    async def delete(self, session: AsyncSession, ids: list[uuid.UUID]):
        await StrategyRepository(session).delete(ids)

    async def get(self, session: AsyncSession, ids: list[uuid.UUID]) -> list[StrategyOutgoingDto]:
        strategys: list[Strategy] = await StrategyRepository(session).get(ids)
        result = StrategyMapper.to_outgoing_dtos(strategys)
        return result

    async def get_all(
        self,
        session: AsyncSession,
        odata_query: Optional[str] = None,
        filter: Optional[StrategyFilter] = None,
    ) -> list[StrategyOutgoingDto]:
        model_filter = filter.construct_filters() if filter else []
        strategys: list[Strategy] = await StrategyRepository(session).get_all(
            model_filter=model_filter,
            odata_query=odata_query,
        )
        result = StrategyMapper.to_outgoing_dtos(strategys)
        return result
