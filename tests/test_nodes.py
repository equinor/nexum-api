import pytest
from httpx import AsyncClient
from tests.utils import (
    parse_response_to_dto_test,
    parse_response_to_dtos_test,
)
from src.dtos.node_dtos import NodeIncomingDto, NodeOutgoingDto
from src.dtos.node_style_dtos import NodeStyleIncomingDto
from src.seed_database import GenerateUuid


@pytest.mark.asyncio
async def test_get_nodes(client: AsyncClient):
    response = await client.get("/nodes")
    print(response)
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, NodeOutgoingDto)


@pytest.mark.asyncio
async def test_get_node(client: AsyncClient):
    response = await client.get(f"/nodes/{GenerateUuid.as_string(20)}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, NodeOutgoingDto)


@pytest.mark.asyncio
async def test_update_node(client: AsyncClient):
    node_id = GenerateUuid.as_string(1)
    example_node = parse_response_to_dto_test(
        await client.get(f"/nodes/{node_id}"), NodeOutgoingDto
    )
    new_project_id = GenerateUuid.as_uuid(1)
    new_y_position = 500

    payload = [
        NodeIncomingDto(
            id=example_node.id,
            issue_id=example_node.issue_id,
            project_id=new_project_id,
            node_style=NodeStyleIncomingDto(
                id=example_node.node_style.id,
                node_id=example_node.id,
                y_position=new_y_position,
            ),
        ).model_dump(mode="json")
    ]

    response = await client.put("/nodes", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, NodeOutgoingDto)
    assert response_content[0].project_id == new_project_id
    assert response_content[0].node_style.y_position == new_y_position


@pytest.mark.asyncio
async def test_delete_node(client: AsyncClient):
    response = await client.delete(f"/nodes/{GenerateUuid.as_string(2)}")
    assert response.status_code == 200, f"Response content: {response.content}"


@pytest.mark.asyncio
async def test_delete_nodes(client: AsyncClient):
    ids = [GenerateUuid.as_string(3), GenerateUuid.as_string(4)]
    response = await client.delete("/nodes", params={"ids": ids})
    assert response.status_code == 200, f"Response content: {response.content}"

    for id in ids:
        response = await client.get(f"/nodes/{id}")
        assert (
            response.status_code == 404
        ), f"Node with id: {id} found, but should have been deleted"
