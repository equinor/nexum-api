import pytest
from uuid import uuid4
from httpx import AsyncClient
from tests.utils import (
    parse_response_to_dto_test,
    parse_response_to_dtos_test,
)
from src.dtos.option_dtos import OptionIncomingDto, OptionOutgoingDto
from src.seed_database import GenerateUuid


@pytest.mark.asyncio
async def test_post_options(client: AsyncClient):
    decision_id = GenerateUuid.as_uuid(1)
    option_dto = OptionIncomingDto(
        name=str(uuid4()),
        utility=0.0,
        decision_id=decision_id,
    )

    response = await client.post("/options", json=[option_dto.model_dump(mode="json")])
    assert response.status_code == 200

    response_content = parse_response_to_dtos_test(response, OptionOutgoingDto)
    assert response_content[0].name == option_dto.name


@pytest.mark.asyncio
async def test_get_options(client: AsyncClient):
    response = await client.get("/options")
    print(response)
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, OptionOutgoingDto)


@pytest.mark.asyncio
async def test_get_option(client: AsyncClient):
    response = await client.get(f"/options/{GenerateUuid.as_string(20)}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, OptionOutgoingDto)


@pytest.mark.asyncio
async def test_update_option(client: AsyncClient):
    option_id = GenerateUuid.as_string(5)
    example_option = parse_response_to_dto_test(
        await client.get(f"/options/{option_id}"), OptionOutgoingDto
    )
    new_name = "new name"
    payload = [
        OptionIncomingDto(
            id=example_option.id,
            name=new_name,
            decision_id=example_option.decision_id,
            utility=example_option.utility,
        ).model_dump(mode="json")
    ]

    response = await client.put("/options", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, OptionOutgoingDto)
    assert response_content[0].name == new_name


@pytest.mark.last
@pytest.mark.asyncio
async def test_delete_option(client: AsyncClient):
    response = await client.delete(f"/options/{GenerateUuid.as_string(2)}")
    assert response.status_code == 200, f"Response content: {response.content}"

@pytest.mark.last
@pytest.mark.asyncio
async def test_delete_options(client: AsyncClient):
    ids = [GenerateUuid.as_string(4), GenerateUuid.as_string(5)]
    response = await client.delete("/options", params={"ids": ids})
    assert response.status_code == 200, f"Response content: {response.content}"

    for id in ids:
        response = await client.get(f"/options/{id}")
        assert response.status_code == 404, f"Option with id: {id} found, but should have been deleted"
