import asyncio
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.influence_diagram import InfluenceDiagramDOT
from src.dtos.edge_dtos import EdgeMapper, EdgeOutgoingDto
from src.dtos.issue_dtos import IssueMapper, IssueOutgoingDto
from src.models.filters.edge_filter import EdgeFilter
from src.models.filters.issues_filter import IssueFilter
from src.repositories.edge_repository import EdgeRepository
from src.repositories.issue_repository import IssueRepository
from src.constants import Boundary, DecisionHierarchy, ProjectRoleType, Type
from src.dtos.project_roles_dtos import ProjectRoleCreateDto, ProjectRoleMapper
from src.models.project_role import ProjectRole
from src.repositories.project_role_repository import ProjectRoleRepository
from src.models import (
    Project,
)
from src.dtos.project_dtos import (
    ProjectMapper,
    ProjectIncomingDto,
    ProjectOutgoingDto,
    ProjectCreateDto,
    PopulatedProjectDto,
)
from src.dtos.user_dtos import (
    UserMapper,
    UserIncomingDto,
)
from src.repositories.project_repository import ProjectRepository
from src.repositories.user_repository import UserRepository
from src.models.filters.project_filter import ProjectFilter


class ProjectService:

    async def _create_role_for_project(
        self,
        session: AsyncSession,
        project_role_dtos: list[ProjectRoleCreateDto],
    ):
        # Ensure this method is always called within an async session context
        project_user_roles = await ProjectRoleRepository(session).create(
            ProjectRoleMapper.from_create_via_project_to_entities(project_role_dtos)
        )
        project_user_role = await ProjectRoleRepository(session).get(
            [role.id for role in project_user_roles]
        )
        return project_user_role

    async def create(
        self,
        session: AsyncSession,
        dtos: list[ProjectCreateDto],
        user_dto: UserIncomingDto,
        is_duplicate: bool = False,
    ) -> list[ProjectOutgoingDto]:
        user = await UserRepository(session).get_or_create(UserMapper.to_entity(user_dto))

        if not is_duplicate:
            for dto in dtos:
                owner_role = ProjectRoleCreateDto(
                    user_name=user.name,
                    azure_id=user.azure_id,
                    user_id=user.id,
                    project_id=dto.id,
                    role=ProjectRoleType.FACILITATOR,
                )
                dto.users.append(owner_role)

        await ProjectRepository(session).create(
            ProjectMapper.from_create_to_project_entities(dtos, user.id)
        )
        for dto in dtos:
            if len(dto.users) > 0:
                await self._create_role_for_project(
                    session, dto.users
                )

        return await self.get(session, ids = [dto.id for dto in dtos])

    async def update(
        self,
        session: AsyncSession,
        dtos: list[ProjectIncomingDto],
        user_dto: UserIncomingDto,
    ) -> list[ProjectOutgoingDto]:
        user = await UserRepository(session).get_or_create(UserMapper.to_entity(user_dto))
        await ProjectRepository(session).update(
            ProjectMapper.to_project_entities(dtos, user.id)
        )
        return await self.get(session, ids = [dto.id for dto in dtos])
    
    async def delete(
        self,
        session: AsyncSession,
        ids: list[uuid.UUID],
        user_dto: UserIncomingDto,
    ) -> None:
        user = await UserRepository(session).get_by_azure_id(azure_id=user_dto.azure_id)
        if user is None or len(user.project_role) == 0:
            return
        ids_to_delete = [
            project_role.project_id
            for project_role in user.project_role
            if (
                project_role.role == ProjectRoleType.FACILITATOR
                or project_role.role == ProjectRoleType.DECISIONMAKER
            )
            and project_role.project_id in ids
        ]
        await ProjectRepository(session).delete(ids=ids_to_delete)

    async def get(self, session: AsyncSession, ids: list[uuid.UUID]) -> list[ProjectOutgoingDto]:
        if not ids:
            return []
        projects: list[Project] = await ProjectRepository(session).get(ids)
        result = ProjectMapper.to_outgoing_dtos(projects)
        return result

    async def get_all(
        self,
        session: AsyncSession,
        user_dto: UserIncomingDto,
        filter: Optional[ProjectFilter] = None,
        odata_query: Optional[str] = None,
    ) -> list[ProjectOutgoingDto]:
        user = await UserRepository(session).get_or_create(UserMapper.to_entity(user_dto))
        if not user:
            return []
        if filter is None:
            filter = ProjectFilter()

        filter.accessing_user_id = user.id
        project_access_filter = filter.construct_access_conditions()

        # Construct model filters
        model_filter = filter.construct_filters() if filter else []
        model_filter.append(project_access_filter)
        projects: list[Project] = await ProjectRepository(session).get_all(
            model_filter=model_filter, odata_query=odata_query
        )
        result = ProjectMapper.to_outgoing_dtos(projects)
        return result

    async def get_populated_projects(
        self, session: AsyncSession, ids: list[uuid.UUID]
    ) -> list[PopulatedProjectDto]:
        projects: list[Project] = await ProjectRepository(session).get(ids)
        result = ProjectMapper.to_populated_dtos(projects)
        return result

    async def get_all_populated_projects(
        self,
        session: AsyncSession,
        filter: Optional[ProjectFilter] = None,
        odata_query: Optional[str] = None,
    ) -> list[PopulatedProjectDto]:
        model_filter = filter.construct_filters() if filter else []
        projects: list[Project] = await ProjectRepository(session).get_all(
            model_filter=model_filter, odata_query=odata_query
        )
        result = ProjectMapper.to_populated_dtos(projects)
        return result

    def _remove_utilities_with_too_few_connections(
        self,
        issue_dtos: list[IssueOutgoingDto],
        edge_dtos: list[EdgeOutgoingDto],
        minimum_number_connections: int = 2,
    ):
        utility_issues = [issue for issue in issue_dtos if issue.type == Type.UTILITY.value]
        utilities_to_remove: list[IssueOutgoingDto] = []
        edges_to_remove: list[EdgeOutgoingDto] = []
        for utility_issue in utility_issues:
            edges = [edge for edge in edge_dtos if edge.head_issue_id == utility_issue.id]
            edges_to_remove.extend(
                [edge for edge in edge_dtos if edge.tail_issue_id == utility_issue.id]
            )
            if len(edges) < minimum_number_connections:
                utilities_to_remove.append(utility_issue)
                edges_to_remove.extend(edges)
        for issue in utilities_to_remove:
            issue_dtos.remove(issue)
        for edge in edges_to_remove:
            edge_dtos.remove(edge)

    async def get_influence_diagram_data(
        self, session: AsyncSession, project_id: uuid.UUID
    ) -> tuple[list[IssueOutgoingDto], list[EdgeOutgoingDto]]:
        issue_filter = IssueFilter(
            project_ids=[project_id],
            boundaries=[Boundary.ON.value, Boundary.IN.value],
            types=[Type.DECISION.value, Type.UNCERTAINTY.value, Type.UTILITY.value],
            decision_types=[DecisionHierarchy.FOCUS.value],
            is_key_uncertainties=[True],
        )
        edge_filter = EdgeFilter(
            project_ids=[project_id],
            issue_boundaries=[Boundary.ON.value, Boundary.IN.value],
            issue_types=[Type.DECISION.value, Type.UNCERTAINTY.value, Type.UTILITY.value],
            decision_types=[DecisionHierarchy.FOCUS.value],
            is_key_uncertainties=[True],
        )

        issues_entities = await IssueRepository(session).get_all(
            model_filter=issue_filter.construct_filters()
        )
        edges_entities = await EdgeRepository(session).get_all(
            model_filter=edge_filter.construct_filters()
        )

        issue_dtos = IssueMapper.to_outgoing_dtos(issues_entities)
        edge_dtos = EdgeMapper.to_outgoing_dtos(edges_entities)
        self._remove_utilities_with_too_few_connections(issue_dtos, edge_dtos)

        # Run influence diagram creation and validation in a separate thread
        influence_diagram = await asyncio.to_thread(
            lambda: InfluenceDiagramDOT(edge_dtos, issue_dtos)
        )
        await asyncio.to_thread(influence_diagram.validate_diagram)

        # Return the validated (potentially filtered) issues and edges
        return influence_diagram.issues, influence_diagram.edges
