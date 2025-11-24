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

async def get_momentum_signals(
    chain: str = "sol",
    min_vol_mcap_ratio: float = 0.2, # Volume is 20% of Market Cap
    min_price_change_1h: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Detect tokens with high momentum (Volume/MCap ratio and positive price action).
    Uses 1h trending data source.
    """
    from app.services.analysis_service import get_trending_data_with_cache
    
    # Reuse trending cache to be efficient
    data = await get_trending_data_with_cache("1h", chain)
    
    raw_tokens = []
    if isinstance(data, dict):
        raw_tokens = data.get("tokens") or data.get("rank") or []
        
    signals = []
    
    for token in raw_tokens:
        try:
            market_cap = float(token.get("market_cap") or 0)
            volume_24h = float(token.get("volume") or 0) 
            # Note: GMGN trending often gives 24h volume. 
            # If we want stricter momentum, we'd want shorter timeframe volume, but 24h/MCap is a standard "Turnover" metric.
            
            price_change = float(token.get("price_change_percent") or 0)
            
            if market_cap <= 0:
                continue
                
            vol_mcap_ratio = volume_24h / market_cap
            
            # Filters
            if vol_mcap_ratio < min_vol_mcap_ratio:
                continue
            if price_change < min_price_change_1h:
                continue
                
            signals.append({
                "signal_type": "momentum_breakout",
                "chain": chain,
                "address": token.get("address"),
                "symbol": token.get("symbol"),
                "metrics": {
                    "turnover_ratio": round(vol_mcap_ratio, 2),
                    "price_change_1h": price_change, # Actually might be 24h depending on source, but labelled 1h in trending
                    "volume": volume_24h,
                    "market_cap": market_cap
                },
                "explanation": (
                    f"High momentum detected: Turnover ratio {round(vol_mcap_ratio*100)}% "
                    f"(> {min_vol_mcap_ratio*100}%) with +{round(price_change)}% price action."
                )
            })
            
        except (ValueError, TypeError):
            continue
            
    # Sort by turnover ratio descending (hottest first)
    signals.sort(key=lambda x: x["metrics"]["turnover_ratio"], reverse=True)
    
    return signals
