import pytest
from httpx import AsyncClient
from tests.utils import (
    parse_response_to_dto_test,
    parse_response_to_dtos_test,
)
from src.dtos.discrete_probability_dtos import DiscreteProbabilityOutgoingDto
from src.seed_database import GenerateUuid


@pytest.mark.asyncio
async def test_get_discrete_probabilities(client: AsyncClient):
    response = await client.get("/discrete_probabilities")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, DiscreteProbabilityOutgoingDto)


@pytest.mark.asyncio
async def test_get_discrete_probability(client: AsyncClient):
    first_outcome_prob_id = GenerateUuid.as_string("0_0_op1")
    response = await client.get(f"/discrete_probabilities/{first_outcome_prob_id}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, DiscreteProbabilityOutgoingDto)
