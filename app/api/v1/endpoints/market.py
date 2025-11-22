from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.services.gmgn import gmgn_client

router = APIRouter()

@router.get("/pairs/new", response_model=List[Any])
async def get_new_pairs(
    limit: int = Query(50, le=50, description="Limit number of pairs (max 50)"),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get new pairs.
    """
    try:
        return await gmgn_client.get_new_pairs(limit=limit, chain=chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tokens/trending", response_model=Dict[str, Any])
async def get_trending_tokens(
    timeframe: str = Query("1h", regex="^(1m|5m|1h|6h|24h)$", description="Timeframe for trending tokens"),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get trending tokens for a specific timeframe.
    """
    try:
        return await gmgn_client.get_trending_tokens(timeframe=timeframe, chain=chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tokens/pump-completion", response_model=List[Any])
async def get_tokens_by_completion(
    limit: int = Query(50, le=50),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get tokens by bonding curve completion progress.
    """
    try:
        return await gmgn_client.get_tokens_by_completion(limit=limit, chain=chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tokens/sniped", response_model=List[Any])
async def get_sniped_tokens(
    size: int = Query(10, le=39),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get recently sniped tokens.
    """
    try:
        return await gmgn_client.find_sniped_tokens(size=size, chain=chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
