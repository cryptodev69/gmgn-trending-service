from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from app.services.gmgn import gmgn_client

router = APIRouter()

@router.get("/gas", response_model=Dict[str, Any])
async def get_gas_fee(chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")):
    """
    Get the current gas fee price.
    """
    try:
        return await gmgn_client.get_gas_fee(chain=chain)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
