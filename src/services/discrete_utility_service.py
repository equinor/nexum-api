import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.discrete_utility import DiscreteUtility
from src.dtos.discrete_utility_dtos import (
    DiscreteUtilityIncomingDto,
    DiscreteUtilityOutgoingDto,
    DiscreteUtilityMapper,
)
from src.repositories.discrete_utility_repository import DiscreteUtilityRepository


class DiscreteUtilityService:
    async def create(
        self, session: AsyncSession, dtos: list[DiscreteUtilityIncomingDto]
    ) -> list[DiscreteUtilityOutgoingDto]:
        entities: list[DiscreteUtility] = await DiscreteUtilityRepository(session).create(
            DiscreteUtilityMapper.to_entities(dtos)
        )
        # get the dtos while the entities are still connected to the session
        result: list[DiscreteUtilityOutgoingDto] = DiscreteUtilityMapper.to_outgoing_dtos(entities)
        return result

    async def update(
        self, session: AsyncSession, dtos: list[DiscreteUtilityIncomingDto]
    ) -> list[DiscreteUtilityOutgoingDto]:
        entities: list[DiscreteUtility] = await DiscreteUtilityRepository(session).update(
            DiscreteUtilityMapper.to_entities(dtos)
        )
        # get the dtos while the entities are still connected to the session
        result: list[DiscreteUtilityOutgoingDto] = DiscreteUtilityMapper.to_outgoing_dtos(entities)
        return result

    async def delete(self, session: AsyncSession, ids: list[uuid.UUID]):
        await DiscreteUtilityRepository(session).delete(ids)

    async def get(
        self, session: AsyncSession, ids: list[uuid.UUID]
    ) -> list[DiscreteUtilityOutgoingDto]:
        discrete_probabilities: list[DiscreteUtility] = await DiscreteUtilityRepository(session).get(ids)
        result = DiscreteUtilityMapper.to_outgoing_dtos(discrete_probabilities)
        return result

    async def get_all(
        self, session: AsyncSession, odata_query: Optional[str] = None
    ) -> list[DiscreteUtilityOutgoingDto]:
        discrete_probabilities: list[DiscreteUtility] = await DiscreteUtilityRepository(session).get_all(
            odata_query=odata_query
        )
        result = DiscreteUtilityMapper.to_outgoing_dtos(discrete_probabilities)
        return result