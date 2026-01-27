from httpx import AsyncClient
import pytest
from src.seed_database import GenerateUuid

@pytest.mark.first
@pytest.mark.asyncio
async def test_post_project_dupllication(client: AsyncClient):
    response = await client.post(f"/project/duplicate/{GenerateUuid.as_string(1)}")
    assert response.status_code == 200, f"Response content: {response.content}"
