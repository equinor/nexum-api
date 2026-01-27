import pytest
from httpx import AsyncClient
from tests.utils import (
    parse_response_to_dto_test,
    parse_response_to_dtos_test,
)
from src.dtos.utility_dtos import (
    UtilityIncomingDto, 
    UtilityOutgoingDto, 
    DiscreteUtilityIncomingDto
)
from src.seed_database import GenerateUuid
from src.constants import default_value_metric_id


@pytest.mark.asyncio
async def test_get_utilities(client: AsyncClient):
    response = await client.get("/utilities")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, UtilityOutgoingDto)


@pytest.mark.asyncio
async def test_get_utility(client: AsyncClient):
    response = await client.get(f"/utilities/{GenerateUuid.as_string(20)}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, UtilityOutgoingDto)


@pytest.mark.asyncio
async def test_update_utility(client: AsyncClient):
    utility_id = GenerateUuid.as_uuid(1)

    new_value = 100.5
    response = await client.get(f"/utilities/{utility_id}")
    utility: UtilityOutgoingDto = parse_response_to_dto_test(response, UtilityOutgoingDto)
    value_to_update = utility.discrete_utilities[0]
    
    updated_value = DiscreteUtilityIncomingDto(
        id=value_to_update.id,
        utility_id=utility.id,
        utility_value=new_value,
        value_metric_id=default_value_metric_id,
        parent_option_ids=value_to_update.parent_option_ids,
        parent_outcome_ids=value_to_update.parent_outcome_ids,
    )
    
    payload = [
        UtilityIncomingDto(
            id=utility_id, issue_id=GenerateUuid.as_uuid(1),
            discrete_utilities=[updated_value]
        ).model_dump(mode="json")
    ]

    response = await client.put("/utilities", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, UtilityOutgoingDto)
    assert response_content[0].discrete_utilities[0].utility_value == new_value
    assert len(response_content[0].discrete_utilities) == len(utility.discrete_utilities)

@pytest.mark.last
@pytest.mark.asyncio
async def test_delete_utility(client: AsyncClient):
    response = await client.delete(f"/utilities/{GenerateUuid.as_string(2)}")
    assert response.status_code == 200, f"Response content: {response.content}"
