from httpx import AsyncClient
import pytest
from app.main import app

@pytest.mark.asyncio
async def test_register_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/register-client", json={"client_name": "TestClient"})
    assert response.status_code == 200
    data = response.json()
    assert "client_id" in data
    assert "client_secret" in data
