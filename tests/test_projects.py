import pytest
from uuid import uuid4
from httpx import AsyncClient
from tests.utils import (
    parse_response_to_dto_test,
    parse_response_to_dtos_test,
)
from src.dtos.project_dtos import (
    ProjectIncomingDto,
    ProjectOutgoingDto,
    ProjectCreateDto,
    PopulatedProjectDto,
)
from src.dtos.strategy_dtos import StrategyIncomingDto
from src.dtos.option_dtos import OptionIncomingDto
from src.seed_database import GenerateUuid


@pytest.mark.asyncio
async def test_get_projects(client: AsyncClient):
    response = await client.get("/projects")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, ProjectOutgoingDto)


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    response = await client.get(f"/projects/{GenerateUuid.as_string(1)}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, ProjectOutgoingDto)


@pytest.mark.asyncio
async def test_get_project_populated(client: AsyncClient):
    response = await client.get(f"/projects-populated/{GenerateUuid.as_string(9)}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, PopulatedProjectDto)


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    test_project_id = uuid4()
    payload = [
        ProjectCreateDto(
            id=test_project_id,
            name=str(uuid4()),
            objectives=[],
            opportunityStatement=str(uuid4()),
            users=[],
        ).model_dump(mode="json")
    ]

    response = await client.post("/projects", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, ProjectOutgoingDto)


@pytest.mark.asyncio
async def test_create_project_with_objectives(client: AsyncClient):

    project = ProjectCreateDto(
        name=str(uuid4()), objectives=[], opportunityStatement=str(uuid4()), users=[],
    )
    payload = [project.model_dump(mode="json")]

    response = await client.post("/projects", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, ProjectOutgoingDto)
    assert response_content[0].id == project.id


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    new_name = str(uuid4())
    payload = [
        ProjectIncomingDto(
            id=GenerateUuid.as_uuid(6), name=new_name, opportunityStatement="", users=[], strategies=[]
        ).model_dump(mode="json")
    ]
    response = await client.put("/projects", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, ProjectOutgoingDto)
    assert response_content[0].name == new_name


@pytest.mark.last
@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    response = await client.delete(f"/projects/{GenerateUuid.as_string(4343434344342123532453453)}")

    assert response.status_code == 200, f"Response content: {response.content}"

@pytest.mark.asyncio
async def test_update_project_with_strategies(client: AsyncClient):
    new_name = str(uuid4())
    test_strategy_id = GenerateUuid.as_uuid(1)
    test_option_id = GenerateUuid.as_uuid(1)
    project_id = GenerateUuid.as_uuid(0)
    
    
    strategy = StrategyIncomingDto(
        id=test_strategy_id,
        project_id=project_id,
        name="Updated Strategy via Project",
        description="Updated strategy created via project update",
        rationale="Updated test strategy rationale",
        options=[
            OptionIncomingDto(
                id=test_option_id,
                decision_id=GenerateUuid.as_uuid("test_decision_issue_1"),
                name="Updated Option via Project Strategy",
                utility=80.0,
            )
        ],
    )
    
    payload = [
        ProjectIncomingDto(
            id=project_id,
            name=new_name,
            opportunityStatement="Updated opportunity statement",
            users=[],
            strategies=[strategy],
        ).model_dump(mode="json")
    ]
    response = await client.put("/projects", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, ProjectOutgoingDto)
    assert response_content[0].name == new_name
    assert len(response_content[0].strategies) == 1
    assert response_content[0].strategies[0].id == strategy.id
    assert response_content[0].strategies[0].name == strategy.name
