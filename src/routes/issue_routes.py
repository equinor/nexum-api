import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession
from src.dtos.issue_dtos import IssueIncomingDto, IssueOutgoingDto
from src.services.issue_service import IssueService
from src.dependencies import get_issue_service
from src.services.user_service import get_current_user
from src.dtos.user_dtos import UserIncomingDto
from src.models.filters.issues_filter import IssueFilter
from src.constants import SwaggerDocumentationConstants
from src.dependencies import get_db


router = APIRouter(tags=["issues"])


@router.post("/issues")
async def create_issues(
    dtos: list[IssueIncomingDto],
    issue_service: IssueService = Depends(get_issue_service),
    current_user: UserIncomingDto = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[IssueOutgoingDto]:
    """
    Endpoint for creating Issues.
    If supplied with nodes/decisions/uncertainties they will be created after the issue with the appropriate Id.
    If node is not supplied an empty node will be created.
    """
    try:
        result = list(await issue_service.create(session, dtos, current_user))
        await session.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issues/{id}")
async def get_issue(
    id: uuid.UUID,
    issue_service: IssueService = Depends(get_issue_service),
    session: AsyncSession = Depends(get_db),
) -> IssueOutgoingDto:
    try:
        issues: list[IssueOutgoingDto] = await issue_service.get(session, [id])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if len(issues) > 0:
        return issues[0]
    else:
        raise HTTPException(status_code=404)


@router.get("/issues")
async def get_all_issue(
    issue_service: IssueService = Depends(get_issue_service),
    filter: Optional[str] = Query(None, description=SwaggerDocumentationConstants.FILTER_DOC),
    session: AsyncSession = Depends(get_db),
) -> list[IssueOutgoingDto]:
    try:
        issues: list[IssueOutgoingDto] = await issue_service.get_all(session, odata_query=filter)
        return issues
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/issues")
async def get_all_issues_from_project(
    project_id: uuid.UUID,
    issue_service: IssueService = Depends(get_issue_service),
    filter: Optional[str] = Query(None, description=SwaggerDocumentationConstants.FILTER_DOC),
    session: AsyncSession = Depends(get_db),
) -> list[IssueOutgoingDto]:
    try:
        issues: list[IssueOutgoingDto] = await issue_service.get_all(
            session, IssueFilter(project_ids=[project_id]), odata_query=filter
        )
        return issues
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/issues/{id}")
async def delete_issue(
    id: uuid.UUID,
    issue_service: IssueService = Depends(get_issue_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        await issue_service.delete(session, [id])
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/issues")
async def delete_issues(
    ids: list[uuid.UUID] = Query([]),
    issue_service: IssueService = Depends(get_issue_service),
    session: AsyncSession = Depends(get_db),
):
    try:
        await issue_service.delete(session, ids)
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/issues")
async def update_issues(
    dtos: list[IssueIncomingDto],
    issue_service: IssueService = Depends(get_issue_service),
    current_user: UserIncomingDto = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[IssueOutgoingDto]:
    try:
        result = list(await issue_service.update(session, dtos, current_user))
        await session.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
