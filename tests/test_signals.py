import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_gmgn_client():
    with patch("app.services.signals_service.gmgn_client") as mock:
        yield mock

def test_pump_graduation_signal(mock_gmgn_client):
    # Mock data for tokens-by-completion
    mock_response = {
        "tokens": [
            # Should pass (96% progress)
            {
                "address": "valid_token",
                "symbol": "GRAD",
                "progress": "0.96",
                "holder_count": 100,
                "market_cap": 50000,
                "sniper_count": 5
            },
            # Should fail (progress too low)
            {
                "address": "low_progress_token",
                "symbol": "LOW",
                "progress": "0.50",
                "holder_count": 100
            },
            # Should fail (holders too low)
            {
                "address": "dead_token",
                "symbol": "DEAD",
                "progress": "0.99",
                "holder_count": 10
            }
        ]
    }
    
    async def async_return(*args, **kwargs):
        return mock_response
        
    mock_gmgn_client.get_tokens_by_completion.side_effect = async_return
    
    response = client.get("/api/v1/signals/pump-graduation?min_progress=90")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["symbol"] == "GRAD"
    assert data[0]["metrics"]["progress_pct"] == 96.0
    assert "explanation" in data[0]

def test_early_gem_signal(mock_gmgn_client):
    import time
    now = time.time()
    
    # Mock data for new-pairs
    mock_response = {
        "pairs": [
            # Should pass (high liq, recent)
            {
                "address": "gem_token",
                "symbol": "GEM",
                "liquidity": 10000,
                "open_timestamp": now - 600, # 10 mins ago
                "initial_liquidity": 5000
            },
            # Should fail (low liq)
            {
                "address": "dust_token",
                "symbol": "DUST",
                "liquidity": 100,
                "open_timestamp": now - 600
            },
            # Should fail (too old)
            {
                "address": "old_token",
                "symbol": "OLD",
                "liquidity": 50000,
                "open_timestamp": now - 7200 # 2 hours ago
            }
        ]
    }
    
    async def async_return(*args, **kwargs):
        return mock_response
        
    mock_gmgn_client.get_new_pairs.side_effect = async_return
    
    response = client.get("/api/v1/signals/early-gems?min_liquidity=5000&max_age_minutes=60")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["symbol"] == "GEM"
    assert data[0]["metrics"]["age_minutes"] < 60
    assert "explanation" in data[0]
