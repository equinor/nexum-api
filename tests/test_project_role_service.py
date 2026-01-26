from httpx import AsyncClient
import pytest

from src.constants import ProjectRoleType
from src.dtos.project_roles_dtos import ProjectRoleIncomingDto, ProjectRoleOutgoingDto
from src.seed_database import GenerateUuid
from tests.utils import parse_response_to_dtos_test


@pytest.mark.asyncio
async def test_get__project_role(client: AsyncClient):
    response = await client.get(f"/project-roles/{GenerateUuid.as_string(1)}")
    assert response.status_code == 200, f"Response content: {response.content}"
    parse_response_to_dtos_test(response, ProjectRoleOutgoingDto)


@pytest.mark.asyncio
async def test_get_all_project_role(client: AsyncClient):
    response = await client.get("/project-roles/")
    assert response.status_code == 200, f"Response content: {response.content}"
    parse_response_to_dtos_test(response, ProjectRoleOutgoingDto)


@pytest.mark.last
@pytest.mark.asyncio
async def test_delete_project_role(client: AsyncClient):
    response = await client.delete(
        f"/project-roles/{GenerateUuid.as_string(0)}/{GenerateUuid.as_string(0)}"
    )
    assert response.status_code == 200, f"Response content: {response.content}"


@pytest.mark.asyncio
async def test_update_project_role(client: AsyncClient):
    payload = [
        ProjectRoleIncomingDto(
            id=GenerateUuid.as_uuid(2),
            user_id=1,
            azure_id=GenerateUuid.as_string(15),
            user_name="",
            project_id=GenerateUuid.as_uuid(2),
            role=ProjectRoleType.MEMBER,
        ).model_dump(mode="json")
    ]
    response = await client.put("/project-roles/", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"
    parse_response_to_dtos_test(response, ProjectRoleOutgoingDto)
