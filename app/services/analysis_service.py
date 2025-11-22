import asyncio
import pandas as pd
from typing import List, Dict, Any
from app.services.gmgn import gmgn_client
from app.services.cache import get_cached, set_cached

async def get_trending_data_with_cache(timeframe: str, chain: str) -> Dict[str, Any]:
    """Fetch trending data with caching."""
    cache_key = f"trending_tokens:{chain}:{timeframe}"
    cached_data = get_cached(cache_key)
    
    if cached_data:
        return cached_data
        
    data = await gmgn_client.get_trending_tokens(timeframe=timeframe, chain=chain)
    set_cached(cache_key, data)
    return data

async def analyze_trending_tokens(
    volume_threshold: float = 1000.0,
    market_cap_threshold: float = 10000.0,
    min_consistency: int = 3,
    chain: str = "sol"
) -> List[Dict[str, Any]]:
    """
    Analyzes trending tokens across multiple timeframes to find consistent performers.
    
    Args:
        volume_threshold: Minimum average volume to filter.
        market_cap_threshold: Minimum median market cap to filter.
        min_consistency: Minimum number of timeframes the token must appear in.
        chain: Blockchain to analyze (sol, eth, base, bsc, etc.).
        
    Returns:
        List of dictionaries containing aggregated token metrics.
    """
    timeframes = ["1m", "5m", "1h", "6h", "24h"]
    data = []

    # Fetch data concurrently
    tasks = [get_trending_data_with_cache(timeframe=tf, chain=chain) for tf in timeframes]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for tf, result in zip(timeframes, results):
        if isinstance(result, Exception):
            print(f"Error fetching timeframe {tf}: {result}")
            continue
        
        # The Wrapper returns {"tokens": [...]}
        # The original GMGN API returned {"rank": [...]} (inside data)
        # We handle both or prioritize wrapper structure
        tokens = result.get("tokens") or result.get("rank") or []
        
        for token in tokens:
            # Safely get numeric values
            try:
                price = float(token.get("price") or 0)
                volume = float(token.get("volume") or 0)
                mcap = float(token.get("market_cap") or 0)
                p_change = float(token.get("price_change_percent") or 0)
            except (ValueError, TypeError):
                continue

            data.append({
                "id": token.get("id"),
                "chain": token.get("chain") or chain, # Wrapper might include chain, fallback to arg
                "address": token.get("address"),
                "symbol": token.get("symbol"),
                "price": price,
                "volume": volume,
                "market_cap": mcap,
                "timeframe": tf,
                "price_change": p_change,
                # Extra fields from Wrapper
                "holder_count": token.get("holder_count"),
                "top_10_holder_rate": token.get("top_10_holder_rate"),
                "renounced_mint": token.get("renounced_mint"),
                "renounced_freeze_account": token.get("renounced_freeze_account"),
                "burn_ratio": token.get("burn_ratio"),
                "launchpad": token.get("launchpad"),
                "bluechip_owner_percentage": token.get("bluechip_owner_percentage")
            })

    if not data:
        return []

    df = pd.DataFrame(data)
    
    if df.empty:
        return []

    # Group by token address and aggregate metrics
    grouped = df.groupby("address").agg({
         "id": "first",
         "chain": "first",
         "symbol": "first",
         "price": "mean",
         "volume": "mean",
         "market_cap": "median",
         "timeframe": "nunique",
         "price_change": "mean",
         # Take the max/latest values for these status fields
         "holder_count": "max",
         "top_10_holder_rate": "max", 
         "renounced_mint": "max",
         "renounced_freeze_account": "max",
         "burn_ratio": "max",
         "launchpad": "first",
         "bluechip_owner_percentage": "max"
    }).rename(columns={
         "timeframe": "consistency_count",
         "price": "avg_price",
         "volume": "avg_volume",
         "market_cap": "median_market_cap",
         "price_change": "avg_price_change"
    })

    # Apply filters
    filtered = grouped[
        (grouped["consistency_count"] >= min_consistency) &
        (grouped["avg_volume"] >= volume_threshold) &
        (grouped["median_market_cap"] >= market_cap_threshold)
    ]

    # Sort by consistency count and then by average volume
    filtered = filtered.sort_values(by=["consistency_count", "avg_volume"], ascending=False).reset_index()
    
    # Convert to list of dicts
    return filtered.to_dict(orient="records")
