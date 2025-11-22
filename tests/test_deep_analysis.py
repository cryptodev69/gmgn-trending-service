import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_gmgn_client():
    with patch("app.services.deep_analysis_service.gmgn_client") as mock:
        yield mock

def test_deep_analysis_endpoint_success(mock_gmgn_client):
    """Test deep analysis endpoint with successful responses."""
    # Mock token info
    token_info_response = {
        "symbol": "TEST",
        "name": "Test Token",
        "price": 1.5,
        "market_cap": 1000000,
        "liquidity": 50000,
        "volume": 100000,
        "price_change_24h": 5.5,
        "holder_count": 500,
        "created_timestamp": 1234567890
    }
    
    # Mock security info
    security_response = {
        "is_honeypot": False,
        "is_open_source": True,
        "is_mintable": False,
        "owner_address": "0x123...",
        "creator_address": "0x456..."
    }
    
    # Mock top buyers
    top_buyers_response = {
        "top_buyers": [
            {"address": "0xaaa", "amount": 1000},
            {"address": "0xbbb", "amount": 500}
        ]
    }
    
    async def mock_get_token_info(*args, **kwargs):
        return token_info_response
    
    async def mock_get_security_info(*args, **kwargs):
        return security_response
    
    async def mock_get_top_buyers(*args, **kwargs):
        return top_buyers_response
    
    mock_gmgn_client.get_token_info.side_effect = mock_get_token_info
    mock_gmgn_client.get_security_info.side_effect = mock_get_security_info
    mock_gmgn_client.get_top_buyers.side_effect = mock_get_top_buyers
    
    # Call endpoint
    response = client.get("/api/v1/analysis/deep/sol/test_address_123")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["address"] == "test_address_123"
    assert data["chain"] == "sol"
    assert data["market_data"]["symbol"] == "TEST"
    assert data["security"]["is_honeypot"] == False
    assert "top_holders" in data["holders"]

def test_deep_analysis_partial_failure(mock_gmgn_client):
    """Test deep analysis handles partial failures gracefully."""
    token_info_response = {
        "symbol": "TEST",
        "name": "Test Token",
        "price": 1.5
    }
    
    async def mock_get_token_info(*args, **kwargs):
        return token_info_response
    
    async def mock_get_security_info(*args, **kwargs):
        raise Exception("Security API failed")
    
    async def mock_get_top_buyers(*args, **kwargs):
        raise Exception("Top buyers API failed")
    
    mock_gmgn_client.get_token_info.side_effect = mock_get_token_info
    mock_gmgn_client.get_security_info.side_effect = mock_get_security_info
    mock_gmgn_client.get_top_buyers.side_effect = mock_get_top_buyers
    
    # Call endpoint - should still return 200 with partial data
    response = client.get("/api/v1/analysis/deep/sol/test_address_123")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["address"] == "test_address_123"
    assert data["market_data"]["symbol"] == "TEST"
    assert len(data["errors"]) == 2  # Two failed calls
