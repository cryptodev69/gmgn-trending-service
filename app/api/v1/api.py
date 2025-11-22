from fastapi import APIRouter
from app.api.v1.endpoints import market, tokens, wallets, chain, analysis, signals

api_router = APIRouter()
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
api_router.include_router(wallets.router, prefix="/wallets", tags=["wallets"])
api_router.include_router(chain.router, prefix="/chain", tags=["chain"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
