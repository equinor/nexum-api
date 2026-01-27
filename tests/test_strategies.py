import pytest
from uuid import uuid4
from httpx import AsyncClient
from tests.utils import (
    parse_response_to_dto_test,
    parse_response_to_dtos_test,
)
from src.dtos.decision_dtos import DecisionOutgoingDto
from src.dtos.strategy_dtos import (
    StrategyIncomingDto,
    StrategyOutgoingDto,
)
from src.dtos.option_dtos import OptionIncomingDto
from src.seed_database import GenerateUuid

@pytest.mark.first
@pytest.mark.asyncio
async def test_get_strategies(client: AsyncClient):
    response = await client.get("/strategies")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dtos_test(response, StrategyOutgoingDto)


@pytest.mark.first
@pytest.mark.asyncio
async def test_get_strategy(client: AsyncClient):
    response = await client.get(f"/strategies/{GenerateUuid.as_string(1)}")
    assert response.status_code == 200, f"Response content: {response.content}"

    parse_response_to_dto_test(response, StrategyOutgoingDto)


@pytest.mark.first
@pytest.mark.asyncio
async def test_create_strategy(client: AsyncClient):
    test_strategy_id = GenerateUuid.as_uuid(5)
    test_option_id = GenerateUuid.as_uuid(5)
    payload = [
        StrategyIncomingDto(
            id=test_strategy_id,
            project_id=GenerateUuid.as_uuid(5),
            name=str(uuid4()),
            description="Test strategy description",
            rationale="Test strategy rationale",
            options=[
                OptionIncomingDto(
                    id=test_option_id,
                    decision_id=GenerateUuid.as_uuid("test_decision_issue_1"),
                    name=str(uuid4()),
                    utility=50.0,
                )
            ],
        ).model_dump(mode="json")
    ]

    response = await client.post("/strategies", json=payload)
    response_content = parse_response_to_dtos_test(response, StrategyOutgoingDto)
    assert response.status_code == 200, f"Response content: {response.content}"
    assert len(response_content[0].options) == 1
    assert response_content[0].options[0].id == test_option_id

    parse_response_to_dtos_test(response, StrategyOutgoingDto)


@pytest.mark.first
@pytest.mark.asyncio
async def test_update_strategy(client: AsyncClient):
    new_name = str(uuid4())
    new_description = "Updated strategy description"
    new_rationale = "Updated strategy rationale"
    test_strategy_id = GenerateUuid.as_uuid(1001)
    test_option_id = GenerateUuid.as_uuid(2)

    get_response = await client.get(f"/strategies/{test_strategy_id}")

    strat_to_update = parse_response_to_dto_test(get_response, StrategyOutgoingDto)
    existing_option = strat_to_update.options[0]

    options=[
        OptionIncomingDto(
            id=existing_option.id,
            decision_id=existing_option.decision_id,
            name=existing_option.name,
            utility=existing_option.utility,
        ),
        OptionIncomingDto(
            id=test_option_id,
            decision_id=test_strategy_id,
            name="Updated Test Option",
            utility=75.0,
        )
    ]

    payload = [
        StrategyIncomingDto(
            id=strat_to_update.id,
            project_id=strat_to_update.project_id,
            name=new_name,
            description=new_description,
            rationale=new_rationale,
            options=options,
        ).model_dump(mode="json")
    ]
    response = await client.put("/strategies", json=payload)
    assert response.status_code == 200, f"Response content: {response.content}"

    response_content = parse_response_to_dtos_test(response, StrategyOutgoingDto)
    assert response_content[0].name == new_name
    assert response_content[0].description == new_description
    assert response_content[0].rationale == new_rationale
    assert response_content[0].options.__len__() == len(options)
    # test that the option was not updated
    assert response_content[0].options[1].name != options[1].name


@pytest.mark.last
@pytest.mark.asyncio
async def test_delete_strategy(client: AsyncClient):
    response = await client.delete(f"/strategies/{GenerateUuid.as_string(8)}")
    assert response.status_code == 200, f"Response content: {response.content}"
