import pytest
from httpx import AsyncClient
from tests.utils import (
    parse_response_to_dto_test,
    parse_response_to_dtos_test,
)
from src.dtos.decision_dtos import DecisionIncomingDto, DecisionOutgoingDto
from src.dtos.option_dtos import OptionIncomingDto
from src.seed_database import GenerateUuid


@pytest.mark.asyncio
async def test_get_decisions(client: AsyncClient):
    response = await client.get("/decisions")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, DecisionOutgoingDto)


@pytest.mark.asyncio
async def test_get_decision(client: AsyncClient):
    decision_id = GenerateUuid.as_string(20)
    response = await client.get(f"/decisions/{decision_id}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, DecisionOutgoingDto)


@pytest.mark.asyncio
async def test_update_decision(client: AsyncClient):
    decision_id = GenerateUuid.as_uuid(1)
    new_alts = ["yes", "no", "this is testing"]
    new_options = [
        OptionIncomingDto(name=x, utility=0.0, decision_id=decision_id) for x in new_alts
    ]
    payload = [
        DecisionIncomingDto(
            id=decision_id, issue_id=GenerateUuid.as_uuid(1), options=new_options
        ).model_dump(mode="json")
    ]

    response = await client.put("/decisions", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, DecisionOutgoingDto)
    assert len(response_content) > 0, "No decisions returned in response"

    decision = response_content[0]
    assert hasattr(decision, "options"), "Decision does not have options attribute"
    assert decision.options is not None, "Decision options is None"

    # Use set comparison to avoid order dependency
    if len(decision.options) > 0:
        actual_names = [x.name for x in decision.options]
        assert set(actual_names) == set(
            new_alts
        ), f"Expected {set(new_alts)}, got {set(actual_names)}"


@pytest.mark.asyncio
async def test_delete_decision(client: AsyncClient):
    decision_id = GenerateUuid.as_string(2)
    response = await client.delete(f"/decisions/{decision_id}")
    assert response.status_code == 200, f"Response content: {response.content}"
