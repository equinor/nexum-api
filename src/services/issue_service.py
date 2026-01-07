import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.models.issue import Issue
from src.dtos.issue_dtos import (
    IssueMapper,
    IssueOutgoingDto,
    IssueIncomingDto,
)
from src.dtos.node_dtos import (
    NodeMapper,
    NodeIncomingDto,
)
from src.dtos.node_style_dtos import NodeStyleIncomingDto
from src.dtos.decision_dtos import (
    DecisionMapper,
    DecisionIncomingDto,
)
from src.dtos.uncertainty_dtos import (
    UncertaintyMapper,
    UncertaintyIncomingDto,
)
from src.dtos.utility_dtos import (
    UtilityMapper,
    UtilityIncomingDto,
)
from src.dtos.user_dtos import (
    UserIncomingDto,
    UserMapper,
)
from src.repositories.issue_repository import IssueRepository
from src.repositories.node_repository import NodeRepository
from src.repositories.decision_repository import DecisionRepository
from src.repositories.uncertainty_repository import UncertaintyRepository
from src.repositories.utility_repository import UtilityRepository
from src.repositories.user_repository import UserRepository
from src.models.filters.issues_filter import IssueFilter


class IssueService:
    def _extract_related_entities(self, dtos: list[IssueIncomingDto]) -> tuple[
        list[IssueIncomingDto],
        list[NodeIncomingDto],
        list[Optional[DecisionIncomingDto]],
        list[Optional[UncertaintyIncomingDto]],
        list[Optional[UtilityIncomingDto]],
    ]:
        nodes: list[NodeIncomingDto] = []
        decisions: list[Optional[DecisionIncomingDto]] = []
        uncertainties: list[Optional[UncertaintyIncomingDto]] = []
        utilities: list[Optional[UtilityIncomingDto]] = []
        for dto in dtos:
            if dto.node:
                nodes.append(dto.node)
            else:
                node_id = uuid.uuid4()
                nodes.append(
                    NodeIncomingDto(
                        id=node_id,
                        project_id=dto.project_id,
                        issue_id=dto.id,
                        node_style=NodeStyleIncomingDto(node_id=node_id),
                    )
                )

            decisions.append(dto.decision)
            uncertainties.append(dto.uncertainty)
            utilities.append(dto.utility)
            dto.node = None
            dto.decision = None
            dto.uncertainty = None
            dto.utility = None
        return dtos, nodes, decisions, uncertainties, utilities

    async def _create_related_entities(
        self,
        session: AsyncSession,
        entity: Issue,
        node_dto: NodeIncomingDto,
        decision_dto: Optional[DecisionIncomingDto],
        uncertainty_dto: Optional[UncertaintyIncomingDto],
        utility_dto: Optional[UtilityIncomingDto],
    ):
        node_dto.issue_id = entity.id
        node = await NodeRepository(session).create_single(NodeMapper.to_entity(node_dto))
        entity.node = node
        if decision_dto:
            decision_dto.issue_id = entity.id
            decision = await DecisionRepository(session).create_single(
                DecisionMapper.to_entity(decision_dto)
            )
            entity.decision = decision
        if uncertainty_dto:
            uncertainty_dto.issue_id = entity.id
            uncertainty = await UncertaintyRepository(session).create_single(
                UncertaintyMapper.to_entity(uncertainty_dto)
            )
            entity.uncertainty = uncertainty
        if utility_dto:
            utility_dto.issue_id = entity.id
            utility = await UtilityRepository(session).create_single(
                UtilityMapper.to_entity(utility_dto)
            )
            entity.utility = utility
        return entity

    async def create(
        self,
        session: AsyncSession,
        dtos: list[IssueIncomingDto],
        user_dto: UserIncomingDto,
    ) -> list[IssueOutgoingDto]:
        user = await UserRepository(session).get_or_create(UserMapper.to_entity(user_dto))
        # remove node dto to create later
        (
            dtos,
            node_dtos,
            decision_dtos,
            uncertainty_dtos,
            utility_dtos,
        ) = self._extract_related_entities(dtos)
        entities: list[Issue] = await IssueRepository(session).create(
            IssueMapper.to_entities(dtos, user.id)
        )
        # get the dtos while the entities are still connected to the session
        for (
            entity,
            node_dto,
            decision_dto,
            uncertainty_dto,
            utility_dto,
        ) in zip(
            entities,
            node_dtos,
            decision_dtos,
            uncertainty_dtos,
            utility_dtos,
        ):
            entity = await self._create_related_entities(
                session,
                entity,
                node_dto,
                decision_dto,
                uncertainty_dto,
                utility_dto,
            )
        result: list[IssueOutgoingDto] = IssueMapper.to_outgoing_dtos(entities)
        return result

    async def update(
        self,
        session: AsyncSession,
        dtos: list[IssueIncomingDto],
        user_dto: UserIncomingDto,
    ) -> list[IssueOutgoingDto]:
        user = await UserRepository(session).get_or_create(UserMapper.to_entity(user_dto))
        entities: list[Issue] = await IssueRepository(session).update(
            IssueMapper.to_entities(dtos, user.id)
        )
        # get the dtos while the entities are still connected to the session
        result: list[IssueOutgoingDto] = IssueMapper.to_outgoing_dtos(entities)
        return result

    async def delete(self, session: AsyncSession, ids: list[uuid.UUID]):
        await IssueRepository(session).delete(ids)

    async def get(self, session: AsyncSession, ids: list[uuid.UUID]) -> list[IssueOutgoingDto]:
        issues: list[Issue] = await IssueRepository(session).get(ids)
        result = IssueMapper.to_outgoing_dtos(issues)
        return result

    async def get_all(
        self,
        session: AsyncSession,
        filter: Optional[IssueFilter] = None,
        odata_query: Optional[str] = None,
    ) -> list[IssueOutgoingDto]:
        model_filter = filter.construct_filters() if filter else []
        issues: list[Issue] = await IssueRepository(session).get_all(
            model_filter=model_filter, odata_query=odata_query
        )
        result = IssueMapper.to_outgoing_dtos(issues)
        return result
