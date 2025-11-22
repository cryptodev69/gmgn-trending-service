from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Any, Dict
from app.services.analysis_service import analyze_trending_tokens
from app.services.deep_analysis_service import deep_analyze_token

router = APIRouter()

@router.get("/trending", response_model=List[Dict[str, Any]])
async def get_analysis_trending(
    volume_threshold: float = Query(1000.0, description="Minimum average volume"),
    market_cap_threshold: float = Query(10000.0, description="Minimum median market cap"),
    min_consistency: int = Query(3, description="Minimum number of timeframes the token must appear in"),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get aggregated trending analysis.
    Fetches trending tokens across multiple timeframes (1m, 5m, 1h, 6h, 24h) and finds consistent performers.
    """
    try:
        return await analyze_trending_tokens(
            volume_threshold=volume_threshold,
            market_cap_threshold=market_cap_threshold,
            min_consistency=min_consistency,
            chain=chain
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/deep/{chain}/{address}", response_model=Dict[str, Any])
async def get_deep_analysis(
    chain: str = Path(..., description="Blockchain (e.g., sol, eth, base, bsc)"),
    address: str = Path(..., description="Token contract address")
):
    """
    Perform deep analysis on a specific token.
    Aggregates market data, security info, and holder analysis.
    """
    try:
        return await deep_analyze_token(address=address, chain=chain)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
