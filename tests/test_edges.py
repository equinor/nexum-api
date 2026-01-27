import pytest
from httpx import AsyncClient
from tests.utils import (
    parse_response_to_dto_test,
    parse_response_to_dtos_test,
)
from src.dtos.edge_dtos import EdgeIncomingDto, EdgeOutgoingDto
from src.seed_database import GenerateUuid


@pytest.mark.asyncio
async def test_get_edges(client: AsyncClient):
    response = await client.get("/edges")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, EdgeOutgoingDto)


@pytest.mark.asyncio
async def test_get_edge(client: AsyncClient):
    response = await client.get(f"/edges/{GenerateUuid.as_string(20)}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, EdgeOutgoingDto)


@pytest.mark.asyncio
async def test_create_edge(client: AsyncClient):
    payload = [
        EdgeIncomingDto(
            project_id=GenerateUuid.as_uuid(1),
            tail_id=GenerateUuid.as_uuid(5),
            head_id=GenerateUuid.as_uuid(4),
        ).model_dump(mode="json")
    ]

    response = await client.post("/edges", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, EdgeOutgoingDto)


@pytest.mark.asyncio
async def test_update_edge(client: AsyncClient):
    edge_id = GenerateUuid.as_uuid(20)  # This should match an existing edge
    new_tail_id = GenerateUuid.as_uuid(2)
    new_head_id = GenerateUuid.as_uuid(8)
    payload = [
        EdgeIncomingDto(
            id=edge_id,
            project_id=GenerateUuid.as_uuid(1),
            tail_id=new_tail_id,
            head_id=new_head_id,
        ).model_dump(mode="json")
    ]

    response = await client.put("/edges", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, EdgeOutgoingDto)
    assert response_content[0].tail_id == new_tail_id and response_content[0].head_id == new_head_id


@pytest.mark.last
@pytest.mark.asyncio
async def test_delete_edge(client: AsyncClient):
    response = await client.delete(f"/edges/{GenerateUuid.as_string(2)}")
    assert response.status_code == 200, f"Response content: {response.content}"


@pytest.mark.last
@pytest.mark.asyncio
async def test_delete_edges(client: AsyncClient):
    ids = [GenerateUuid.as_string(3), GenerateUuid.as_string(4)]
    response = await client.delete("/edges", params={"ids": ids})
    assert response.status_code == 200, f"Response content: {response.content}"

    for id in ids:
        response = await client.get(f"/edges/{id}")
        assert (
            response.status_code == 404
        ), f"Edge with id: {id} found, but should have been deleted"
