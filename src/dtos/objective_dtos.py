import uuid
from pydantic import BaseModel, Field
from typing import Annotated
from src.models.objective import Objective
from src.constants import (
    DatabaseConstants,
    ObjectiveTypes,
)
from datetime import datetime


class ObjectiveDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: Annotated[str, Field(max_length=DatabaseConstants.MAX_SHORT_STRING_LENGTH.value)]
    description: Annotated[str, Field(max_length=DatabaseConstants.MAX_LONG_STRING_LENGTH.value)]


class ObjectiveViaProjectDto(ObjectiveDto):
    """
    Class should only be a property of project when creating the project with objective(s)
    """

    type: ObjectiveTypes = ObjectiveTypes.FUNDAMENTAL


class ObjectiveIncomingDto(ObjectiveDto):
    project_id: uuid.UUID
    type: ObjectiveTypes = ObjectiveTypes.FUNDAMENTAL


class ObjectiveOutgoingDto(ObjectiveDto):
    project_id: uuid.UUID
    type: str
    created_at: datetime
    updated_at: datetime


class ObjectiveMapper:
    @staticmethod
    def via_project_to_entity(
        dto: ObjectiveViaProjectDto, user_id: int, project_id: uuid.UUID
    ) -> Objective:
        return Objective(
            id=dto.id,
            project_id=project_id,
            name=dto.name,
            type=dto.type,
            description=dto.description,
            user_id=user_id,
        )

    @staticmethod
    def to_outgoing_dto(entity: Objective) -> ObjectiveOutgoingDto:
        return ObjectiveOutgoingDto(
            id=entity.id,
            project_id=entity.project_id,
            name=entity.name,
            type=entity.type,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def to_entity(dto: ObjectiveIncomingDto, user_id: int) -> Objective:
        return Objective(
            id=dto.id,
            project_id=dto.project_id,
            name=dto.name,
            type=dto.type,
            description=dto.description,
            user_id=user_id,
        )

    @staticmethod
    def via_project_to_entities(
        dtos: list[ObjectiveViaProjectDto],
        user_id: int,
        project_id: uuid.UUID,
    ) -> list[Objective]:
        return [ObjectiveMapper.via_project_to_entity(dto, user_id, project_id) for dto in dtos]

    @staticmethod
    def to_outgoing_dtos(
        entities: list[Objective],
    ) -> list[ObjectiveOutgoingDto]:
        return [ObjectiveMapper.to_outgoing_dto(entity) for entity in entities]

    @staticmethod
    def to_entities(dtos: list[ObjectiveIncomingDto], user_id: int) -> list[Objective]:
        return [ObjectiveMapper.to_entity(dto, user_id) for dto in dtos]
