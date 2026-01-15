import uuid
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from src.services.project_duplication_service import ProjectDuplicationService
from src.dtos.project_dtos import (
    ProjectOutgoingDto,
)
from src.dependencies import get_project_duplication_service
from src.services.user_service import get_current_user
from src.dtos.user_dtos import UserIncomingDto
from src.dependencies import get_db
from src.constants import SessionInfoParameters

router = APIRouter(tags=["projects"])


@router.post("/project/duplicate/{id}")
async def duplicate_project(
    id: uuid.UUID,
    project_duplication_service: ProjectDuplicationService = Depends(
        get_project_duplication_service
    ),
    session: AsyncSession = Depends(get_db),
    current_user: UserIncomingDto = Depends(get_current_user),
) -> ProjectOutgoingDto | None:
    """
    Endpoint for duplicating a Project.
    The duplicated Project will have a new Id.
    """
    try:
        session.info[SessionInfoParameters.IS_EVENT_DISABLED.value] = True
        result = await project_duplication_service.project_duplication(session, id, current_user)
        await session.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
