import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.uncertainty import Uncertainty
from src.dtos.uncertainty_dtos import (
    UncertaintyIncomingDto,
    UncertaintyOutgoingDto,
    UncertaintyMapper,
)
from src.repositories.uncertainty_repository import UncertaintyRepository


class UncertaintyService:
    async def create(
        self, session: AsyncSession, dtos: list[UncertaintyIncomingDto]
    ) -> list[UncertaintyOutgoingDto]:
        entities: list[Uncertainty] = await UncertaintyRepository(session).create(
            UncertaintyMapper.to_entities(dtos)
        )
        # get the dtos while the entities are still connected to the session
        result: list[UncertaintyOutgoingDto] = UncertaintyMapper.to_outgoing_dtos(entities)
        return result

    async def update(
        self, session: AsyncSession, dtos: list[UncertaintyIncomingDto]
    ) -> list[UncertaintyOutgoingDto]:
        entities: list[Uncertainty] = await UncertaintyRepository(session).update(
            UncertaintyMapper.to_entities(dtos)
        )
        # get the dtos while the entities are still connected to the session
        result: list[UncertaintyOutgoingDto] = UncertaintyMapper.to_outgoing_dtos(entities)
        return result

    async def delete(self, session: AsyncSession, ids: list[uuid.UUID]):
        await UncertaintyRepository(session).delete(ids)

    async def get(
        self, session: AsyncSession, ids: list[uuid.UUID]
    ) -> list[UncertaintyOutgoingDto]:
        decisions: list[Uncertainty] = await UncertaintyRepository(session).get(ids)
        result = UncertaintyMapper.to_outgoing_dtos(decisions)
        return result

    async def get_all(
        self, session: AsyncSession, odata_query: Optional[str] = None
    ) -> list[UncertaintyOutgoingDto]:
        decisions: list[Uncertainty] = await UncertaintyRepository(session).get_all(
            odata_query=odata_query
        )
        result = UncertaintyMapper.to_outgoing_dtos(decisions)
        return result

    async def recalculate_discrete_probability_table_async(self, session: AsyncSession, id: uuid.UUID) -> Optional[UncertaintyOutgoingDto]:
        entity = await UncertaintyRepository(session).recalculate_discrete_probability_table_async(id)
        return UncertaintyMapper.to_outgoing_dto(entity) if entity is not None else None