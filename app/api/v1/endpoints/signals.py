from fastapi import APIRouter, HTTPException, Query
from typing import List, Any, Dict
from app.services.signals_service import get_pump_graduation_signals, get_early_gem_signals

router = APIRouter()

@router.get("/pump-graduation", response_model=List[Dict[str, Any]])
async def get_graduation_signals(
    chain: str = Query("sol", description="Blockchain (primarily 'sol' for pump.fun)"),
    min_progress: float = Query(95.0, description="Minimum bonding curve progress %"),
    max_progress: float = Query(100.0, description="Maximum bonding curve progress %"),
    min_holders: int = Query(50, description="Minimum holder count")
):
    """
    Graduation Radar: Detect tokens about to complete their bonding curve (e.g., Pump.fun -> Raydium).
    """
    try:
        return await get_pump_graduation_signals(
            chain=chain,
            min_progress=min_progress,
            max_progress=max_progress,
            min_holders=min_holders
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/early-gems", response_model=List[Dict[str, Any]])
async def get_gem_signals(
    chain: str = Query("sol", description="Blockchain (sol, eth, base, bsc)"),
    min_liquidity: float = Query(5000.0, description="Minimum liquidity in USD"),
    max_age_minutes: int = Query(60, description="Maximum age in minutes")
):
    """
    Early Gem Detection: Find newly listed pairs with high initial liquidity.
    """
    try:
        return await get_early_gem_signals(
            chain=chain,
            min_liquidity=min_liquidity,
            max_age_minutes=max_age_minutes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
