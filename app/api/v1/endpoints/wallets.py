from fastapi import APIRouter, HTTPException, Query, Path
from typing import Dict, Any, List
from app.services.gmgn import gmgn_client

router = APIRouter()

@router.get("/trending", response_model=List[Any])
async def get_trending_wallets(
    timeframe: str = Query("7d", regex="^(1d|7d|30d)$"),
    tag: str = Query("smart_degen", description="Wallet tag: pump_smart, smart_degen, reowned, snipe_bot"),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get trending wallets based on a timeframe and wallet tag.
    """
    try:
        return await gmgn_client.get_trending_wallets(timeframe=timeframe, wallet_tag=tag, chain=chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{address}", response_model=Dict[str, Any])
async def get_wallet_info(
    address: str = Path(..., description="Wallet address"),
    period: str = Query("7d", regex="^(7d|30d)$"),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get various information about a wallet address.
    """
    try:
        return await gmgn_client.get_wallet_info(wallet_address=address, period=period, chain=chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
