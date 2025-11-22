from typing import List, Dict, Any
import time
from app.services.gmgn import gmgn_client

async def get_pump_graduation_signals(
    chain: str = "sol",
    min_progress: float = 95.0,
    max_progress: float = 100.0,
    min_holders: int = 50
) -> List[Dict[str, Any]]:
    """
    Detect tokens nearing bonding curve completion (graduation).
    
    Args:
        chain: Blockchain to scan (primarily 'sol' for pump.fun).
        min_progress: Minimum bonding curve progress % (e.g., 95.0).
        max_progress: Maximum bonding curve progress % (e.g., 100.0).
        min_holders: Minimum holder count to filter out dead tokens.
        
    Returns:
        List of signal objects with explanation.
    """
    # Fetch data from wrapper
    # Wrapper endpoint: /api/{chain}/tokens-by-completion?limit=50
    data = await gmgn_client.get_tokens_by_completion(limit=50, chain=chain)
    
    raw_tokens = []
    if isinstance(data, dict):
        raw_tokens = data.get("tokens") or data.get("rank") or []
    elif isinstance(data, list):
        raw_tokens = data
        
    signals = []
    
    for token in raw_tokens:
        # Extract metrics
        try:
            progress_raw = token.get("progress")
            if progress_raw is None:
                continue
            progress = float(progress_raw) * 100 if float(progress_raw) <= 1.0 else float(progress_raw)
            
            holder_count = int(token.get("holder_count") or 0)
            
            # Filter
            if not (min_progress <= progress <= max_progress):
                continue
            if holder_count < min_holders:
                continue
                
            # Create Signal Object
            signals.append({
                "signal_type": "pump_graduation",
                "chain": chain,
                "address": token.get("address"),
                "symbol": token.get("symbol"),
                "metrics": {
                    "progress_pct": round(progress, 2),
                    "holder_count": holder_count,
                    "sniper_count": token.get("sniper_count", 0),
                    "market_cap": token.get("market_cap")
                },
                "explanation": (
                    f"Token is {round(progress, 2)}% through bonding curve "
                    f"(Threshold: {min_progress}-{max_progress}%) with {holder_count} holders. "
                    f"Imminent graduation to DEX expected."
                )
            })
            
        except (ValueError, TypeError):
            continue
            
    return signals

async def get_early_gem_signals(
    chain: str = "sol",
    min_liquidity: float = 5000.0,
    max_age_minutes: int = 60
) -> List[Dict[str, Any]]:
    """
    Detect highly liquid new pairs (Early Gems).
    
    Args:
        chain: Blockchain to scan.
        min_liquidity: Minimum liquidity in USD.
        max_age_minutes: Maximum age in minutes since open.
        
    Returns:
        List of signal objects with explanation.
    """
    # Fetch data
    data = await gmgn_client.get_new_pairs(limit=50, chain=chain)
    
    raw_pairs = []
    if isinstance(data, dict):
        raw_pairs = data.get("pairs") or data.get("tokens") or []
    elif isinstance(data, list):
        raw_pairs = data
        
    signals = []
    now = time.time()
    
    for pair in raw_pairs:
        try:
            open_ts = pair.get("open_timestamp") or pair.get("creation_timestamp")
            if not open_ts:
                continue
                
            age_minutes = (now - int(open_ts)) / 60
            liquidity = float(pair.get("liquidity") or 0)
            
            # Filter
            if age_minutes > max_age_minutes:
                continue
            if liquidity < min_liquidity:
                continue
                
            # Create Signal Object
            signals.append({
                "signal_type": "early_gem",
                "chain": chain,
                "address": pair.get("address"),
                "symbol": pair.get("symbol"),
                "metrics": {
                    "age_minutes": round(age_minutes, 1),
                    "liquidity": liquidity,
                    "initial_liquidity": pair.get("initial_liquidity"),
                    "bot_degen_count": pair.get("bot_degen_count", 0) # ETH specific often
                },
                "explanation": (
                    f"New pair launched {round(age_minutes, 1)}m ago with high liquidity "
                    f"(${liquidity:,.0f} > ${min_liquidity:,.0f}). "
                    f"Potential strong launch."
                )
            })
            
        except (ValueError, TypeError):
            continue
            
    return signals
