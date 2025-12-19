import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.utility import Utility
from src.dtos.utility_dtos import (
    UtilityIncomingDto,
    UtilityOutgoingDto,
    UtilityMapper,
)
from src.repositories.utility_repository import UtilityRepository


class UtilityService:
    async def create(
        self, session: AsyncSession, dtos: list[UtilityIncomingDto]
    ) -> list[UtilityOutgoingDto]:
        entities: list[Utility] = await UtilityRepository(session).create(
            UtilityMapper.to_entities(dtos)
        )
        # get the dtos while the entities are still connected to the session
        result: list[UtilityOutgoingDto] = UtilityMapper.to_outgoing_dtos(entities)
        return result

    async def update(
        self, session: AsyncSession, dtos: list[UtilityIncomingDto]
    ) -> list[UtilityOutgoingDto]:
        entities: list[Utility] = await UtilityRepository(session).update(
            UtilityMapper.to_entities(dtos)
        )
        # get the dtos while the entities are still connected to the session
        result: list[UtilityOutgoingDto] = UtilityMapper.to_outgoing_dtos(entities)
        return result

    async def delete(self, session: AsyncSession, ids: list[uuid.UUID]):
        await UtilityRepository(session).delete(ids)

    async def get(self, session: AsyncSession, ids: list[uuid.UUID]) -> list[UtilityOutgoingDto]:
        entities: list[Utility] = await UtilityRepository(session).get(ids)
        result = UtilityMapper.to_outgoing_dtos(entities)
        return result

    async def get_all(
        self, session: AsyncSession, odata_query: Optional[str] = None
    ) -> list[UtilityOutgoingDto]:
        entities: list[Utility] = await UtilityRepository(session).get_all(odata_query=odata_query)
        result = UtilityMapper.to_outgoing_dtos(entities)
        return result
    
    async def recalculate_discrete_utility_tables_async(self, session: AsyncSession, ids: list[uuid.UUID]):
        for id in ids:
            await UtilityRepository(session).recalculate_discrete_utility_table_async(id)
