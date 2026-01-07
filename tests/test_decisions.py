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
    # Clear any potential session state
    await client.get("/health")  # Simple endpoint to reset session state

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
    # Use completely unique IDs for this test
    decision_id = GenerateUuid.as_uuid(1)  # Changed from "update_test_decision"
    issue_id = GenerateUuid.as_uuid(1)  # Changed from "update_test_issue"

    new_alts = ["option_a", "option_b", "option_c"]
    new_options = [
        OptionIncomingDto(name=x, utility=0.5, decision_id=decision_id) for x in new_alts
    ]

    payload = [
        DecisionIncomingDto(id=decision_id, issue_id=issue_id, options=new_options).model_dump(
            mode="json"
        )
    ]

    response = await client.put("/decisions", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, DecisionOutgoingDto)
    assert len(response_content) > 0, "No decisions returned in response"

    decision = response_content[0]
    assert hasattr(decision, "options"), "Decision does not have options attribute"
    assert decision.options is not None, "Decision options is None"

    if len(decision.options) > 0:
        actual_names = [x.name for x in decision.options]
        assert set(actual_names) == set(new_alts), f"Expected {new_alts}, got {actual_names}"


@pytest.mark.asyncio
async def test_delete_decision(client: AsyncClient):
    decision_id = GenerateUuid.as_string("delete_test_decision")
    response = await client.delete(f"/decisions/{decision_id}")
    assert response.status_code == 200, f"Response content: {response.content}"
