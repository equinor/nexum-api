import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Annotated
from src.dtos.objective_dtos import ObjectiveMapper, ObjectiveOutgoingDto, ObjectiveViaProjectDto
from src.dtos.project_roles_dtos import (
    ProjectRoleCreateDto,
    ProjectRoleIncomingDto,
    ProjectRoleMapper,
)
from src.models.project import Project, default_endtime

from src.constants import DatabaseConstants

from src.dtos.project_roles_dtos import ProjectRoleOutgoingDto


class ProjectDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: Annotated[str, Field(max_length=DatabaseConstants.MAX_SHORT_STRING_LENGTH.value)] = ""
    opportunityStatement: Annotated[
        str, Field(max_length=DatabaseConstants.MAX_LONG_STRING_LENGTH.value)
    ] = ""

    parent_project_id: uuid.UUID | None = None
    parent_project_name: Annotated[
        str | None, Field(max_length=DatabaseConstants.MAX_SHORT_STRING_LENGTH.value)
    ] = None
    public: bool = False
    end_date: datetime = Field(default_factory=default_endtime)


class ProjectCreateDto(ProjectDto):
    objectives: list[ObjectiveViaProjectDto] = []
    users: list[ProjectRoleCreateDto]


class ProjectIncomingDto(ProjectDto):
    objectives: list[ObjectiveViaProjectDto] = []
    users: list[ProjectRoleIncomingDto]


class ProjectOutgoingDto(ProjectDto):
    objectives: list[ObjectiveOutgoingDto] = []
    users: list[ProjectRoleOutgoingDto]


class PopulatedProjectDto(ProjectDto):
    objectives: list[ObjectiveOutgoingDto] = []
    users: list[ProjectRoleOutgoingDto]


class ProjectMapper:
    @staticmethod
    def from_create_to_entity(dto: ProjectCreateDto, user_id: int) -> Project:
        return Project(
            id=dto.id,
            parent_project_name=dto.parent_project_name,
            parent_project_id=dto.parent_project_id,
            name=dto.name,
            opportunityStatement=dto.opportunityStatement,
            user_id=user_id,
            public=dto.public,
            end_date=dto.end_date,
            objectives=ObjectiveMapper.via_project_to_entities(dto.objectives, user_id, dto.id),
            project_role=[],
        )

    @staticmethod
    def to_outgoing_dto(entity: Project) -> ProjectOutgoingDto:
        return ProjectOutgoingDto(
            id=entity.id,
            name=entity.name,
            parent_project_id=entity.parent_project_id,
            parent_project_name=entity.parent_project_name,
            opportunityStatement=entity.opportunityStatement,
            objectives=ObjectiveMapper.to_outgoing_dtos(entity.objectives),
            public=entity.public,
            end_date=entity.end_date,
            users=ProjectRoleMapper.to_outgoing_dtos(entity.project_role),
        )

    @staticmethod
    def to_populated_dto(entity: Project) -> PopulatedProjectDto:
        return PopulatedProjectDto(
            id=entity.id,
            name=entity.name,
            parent_project_id=entity.parent_project_id,
            parent_project_name=entity.parent_project_name,
            opportunityStatement=entity.opportunityStatement,
            public=entity.public,
            end_date=entity.end_date,
            objectives=ObjectiveMapper.to_outgoing_dtos(entity.objectives),
            users=ProjectRoleMapper.to_outgoing_dtos(entity.project_role),
        )

    @staticmethod
    def to_project_entity(dto: ProjectIncomingDto, user_id: int) -> Project:
        return Project(
            id=dto.id,
            parent_project_id=dto.parent_project_id,
            parent_project_name=dto.parent_project_name,
            name=dto.name,
            opportunityStatement=dto.opportunityStatement,
            objectives=ObjectiveMapper.via_project_to_entities(dto.objectives, user_id, dto.id),
            user_id=user_id,
            public=dto.public,
            end_date=dto.end_date,
            project_role=ProjectRoleMapper.to_project_role_entities(dto.users),
        )

    @staticmethod
    def from_create_to_project_entities(
        dtos: list[ProjectCreateDto], user_id: int
    ) -> list[Project]:
        return [ProjectMapper.from_create_to_entity(dto, user_id) for dto in dtos]

    @staticmethod
    def to_outgoing_dtos(entities: list[Project]) -> list[ProjectOutgoingDto]:
        return [ProjectMapper.to_outgoing_dto(entity) for entity in entities]

    @staticmethod
    def to_populated_dtos(
        entities: list[Project],
    ) -> list[PopulatedProjectDto]:
        return [ProjectMapper.to_populated_dto(entity) for entity in entities]

    @staticmethod
    def to_project_entities(dtos: list[ProjectIncomingDto], user_id: int) -> list[Project]:
        return [ProjectMapper.to_project_entity(dto, user_id) for dto in dtos]
