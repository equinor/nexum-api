import pytest
from uuid import uuid4
from httpx import AsyncClient
from tests.utils import (
    parse_response_to_dto_test,
    parse_response_to_dtos_test,
)
from src.constants import (
    Type,
    Boundary,
)
from src.dtos.issue_dtos import IssueIncomingDto, IssueOutgoingDto
from src.dtos.decision_dtos import DecisionIncomingDto
from src.dtos.uncertainty_dtos import UncertaintyIncomingDto
from src.dtos.node_dtos import NodeIncomingDto
from src.dtos.node_style_dtos import NodeStyleIncomingDto
from src.dtos.option_dtos import OptionIncomingDto
from src.dtos.outcome_dtos import OutcomeIncomingDto
from src.seed_database import GenerateUuid


@pytest.mark.asyncio
async def test_get_issues(client: AsyncClient):
    response = await client.get("/issues")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, IssueOutgoingDto)


@pytest.mark.asyncio
async def test_get_issue(client: AsyncClient):
    response = await client.get(f"/issues/{GenerateUuid.as_string(20)}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, IssueOutgoingDto)


@pytest.mark.asyncio
async def test_create_issue(client: AsyncClient):
    scenario_id = GenerateUuid.as_uuid(4)
    decision_id = uuid4()
    alternatives = ["alt1", "alt2"]

    options = [
        OptionIncomingDto(name=alt, decision_id=decision_id, utility=0) for alt in alternatives
    ]
    x_position = 600
    node = NodeIncomingDto(
        scenario_id=scenario_id,
        issue_id=uuid4(),
        node_style=NodeStyleIncomingDto(
            node_id=uuid4(), x_position=x_position,
        ),
    )
    issue = IssueIncomingDto(
        decision=DecisionIncomingDto(id=decision_id, issue_id=uuid4(), options=options),
        scenario_id=scenario_id,
        type=Type.DECISION,
        boundary=Boundary.OUT,
        order=2,
        node=node,
        uncertainty=None,
        utility=None,
    )
    payload = [issue.model_dump(mode="json")]

    response = await client.post("/issues", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"
    response_content = parse_response_to_dtos_test(response, IssueOutgoingDto)
    r = response_content[0]

    assert r.decision is not None and [option.name for option in r.decision.options] == alternatives
    assert (
        r.node is not None
        and r.node.node_style is not None
        and r.node.node_style.x_position == x_position
    )
    assert r.decision.issue_id == issue.id
    assert r.node.issue_id == issue.id
    assert r.node.node_style.node_id == r.node.id


@pytest.mark.asyncio
async def test_update_issue(client: AsyncClient):
    issue_id = GenerateUuid.as_string(3)
    example_issue = parse_response_to_dto_test(
        await client.get(f"/issues/{issue_id}"), IssueOutgoingDto
    )
    if example_issue.decision is None or example_issue.uncertainty is None:
        raise Exception("example_issue.decision should not be None")
    node = NodeIncomingDto(
        scenario_id=example_issue.scenario_id,
        id=example_issue.node.id,
        issue_id=example_issue.id,
        node_style=None,
    )

    new_alternatives = ["yes", "no", "this is testing issue update"]
    new_options = [
        OptionIncomingDto(name=x, utility=0, decision_id=example_issue.decision.id)
        for x in new_alternatives
    ]
    new_outcomes_names = ["A", "B", "C"]
    new_outcomes = [
        OutcomeIncomingDto(
            name=outcome, uncertainty_id=example_issue.uncertainty.id, utility=0
        )
        for outcome in new_outcomes_names
    ]

    new_type = Type.UNCERTAINTY
    new_boundary = Boundary.IN
    payload = [
        IssueIncomingDto(
            id=example_issue.id,
            scenario_id=example_issue.scenario_id,
            type=new_type,
            boundary=new_boundary,
            order=0,
            node=node,
            decision=DecisionIncomingDto(
                id=example_issue.decision.id, issue_id=example_issue.id, options=new_options
            ),
            uncertainty=UncertaintyIncomingDto(
                id=example_issue.uncertainty.id, issue_id=example_issue.id, outcomes=new_outcomes,
            ),
            utility=None,
        ).model_dump(mode="json")
    ]

    response = await client.put("/issues", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, IssueOutgoingDto)
    r = response_content[0]

    assert r.uncertainty is not None and [x.name for x in r.uncertainty.outcomes] == new_outcomes_names
    assert r.decision is not None and [x.name for x in r.decision.options] == new_alternatives
    assert r.type == new_type


@pytest.mark.asyncio
async def test_delete_issue(client: AsyncClient):
    issue_id = GenerateUuid.as_string(3)
    response = await client.delete(f"/issues/{issue_id}")

    assert response.status_code == 200, f"Response content: {response.content}"


@pytest.mark.asyncio
async def test_delete_issues(client: AsyncClient):
    ids = [GenerateUuid.as_string(14), GenerateUuid.as_string(15)]
    response = await client.delete("/issues", params={"ids": ids})
    assert response.status_code == 200, f"Response content: {response.content}"

    for id in ids:
        response = await client.get(f"/issues/{id}")
        assert (
            response.status_code == 404
        ), f"Issue with id: {id} found, but should have been deleted"
