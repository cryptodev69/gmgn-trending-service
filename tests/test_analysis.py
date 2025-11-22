import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_gmgn_client():
    with patch("app.services.analysis_service.gmgn_client") as mock:
        yield mock

def test_get_analysis_trending(mock_gmgn_client):
    # Mock response for get_trending_tokens (Wrapper format)
    mock_response = {
        "tokens": [
            {
                "id": 1,
                "chain": "sol",
                "address": "token1",
                "symbol": "TKN1",
                "price": 1.0,
                "volume": 50000,
                "market_cap": 500000,
                "price_change_percent": 10,
                "holder_count": 100,
                "top_10_holder_rate": 0.15
            }
        ]
    }
    
    async def async_return(*args, **kwargs):
        return mock_response

    mock_gmgn_client.get_trending_tokens.side_effect = async_return

    response = client.get("/api/v1/analysis/trending?min_consistency=1&volume_threshold=1000&market_cap_threshold=1000")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["symbol"] == "TKN1"
    assert data[0]["consistency_count"] == 5 # appearing in all 5 mocked calls
    assert data[0]["avg_volume"] == 50000.0
    # Assert new fields are passed through
    assert data[0]["holder_count"] == 100
    assert data[0]["top_10_holder_rate"] == 0.15
