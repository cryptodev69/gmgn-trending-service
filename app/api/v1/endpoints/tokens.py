from fastapi import APIRouter, HTTPException, Path, Query
from typing import Dict, Any
from app.services.gmgn import gmgn_client

router = APIRouter()

@router.get("/{address}/info", response_model=Dict[str, Any])
async def get_token_info(
    address: str = Path(..., description="Token contract address"),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get info on a token.
    """
    try:
        return await gmgn_client.get_token_info(contract_address=address, chain=chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{address}/price", response_model=Dict[str, Any])
async def get_token_price(
    address: str = Path(..., description="Token contract address"),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get realtime USD price of the token.
    """
    try:
        return await gmgn_client.get_token_usd_price(contract_address=address, chain=chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{address}/top-buyers", response_model=Dict[str, Any])
async def get_top_buyers(
    address: str = Path(..., description="Token contract address"),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get the top buyers of a token.
    """
    try:
        return await gmgn_client.get_top_buyers(contract_address=address, chain=chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{address}/security", response_model=Dict[str, Any])
async def get_security_info(
    address: str = Path(..., description="Token contract address"),
    chain: str = Query("sol", description="Chain to analyze (e.g., sol, eth, base, bsc)")
):
    """
    Get security info about the token.
    """
    try:
        return await gmgn_client.get_security_info(contract_address=address, chain=chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
