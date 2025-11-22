import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_gmgn_client():
    with patch("app.services.analysis_service.gmgn_client") as mock:
        yield mock

def test_get_analysis_trending_multi_chain(mock_gmgn_client):
    # Mock response for get_trending_tokens
    mock_response = {
        "tokens": [
            {
                "id": 1,
                "chain": "eth",
                "address": "0x123...",
                "symbol": "PEPE",
                "price": 1.0,
                "volume": 50000,
                "market_cap": 500000,
                "price_change_percent": 10
            }
        ]
    }
    
    async def async_return(*args, **kwargs):
        # Verify the chain argument was passed
        assert kwargs.get("chain") == "eth"
        return mock_response

    mock_gmgn_client.get_trending_tokens.side_effect = async_return

    # Call endpoint with chain=eth
    response = client.get("/api/v1/analysis/trending?chain=eth&min_consistency=1&volume_threshold=1000&market_cap_threshold=1000")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["chain"] == "eth"
    assert data[0]["symbol"] == "PEPE"
