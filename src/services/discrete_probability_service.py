import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.discrete_probability import DiscreteProbability
from src.dtos.discrete_probability_dtos import (
    DiscreteProbabilityIncomingDto,
    DiscreteProbabilityOutgoingDto,
    DiscreteProbabilityMapper,
)
from src.repositories.discrete_probability_repository import DiscreteProbabilityRepository


class DiscreteProbabilityService:
    async def create(
        self, session: AsyncSession, dtos: list[DiscreteProbabilityIncomingDto]
    ) -> list[DiscreteProbabilityOutgoingDto]:
        entities: list[DiscreteProbability] = await DiscreteProbabilityRepository(session).create(
            DiscreteProbabilityMapper.to_entities(dtos)
        )
        # get the dtos while the entities are still connected to the session
        result: list[DiscreteProbabilityOutgoingDto] = DiscreteProbabilityMapper.to_outgoing_dtos(entities)
        return result

    async def update(
        self, session: AsyncSession, dtos: list[DiscreteProbabilityIncomingDto]
    ) -> list[DiscreteProbabilityOutgoingDto]:
        entities: list[DiscreteProbability] = await DiscreteProbabilityRepository(session).update(
            DiscreteProbabilityMapper.to_entities(dtos)
        )
        # get the dtos while the entities are still connected to the session
        result: list[DiscreteProbabilityOutgoingDto] = DiscreteProbabilityMapper.to_outgoing_dtos(entities)
        return result

    async def delete(self, session: AsyncSession, ids: list[uuid.UUID]):
        await DiscreteProbabilityRepository(session).delete(ids)

    async def get(
        self, session: AsyncSession, ids: list[uuid.UUID]
    ) -> list[DiscreteProbabilityOutgoingDto]:
        discrete_probabilities: list[DiscreteProbability] = await DiscreteProbabilityRepository(session).get(ids)
        result = DiscreteProbabilityMapper.to_outgoing_dtos(discrete_probabilities)
        return result

    async def get_all(
        self, session: AsyncSession, odata_query: Optional[str] = None
    ) -> list[DiscreteProbabilityOutgoingDto]:
        discrete_probabilities: list[DiscreteProbability] = await DiscreteProbabilityRepository(session).get_all(
            odata_query=odata_query
        )
        result = DiscreteProbabilityMapper.to_outgoing_dtos(discrete_probabilities)
        return result