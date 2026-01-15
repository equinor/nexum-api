import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.filters.objective_filter import ObjectiveFilter
from src.models.objective import Objective
from src.dtos.objective_dtos import (
    ObjectiveIncomingDto,
    ObjectiveOutgoingDto,
    ObjectiveMapper,
)
from src.dtos.user_dtos import (
    UserIncomingDto,
    UserMapper,
)
from src.repositories.objective_repository import ObjectiveRepository
from src.repositories.user_repository import UserRepository


class ObjectiveService:
    async def create(
        self,
        session: AsyncSession,
        dtos: list[ObjectiveIncomingDto],
        user_dto: UserIncomingDto,
    ) -> list[ObjectiveOutgoingDto]:
        user = await UserRepository(session).get_or_create(UserMapper.to_entity(user_dto))
        entities: list[Objective] = await ObjectiveRepository(session).create(
            ObjectiveMapper.to_entities(dtos, user.id)
        )
        # get the dtos while the entities are still connected to the session
        result: list[ObjectiveOutgoingDto] = ObjectiveMapper.to_outgoing_dtos(entities)
        return result

    async def update(
        self,
        session: AsyncSession,
        dtos: list[ObjectiveIncomingDto],
        user_dto: UserIncomingDto,
    ) -> list[ObjectiveOutgoingDto]:
        user = await UserRepository(session).get_or_create(UserMapper.to_entity(user_dto))
        entities: list[Objective] = await ObjectiveRepository(session).update(
            ObjectiveMapper.to_entities(dtos, user.id)
        )
        # get the dtos while the entities are still connected to the session
        result: list[ObjectiveOutgoingDto] = ObjectiveMapper.to_outgoing_dtos(entities)
        return result

    async def delete(self, session: AsyncSession, ids: list[uuid.UUID]):
        await ObjectiveRepository(session).delete(ids)

    async def get(self, session: AsyncSession, ids: list[uuid.UUID]) -> list[ObjectiveOutgoingDto]:
        objectives: list[Objective] = await ObjectiveRepository(session).get(ids)
        result = ObjectiveMapper.to_outgoing_dtos(objectives)
        return result

    async def get_all(
        self,
        session: AsyncSession,
        odata_query: Optional[str] = None,
        filter: Optional[ObjectiveFilter] = None,
    ) -> list[ObjectiveOutgoingDto]:
        model_filter = filter.construct_filters() if filter else []
        objectives: list[Objective] = await ObjectiveRepository(session).get_all(
            model_filter=model_filter,
            odata_query=odata_query,
        )
        result = ObjectiveMapper.to_outgoing_dtos(objectives)
        return result
