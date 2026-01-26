import pytest
import uuid
from httpx import AsyncClient
from tests.utils import (
    parse_response_to_dto_test,
    parse_response_to_dtos_test,
)
from src.dtos.uncertainty_dtos import UncertaintyIncomingDto, UncertaintyOutgoingDto
from src.dtos.outcome_dtos import OutcomeIncomingDto
from src.dtos.discrete_probability_dtos import DiscreteProbabilityIncomingDto
from src.seed_database import GenerateUuid


@pytest.mark.asyncio
async def test_get_uncertainties(client: AsyncClient):
    response = await client.get("/uncertainties")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, UncertaintyOutgoingDto)


@pytest.mark.asyncio
async def test_get_uncertainty(client: AsyncClient):
    response = await client.get(f"/uncertainties/{GenerateUuid.as_string(20)}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, UncertaintyOutgoingDto)


@pytest.mark.asyncio
async def test_update_uncertainty(client: AsyncClient):
    uncert_id = GenerateUuid.as_uuid(1)
    new_outcome_id = uuid.uuid4()
    new_outcomes = [
        OutcomeIncomingDto(
            id=new_outcome_id,
            name=str(new_outcome_id),
            utility=0,
            uncertainty_id=uncert_id,
        )
    ]
    payload = [
        UncertaintyIncomingDto(
            id=uncert_id,
            issue_id=GenerateUuid.as_uuid(1),
            outcomes=new_outcomes,
        ).model_dump(mode="json")
    ]

    response = await client.put("/uncertainties", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, UncertaintyOutgoingDto)
    assert response_content[0].outcomes[0].name == new_outcomes[0].name


@pytest.mark.asyncio
async def test_update_probability(client: AsyncClient):
    # First, get all uncertainties to find one with discrete_probabilities
    response = await client.get("/uncertainties")
    assert response.status_code == 200, f"Response content: {response.content}"

    uncertainties = parse_response_to_dtos_test(response, UncertaintyOutgoingDto)

    # Find an uncertainty that has discrete_probabilities
    uncertainty = None
    for u in uncertainties:
        if u.discrete_probabilities and len(u.discrete_probabilities) > 0:
            uncertainty = u
            break

    assert uncertainty is not None, "No uncertainty with discrete_probabilities found"

    new_probability = 0.6

    # Build ALL discrete probabilities, updating only the first one's probability
    all_updated_probs = [
        DiscreteProbabilityIncomingDto(
            id=prob.id,
            uncertainty_id=uncertainty.id,
            probability=new_probability if i == 0 else prob.probability,
            outcome_id=prob.outcome_id,
            parent_option_ids=prob.parent_option_ids or [],
            parent_outcome_ids=prob.parent_outcome_ids or [],
        )
        for i, prob in enumerate(uncertainty.discrete_probabilities)
    ]

    payload = [
        UncertaintyIncomingDto(
            id=uncertainty.id,
            issue_id=uncertainty.issue_id,
            outcomes=[
                OutcomeIncomingDto(
                    id=x.id, name=x.name, uncertainty_id=x.uncertainty_id, utility=x.utility
                )
                for x in uncertainty.outcomes
            ],
            is_key=uncertainty.is_key,
            discrete_probabilities=all_updated_probs,
        ).model_dump(mode="json")
    ]

    response = await client.put("/uncertainties", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, UncertaintyOutgoingDto)
    assert response_content[0].discrete_probabilities[0].probability == new_probability
    assert len(response_content[0].discrete_probabilities) == len(
        uncertainty.discrete_probabilities
    )


@pytest.mark.last
@pytest.mark.asyncio
async def test_delete_uncertainty(client: AsyncClient):
    response = await client.delete(f"/uncertainties/{GenerateUuid.as_string(2)}")
    assert response.status_code == 200, f"Response content: {response.content}"
